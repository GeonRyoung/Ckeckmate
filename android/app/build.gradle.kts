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
        versionCode = 1
        versionName = "0.3.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    }

    buildFeatures {
        viewBinding = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildTypes {
        release {
            // Signing is configured locally when preparing a submission build.
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
    testImplementation("junit:junit:4.13.2")
}

ksp { arg("room.schemaLocation", "$projectDir/schemas") }
