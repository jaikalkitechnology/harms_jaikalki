plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
    // Firebase / FCM. Must come AFTER the android + kotlin plugins so it
    // can read the merged manifest. The classpath comes from settings.gradle.kts.
    id("com.google.gms.google-services")
}

android {
    // namespace + applicationId must match `package_name` in
    // android/app/google-services.json (currently `com.hrms.jaikalki`).
    namespace = "com.hrms.jaikalki"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        applicationId = "com.hrms.jaikalki"
        // firebase_messaging requires minSdk ≥ 19; flutter_local_notifications
        // requires multidex on minSdk < 21, so we anchor at 21.
        minSdk = maxOf(flutter.minSdkVersion, 21)
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
        multiDexEnabled = true
    }

    buildTypes {
        release {
            // TODO: Add your own signing config for the release build.
            // Signing with the debug keys for now, so `flutter run --release` works.
            signingConfig = signingConfigs.getByName("debug")
        }
    }
}

flutter {
    source = "../.."
}
