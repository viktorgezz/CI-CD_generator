"""
plugins/languages/go.py

Определяет, включён ли Go в анализ и какие стадии он добавляет.
"""

GO_STAGES = [
    "lint",
    "type_check",
    "security",
    "build",
    "migration",
]

def enabled(analysis: dict) -> bool:
    return "go" in analysis.get("languages", [])

def _has_supported_migration_framework(analysis: dict) -> bool:
    """
    Возвращает True, если в analysis есть инструменты для миграций.
    """
    # Проверяем наличие баз данных, которые обычно требуют миграций
    databases = [d.lower() for d in analysis.get("databases", [])]
    # Если есть БД, то миграции могут быть нужны
    return bool(databases)

def get_stages(analysis: dict, user_settings: dict):
    # If user gave explicit stages list, selection done later; plugin returns possible stages
    enabled_stages = list(GO_STAGES)
    # если нет БД — не добавляем migration
    if not _has_supported_migration_framework(analysis):
        if "migration" in enabled_stages:
            enabled_stages.remove("migration")
    # НЕ удаляем build даже если есть docker - многие проекты требуют предварительной сборки бинарников
    # (например, Traefik собирает бинарники в dist/ перед docker build)

    return enabled_stages

