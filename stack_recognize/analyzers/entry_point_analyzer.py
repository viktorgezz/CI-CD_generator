"""Анализатор точек входа в приложение."""
import json
import re
import logging
from pathlib import Path
from typing import Dict

from ..models import ProjectStack, EntryPoint
from ..config import ConfigLoader, PatternConfig
from ..utils import get_language_by_extension, detect_language_from_command, get_relevant_files, read_file_sample

logger = logging.getLogger(__name__)


class EntryPointAnalyzer:
    """Анализатор для определения точек входа в приложение."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация анализатора.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config_loader = config_loader
        self.pattern_config = PatternConfig()

        # Конфигурационные файлы, указывающие на точку входа (только для поддерживаемых языков)
        self.config_files = {
            'package.json': self._parse_package_json_entry,
            'pyproject.toml': self._parse_pyproject_toml_entry,
            'pom.xml': self._parse_pom_xml_entry,
            'build.gradle': self._parse_gradle_entry,
            'next.config.js': self._parse_next_config,
            'angular.json': self._parse_angular_config,
            'vue.config.js': self._parse_vue_config,
            'dockerfile': self._parse_dockerfile_entry,
            'docker-compose.yml': self._parse_docker_compose_entry,
        }

    def analyze(self, repo_path: Path, stack: ProjectStack):
        """
        Анализ точек входа в приложение.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        logger.info("Поиск точек входа в приложение...")

        # 1. Поиск по стандартным именам файлов
        self._find_standard_entry_points(repo_path, stack)

        # 2. Анализ конфигурационных файлов
        self._analyze_config_files(repo_path, stack)

        # 3. Поиск по содержимому файлов
        self._find_entry_points_by_content(repo_path, stack)

        # 4. Анализ Docker файлов
        self._analyze_docker_entry_points(repo_path, stack)

        # 5. Определение основной точки входа
        self._determine_main_entry_point(stack)

        logger.info(f"Найдено точек входа: {len(stack.entry_points)}")

    def _find_standard_entry_points(self, repo_path: Path, stack: ProjectStack):
        """Поиск точек входа по стандартным именам файлов."""
        for language, patterns in self.pattern_config.STANDARD_ENTRY_FILES.items():
            for pattern in patterns:
                matches = list(repo_path.rglob(pattern))
                for match in matches:
                    if match.is_file():
                        entry_point = EntryPoint(
                            type='main',
                            file_path=str(match.relative_to(repo_path)),
                            language=language,
                            confidence=0.7
                        )
                        self._add_entry_point(entry_point, stack)

    def _analyze_config_files(self, repo_path: Path, stack: ProjectStack):
        """Анализ конфигурационных файлов для определения точек входа."""
        for config_file, parser_method in self.config_files.items():
            if config_file == 'dockerfile':
                continue  # Обрабатывается отдельно
            # Используем оптимизированный поиск файлов
            matches = [f for f in get_relevant_files(repo_path) 
                      if f.name == config_file]
            for match in matches:
                try:
                    parser_method(match, stack)
                except Exception as e:
                    logger.warning(f"Ошибка анализа {config_file}: {e}")

    def _find_entry_points_by_content(self, repo_path: Path, stack: ProjectStack):
        """Поиск точек входа по содержимому файлов."""
        # Только расширения поддерживаемых языков: Python, TypeScript, Java/Kotlin, Go
        code_extensions = ['.py', '.pyw', '.ts', '.tsx', '.java', '.kt', '.kts', '.go']

        # Используем оптимизированную функцию для получения релевантных файлов
        relevant_files = get_relevant_files(repo_path, extensions=code_extensions, max_file_size=200 * 1024)

        for file_path in relevant_files:
            # Читаем только начало файла (достаточно для поиска паттернов точек входа)
            content = read_file_sample(file_path, max_lines=50, max_bytes=4096)

            if not content:
                continue

            # Определяем язык файла по расширению
            file_lang = get_language_by_extension(file_path.suffix)
            if file_lang and file_lang in self.pattern_config.ENTRY_POINT_PATTERNS:
                patterns = self.pattern_config.ENTRY_POINT_PATTERNS[file_lang]
                for pattern, framework, confidence in patterns:
                    if re.search(pattern, content):
                        entry_point = EntryPoint(
                            type='app' if framework != 'main' else 'main',
                            file_path=str(file_path.relative_to(repo_path)),
                            framework=framework,
                            language=file_lang,
                            confidence=confidence
                        )
                        self._add_entry_point(entry_point, stack)
                        break

    def _analyze_docker_entry_points(self, repo_path: Path, stack: ProjectStack):
        """Анализ Docker файлов для определения точек входа."""
        # Используем оптимизированный поиск Docker файлов
        relevant_files = get_relevant_files(repo_path)
        docker_files = [f for f in relevant_files 
                       if f.name.startswith('Dockerfile') or f.name.endswith('.dockerfile')]

        for docker_file in docker_files:
            self._parse_dockerfile_entry(docker_file, stack)

    def _parse_package_json_entry(self, file_path: Path, stack: ProjectStack):
        """Анализ package.json для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)

            # Основная точка входа
            main_file = package_data.get('main')
            if main_file:
                # Определяем язык по расширению файла
                main_path = Path(main_file)
                lang = 'typescript' if main_path.suffix in ['.ts', '.tsx'] else 'typescript'
                entry_point = EntryPoint(
                    type='main',
                    file_path=str(file_path.parent / main_file),
                    language=lang,
                    framework='node',
                    confidence=0.9
                )
                self._add_entry_point(entry_point, stack)

            # Скрипты
            scripts = package_data.get('scripts', {})
            for script_name, script_command in scripts.items():
                if script_name in ['start', 'dev', 'serve']:
                    # Пытаемся извлечь файл из команды
                    file_match = re.search(r'(?:node|ts-node|tsx)\s+(\S+)', script_command)
                    if file_match:
                        entry_file = file_match.group(1)
                        entry_path = Path(entry_file)
                        lang = 'typescript' if entry_path.suffix in ['.ts', '.tsx'] else 'typescript'
                        entry_point = EntryPoint(
                            type='script',
                            file_path=str(file_path.parent / entry_file),
                            language=lang,
                            framework='node',
                            confidence=0.8,
                            description=f"Script: {script_name}"
                        )
                        self._add_entry_point(entry_point, stack)

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Не удалось проанализировать package.json: {e}")

    def _parse_pyproject_toml_entry(self, file_path: Path, stack: ProjectStack):
        """Анализ pyproject.toml для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Поиск конфигурации Poetry
            poetry_match = re.search(r'\[tool\.poetry\]', content)
            if poetry_match:
                # Ищем scripts или main модуль
                scripts_match = re.search(r'\[tool\.poetry\.scripts\]\s*(\w+)\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                if scripts_match:
                    module_path = scripts_match.group(2)
                    entry_point = EntryPoint(
                        type='main',
                        file_path=module_path.replace('.', '/') + '.py',
                        language='python',
                        framework='poetry',
                        confidence=0.8
                    )
                    self._add_entry_point(entry_point, stack)

        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Не удалось проанализировать pyproject.toml: {e}")

    def _parse_pom_xml_entry(self, file_path: Path, stack: ProjectStack):
        """Анализ pom.xml для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем main class в плагинах
            main_class_match = re.search(r'<mainClass>([^<]+)</mainClass>', content)
            if main_class_match:
                main_class = main_class_match.group(1)
                class_path = main_class.replace('.', '/') + '.java'
                entry_point = EntryPoint(
                    type='main',
                    file_path=f"src/main/java/{class_path}",
                    language='java',
                    framework='spring',
                    confidence=0.9
                )
                self._add_entry_point(entry_point, stack)

        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Не удалось проанализировать pom.xml: {e}")

    def _parse_gradle_entry(self, file_path: Path, stack: ProjectStack):
        """Анализ build.gradle для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем Spring Boot plugin
            if 'org.springframework.boot' in content:
                entry_point = EntryPoint(
                    type='main',
                    file_path='src/main/java/**/Application.java',
                    language='java',
                    framework='spring',
                    confidence=0.7
                )
                self._add_entry_point(entry_point, stack)

        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Не удалось проанализировать build.gradle: {e}")


    def _parse_dockerfile_entry(self, file_path: Path, stack: ProjectStack):
        """Анализ Dockerfile для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем CMD и ENTRYPOINT инструкции
            cmd_match = re.search(r'CMD\s+\[?"?([^]"]+)"?\]?', content)
            entrypoint_match = re.search(r'ENTRYPOINT\s+\[?"?([^]"]+)"?\]?', content)

            command = cmd_match.group(1) if cmd_match else (
                entrypoint_match.group(1) if entrypoint_match else None
            )

            if command:
                # Пытаемся извлечь файл из команды
                file_match = re.search(r'(?:node|ts-node|tsx|python|java|go)\s+(\S+)', command)
                if file_match:
                    entry_file = file_match.group(1)
                    entry_point = EntryPoint(
                        type='docker',
                        file_path=entry_file,
                        language=detect_language_from_command(command),
                        confidence=0.9,
                        description=f"Docker command: {command}"
                    )
                    self._add_entry_point(entry_point, stack)

        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Не удалось проанализировать Dockerfile: {e}")

    def _parse_docker_compose_entry(self, file_path: Path, stack: ProjectStack):
        """Анализ docker-compose.yml для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Ищем service configuration
            services_match = re.search(r'services:\s*\n(\s+\w+:\s*\n(?:\s+.*\n)*)', content)
            if services_match:
                services_content = services_match.group(1)
                # Упрощенный анализ - ищем build context
                build_match = re.search(r'build:\s*[\'"]?([^\s\'"]+)[\'"]?', services_content)
                if build_match:
                    build_context = build_match.group(1)
                    entry_point = EntryPoint(
                        type='docker-compose',
                        file_path=build_context,
                        confidence=0.7,
                        description="Docker Compose service"
                    )
                    self._add_entry_point(entry_point, stack)

        except (UnicodeDecodeError, IOError) as e:
            logger.warning(f"Не удалось проанализировать docker-compose.yml: {e}")

    def _parse_next_config(self, file_path: Path, stack: ProjectStack):
        """Анализ next.config.js для определения точки входа."""
        entry_point = EntryPoint(
            type='nextjs',
            file_path='pages/index.ts',
            language='typescript',
            framework='nextjs',
            confidence=0.8
        )
        self._add_entry_point(entry_point, stack)

    def _parse_angular_config(self, file_path: Path, stack: ProjectStack):
        """Анализ angular.json для определения точки входа."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                angular_data = json.load(f)

            # Ищем main entry point в конфигурации
            projects = angular_data.get('projects', {})
            for project_name, project_config in projects.items():
                main_file = project_config.get('architect', {}).get('build', {}).get('options', {}).get('main')
                if main_file:
                    entry_point = EntryPoint(
                        type='angular',
                        file_path=main_file,
                        language='typescript',
                        framework='angular',
                        confidence=0.9
                    )
                    self._add_entry_point(entry_point, stack)

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Не удалось проанализировать angular.json: {e}")

    def _parse_vue_config(self, file_path: Path, stack: ProjectStack):
        """Анализ vue.config.js для определения точки входа."""
        entry_point = EntryPoint(
            type='vue',
            file_path='src/main.ts',
            language='typescript',
            framework='vue',
            confidence=0.8
        )
        self._add_entry_point(entry_point, stack)

    def _determine_main_entry_point(self, stack: ProjectStack):
        """Определение основной точки входа на основе уверенности и типа."""
        if not stack.entry_points:
            return

        # Сортируем точки входа по уверенности
        sorted_entries = sorted(stack.entry_points, key=lambda x: x.confidence, reverse=True)

        # Предпочитаем определенные типы
        preferred_types = ['main', 'app', 'docker', 'script']

        for preferred_type in preferred_types:
            for entry in sorted_entries:
                if entry.type == preferred_type:
                    stack.main_entry_point = entry
                    return

        # Если не нашли предпочтительный тип, берем самый уверенный
        stack.main_entry_point = sorted_entries[0]

    def _add_entry_point(self, entry_point: EntryPoint, stack: ProjectStack):
        """Добавление точки входа, если она еще не существует."""
        # Проверяем, существует ли уже такая точка входа
        for existing in stack.entry_points:
            if (existing.file_path == entry_point.file_path and
                    existing.type == entry_point.type):
                return

        stack.entry_points.append(entry_point)
        
        # Добавляем язык в список языков, если он определен в точке входа
        if entry_point.language:
            # Нормализация: kotlin -> java
            normalized_language = 'java' if entry_point.language in {'kotlin', 'java'} else entry_point.language
            allowed_languages = {'python', 'typescript', 'java', 'go'}
            if normalized_language in allowed_languages and normalized_language not in stack.languages:
                stack.languages.append(normalized_language)
                logger.debug(f"Добавлен язык из точки входа: {normalized_language}")

