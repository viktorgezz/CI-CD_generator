"""Анализатор языков программирования и менеджеров пакетов."""
import json
import logging
from pathlib import Path
from typing import Dict

from ..models import ProjectStack
from ..config import ConfigLoader
from ..utils import get_language_extensions, get_relevant_files

logger = logging.getLogger(__name__)


class LanguageAnalyzer:
    """Анализатор для определения языков программирования и менеджеров пакетов."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация анализатора.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config_loader = config_loader
        self.language_extensions = get_language_extensions()

    def analyze(self, repo_path: Path, stack: ProjectStack):
        """
        Анализ языков программирования и менеджеров пакетов.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        detected_files = {}

        # Сначала проверяем приоритетные менеджеры пакетов (Java, Go, Python) в корне
        # Они имеют приоритет над package.json
        # Приоритет: go.mod > build.gradle/build.gradle.kts > pom.xml > build.xml > Gemfile > composer.json > pyproject.toml > requirements.txt
        # go.mod имеет высший приоритет, так как Go проекты редко смешиваются с другими
        priority_package_managers = [
            ('go.mod', 'go mod', 'go_mod'),  # Высший приоритет для Go
            ('build.gradle', 'gradle', 'build_gradle'),  # Gradle имеет приоритет над Maven
            ('build.gradle.kts', 'gradle', 'build_gradle_kts'),
            ('pom.xml', 'maven', 'pom_xml'),
            ('build.xml', 'ant', 'build_xml'),  # Apache Ant
            ('Gemfile', 'bundler', 'gemfile'),  # Ruby
            ('composer.json', 'composer', 'composer_json'),  # PHP
            ('pyproject.toml', 'poetry', 'pyproject_toml'),  # Python (проверяем содержимое позже)
            ('requirements.txt', 'pip', 'requirements_txt'),  # Низший приоритет для Python
        ]
        
        for pm_file, pm_name, file_key in priority_package_managers:
            pm_path = repo_path / pm_file
            if pm_path.exists() and pm_path.is_file():
                # Специальная обработка pyproject.toml - проверяем, используется ли poetry
                # НО пропускаем, если уже установлен более приоритетный менеджер (go.mod, build.gradle, pom.xml)
                if pm_file == 'pyproject.toml':
                    # КРИТИЧНО: ВСЕГДА проверяем наличие более приоритетных менеджеров ПЕРЕД обработкой pyproject.toml
                    # Это должно быть ПЕРВОЙ проверкой, до любых других действий
                    # Проверяем наличие go.mod ПЕРВЫМ, так как он имеет высший приоритет
                    go_mod_path = repo_path / 'go.mod'
                    if go_mod_path.exists() and go_mod_path.is_file():
                        logger.info(f"pyproject.toml найден в начальной проверке, но go.mod тоже есть в корне - go.mod имеет приоритет, пропускаем pyproject.toml")
                        continue  # Пропускаем pyproject.toml, если есть go.mod - ВАЖНО: continue, а не break!
                    
                    high_priority_files = ['build.gradle', 'build.gradle.kts', 'pom.xml', 'build.xml', 'Gemfile', 'composer.json']
                    has_high_priority = any((repo_path / f).exists() and (repo_path / f).is_file() for f in high_priority_files)
                    if has_high_priority:
                        logger.info(f"pyproject.toml найден в начальной проверке, но есть более приоритетный менеджер пакетов в корне, пропускаем pyproject.toml")
                        continue  # Пропускаем pyproject.toml, если есть более приоритетный менеджер
                    
                    # Если уже установлен приоритетный менеджер (go.mod, build.gradle, pom.xml), пропускаем
                    if stack.package_manager and stack.package_manager in {'go mod', 'gradle', 'maven', 'ant', 'bundler', 'composer'}:
                        logger.info(f"pyproject.toml найден в начальной проверке, но уже установлен приоритетный менеджер {stack.package_manager}, пропускаем")
                        continue
                    try:
                        import tomllib
                        with open(pm_path, 'rb') as f:
                            pyproject_data = tomllib.load(f)
                        # Проверяем наличие секции tool.poetry
                        if 'tool' in pyproject_data and 'poetry' in pyproject_data['tool']:
                            logger.info(f"Найден приоритетный менеджер пакетов: {pm_file} (poetry)")
                            stack.package_manager = pm_name
                            detected_files[file_key] = str(pm_path.relative_to(repo_path))
                            logger.info(f"Установлен package_manager: {pm_name}")
                            break
                        else:
                            # pyproject.toml есть, но не poetry - пропускаем, будет обработан позже
                            logger.debug(f"pyproject.toml найден, но не poetry, пропускаем")
                            continue
                    except (ImportError, Exception) as e:
                        logger.debug(f"Не удалось прочитать pyproject.toml: {e}")
                        # Если не удалось прочитать, не устанавливаем poetry (может быть setuptools)
                        continue
                else:
                    logger.info(f"Найден приоритетный менеджер пакетов: {pm_file}")
                    stack.package_manager = pm_name  # Всегда устанавливаем приоритетный менеджер
                    detected_files[file_key] = str(pm_path.relative_to(repo_path))
                    logger.info(f"Установлен package_manager: {pm_name}")
                    break  # Используем первый найденный (с наивысшим приоритетом)

        # Затем проверяем package.json в корне (если еще не установлен менеджер пакетов)
        package_json_path = repo_path / 'package.json'
        if package_json_path.exists() and package_json_path.is_file():
            if not stack.package_manager:
                logger.info(f"Найден package.json в корне: {package_json_path}")
                self._detect_package_manager('package.json', package_json_path, repo_path, stack, detected_files)
                logger.info(f"package_manager после обработки package.json: {stack.package_manager}")

        # Используем оптимизированную функцию для получения релевантных файлов
        # Ограничиваем размер файлов до 500KB для анализа языков
        relevant_files = get_relevant_files(repo_path, max_file_size=512 * 1024)
        logger.debug(f"Найдено релевантных файлов для анализа языков: {len(relevant_files)}")

        for file_path in relevant_files:
            filename = file_path.name
            file_path_str = str(file_path.relative_to(repo_path))

            # Определение языков по расширениям файлов
            file_suffix = file_path.suffix.lower() if file_path.suffix else None
            for language, extensions in self.language_extensions.items():
                # Проверяем расширение файла (с точкой) или имя файла без расширения для специальных случаев
                if file_suffix and file_suffix in extensions:
                    self._add_language(language, stack)
                    key = f'{language}_files'
                    detected_files[key] = detected_files.get(key, []) + [file_path_str]
                    logger.debug(f"Обнаружен файл {file_path_str} с языком {language} (расширение: {file_suffix})")
                    break  # Язык определен, переходим к следующему файлу

            # Определение менеджеров пакетов и сборщиков
            # КРИТИЧНО: Пропускаем обработку pyproject.toml в цикле, если go.mod существует в корне
            # Это должно быть ПЕРВОЙ проверкой перед вызовом _detect_package_manager
            if filename == 'pyproject.toml' and file_path.parent == repo_path:
                # Проверяем наличие go.mod ПЕРВЫМ, так как он имеет высший приоритет
                go_mod_path = repo_path / 'go.mod'
                if go_mod_path.exists() and go_mod_path.is_file():
                    logger.info(f"pyproject.toml найден в цикле файлов, но go.mod тоже есть в корне - go.mod имеет приоритет, пропускаем pyproject.toml")
                    detected_files['pyproject_toml'] = str(file_path.relative_to(repo_path))
                    continue
                # Проверяем, если уже установлен приоритетный менеджер
                high_priority_managers = {'go mod', 'gradle', 'maven', 'ant', 'bundler', 'composer'}
                if stack.package_manager in high_priority_managers:
                    logger.info(f"pyproject.toml найден в цикле файлов, но уже установлен приоритетный менеджер {stack.package_manager}, пропускаем")
                    detected_files['pyproject_toml'] = str(file_path.relative_to(repo_path))
                    continue
            
            self._detect_package_manager(filename, file_path, repo_path, stack, detected_files)

        stack.files_detected.update(detected_files)

    def _detect_package_manager(self, filename: str, file_path: Path, repo_path: Path, stack: ProjectStack, detected_files: Dict):
        """Определение менеджера пакетов по имени файла."""
        # Приоритетные менеджеры пакетов (не должны перезаписываться package.json)
        priority_managers = {'maven', 'gradle', 'ant', 'go mod', 'pip', 'poetry', 'setuptools'}
        
        # КРИТИЧНО: Если pyproject.toml в корне и go.mod существует, НИКОГДА не обрабатываем pyproject.toml
        if filename == 'pyproject.toml' and file_path.parent == repo_path:
            go_mod_path = repo_path / 'go.mod'
            if go_mod_path.exists() and go_mod_path.is_file():
                logger.info(f"pyproject.toml найден в _detect_package_manager, но go.mod тоже есть в корне - go.mod имеет приоритет, пропускаем")
                detected_files['pyproject_toml'] = str(file_path.relative_to(repo_path))
                return
        
        # Специальная обработка package.json (не входит в общий map, так как требует анализа содержимого)
        if filename == 'package.json':
            # Не перезаписываем приоритетные менеджеры пакетов
            if stack.package_manager in priority_managers:
                logger.info(f"Пропущен package.json: уже установлен приоритетный менеджер {stack.package_manager}")
                detected_files['package_json'] = str(file_path.relative_to(repo_path))
                return
            
            logger.info(f"Обработка package.json: {file_path}")
            self._analyze_package_json(file_path, stack)
            logger.info(f"package_manager после _analyze_package_json: {stack.package_manager}")
            detected_files['package_json'] = str(file_path.relative_to(repo_path))
            return
        
        package_manager_map = {
            'requirements.txt': ('pip', 'requirements_txt'),
            'pyproject.toml': ('poetry', 'pyproject_toml'),
            'setup.py': ('setuptools', 'setup_py'),
            'go.mod': ('go mod', 'go_mod'),
            'build.gradle': ('gradle', 'build_gradle'),
            'build.gradle.kts': ('gradle', 'build_gradle_kts'),
            'pom.xml': ('maven', 'pom_xml'),
            'build.xml': ('ant', 'build_xml'),  # Apache Ant для Java
            'composer.json': ('composer', 'composer_json'),
            'Cargo.toml': ('cargo', 'cargo_toml'),
            'Gemfile': ('bundler', 'gemfile'),
            'mix.exs': ('mix', 'mix_exs'),
            'pubspec.yaml': ('pub', 'pubspec_yaml'),
            'Podfile': ('cocoapods', 'podfile'),
            'Cartfile': ('carthage', 'cartfile'),
            'Package.swift': ('swift package manager', 'package_swift'),
        }

        if filename in package_manager_map:
            pm_name, file_key = package_manager_map[filename]
            # Приоритетные менеджеры всегда устанавливаются, даже если уже есть package_manager
            # Но только если файл в корне репозитория (для избежания конфликтов с подпроектами)
            is_root_file = file_path.parent == repo_path
            
            # Если уже установлен приоритетный менеджер из корня, не перезаписываем его
            if stack.package_manager in priority_managers and not is_root_file:
                # Уже есть приоритетный менеджер из корня, не перезаписываем файлами из поддиректорий
                detected_files[file_key] = str(file_path.relative_to(repo_path))
                return
            
            # Специальная обработка pyproject.toml - проверяем, используется ли poetry
            # НО только если еще не установлен приоритетный менеджер (go.mod, build.gradle, pom.xml и т.д.)
            if filename == 'pyproject.toml' and is_root_file:
                # ВСЕГДА проверяем, есть ли более приоритетные менеджеры в корне ПЕРЕД обработкой pyproject.toml
                # Это критично для проектов типа Gitea, где есть и go.mod и pyproject.toml
                high_priority_files = ['go.mod', 'build.gradle', 'build.gradle.kts', 'pom.xml', 'build.xml', 'Gemfile', 'composer.json']
                has_high_priority = any((repo_path / f).exists() and (repo_path / f).is_file() for f in high_priority_files)
                if has_high_priority:
                    logger.info(f"pyproject.toml найден в цикле файлов, но есть более приоритетный менеджер пакетов в корне, пропускаем pyproject.toml")
                    detected_files[file_key] = str(file_path.relative_to(repo_path))
                    return
                # Если уже установлен приоритетный менеджер (go.mod, build.gradle, pom.xml, ant, bundler, composer), не перезаписываем
                high_priority_managers = {'go mod', 'gradle', 'maven', 'ant', 'bundler', 'composer'}
                if stack.package_manager in high_priority_managers:
                    logger.info(f"pyproject.toml найден в цикле файлов, но уже установлен приоритетный менеджер {stack.package_manager}, пропускаем pyproject.toml")
                    detected_files[file_key] = str(file_path.relative_to(repo_path))
                    return
                # Дополнительная проверка: если go.mod существует в корне, НИКОГДА не устанавливаем poetry
                go_mod_path = repo_path / 'go.mod'
                if go_mod_path.exists() and go_mod_path.is_file():
                    logger.info(f"pyproject.toml найден, но go.mod тоже есть в корне - go.mod имеет приоритет, пропускаем pyproject.toml")
                    detected_files[file_key] = str(file_path.relative_to(repo_path))
                    return
                try:
                    import tomllib
                    with open(file_path, 'rb') as f:
                        pyproject_data = tomllib.load(f)
                    # Проверяем наличие секции tool.poetry
                    if 'tool' in pyproject_data and 'poetry' in pyproject_data['tool']:
                        # КРИТИЧНО: НЕ устанавливаем poetry, если go.mod существует в корне
                        # Это должно быть ПЕРВОЙ проверкой перед установкой poetry
                        go_mod_path = repo_path / 'go.mod'
                        if go_mod_path.exists() and go_mod_path.is_file():
                            logger.info(f"pyproject.toml содержит poetry, но go.mod тоже есть в корне - go.mod имеет приоритет, не устанавливаем poetry")
                            detected_files[file_key] = str(file_path.relative_to(repo_path))
                            return
                        # НЕ устанавливаем poetry, если уже установлен приоритетный менеджер
                        high_priority_managers = {'go mod', 'gradle', 'maven', 'ant', 'bundler', 'composer'}
                        if stack.package_manager in high_priority_managers:
                            logger.info(f"pyproject.toml содержит poetry, но уже установлен приоритетный менеджер {stack.package_manager}, не перезаписываем")
                            detected_files[file_key] = str(file_path.relative_to(repo_path))
                            return
                        if not stack.package_manager or stack.package_manager not in priority_managers:
                            stack.package_manager = pm_name
                            logger.info(f"Установлен менеджер пакетов poetry (файл в корне: {filename})")
                    else:
                        # pyproject.toml есть, но не poetry - не устанавливаем, будет обработан как setuptools позже
                        logger.debug(f"pyproject.toml найден, но не poetry, пропускаем")
                        detected_files[file_key] = str(file_path.relative_to(repo_path))
                        return
                except (ImportError, Exception) as e:
                    logger.debug(f"Не удалось прочитать pyproject.toml: {e}")
                    # Если не удалось прочитать, не устанавливаем poetry
                    detected_files[file_key] = str(file_path.relative_to(repo_path))
                    return
            
            if pm_name in priority_managers:
                # Для приоритетных менеджеров: если файл в корне, всегда устанавливаем
                # Если файл не в корне, устанавливаем только если еще не установлен менеджер
                if is_root_file:
                    stack.package_manager = pm_name
                    logger.info(f"Установлен приоритетный менеджер пакетов: {pm_name} (файл в корне: {filename})")
                elif not stack.package_manager:
                    stack.package_manager = pm_name
                    logger.info(f"Установлен приоритетный менеджер пакетов: {pm_name} (файл: {filename})")
            elif not stack.package_manager:
                stack.package_manager = pm_name
            detected_files[file_key] = str(file_path.relative_to(repo_path))

    def _analyze_package_json(self, file_path: Path, stack: ProjectStack):
        """Анализ package.json для определения менеджера пакетов и фреймворков."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)

            # Определение менеджера пакетов
            if (file_path.parent / 'yarn.lock').exists():
                stack.package_manager = 'yarn'
                logger.debug(f"Определен менеджер пакетов: yarn (найден yarn.lock)")
            elif (file_path.parent / 'pnpm-lock.yaml').exists():
                stack.package_manager = 'pnpm'
                logger.debug(f"Определен менеджер пакетов: pnpm (найден pnpm-lock.yaml)")
            elif (file_path.parent / 'package-lock.json').exists():
                stack.package_manager = 'npm'
                logger.debug(f"Определен менеджер пакетов: npm (найден package-lock.json)")
            else:
                stack.package_manager = 'npm'  # по умолчанию для Node.js проектов
                logger.debug(f"Определен менеджер пакетов: npm (по умолчанию, lock файлы не найдены)")

            # Определение фреймворков из зависимостей (только поддерживаемые)
            dependencies = {**package_data.get('dependencies', {}),
                            **package_data.get('devDependencies', {})}

            framework_mappings = {
                # TypeScript/JavaScript фреймворки (Frontend)
                'react': 'react',
                'vue': 'vue',
                '@angular/core': 'angular',
                'next': 'nextjs',
                # TypeScript/JavaScript фреймворки (Backend)
                'express': 'express',
                '@nestjs/core': 'nest',
            }

            for dep, framework in framework_mappings.items():
                if dep in dependencies:
                    if framework not in stack.frameworks:
                        stack.frameworks.append(framework)

        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.warning(f"Не удалось проанализировать package.json: {e}")

    def _add_language(self, language: str, stack: ProjectStack):
        """Добавление языка в список, если его еще нет.
        
        Поддерживаются только 4 языка: Python, TypeScript, Java/Kotlin, Go.
        """
        # Разрешенные языки
        allowed_languages = {'python', 'typescript', 'java', 'go'}
        
        # Нормализация языка (kotlin -> java)
        normalized_language = 'java' if language in {'kotlin', 'java'} else language
        
        # Логирование попыток добавить неразрешенные языки
        if language not in allowed_languages and normalized_language not in allowed_languages:
            logger.debug(f"Попытка добавить неразрешенный язык: {language} (нормализован: {normalized_language})")
            return
        
        if normalized_language in allowed_languages and normalized_language not in stack.languages:
            stack.languages.append(normalized_language)
            logger.debug(f"Добавлен язык: {normalized_language}")

