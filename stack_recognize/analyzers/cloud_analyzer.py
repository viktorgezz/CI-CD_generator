"""Анализатор облачных платформ."""
import re
import logging
from pathlib import Path

from ..models import ProjectStack
from ..config import ConfigLoader, PatternConfig
from ..utils import get_relevant_files, read_file_sample

logger = logging.getLogger(__name__)


class CloudAnalyzer:
    """Анализатор для определения облачных платформ."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация анализатора.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config_loader = config_loader
        self.pattern_config = PatternConfig()

    def analyze(self, repo_path: Path, stack: ProjectStack):
        """
        Анализ облачных платформ.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        # Анализ по конфигурационным файлам
        self._analyze_by_files(repo_path, stack)

        # Анализ по зависимостям и импортам
        self._analyze_by_content(repo_path, stack)

    def _analyze_by_files(self, repo_path: Path, stack: ProjectStack):
        """Анализ облачных платформ по наличию специфичных файлов."""
        cloud_files = {
            'aws': ['.aws/', 'aws.yml', 'aws.yaml'],
            'azure': ['.azure/', 'azure-pipelines.yml'],
            'gcp': ['.gcp/', 'gcp.yaml', 'app.yaml'],
            'heroku': ['Procfile', 'app.json'],
        }

        for cloud, patterns in cloud_files.items():
            for pattern in patterns:
                if list(repo_path.rglob(pattern)):
                    if cloud not in stack.cloud_platforms:
                        stack.cloud_platforms.append(cloud)
                    break

    def _analyze_by_content(self, repo_path: Path, stack: ProjectStack):
        """Анализ облачных платформ по содержимому файлов."""
        # Только расширения поддерживаемых языков: Python, TypeScript, Java/Kotlin, Go + конфиги
        code_extensions = ['.py', '.pyw', '.ts', '.tsx', '.java', '.kt', '.kts', '.go', '.yaml', '.yml']

        # Используем оптимизированную функцию для получения релевантных файлов
        relevant_files = get_relevant_files(repo_path, extensions=code_extensions, max_file_size=200 * 1024)

        for file_path in relevant_files:
            # Читаем только начало файла (достаточно для поиска паттернов облачных платформ)
            content = read_file_sample(file_path, max_lines=50, max_bytes=4096)

            if not content:
                continue

            for cloud, patterns in self.pattern_config.CLOUD_PATTERNS.items():
                if cloud not in stack.cloud_platforms:
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            stack.cloud_platforms.append(cloud)
                            break


