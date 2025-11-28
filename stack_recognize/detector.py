"""Основной класс для определения технологического стека проекта."""
import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional

try:
    from .models import ProjectStack
    from .config import ConfigLoader
    from .analyzers import (
        LanguageAnalyzer,
        FrameworkAnalyzer,
        EntryPointAnalyzer,
        DevOpsAnalyzer,
        TestAnalyzer,
        DatabaseAnalyzer,
        CloudAnalyzer,
        BuildToolsAnalyzer,
        CICDAnalyzer,
        HintsAnalyzer,
    )
except ImportError:
    from models import ProjectStack
    from config import ConfigLoader
    from analyzers import (
        LanguageAnalyzer,
        FrameworkAnalyzer,
        EntryPointAnalyzer,
        DevOpsAnalyzer,
        TestAnalyzer,
        DatabaseAnalyzer,
        CloudAnalyzer,
        BuildToolsAnalyzer,
        CICDAnalyzer,
        HintsAnalyzer,
    )

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProjectStackDetector:
    """Детектор технологического стека проекта по Git-репозиторию."""

    def __init__(self, config_path: str = None):
        """
        Инициализация детектора.

        Args:
            config_path: Путь к конфигурационному файлу (опционально)
        """
        self.temp_dir = None
        self.repo_path = None
        self.config_loader = ConfigLoader(config_path)

        # Инициализация анализаторов
        self.language_analyzer = LanguageAnalyzer(self.config_loader)
        self.framework_analyzer = FrameworkAnalyzer(self.config_loader)
        self.entry_point_analyzer = EntryPointAnalyzer(self.config_loader)
        self.devops_analyzer = DevOpsAnalyzer(self.config_loader)
        self.test_analyzer = TestAnalyzer(self.config_loader)
        self.database_analyzer = DatabaseAnalyzer(self.config_loader)
        self.cloud_analyzer = CloudAnalyzer(self.config_loader)
        self.build_tools_analyzer = BuildToolsAnalyzer(self.config_loader)
        self.cicd_analyzer = CICDAnalyzer(self.config_loader)
        self.hints_analyzer = HintsAnalyzer(self.config_loader)

    def detect_stack(self, repo_url: str) -> ProjectStack:
        """
        Основной метод для определения технологического стека.

        Args:
            repo_url: URL Git-репозитория

        Returns:
            ProjectStack: Объект с информацией о стеке
        """
        stack = ProjectStack()

        try:
            # Клонирование репозитория
            self._clone_repository(repo_url)

            # Анализ содержимого
            self.language_analyzer.analyze(self.repo_path, stack)
            self.framework_analyzer.analyze(self.repo_path, stack)
            self.devops_analyzer.analyze(self.repo_path, stack)
            self.test_analyzer.analyze(self.repo_path, stack)
            self.database_analyzer.analyze(self.repo_path, stack)
            self.cloud_analyzer.analyze(self.repo_path, stack)
            self.build_tools_analyzer.analyze(self.repo_path, stack)
            self.cicd_analyzer.analyze(self.repo_path, stack)
            self.hints_analyzer.analyze(self.repo_path, stack)

            # Анализ точек входа
            self.entry_point_analyzer.analyze(self.repo_path, stack)
            
            # Определяем версию Java из pom.xml до очистки
            java_version = self._extract_java_version_from_pom()
            if java_version:
                if not hasattr(stack, 'java_version'):
                    stack.files_detected['java_version'] = java_version
                else:
                    stack.java_version = java_version

        except Exception as e:
            logger.error(f"Ошибка при анализе репозитория: {e}")
            stack.hints.append(f"Ошибка анализа: {str(e)}")
        finally:
            # Очистка временных файлов
            self._cleanup()

        return stack

    def _clone_repository(self, repo_url: str):
        """Клонирование репозитория во временную директорию."""
        self.temp_dir = tempfile.mkdtemp(prefix="repo_analyzer_")
        logger.info(f"Клонирование репозитория {repo_url} в {self.temp_dir}")

        try:
            subprocess.run([
                'git', 'clone', '--depth', '1', repo_url, self.temp_dir
            ], check=True, capture_output=True, text=True)

            self.repo_path = Path(self.temp_dir)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка клонирования репозитория: {e.stderr}")

    def _extract_java_version_from_pom(self) -> Optional[str]:
        """Извлечь версию Java из pom.xml файлов в репозитории.
        
        Возвращает максимальную версию Java из всех найденных pom.xml файлов,
        чтобы образ поддерживал все модули монорепозитория.
        """
        import re
        
        if not self.repo_path or not self.repo_path.exists():
            return None
        
        # Ищем все pom.xml файлы
        pom_files = list(self.repo_path.rglob("pom.xml"))
        if not pom_files:
            return None
        
        versions = []
        
        # Пробуем найти версию Java в каждом pom.xml
        for pom_file in pom_files:
            try:
                with open(pom_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Ищем maven.compiler.release, source, target или java.version
                patterns = [
                    r'<maven\.compiler\.release>(\d+)</maven\.compiler\.release>',
                    r'<maven\.compiler\.source>(\d+)</maven\.compiler\.source>',
                    r'<maven\.compiler\.target>(\d+)</maven\.compiler\.target>',
                    r'<java\.version>(\d+)</java\.version>',
                    r'<javaVersion>(\d+)</javaVersion>',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, content)
                    if match:
                        version = match.group(1)
                        # Нормализуем версию (например, 21 -> 21, 1.8 -> 8)
                        if version.startswith('1.'):
                            version = version[2:]
                        try:
                            versions.append(int(version))
                        except ValueError:
                            pass
                        break
            except Exception:
                continue
        
        # Возвращаем максимальную версию Java
        if versions:
            return str(max(versions))
        
        return None

    def _cleanup(self):
        """Очистка временных файлов."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            logger.info(f"Временная директория {self.temp_dir} удалена")

