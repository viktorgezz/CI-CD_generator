"""
stage_selector.py

Собирает список стадий, используя плагины (languages + technologies).
"""

from typing import List, Dict

# import plugins (абсолютные импорты от корня проекта)
from plugins.languages import python as python_plugin
from plugins.languages import java as java_plugin
from plugins.languages import go as go_plugin
from plugins.languages import typescript as typescript_plugin
from plugins.technologies import docker as docker_plugin
from plugins.technologies import kubernetes as k8s_plugin
from plugins.tests import pytest as pytest_tests_plugin

# canonical order
ALL_STAGES = [
    "pre_checks",
    "lint",
    "type_check",
    "security",
    "test",
    "build",
    "docker_build",
    "docker_push",
    "integration",
    "migration",
    "deploy",
    "post_deploy",
    "cleanup",
]

def select_stages(analysis: Dict, user_settings: Dict) -> List[str]:
    """
    Сбор стадий через плагины. Если user_settings['stages'] непустой — это whitelist.
    """
    user_defined = user_settings.get("stages") or []

    stages = []

    # language plugins
    if python_plugin.enabled(analysis):
        stages += python_plugin.get_stages(analysis, user_settings)
    if java_plugin.enabled(analysis):
        stages += java_plugin.get_stages(analysis, user_settings)
    if go_plugin.enabled(analysis):
        stages += go_plugin.get_stages(analysis, user_settings)
    if typescript_plugin.enabled(analysis):
        stages += typescript_plugin.get_stages(analysis, user_settings)
    # tests (зависят только от test_runner, а не от языка)
    if pytest_tests_plugin.enabled(analysis):
        stages += pytest_tests_plugin.get_stages(analysis, user_settings)
    # docker
    if docker_plugin.enabled(analysis):
        stages += docker_plugin.get_stages(analysis, user_settings)
    # kubernetes
    if k8s_plugin.enabled(analysis):
        stages += k8s_plugin.get_stages(analysis, user_settings)

    # always include pre_checks from shared if user allows
    if "pre_checks" not in stages:
        stages = ["pre_checks"] + stages

    # If user provided whitelist, intersect and preserve canonical order
    if user_defined:
        chosen = [s for s in ALL_STAGES if s in user_defined and s in stages]
    else:
        chosen = [s for s in ALL_STAGES if s in stages]

    return chosen
