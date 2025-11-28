"""Анализатор фреймворков."""
import re
import logging
from pathlib import Path

from ..models import ProjectStack
from ..config import ConfigLoader, PatternConfig
from ..utils import get_relevant_files, read_file_sample, get_language_by_extension

logger = logging.getLogger(__name__)


class FrameworkAnalyzer:
    """Анализатор для определения фреймворков."""

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
        Анализ фреймворков.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        # Анализ по файлам
        self._analyze_by_files(repo_path, stack)

        # Анализ по содержимому файлов
        self._analyze_by_content(repo_path, stack)

        # Классификация фреймворков
        self._classify_frameworks(stack)

    def _analyze_by_files(self, repo_path: Path, stack: ProjectStack):
        """Анализ фреймворков по наличию специфичных файлов."""
        framework_files = {
            # Python фреймворки
            # Django: manage.py - уникальный файл Django, wsgi.py/asgi.py - общие для WSGI/ASGI
            'django': ['manage.py'],
            # Flask: app.py и application.py - типичные имена для Flask приложений
            # wsgi.py убран, так как он общий для всех WSGI приложений (включая Django)
            'flask': ['app.py', 'application.py'],
            # FastAPI не определяется только по main.py - слишком общий файл
            # Java/Kotlin фреймворки
            # spring-boot определяется по pom.xml/build.gradle только если есть Spring Boot зависимости
            # quarkus и micronaut не определяются только по pom.xml - слишком общий файл
            'spring-boot': [],  # Определяется только по содержимому файлов
            'quarkus': [],  # Определяется только по содержимому файлов
            'micronaut': ['micronaut-cli.yml'],
            # TypeScript фреймворки
            'nextjs': ['next.config.js'],
            'nestjs': ['nest-cli.json'],
        }

        # Используем оптимизированный поиск файлов
        relevant_files = get_relevant_files(repo_path)
        logger.debug(f"Найдено релевантных файлов для анализа фреймворков: {len(relevant_files)}")
        
        for framework, files in framework_files.items():
            for pattern in files:
                # Используем get_relevant_files для фильтрации
                matches = [f for f in relevant_files 
                          if f.name == pattern or str(f.relative_to(repo_path)) == pattern]
                if matches:
                    if framework not in stack.frameworks:
                        stack.frameworks.append(framework)
                        logger.debug(f"Обнаружен фреймворк {framework} по файлу: {[str(m.relative_to(repo_path)) for m in matches]}")
                    break

    def _analyze_by_content(self, repo_path: Path, stack: ProjectStack):
        """Анализ фреймворков по содержимому файлов."""
        # Только расширения поддерживаемых языков: Python, TypeScript/JavaScript, Java/Kotlin, Go
        code_extensions = ['.py', '.pyw', '.ts', '.tsx', '.js', '.jsx', '.java', '.kt', '.kts', '.go']

        # Используем оптимизированную функцию для получения только релевантных файлов
        # Ограничиваем размер файлов до 200KB для анализа фреймворков
        relevant_files = get_relevant_files(repo_path, extensions=code_extensions, max_file_size=200 * 1024)
        logger.info(f"Найдено файлов для анализа фреймворков по содержимому: {len(relevant_files)}")

        for file_path in relevant_files:
            # Читаем начало файла (достаточно для поиска импортов)
            # Увеличиваем лимит для лучшего обнаружения фреймворков
            content = read_file_sample(file_path, max_lines=100, max_bytes=8192)

            if not content:
                continue
            
            # Логируем первые несколько файлов для отладки
            file_rel = str(file_path.relative_to(repo_path))
            if 'main.py' in file_rel or 'app.py' in file_rel:
                logger.info(f"Анализ файла {file_rel}, первые 200 символов: {content[:200]}")

            # Определяем язык файла по расширению
            file_lang = get_language_by_extension(file_path.suffix)
            
            for framework, patterns in self.pattern_config.FRAMEWORK_PATTERNS.items():
                if framework not in stack.frameworks:
                    # Проверка совместимости языка файла и фреймворка
                    # Java/Kotlin фреймворки применяются только к Java/Kotlin файлам
                    java_frameworks = {'spring', 'spring-boot', 'quarkus', 'micronaut', 'vertx'}
                    if framework in java_frameworks and file_lang != 'java':
                        continue
                    
                    # Python фреймворки применяются только к Python файлам
                    python_frameworks = {'django', 'flask', 'fastapi'}
                    if framework in python_frameworks and file_lang != 'python':
                        continue
                    
                    # Go фреймворки применяются только к Go файлам
                    go_frameworks = {'gin', 'echo', 'fiber', 'beego'}
                    if framework in go_frameworks and file_lang != 'go':
                        continue
                    
                    # TypeScript/JavaScript фреймворки применяются только к TypeScript файлам
                    ts_frameworks = {'express', 'nest', 'react', 'vue', 'angular', 'nextjs'}
                    if framework in ts_frameworks and file_lang != 'typescript':
                        continue
                    
                    # Специальная логика для Spring: если уже определен spring-boot, не добавлять spring
                    # spring-boot включает в себя spring, поэтому spring избыточен
                    if framework == 'spring' and 'spring-boot' in stack.frameworks:
                        continue
                    
                    # Quarkus и Spring Boot не используются вместе - если найден spring-boot, не добавлять quarkus
                    if framework == 'quarkus' and 'spring-boot' in stack.frameworks:
                        continue
                    
                    # И наоборот: если найден quarkus, не добавлять spring-boot
                    if framework == 'spring-boot' and 'quarkus' in stack.frameworks:
                        continue
                    
                    # Специальная логика для Flask: если уже определен Django, 
                    # требуем более строгие признаки Flask (чтобы избежать ложных срабатываний)
                    if framework == 'flask' and 'django' in stack.frameworks:
                        # Для Flask при наличии Django требуем явные признаки: Flask() или @app.route
                        flask_strict_patterns = [r'\bFlask\(\)', r'@app\.route', r'from flask import']
                        found_flask = False
                        for pattern in flask_strict_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_flask = True
                                stack.frameworks.append(framework)
                                logger.info(f"Обнаружен фреймворк {framework} в файле {file_rel} по строгому паттерну: {pattern}")
                                break
                        if found_flask:
                            break
                        continue
                    
                    # Специальная логика для Vue: не путать createApp с createApplication
                    if framework == 'vue':
                        # Для Vue требуем более строгие признаки, чтобы не путать с Express createApplication
                        vue_strict_patterns = [r'Vue\.createApp\(', r'from [\'"]vue[\'"]', r'import.*vue', r'createApp\(.*vue']
                        found_vue = False
                        for pattern in vue_strict_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_vue = True
                                stack.frameworks.append(framework)
                                logger.info(f"Обнаружен фреймворк {framework} в файле {file_rel} по строгому паттерну: {pattern}")
                                break
                        if found_vue:
                            break
                        # Если найден createApplication (Express), не добавлять Vue
                        if re.search(r'createApplication', content, re.IGNORECASE):
                            logger.debug(f"Пропущен Vue в файле {file_rel}, так как найден createApplication (Express)")
                            continue
                        continue
                    
                    # Специальная логика для Django: если уже определен Flask,
                    # требуем явные признаки Django (manage.py уже проверен в _analyze_by_files)
                    if framework == 'django' and 'flask' in stack.frameworks:
                        # Для Django при наличии Flask требуем явные признаки: manage.py или from django
                        django_strict_patterns = [r'from django', r'import django', r'DJANGO_SETTINGS']
                        found_django = False
                        for pattern in django_strict_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_django = True
                                # Django уже должен быть определен по manage.py, но на всякий случай
                                if framework not in stack.frameworks:
                                    stack.frameworks.append(framework)
                                logger.info(f"Обнаружен фреймворк {framework} в файле {file_rel} по строгому паттерну: {pattern}")
                                break
                        if found_django:
                            break
                        continue
                    
                    # Обычная проверка паттернов
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            stack.frameworks.append(framework)
                            logger.info(f"Обнаружен фреймворк {framework} в файле {file_rel} по паттерну: {pattern}")
                            
                            # Если найден spring-boot, удалить spring (если он был добавлен ранее)
                            if framework == 'spring-boot' and 'spring' in stack.frameworks:
                                stack.frameworks.remove('spring')
                                logger.info("Удален фреймворк 'spring', так как найден 'spring-boot'")
                            
                            # Если найден spring-boot, удалить quarkus (если он был добавлен ранее)
                            if framework == 'spring-boot' and 'quarkus' in stack.frameworks:
                                stack.frameworks.remove('quarkus')
                                logger.info("Удален фреймворк 'quarkus', так как найден 'spring-boot'")
                            
                            # Если найден quarkus, удалить spring-boot (если он был добавлен ранее)
                            if framework == 'quarkus' and 'spring-boot' in stack.frameworks:
                                stack.frameworks.remove('spring-boot')
                                logger.info("Удален фреймворк 'spring-boot', так как найден 'quarkus'")
                            
                            break

    def _classify_frameworks(self, stack: ProjectStack):
        """Классификация фреймворков по типам."""
        for framework in stack.frameworks:
            if framework in self.pattern_config.FRONTEND_FRAMEWORKS:
                if framework not in stack.frontend_frameworks:
                    stack.frontend_frameworks.append(framework)
            elif framework in self.pattern_config.BACKEND_FRAMEWORKS:
                if framework not in stack.backend_frameworks:
                    stack.backend_frameworks.append(framework)
            elif framework in self.pattern_config.MOBILE_FRAMEWORKS:
                if framework not in stack.mobile_frameworks:
                    stack.mobile_frameworks.append(framework)

