"""
plugins/languages/typescript.py

Определяет, включён ли TypeScript/JavaScript в анализ и какие стадии он добавляет.
"""

TYPESCRIPT_STAGES = [
    "lint",
    "type_check",
    "security",
    "build",
    "migration",
]

def enabled(analysis: dict) -> bool:
    languages = [l.lower() for l in analysis.get("languages", [])]
    return "typescript" in languages or "javascript" in languages

def _has_supported_migration_framework(analysis: dict) -> bool:
    """
    Возвращает True, если в analysis есть фреймворк, для которого
    мы умеем запускать миграции.
    """
    frameworks = [f.lower() for f in analysis.get("frameworks", [])]
    backend_frameworks = [f.lower() for f in analysis.get("backend_frameworks", [])]
    all_fw = set(frameworks + backend_frameworks)
    # поддерживаемые backend фреймворки для миграций
    supported = {"express", "nest", "nextjs"}
    return bool(all_fw & supported)

def get_stages(analysis: dict, user_settings: dict):
    # If user gave explicit stages list, selection done later; plugin returns possible stages
    enabled_stages = list(TYPESCRIPT_STAGES)
    # если нет подходящего фреймворка — не добавляем migration
    if not _has_supported_migration_framework(analysis):
        if "migration" in enabled_stages:
            enabled_stages.remove("migration")
    # Если есть docker_build, то build (сборка TypeScript) не нужен
    if analysis.get("docker") and "build" in enabled_stages:
        enabled_stages.remove("build")

    return enabled_stages

