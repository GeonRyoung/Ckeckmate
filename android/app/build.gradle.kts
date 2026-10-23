plugins {
    alias(libs.plugins.android.application)
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
        versionName = "0.1.0"
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
    testImplementation("junit:junit:4.13.2")
}
