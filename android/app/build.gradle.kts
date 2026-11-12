import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.ksp)
}

android {
    namespace = "com.checkmate.pleos"
    compileSdk = 35
    useLibrary("android.car")

    defaultConfig {
        applicationId = "com.checkmate.pleos"
        minSdk = 28
        targetSdk = 35
        versionCode = 3
        versionName = "1.0.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures {
        viewBinding = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    // Release signing comes from android/keystore.properties (git-ignored), never from the repo.
    val keystoreFile = rootProject.file("keystore.properties")
    val releaseSigning = if (keystoreFile.exists()) {
        val props = Properties().apply { keystoreFile.inputStream().use { load(it) } }
        signingConfigs.create("release") {
            storeFile = rootProject.file(props.getProperty("storeFile"))
            storePassword = props.getProperty("storePassword")
            keyAlias = props.getProperty("keyAlias")
            keyPassword = props.getProperty("keyPassword")
        }
    } else null

    buildTypes {
        debug {
            buildConfigField("String", "EXPLANATION_BASE_URL", "\"http://127.0.0.1:8000\"")
        }
        release {
            val serverUrl = providers.gradleProperty("checkmateServerUrl").orElse("").get()
            require(serverUrl.isEmpty() || serverUrl.matches(Regex("https://[A-Za-z0-9.-]+(?::[0-9]+)?"))) {
                "checkmateServerUrl must be an HTTPS origin"
            }
            buildConfigField("String", "EXPLANATION_BASE_URL", "\"$serverUrl\"")
            // Without keystore.properties the release APK stays unsigned (not installable).
            releaseSigning?.let { signingConfig = it }
            isMinifyEnabled = false
        }
    }
}

dependencies {
    implementation(libs.androidx.appcompat)
    implementation(libs.androidx.core.ktx)
    implementation(libs.pleos.vehicle)
    implementation(libs.room.runtime)
    ksp(libs.room.compiler)
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test:runner:1.5.2")
    implementation("ai.pleos.playground:TextToSpeech:3.3.1")
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.json:json:20240303")
}

ksp { arg("room.schemaLocation", "$projectDir/schemas") }
