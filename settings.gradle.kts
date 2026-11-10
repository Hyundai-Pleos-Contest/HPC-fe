pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        if (providers.gradleProperty("enablePleos").orNull == "true") {
            exclusiveContent {
                forRepository {
                    maven {
                        name = "Pleos"
                        url = uri("https://nexus-playground.pleos.ai/repository/maven-releases/")
                    }
                }
                filter { includeGroup("ai.pleos.playground") }
            }
        }
    }
}

rootProject.name = "HPC-fe"
include(":app")
