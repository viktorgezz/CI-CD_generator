"""Модули анализаторов для определения технологического стека."""
from .language_analyzer import LanguageAnalyzer
from .framework_analyzer import FrameworkAnalyzer
from .entry_point_analyzer import EntryPointAnalyzer
from .devops_analyzer import DevOpsAnalyzer
from .test_analyzer import TestAnalyzer
from .database_analyzer import DatabaseAnalyzer
from .cloud_analyzer import CloudAnalyzer
from .build_tools_analyzer import BuildToolsAnalyzer
from .cicd_analyzer import CICDAnalyzer
from .hints_analyzer import HintsAnalyzer

__all__ = [
    'LanguageAnalyzer',
    'FrameworkAnalyzer',
    'EntryPointAnalyzer',
    'DevOpsAnalyzer',
    'TestAnalyzer',
    'DatabaseAnalyzer',
    'CloudAnalyzer',
    'BuildToolsAnalyzer',
    'CICDAnalyzer',
    'HintsAnalyzer',
]

