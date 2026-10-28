[CmdletBinding()]
param(
    [ValidatePattern('^[A-Za-z0-9_.-]+$')]
    [string]$AvdName = 'Checkmate_Pleos_API_34',
    [string]$SdkPath = "$env:LOCALAPPDATA\Android\Sdk",
    [string]$JavaHome = "$env:ProgramFiles\Android\Android Studio\jbr",
    [ValidateSet('ollama', 'reviewed')]
    [string]$GenerationMode = 'ollama',
    [string]$OllamaModel = 'qwen2.5:7b',
    [ValidateRange(30, 900)]
    [int]$BootTimeoutSeconds = 300,
    [switch]$SkipBuild,
    [switch]$CheckOnly
)

# Windows PowerShell 5.1 compatible. Logs and downloaded tools stay out of Git.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$backend = Join-Path $repo 'backend'
$android = Join-Path $repo 'android'
$logs = Join-Path $repo '.local\logs'
$adb = Join-Path $SdkPath 'platform-tools\adb.exe'
$emulator = Join-Path $SdkPath 'emulator\emulator.exe'
$apk = Join-Path $android 'app\build\outputs\apk\debug\app-debug.apk'

function Run-Tool([string]$Tool, [string[]]$Arguments) {
    $result = & $Tool @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Tool failed ($LASTEXITCODE): $($Arguments -join ' ')" }
    return $result
}

function Get-Json([string]$Url) {
    try { Invoke-RestMethod -Uri $Url -TimeoutSec 3 } catch { return $null }
}

function Wait-Ready([scriptblock]$Probe, [string]$Label, [int]$Seconds = 60) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        if (& $Probe) { return }
        Start-Sleep -Seconds 2
    } while ((Get-Date) -lt $deadline)
    throw "Timed out waiting for $Label. See $logs"
}

function Find-Avd {
    $devices = @(Run-Tool $adb @('devices'))
    foreach ($line in $devices) {
        if ($line -match '^(emulator-\d+)\s+device\b') {
            $candidate = $Matches[1]
            $name = @(Run-Tool $adb @('-s', $candidate, 'emu', 'avd', 'name'))
            if ($name -contains $AvdName) { $candidate }
        }
    }
}

function Test-Backend {
    $health = Get-Json 'http://127.0.0.1:8000/health'
    $schema = Get-Json 'http://127.0.0.1:8000/openapi.json'
    return ($health.status -eq 'ok' -and $schema.info.title -eq 'CHECKMATE Manual API')
}

function Test-Console {
    try {
        $page = Invoke-WebRequest 'http://127.0.0.1:8088/' -UseBasicParsing -TimeoutSec 3
        return ($page.StatusCode -eq 200 -and $page.Content -match 'Pleos')
    } catch { return $false }
}

try {
    if (!(Test-Path -LiteralPath $adb)) { throw "Android platform-tools missing: $adb. Set -SdkPath." }
    $serials = @(Find-Avd)
    if ($serials.Count -gt 1) { throw "Multiple instances of $AvdName are running. Keep one instance." }
    $serial = if ($serials.Count) { $serials[0] } else { $null }

    if ($CheckOnly) {
        if (!$serial) { throw "AVD $AvdName is not running. Run this script without -CheckOnly." }
        if ((Run-Tool $adb @('-s', $serial, 'shell', 'getprop', 'sys.boot_completed')) -ne '1') {
            throw 'Pleos has not finished booting.'
        }
        $forwards = @(Run-Tool $adb @('forward', '--list'))
        if (!($forwards -match "^$serial\s+tcp:8088\s+tcp:8088$")) { throw 'Pleos console forwarding is missing. Run without -CheckOnly.' }
        $reverses = @(Run-Tool $adb @('-s', $serial, 'reverse', '--list'))
        if (!($reverses -match '\s+tcp:8000\s+tcp:8000$')) { throw 'Backend reverse forwarding is missing. Run without -CheckOnly.' }
    } else {
        New-Item -Path $logs -ItemType Directory -Force | Out-Null
        if (!$serial) {
            if (!(Test-Path -LiteralPath $emulator)) { throw "Android emulator missing: $emulator" }
            if (!(@(Run-Tool $emulator @('-list-avds')) -contains $AvdName)) {
                throw "AVD $AvdName is not installed. Create the official Pleos AVD or set -AvdName."
            }
            $busyPorts = @(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty LocalPort)
            $port = @(5554..5584 | Where-Object { $_ % 2 -eq 0 -and $_ -notin $busyPorts -and ($_ + 1) -notin $busyPorts })[0]
            if (!$port) { throw 'No free emulator port pair.' }
            $serial = "emulator-$port"
            Write-Host "Starting Pleos ($AvdName)..."
            # Visible window is intentional: this launcher opens the requested vehicle app.
            Start-Process -FilePath $emulator -ArgumentList @('-avd', $AvdName, '-port', $port, '-no-snapshot', '-memory', '4096', '-no-boot-anim') `
                -RedirectStandardOutput "$logs\pleos-out.log" -RedirectStandardError "$logs\pleos-error.log" | Out-Null
        } else { Write-Host "Reusing Pleos: $serial" }
        Wait-Ready {
            try {
                $state = & $adb -s $serial shell getprop sys.boot_completed 2>$null
                $LASTEXITCODE -eq 0 -and $state -eq '1'
            } catch { $false }
        } 'Pleos boot' $BootTimeoutSeconds

        $uv = (Get-Command uv -ErrorAction Stop).Source
        Push-Location $backend
        try { Run-Tool $uv @('sync', '--locked') | Out-Host } finally { Pop-Location }

        if ($GenerationMode -eq 'ollama') {
            $tags = Get-Json 'http://127.0.0.1:11434/api/tags'
            if (!$tags) {
                $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
                $ollama = if ($ollamaCommand) { $ollamaCommand.Source } else { "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" }
                if (!(Test-Path -LiteralPath $ollama)) { throw 'Ollama is missing. Install it or use -GenerationMode reviewed.' }
                Start-Process -FilePath $ollama -ArgumentList 'serve' -WindowStyle Hidden `
                    -RedirectStandardOutput "$logs\ollama-out.log" -RedirectStandardError "$logs\ollama-error.log" | Out-Null
                Wait-Ready { $null -ne (Get-Json 'http://127.0.0.1:11434/api/tags') } 'Ollama'
                $tags = Get-Json 'http://127.0.0.1:11434/api/tags'
            }
            if ($OllamaModel -notin @($tags.models.name)) {
                throw "Model $OllamaModel is missing. Run: ollama pull $OllamaModel"
            }
        }

        if (Test-Backend) {
            Write-Host 'Reusing CHECKMATE backend on port 8000.'
        } else {
            if (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue) {
                throw 'Port 8000 is occupied by a service that is not a healthy CHECKMATE API. Nothing was stopped.'
            }
            $savedMode = $env:CHECKMATE_GENERATION
            $savedModel = $env:OLLAMA_MODEL
            $savedBase = $env:OLLAMA_BASE_URL
            try {
                $env:CHECKMATE_GENERATION = $GenerationMode
                $env:OLLAMA_MODEL = $OllamaModel
                $env:OLLAMA_BASE_URL = 'http://127.0.0.1:11434'
                Start-Process -FilePath "$backend\.venv\Scripts\python.exe" -WorkingDirectory $backend -WindowStyle Hidden `
                    -ArgumentList @('-m', 'uvicorn', 'checkmate.main:app', '--host', '127.0.0.1', '--port', '8000') `
                    -RedirectStandardOutput "$logs\backend-out.log" -RedirectStandardError "$logs\backend-error.log" | Out-Null
            } finally {
                $env:CHECKMATE_GENERATION = $savedMode
                $env:OLLAMA_MODEL = $savedModel
                $env:OLLAMA_BASE_URL = $savedBase
            }
            Wait-Ready { Test-Backend } 'CHECKMATE backend'
        }
        $mode = (Get-Json 'http://127.0.0.1:8000/health').generationMode
        if ($mode -ne $GenerationMode) { throw "Existing backend mode is $mode, requested $GenerationMode. Restart that backend explicitly or match -GenerationMode." }

        $forwards = @(Run-Tool $adb @('forward', '--list'))
        if ($forwards | Where-Object { $_ -match '\s+tcp:8088\s+' -and $_ -notmatch "^$serial\s+tcp:8088\s+tcp:8088$" }) {
            throw 'Port 8088 is forwarded to another target. Existing mapping was preserved.'
        }
        if (!($forwards -match "^$serial\s+tcp:8088\s+tcp:8088$")) {
            Run-Tool $adb @('-s', $serial, 'forward', '--no-rebind', 'tcp:8088', 'tcp:8088') | Out-Host
        }
        $reverses = @(Run-Tool $adb @('-s', $serial, 'reverse', '--list'))
        if ($reverses | Where-Object { $_ -match '\s+tcp:8000\s+' -and $_ -notmatch '\s+tcp:8000\s+tcp:8000$' }) {
            throw 'Device port 8000 is already mapped elsewhere. Existing mapping was preserved.'
        }
        if (!($reverses -match '\s+tcp:8000\s+tcp:8000$')) {
            Run-Tool $adb @('-s', $serial, 'reverse', '--no-rebind', 'tcp:8000', 'tcp:8000') | Out-Host
        }

        if (!$SkipBuild) {
            if (!(Test-Path -LiteralPath "$JavaHome\bin\java.exe")) { throw "JDK missing: $JavaHome. Set -JavaHome." }
            $savedJava = $env:JAVA_HOME
            $savedSdk = $env:ANDROID_HOME
            try {
                $env:JAVA_HOME = $JavaHome
                $env:ANDROID_HOME = $SdkPath
                Push-Location $android
                try { Run-Tool '.\gradlew.bat' @('--no-daemon', ':app:assembleDebug') | Out-Host } finally { Pop-Location }
            } finally { $env:JAVA_HOME = $savedJava; $env:ANDROID_HOME = $savedSdk }
        }
        if (!(Test-Path -LiteralPath $apk)) { throw 'Debug APK missing. Run without -SkipBuild.' }
        Run-Tool $adb @('-s', $serial, 'install', '-r', $apk) | Out-Host
        Run-Tool $adb @('-s', $serial, 'shell', 'am', 'start', '-W', '-n', 'com.checkmate.pleos/.MainActivity') | Out-Host
    }

    Wait-Ready { Test-Console } 'Pleos console' 30
    if (!(Test-Backend)) { throw 'CHECKMATE backend is not healthy.' }
    $api = Invoke-WebRequest 'http://127.0.0.1:8000/docs' -UseBasicParsing -TimeoutSec 5
    if ($api.StatusCode -ne 200) { throw 'API documentation is unavailable.' }
    $appProcess = Run-Tool $adb @('-s', $serial, 'shell', 'pidof', 'com.checkmate.pleos')
    if (!$appProcess) { throw 'CHECKMATE app is not running. Run without -CheckOnly.' }
    Write-Host "`nREADY ($serial)"
    Write-Host 'Pleos console: http://127.0.0.1:8088/'
    Write-Host 'CHECKMATE API: http://127.0.0.1:8000/docs'
    Write-Host "Backend mode: $((Get-Json 'http://127.0.0.1:8000/health').generationMode)"
    Write-Host "App process: $appProcess"
    Write-Host 'URLs work on this PC only. AI generation and visible UI are separate checks.'
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
}
