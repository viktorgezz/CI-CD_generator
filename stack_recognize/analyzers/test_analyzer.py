"""Анализатор тестовых раннеров."""
import re
import logging
from pathlib import Path
from typing import Dict, List

from ..models import ProjectStack
from ..config import ConfigLoader, PatternConfig
from ..utils import get_relevant_files, read_file_sample, get_language_by_extension

logger = logging.getLogger(__name__)


class TestAnalyzer:
    """Анализатор для определения тестовых раннеров."""

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
        Анализ тестовых раннеров.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        # Определяем структуру монорепозитория (если есть)
        monorepo_structure = self._detect_monorepo_structure(repo_path)
        is_monorepo = any(len(v) > 0 for v in monorepo_structure.values() if isinstance(v, list))
        
        # Анализ по файлам
        self._analyze_by_files(repo_path, stack)

        # Анализ по содержимому файлов
        # Продолжаем поиск, чтобы найти тестовые раннеры для всех языков
        self._analyze_by_content(repo_path, stack)
        
        # Для монорепозиториев анализируем тесты по категориям
        if is_monorepo:
            self._analyze_monorepo_tests(repo_path, stack, monorepo_structure)
    
    @staticmethod
    def _detect_monorepo_structure(repo_path: Path) -> Dict[str, List[Path]]:
        """Определить структуру монорепозитория (используем ту же логику, что и в DevOpsAnalyzer)."""
        structure = {
            'frontend': [],
            'backend': [],
            'root': [],
            'apps': [],
            'packages': []
        }
        
        frontend_dirs = ['frontend', 'web', 'client', 'ui', 'app']
        backend_dirs = ['backend', 'server', 'api', 'services']
        apps_dirs = ['apps', 'applications']
        
        for item in repo_path.iterdir():
            if not item.is_dir():
                continue
            
            dir_name = item.name.lower()
            
            if dir_name in frontend_dirs:
                structure['frontend'].append(item)
            elif dir_name in backend_dirs:
                structure['backend'].append(item)
            elif dir_name in apps_dirs:
                structure['apps'].append(item)
        
        # Проверяем apps/ на наличие frontend/backend подпапок
        for apps_dir in structure['apps']:
            for subdir in apps_dir.iterdir():
                if not subdir.is_dir():
                    continue
                subdir_name = subdir.name.lower()
                if subdir_name in frontend_dirs:
                    structure['frontend'].append(subdir)
                elif subdir_name in backend_dirs:
                    structure['backend'].append(subdir)
        
        return structure
    
    def _analyze_monorepo_tests(self, repo_path: Path, stack: ProjectStack, monorepo_structure: Dict[str, List[Path]]):
        """Анализ тестов для монорепозиториев по категориям (frontend/backend)."""
        test_by_category = {}
        
        # Анализируем тесты в frontend частях
        for frontend_dir in monorepo_structure.get('frontend', []):
            frontend_tests = self._analyze_directory_tests(frontend_dir, repo_path)
            if frontend_tests:
                test_by_category['frontend'] = frontend_tests
        
        # Анализируем тесты в backend частях
        for backend_dir in monorepo_structure.get('backend', []):
            backend_tests = self._analyze_directory_tests(backend_dir, repo_path)
            if backend_tests:
                test_by_category['backend'] = backend_tests
        
        # Сохраняем информацию о тестах по категориям
        if test_by_category:
            stack.files_detected['test_by_category'] = test_by_category
            logger.info(f"Тесты в монорепозитории по категориям: {test_by_category}")
    
    def _analyze_directory_tests(self, directory: Path, repo_path: Path) -> List[str]:
        """Анализ тестов в конкретной директории."""
        found_runners = []
        code_extensions = ['.py', '.pyw', '.ts', '.tsx', '.js', '.jsx', '.java', '.kt', '.kts', '.go']
        
        relevant_files = get_relevant_files(directory, extensions=code_extensions, max_file_size=200 * 1024)
        
        for file_path in relevant_files:
            content = read_file_sample(file_path, max_lines=50, max_bytes=4096)
            if not content:
                continue
            
            file_lang = get_language_by_extension(file_path.suffix)
            
            for runner, patterns in self.pattern_config.TEST_RUNNER_PATTERNS.items():
                if runner in found_runners:
                    continue
                
                # Проверка совместимости языка
                python_runners = {'pytest', 'unittest'}
                js_runners = {'jest', 'mocha', 'jasmine', 'karma', 'cypress', 'playwright', 'vitest'}
                java_runners = {'junit', 'testng'}
                go_runners = {'go-testing'}
                
                if runner in python_runners and file_lang != 'python':
                    continue
                if runner in js_runners and file_lang != 'typescript':
                    continue
                if runner in java_runners and file_lang != 'java':
                    continue
                if runner in go_runners and file_lang != 'go':
                    continue
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        found_runners.append(runner)
                        break
        
        return found_runners

    def _analyze_by_files(self, repo_path: Path, stack: ProjectStack):
        """Анализ тестовых раннеров по наличию специфичных файлов."""
        test_files = {
            # Убрали 'pyproject.toml' из pytest - слишком общий файл
            'pytest': ['pytest.ini', 'tox.ini', 'conftest.py'],
            'jest': ['jest.config.js', 'jest.config.ts', 'jest.config.json'],
            'mocha': ['.mocharc.js', '.mocharc.json', '.mocharc.yaml'],
            'jasmine': ['jasmine.json'],
            'karma': ['karma.conf.js', 'karma.conf.ts'],
            'cypress': ['cypress.json', 'cypress.config.js', 'cypress.env.json'],
            'playwright': ['playwright.config.js', 'playwright.config.ts'],
            'vitest': ['vitest.config.js', 'vitest.config.ts', 'vitest.config.mjs'],
            'phpunit': ['phpunit.xml', 'phpunit.xml.dist'],
            'rspec': ['.rspec'],
            'cucumber': ['cucumber.yml', 'cucumber.js'],
        }

        # Используем оптимизированный поиск файлов
        relevant_files = get_relevant_files(repo_path)
        for runner, patterns in test_files.items():
            for pattern in patterns:
                matches = [f for f in relevant_files if f.name == pattern]
                if matches:
                    if runner not in stack.test_runner:
                        stack.test_runner.append(runner)
                        logger.info(f"Обнаружен тестовый раннер {runner} по файлу: {pattern}")
                    # Не возвращаемся, продолжаем поиск для других языков

    def _analyze_by_content(self, repo_path: Path, stack: ProjectStack):
        """Анализ тестовых раннеров по содержимому файлов."""
        # Только расширения поддерживаемых языков: Python, TypeScript, Java/Kotlin, Go
        code_extensions = ['.py', '.pyw', '.ts', '.tsx', '.js', '.jsx', '.java', '.kt', '.kts', '.go']

        # Используем оптимизированную функцию для получения релевантных файлов
        relevant_files = get_relevant_files(repo_path, extensions=code_extensions, max_file_size=200 * 1024)

        for file_path in relevant_files:
            # Читаем только начало файла (достаточно для поиска паттернов тестов)
            content = read_file_sample(file_path, max_lines=50, max_bytes=4096)

            if not content:
                continue

            # Определяем язык файла по расширению
            file_lang = get_language_by_extension(file_path.suffix)
            
            for runner, patterns in self.pattern_config.TEST_RUNNER_PATTERNS.items():
                # Пропускаем, если этот раннер уже найден
                if runner in stack.test_runner:
                    continue
                
                # Проверка совместимости языка файла и тестового раннера
                # Python тестовые раннеры применяются только к Python файлам
                python_runners = {'pytest', 'unittest'}
                if runner in python_runners and file_lang != 'python':
                    continue
                
                # JavaScript/TypeScript тестовые раннеры применяются только к TypeScript файлам
                js_runners = {'jest', 'mocha', 'jasmine', 'karma', 'cypress', 'playwright', 'vitest'}
                if runner in js_runners and file_lang != 'typescript':
                    continue
                
                # Java/Kotlin тестовые раннеры применяются только к Java/Kotlin файлам
                java_runners = {'junit', 'testng'}
                if runner in java_runners and file_lang != 'java':
                    continue
                
                # Go тестовые раннеры применяются только к Go файлам
                go_runners = {'go-testing'}
                if runner in go_runners and file_lang != 'go':
                    continue
                
                # PHP тестовые раннеры - не поддерживаются (нет PHP в списке языков)
                if runner == 'phpunit':
                    continue
                
                # Ruby тестовые раннеры - не поддерживаются (нет Ruby в списке языков)
                if runner == 'rspec':
                    continue
                
                # Go не имеет специфичных тестовых раннеров в списке
                # E2E/BDD тестовые раннеры могут быть в любом языке
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        stack.test_runner.append(runner)
                        logger.info(f"Обнаружен тестовый раннер {runner} в файле {file_path.relative_to(repo_path)} по паттерну: {pattern}")
                        break  # Переходим к следующему раннеру, не выходим из цикла
