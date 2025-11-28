"""Анализатор CI/CD конфигураций."""
import logging
from pathlib import Path

from ..models import ProjectStack
from ..config import ConfigLoader
from ..utils import get_relevant_files

logger = logging.getLogger(__name__)


class CICDAnalyzer:
    """Анализатор для определения CI/CD конфигураций."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация анализатора.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config_loader = config_loader

    def analyze(self, repo_path: Path, stack: ProjectStack):
        """
        Анализ CI/CD конфигураций.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        cicd_files = {
            'github-actions': ['.github/workflows/*.yml', '.github/workflows/*.yaml'],
            'gitlab': ['.gitlab-ci.yml'],
            'jenkins': ['Jenkinsfile'],
            'bitbucket': ['bitbucket-pipelines.yml'],
            'azure-pipelines': ['azure-pipelines.yml'],
            'circleci': ['.circleci/config.yml'],
            'travis': ['.travis.yml'],
            'teamcity': ['.teamcity/'],
            'bamboo': ['bamboo-specs/'],
        }

        detected_files = {}
        
        # Используем оптимизированный поиск файлов
        relevant_files = get_relevant_files(repo_path)

        for provider, patterns in cicd_files.items():
            for pattern in patterns:
                # Упрощенный поиск по имени файла или пути
                matches = [f for f in relevant_files 
                          if f.name == pattern or 
                          str(f.relative_to(repo_path)) == pattern or
                          str(f.relative_to(repo_path)).startswith(pattern.rstrip('*'))]
                
                if matches:
                    stack.cicd.append(provider)
                    detected_files[f'cicd_{provider}'] = [str(m.relative_to(repo_path)) for m in matches]
                    break

        stack.files_detected.update(detected_files)


