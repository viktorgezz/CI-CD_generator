"""Сервис для генерации CI/CD пайплайнов."""
import sys
from pathlib import Path
from typing import Dict, Any

# Добавляем путь к ci_generator в sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
CI_GENERATOR_PATH = PROJECT_ROOT / "ci_generator"
if str(CI_GENERATOR_PATH) not in sys.path:
    sys.path.insert(0, str(CI_GENERATOR_PATH))

try:
    from generator.stage_selector import select_stages
    from generator.renderer import PipelineRenderer
except ImportError:
    # Попытка прямого импорта
    import importlib.util
    
    # Импорт stage_selector
    spec = importlib.util.spec_from_file_location("stage_selector", CI_GENERATOR_PATH / "generator" / "stage_selector.py")
    stage_selector_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stage_selector_module)
    select_stages = stage_selector_module.select_stages
    
    # Импорт renderer
    spec = importlib.util.spec_from_file_location("renderer", CI_GENERATOR_PATH / "generator" / "renderer.py")
    renderer_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer_module)
    PipelineRenderer = renderer_module.PipelineRenderer
from app.schemas import ProjectAnalysis


def generate_pipeline(analysis: ProjectAnalysis, user_settings: Dict[str, Any]) -> str:
    """
    Сгенерировать CI/CD пайплайн на основе анализа и настроек.
    
    Args:
        analysis: Анализ технологического стека
        user_settings: Настройки генерации пайплайна
    
    Returns:
        str: Сгенерированный пайплайн в формате YAML
    """
    # Конвертация ProjectAnalysis в словарь
    analysis_dict = {
        "languages": analysis.languages,
        "frameworks": analysis.frameworks,
        "frontend_frameworks": analysis.frontend_frameworks,
        "backend_frameworks": analysis.backend_frameworks,
        "package_manager": analysis.package_manager,
        "test_runner": analysis.test_runner,
        "java_version": analysis.java_version,  # Версия Java из pom.xml
        "docker": analysis.docker,
        "docker_context": analysis.docker_context,
        "dockerfile_path": analysis.dockerfile_path,
        "dockerfile_paths": analysis.dockerfile_paths,
        "kubernetes": analysis.kubernetes,
        "terraform": analysis.terraform,
        "databases": analysis.databases,
    }
    
    user_settings_dict = user_settings.copy()
    
    # Определение платформы
    platform = (user_settings_dict.get("platform") or "gitlab").lower()
    
    # Выбор стадий
    stages = select_stages(analysis_dict, user_settings_dict)
    
    # Определяем build_tool для Java
    build_tool = None
    if "java" in analysis_dict.get("languages", []):
        package_manager = analysis_dict.get("package_manager", "").lower()
        if package_manager in ["maven", "gradle"]:
            build_tool = package_manager
        elif package_manager == "ant":
            build_tool = "ant"
        else:
            build_tool = user_settings_dict.get("build_tool", "maven")
    
    # Определяем основной язык
    languages = [l.lower() for l in analysis_dict.get("languages", [])]
    main_languages = ["python", "java", "kotlin", "go", "golang", "typescript", "javascript"]
    language = None
    for lang in languages:
        if lang in main_languages:
            language = lang
            break
    if not language and languages:
        language = languages[0]
    elif not language:
        language = "python"
    
    # Создание контекста для шаблонов
    ctx = {
        "language": language,
        "project_name": user_settings_dict.get("project_name", "myapp"),
        "build_tool": build_tool or user_settings_dict.get("build_tool"),
    }
    
    # Добавляем версию для используемого языка
    if language == "python":
        ctx["python_version"] = user_settings_dict.get("python_version", analysis_dict.get("python_version", "3.11"))
    elif language in ["java", "kotlin"]:
        ctx["java_version"] = user_settings_dict.get("java_version", analysis_dict.get("java_version", "17"))
    elif language in ["go", "golang"]:
        ctx["go_version"] = user_settings_dict.get("go_version", analysis_dict.get("go_version", "1.21"))
    elif language in ["typescript", "javascript"]:
        ctx["node_version"] = user_settings_dict.get("node_version", analysis_dict.get("node_version", "18"))
    
    # Добавляем build_image для Java/Kotlin
    if language in ["java", "kotlin"]:
        # Используем версию Java из анализа, если она определена, иначе из настроек, иначе 17
        java_version = analysis_dict.get('java_version') or user_settings_dict.get('java_version', '17')
        ctx["java_version"] = java_version  # Сохраняем в контекст для шаблонов
        ctx["build_image"] = user_settings_dict.get("build_image") or (
            f"maven:3.9-eclipse-temurin-{java_version}" 
            if (build_tool or user_settings_dict.get("build_tool") or "maven") == "maven"
            else f"gradle:8.5-jdk{java_version}"
            if (build_tool or user_settings_dict.get("build_tool")) == "gradle"
            else None
        )
    
    # Добавляем остальные поля
    # Получаем список всех Dockerfile
    dockerfile_paths = analysis_dict.get("dockerfile_paths", [])
    if not dockerfile_paths and analysis_dict.get("dockerfile_path"):
        dockerfile_paths = [analysis_dict.get("dockerfile_path")]
    
    ctx.update({
        "registry": user_settings_dict.get("docker_registry", analysis_dict.get("docker_registry", "$CI_REGISTRY")),
        "tag": user_settings_dict.get("docker_tag", "$CI_COMMIT_SHORT_SHA"),
        "variables": user_settings_dict.get("variables", {}),
        "triggers": user_settings_dict.get("triggers", {}),
        "docker_context": user_settings_dict.get("docker_context", analysis_dict.get("docker_context", ".")),
        "dockerfile_path": user_settings_dict.get("dockerfile_path", analysis_dict.get("dockerfile_path", "Dockerfile")),
        "dockerfile_paths": dockerfile_paths,  # Список всех Dockerfile
        "analysis": analysis_dict,
        "user_settings": user_settings_dict,
        "use_docker_compose": user_settings_dict.get("use_docker_compose", False),  # Флаг для генерации docker-compose
    })
    
    # Рендеринг пайплайна
    templates_root = CI_GENERATOR_PATH / "pipelines"
    renderer = PipelineRenderer(templates_root=str(templates_root))
    
    if platform == "gitlab":
        return renderer.render_gitlab(stages, ctx)
    elif platform == "jenkins":
        return renderer.render_jenkins(stages, ctx)
    else:
        raise ValueError(f"Unsupported platform: {platform}")

