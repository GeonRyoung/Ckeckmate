"""Run opt-in console -> SDK -> UI -> live API -> Room report tests on the test AVD only.

Prerequisites: reviewed/Qdrant backend at localhost:8000, built debug and androidTest APKs,
Checkmate_Verification_Empty_API_34 running, adb forward 8088 and reverse 8000 configured.
No Qwen generation, physical device control, DB clearing or external report delivery.
"""
from __future__ import annotations

import hashlib
import argparse
import json
from pathlib import Path
import subprocess
import threading
import time
import urllib.request
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / ".local" / "verification" / "three-scenarios"
SERIAL = "emulator-5554"
AVD = "Checkmate_Verification_Empty_API_34"
CASES = ("tpms-first", "tpms-blink", "epb-first")


def adb(*args, timeout=60):
    return subprocess.run(["adb", "-s", SERIAL, *args], capture_output=True, check=True, timeout=timeout).stdout


def request(path, method="GET"):
    with urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:8088" + path, method=method), timeout=10) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=CASES, help="Verify one scenario; default verifies all three")
    selected = parser.parse_args().case
    cases = (selected,) if selected else CASES
    test_class = "com.checkmate.pleos.assistance.ConsoleScenariosTest"
    if selected:
        test_class += "#" + {"tpms-first": "tpmsFirstOn", "tpms-blink": "tpmsBlinkThenOn", "epb-first": "epbRemainsOn"}[selected]
    assert adb("emu", "avd", "name").decode().splitlines()[0] == AVD, "Wrong emulator; no writes performed"
    assert adb("shell", "getprop", "ro.kernel.qemu").strip() == b"1", "Not an emulator"
    mappings = subprocess.check_output(["adb", "forward", "--list"]).decode()
    assert f"{SERIAL} tcp:8088 tcp:8088" in mappings, "Console must map to the test emulator"
    assert "tcp:8000 tcp:8000" in adb("reverse", "--list").decode(), "Missing local API reverse"
    with urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=5) as response:
        health = json.load(response)
    assert health["generationMode"] == "reviewed", "This CPU verification must not use Qwen"
    assert health.get("retrievalMode", "").startswith("qdrant:"), "Live Qdrant retrieval required"
    assert health.get("embeddingNumGpu") == 0, "Explicit CPU embeddings required"
    OUT.mkdir(parents=True, exist_ok=True)
    # Unique run IDs prevent earlier passing artifacts from masking a failed new run.
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_out = OUT / run_id
    run_out.mkdir()
    stop = threading.Event()
    heartbeat_errors = []

    def keep_console_active():
        while not stop.is_set():
            try:
                request("/browser/session?client=checkmate-three-scenarios", "POST")
            except Exception as exc:
                heartbeat_errors.append(str(exc))
            stop.wait(0.7)

    worker = threading.Thread(target=keep_console_active, daemon=True)
    worker.start()
    manifest = {"runId": run_id, "avd": AVD, "health": health, "physicalVehicle": False,
                "qwenUsed": False, "externalReportSent": False, "cases": [], "passed": False}
    try:
        for _ in range(40):
            state = request("/vehicle/state")
            if state["telltales"]["bridge_ready"] and state["telltales"]["emulator_active"]:
                break
            time.sleep(0.5)
        else:
            raise RuntimeError("Virtual Console did not activate")
        (run_out / "console-before.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        apk = ROOT / "android/app/build/outputs/apk/debug/app-debug.apk"
        tests = ROOT / "android/app/build/outputs/apk/androidTest/debug/app-debug-androidTest.apk"
        manifest["apkSha256"] = hashlib.sha256(apk.read_bytes()).hexdigest()
        adb("install", "-r", str(apk))
        adb("install", "-r", str(tests))
        print(f"Running {len(cases)} real-console scenario(s); evidence: {run_out}", flush=True)
        output = adb("shell", "am", "instrument", "-w", "-e", "verificationAvd", AVD,
                     "-e", "verificationRunId", run_id,
                     "-e", "class", test_class,
                     "com.checkmate.pleos.test/androidx.test.runner.AndroidJUnitRunner", timeout=480).decode("utf-8", errors="replace")
        (run_out / "instrumentation.txt").write_text(output, encoding="utf-8")
        user = adb("shell", "am", "get-current-user").decode().strip()
        for case in cases:
            try:
                data = adb("exec-out", "run-as", "com.checkmate.pleos", "--user", user,
                           "cat", f"files/console-scenarios/{case}.json")
                (run_out / f"{case}.json").write_bytes(data)
                case_result = json.loads(data)
                assert case_result.get("runId") == run_id, "Stale device evidence"
                manifest["cases"].append(case_result)
            except Exception as exc:
                manifest["cases"].append({"id": case, "passed": False, "error": str(exc)})
            for stage in ("guidance", "answer", "report"):
                try:
                    image = adb("exec-out", "run-as", "com.checkmate.pleos", "--user", user,
                                "cat", f"files/console-scenarios/{case}-{stage}.png")
                    if image.startswith(b"\x89PNG"):
                        (run_out / f"{case}-{stage}.png").write_bytes(image)
                except subprocess.CalledProcessError:
                    pass
        expected = f"OK ({len(cases)} {'test' if len(cases) == 1 else 'tests'})"
        if expected not in output:
            print(output, flush=True)
            try:
                (run_out / "failure.txt").write_bytes(adb("exec-out", "run-as", "com.checkmate.pleos", "--user", user,
                                                           "cat", "files/console-scenarios/failure.txt"))
            except subprocess.CalledProcessError:
                pass
            raise RuntimeError("At least one console scenario failed")
        assert all(case["passed"] for case in manifest["cases"])
        if "tpms-first" in cases:
            voice_log = adb("logcat", "-d", "-s", "CheckmateVoice").decode("utf-8", errors="replace")
            marker = f"verification start {run_id}"
            assert marker in voice_log, "Missing current voice verification log"
            voice_log = voice_log.split(marker, 1)[1]
            (run_out / "voice-service.log").write_text(voice_log, encoding="utf-8")
            assert "timed out" not in voice_log, "TTS cancellation was not acknowledged"
            assert voice_log.count("TTS stop acknowledged") >= 3, "Button, background and driving cancellation must reach the service"
            manifest["ttsCancellationAcknowledged"] = True
        with urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5) as response:
            models = json.load(response)["models"]
        manifest["embeddingRuntime"] = [{"name": m["name"], "size_vram": m["size_vram"]}
                                        for m in models if m["name"].startswith("bge-m3")]
        assert manifest["embeddingRuntime"] and all(m["size_vram"] == 0 for m in manifest["embeddingRuntime"])
        manifest["passed"] = True
        print(json.dumps({"passed": True, "cases": [{"id": c["id"], "questionElapsedMs": c["questionElapsedMs"]}
                                                   for c in manifest["cases"]]}, ensure_ascii=False), flush=True)
    finally:
        # Leave the test emulator parked, with the two test warning types off.
        for path in ("/vehicle/controls?speed=0&accelerator=0&brake=0&steering=0", "/vehicle/gear?gear=Park",
                     "/vehicle/telltales/simulator?type=TPMS&state=Off&color=Yellow",
                     "/vehicle/telltales/simulator?type=ElectronicParkingBrake&state=Off&color=Yellow"):
            try:
                request(path, "PUT")
            except Exception as exc:
                manifest.setdefault("cleanupErrors", []).append(str(exc))
        stop.set()
        worker.join(timeout=12)
        try:
            request("/browser/session?client=checkmate-three-scenarios&closing=1", "POST")
        except Exception:
            pass
        manifest["heartbeatErrors"] = heartbeat_errors
        (run_out / "result.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Result: {run_out / 'result.json'}", flush=True)


if __name__ == "__main__":
    main()
