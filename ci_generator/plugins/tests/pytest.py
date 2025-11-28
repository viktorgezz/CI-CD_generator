"""
plugins/tests/pytest.py

Сейчас это общий плагин тестов:
- включает стадию `test`, если в analysis.test_runner указан любой тестовый фреймворк;
- конкретные команды зависят от test_runner и описаны в Jinja-шаблоне.
"""

TEST_STAGES = [
    "test",
]


def enabled(analysis: dict) -> bool:
    """
    Включён, если test_runner непустой.
    Конкретный фреймворк (pytest / unittest / nose / ...) обрабатывается в шаблоне.
    """
    test_runner = analysis.get("test_runner") or ""
    return bool(str(test_runner).strip())


def get_stages(analysis: dict, user_settings: dict):
    """
    Возвращает список тестовых стадий.
    Пока только 'test', но можно расширить ('test_integration', 'test_e2e', ...).
    """
    return list(TEST_STAGES)


