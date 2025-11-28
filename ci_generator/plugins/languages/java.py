"""
plugins/languages/java.py

Определяет, включён ли Java/Kotlin в анализ и какие стадии он добавляет.
"""

JAVA_STAGES = [
    "lint",
    "type_check",
    "security",
    "build",
    "migration",
]

def enabled(analysis: dict) -> bool:
    return "java" in analysis.get("languages", [])

def _has_supported_migration_framework(analysis: dict) -> bool:
    """
    Возвращает True, если в analysis есть фреймворк, для которого
    мы умеем запускать миграции.
    """
    frameworks = [f.lower() for f in analysis.get("frameworks", [])]
    backend_frameworks = [f.lower() for f in analysis.get("backend_frameworks", [])]
    all_fw = set(frameworks + backend_frameworks)
    # поддерживаемые фреймворки для миграций
    supported = {"spring", "spring-boot", "quarkus", "micronaut", "vertx"}
    return bool(all_fw & supported)

def get_stages(analysis: dict, user_settings: dict):
    # If user gave explicit stages list, selection done later; plugin returns possible stages
    enabled_stages = list(JAVA_STAGES)
    # если нет подходящего фреймворка — не добавляем migration
    if not _has_supported_migration_framework(analysis):
        if "migration" in enabled_stages:
            enabled_stages.remove("migration")
    # Если есть docker_build, то build (создание JAR) не нужен
    if analysis.get("docker") and "build" in enabled_stages:
        enabled_stages.remove("build")

    return enabled_stages

