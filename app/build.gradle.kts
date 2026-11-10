import java.net.URI
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
}

val enablePleos = providers.gradleProperty("enablePleos").orNull == "true"

fun endpoint(propertyName: String, fallback: String, allowEmulatorHttp: Boolean): String {
    val value = providers.gradleProperty(propertyName).getOrElse(fallback)
    val uri = URI(value)
    require(uri.host != null && uri.userInfo == null && uri.fragment == null && uri.query == null) {
        "$propertyName must be an absolute URL without credentials, query, or fragment."
    }
    require(uri.scheme == "https" || (allowEmulatorHttp && uri.scheme == "http" && uri.host == "10.0.2.2")) {
        "$propertyName requires HTTPS; debug alone permits http://10.0.2.2."
    }
    return "\"${uri.toASCIIString()}\""
}

android {
    namespace = "com.hpc.app"
    compileSdk = 35
    buildToolsVersion = "35.0.0"

    defaultConfig {
        applicationId = "com.hpc.app"
        minSdk = 28
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"
        if (enablePleos) {
            testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        }
    }

    testBuildType = "debug"

    flavorDimensions += "vehicle"
    productFlavors {
        create("mock") {
            dimension = "vehicle"
            applicationIdSuffix = ".mock"
            versionNameSuffix = "-mock"
        }
        if (enablePleos) {
            create("pleos") {
                dimension = "vehicle"
            }
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            buildConfigField("String", "API_BASE_URL", endpoint("apiBaseUrl", "http://10.0.2.2:8080", true))
        }
        release {
            isMinifyEnabled = false
            buildConfigField("String", "API_BASE_URL", endpoint("releaseApiBaseUrl", "https://api.example.invalid", false))
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    lint {
        abortOnError = true
        checkReleaseBuilds = true
    }
}

kotlin {
    compilerOptions { jvmTarget.set(JvmTarget.JVM_17) }
}

dependencies {
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.material3)
    if (enablePleos) {
        add("pleosImplementation", libs.pleos.vehicle)
        add("androidTestImplementation", libs.androidx.test.runner)
        add("androidTestImplementation", libs.androidx.test.junit)
    }
}
