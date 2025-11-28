"""Анализатор инструментов сборки."""
import logging
from pathlib import Path

from ..models import ProjectStack
from ..config import ConfigLoader
from ..utils import get_relevant_files

logger = logging.getLogger(__name__)


class BuildToolsAnalyzer:
    """Анализатор для определения инструментов сборки."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация анализатора.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config_loader = config_loader

    def analyze(self, repo_path: Path, stack: ProjectStack):
        """
        Анализ инструментов сборки.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        build_tools_files = {
            'webpack': ['webpack.config.js', 'webpack.config.ts'],
            'vite': ['vite.config.js', 'vite.config.ts'],
            'rollup': ['rollup.config.js'],
            'parcel': ['.parcelrc', 'parcel.json'],
            'gulp': ['gulpfile.js', 'gulpfile.ts'],
            'grunt': ['Gruntfile.js'],
            'babel': ['.babelrc', 'babel.config.js', 'babel.config.json'],
            'esbuild': ['esbuild.js', 'esbuild.config.js'],
            'swc': ['.swcrc', 'swc.config.js'],
            'make': ['Makefile'],
            'cmake': ['CMakeLists.txt'],
            'gradle': ['build.gradle', 'build.gradle.kts'],
            'maven': ['pom.xml'],
            'ant': ['build.xml'],
        }

        # Используем оптимизированный поиск файлов
        relevant_files = get_relevant_files(repo_path)
        
        for tool, patterns in build_tools_files.items():
            for pattern in patterns:
                matches = [f for f in relevant_files if f.name == pattern]
                if matches:
                    if tool not in stack.build_tools:
                        stack.build_tools.append(tool)
                    break


