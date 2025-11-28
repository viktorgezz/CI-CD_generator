"""Сервис для анализа технологического стека репозитория."""
import sys
import os
from pathlib import Path
from typing import Optional

# Добавляем путь к корню проекта в sys.path для правильной работы импортов
PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Устанавливаем PYTHONPATH
os.environ['PYTHONPATH'] = str(PROJECT_ROOT) + os.pathsep + os.environ.get('PYTHONPATH', '')

# Импортируем через sys.path (stack_recognize должен быть в PYTHONPATH)
try:
    # Пробуем импортировать как пакет
    import stack_recognize.detector as detector_module
    ProjectStackDetector = detector_module.ProjectStackDetector
except ImportError:
    # Если не работает, пробуем прямой импорт
    STACK_RECOGNIZE_PATH = PROJECT_ROOT / "stack_recognize"
    sys.path.insert(0, str(STACK_RECOGNIZE_PATH))
    
    # Загружаем модули в правильном порядке через importlib
    import importlib.util
    
    # models
    models_spec = importlib.util.spec_from_file_location("stack_recognize.models", STACK_RECOGNIZE_PATH / "models.py")
    models_module = importlib.util.module_from_spec(models_spec)
    sys.modules['stack_recognize.models'] = models_module
    sys.modules['models'] = models_module
    models_spec.loader.exec_module(models_module)
    
    # config
    config_spec = importlib.util.spec_from_file_location("stack_recognize.config", STACK_RECOGNIZE_PATH / "config.py")
    config_module = importlib.util.module_from_spec(config_spec)
    sys.modules['stack_recognize.config'] = config_module
    sys.modules['config'] = config_module
    config_spec.loader.exec_module(config_module)
    
    # utils
    utils_spec = importlib.util.spec_from_file_location("stack_recognize.utils", STACK_RECOGNIZE_PATH / "utils.py")
    utils_module = importlib.util.module_from_spec(utils_spec)
    sys.modules['stack_recognize.utils'] = utils_module
    sys.modules['utils'] = utils_module
    utils_spec.loader.exec_module(utils_module)
    
    # analyzers пакет
    analyzers_path = STACK_RECOGNIZE_PATH / "analyzers"
    analyzers_init = importlib.util.spec_from_file_location("stack_recognize.analyzers", analyzers_path / "__init__.py")
    analyzers_pkg = importlib.util.module_from_spec(analyzers_init)
    sys.modules['stack_recognize.analyzers'] = analyzers_pkg
    sys.modules['analyzers'] = analyzers_pkg
    analyzers_init.loader.exec_module(analyzers_pkg)
    
    # Загружаем каждый анализатор
    for analyzer_file in sorted(analyzers_path.glob("*.py")):
        if analyzer_file.name != "__init__.py":
            module_name = analyzer_file.stem
            spec = importlib.util.spec_from_file_location(
                f"stack_recognize.analyzers.{module_name}", 
                analyzer_file
            )
            module = importlib.util.module_from_spec(spec)
            sys.modules[f"stack_recognize.analyzers.{module_name}"] = module
            sys.modules[f"analyzers.{module_name}"] = module
            spec.loader.exec_module(module)
    
    # detector
    detector_spec = importlib.util.spec_from_file_location("stack_recognize.detector", STACK_RECOGNIZE_PATH / "detector.py")
    detector_module = importlib.util.module_from_spec(detector_spec)
    sys.modules['stack_recognize.detector'] = detector_module
    sys.modules['detector'] = detector_module
    detector_spec.loader.exec_module(detector_module)
    ProjectStackDetector = detector_module.ProjectStackDetector
from app.schemas import ProjectAnalysis


def _build_authenticated_url(repo_url: str, token: Optional[str]) -> str:
    """Построить URL с токеном, если он передан."""
    if not token:
        return repo_url

    # Если в URL уже есть креды, не трогаем
    if "@" in repo_url:
        return repo_url

    if "://" not in repo_url:
        return repo_url

    scheme, rest = repo_url.split("://", 1)

    if "gitlab" in rest:
        return f"{scheme}://oauth2:{token}@{rest}"

    return f"{scheme}://{token}@{rest}"


def _extract_java_version_from_pom(stack) -> Optional[str]:
    """Извлечь версию Java из pom.xml файлов."""
    import re
    import xml.etree.ElementTree as ET
    
    # Получаем все pom.xml файлы
    pom_files = []
    if hasattr(stack, "files_detected"):
        pom_files_list = stack.files_detected.get("pom_xml") or []
        if isinstance(pom_files_list, list):
            pom_files = pom_files_list
        elif isinstance(pom_files_list, str):
            pom_files = [pom_files_list]
    
    # Если нет в files_detected, пробуем найти через другие источники
    if not pom_files and hasattr(stack, "files_detected"):
        # Ищем pom.xml в других ключах
        for key, value in stack.files_detected.items():
            if "pom" in key.lower() or "maven" in key.lower():
                if isinstance(value, list):
                    pom_files.extend(value)
                elif isinstance(value, str) and "pom.xml" in value:
                    pom_files.append(value)
    
    # Пробуем найти версию Java в pom.xml
    for pom_path in pom_files:
        try:
            # Если это путь относительно репозитория, нужно получить полный путь
            # Но у нас нет доступа к repo_path здесь, поэтому пробуем просто прочитать
            # В реальности это должно работать при анализе репозитория
            pass
        except:
            pass
    
    # Возвращаем None, если не удалось определить
    return None

def _convert_stack_to_analysis(stack) -> ProjectAnalysis:
    """Конвертировать ProjectStack в ProjectAnalysis."""
    # Извлечение docker путей - получаем все Dockerfile
    docker_context = None
    dockerfile_path = None
    dockerfile_paths = []
    
    # Получаем все Dockerfile из docker_all или docker
    docker_all = stack.files_detected.get("docker_all") if hasattr(stack, "files_detected") else None
    docker_files = stack.files_detected.get("docker") if hasattr(stack, "files_detected") else None
    
    # Собираем все Dockerfile
    if docker_all:
        if isinstance(docker_all, list):
            dockerfile_paths = docker_all
        elif isinstance(docker_all, str):
            dockerfile_paths = [docker_all]
    elif docker_files:
        if isinstance(docker_files, list):
            dockerfile_paths = docker_files
        elif isinstance(docker_files, str):
            dockerfile_paths = [docker_files]
    
    # Убираем дубликаты и сохраняем порядок
    seen = set()
    unique_paths = []
    for path in dockerfile_paths:
        if path not in seen:
            seen.add(path)
            unique_paths.append(path)
    dockerfile_paths = unique_paths
    
    # Определяем основной Dockerfile (первый) и его контекст
    if dockerfile_paths:
        dockerfile_path = dockerfile_paths[0]
        from pathlib import Path as PathLib
        context_path = str(PathLib(dockerfile_path).parent)
        docker_context = context_path if context_path != "." else ""
    
    # Конвертация test_runner из списка в строку
    test_runner = None
    if stack.test_runner:
        if isinstance(stack.test_runner, list):
            test_runner = stack.test_runner[0] if stack.test_runner else None
        else:
            test_runner = str(stack.test_runner)
    
    # Фильтрация языков: только поддерживаемые
    allowed_languages = {'python', 'typescript', 'java', 'go'}
    filtered_languages = []
    for lang in stack.languages:
        normalized = 'java' if lang in {'kotlin', 'java'} else lang
        if normalized in allowed_languages and normalized not in filtered_languages:
            filtered_languages.append(normalized)
    
    return ProjectAnalysis(
        languages=filtered_languages,
        frameworks=stack.frameworks,
        frontend_frameworks=stack.frontend_frameworks,
        backend_frameworks=stack.backend_frameworks,
        package_manager=stack.package_manager,
        test_runner=test_runner,
        java_version=None,  # Будет установлено в analyze_repository
        docker=stack.docker,
        docker_context=docker_context or "",
        dockerfile_path=dockerfile_path,
        dockerfile_paths=dockerfile_paths,
        kubernetes=stack.kubernetes,
        terraform=stack.terraform,
        databases=stack.databases,
    )


def _extract_java_version_from_pom(repo_path: Path) -> Optional[str]:
    """Извлечь версию Java из pom.xml файлов в репозитории."""
    import re
    
    # Ищем все pom.xml файлы
    pom_files = list(repo_path.rglob("pom.xml"))
    if not pom_files:
        return None
    
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
                    return version
        except Exception:
            continue
    
    return None

def analyze_repository(repo_url: str, token: str = "") -> ProjectAnalysis:
    """
    Проанализировать репозиторий и вернуть анализ стека.
    
    Args:
        repo_url: URL Git-репозитория
        token: Токен для клонирования (опционально)
    
    Returns:
        ProjectAnalysis: Анализ технологического стека
    """
    detector = ProjectStackDetector()
    auth_url = _build_authenticated_url(repo_url, token)
    stack = detector.detect_stack(auth_url)
    
    # Извлекаем версию Java из stack.files_detected (определяется в detector)
    java_version = stack.files_detected.get('java_version') if hasattr(stack, 'files_detected') else None
    
    analysis = _convert_stack_to_analysis(stack)
    
    # Сохраняем версию Java в анализ, если она определена
    if java_version:
        analysis.java_version = java_version
    
    return analysis


def get_full_stack(repo_url: str, token: str = ""):
    """
    Получить полный стек проекта (ProjectStack объект).
    
    Args:
        repo_url: URL Git-репозитория
        token: Токен для клонирования (опционально)
    
    Returns:
        ProjectStack: Полный объект стека
    """
    detector = ProjectStackDetector()
    auth_url = _build_authenticated_url(repo_url, token)
    return detector.detect_stack(auth_url)

