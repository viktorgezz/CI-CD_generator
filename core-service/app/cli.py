"""CLI интерфейс для Self-Deploy Core Service."""
import sys
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import click

from app import storage
from app.database import Base, engine, get_db
from app.schemas import Project, ProjectCreate, PipelineGenerationCreate
from app.services.analyzer import analyze_repository, get_full_stack
from app.services.pipeline_generator import generate_pipeline


def format_stack_to_markdown(analysis, full_stack) -> str:
    """Форматировать стек проекта в Markdown для README."""
    lines = ["# Технологический стек проекта\n"]
    
    # Языки программирования
    if analysis.languages:
        lines.append("## Языки программирования")
        lines.append(", ".join(analysis.languages))
        lines.append("")
    
    # Фреймворки
    if analysis.frameworks:
        lines.append("## Фреймворки")
        lines.append(", ".join(analysis.frameworks))
        lines.append("")
    
    # Frontend фреймворки
    if analysis.frontend_frameworks:
        lines.append("## Frontend фреймворки")
        lines.append(", ".join(analysis.frontend_frameworks))
        lines.append("")
    
    # Backend фреймворки
    if analysis.backend_frameworks:
        lines.append("## Backend фреймворки")
        lines.append(", ".join(analysis.backend_frameworks))
        lines.append("")
    
    # Менеджер пакетов
    if analysis.package_manager:
        lines.append("## Менеджер пакетов")
        lines.append(analysis.package_manager)
        lines.append("")
    
    # Инструмент тестирования
    if analysis.test_runner:
        lines.append("## Инструмент тестирования")
        lines.append(analysis.test_runner)
        lines.append("")
    
    # Docker
    if analysis.docker:
        lines.append("## Docker")
        lines.append("✓ Используется Docker")
        if analysis.dockerfile_paths:
            lines.append(f"\n**Dockerfile:**")
            for df_path in analysis.dockerfile_paths:
                lines.append(f"- `{df_path}`")
        if analysis.docker_context:
            lines.append(f"\n**Docker context:** `{analysis.docker_context}`")
        lines.append("")
    
    # Kubernetes
    if analysis.kubernetes:
        lines.append("## Kubernetes")
        lines.append("✓ Используется Kubernetes")
        lines.append("")
    
    # Terraform
    if analysis.terraform:
        lines.append("## Terraform")
        lines.append("✓ Используется Terraform")
        lines.append("")
    
    # Базы данных
    if analysis.databases:
        lines.append("## Базы данных")
        lines.append(", ".join(analysis.databases))
        lines.append("")
    
    # Java версия
    if analysis.java_version:
        lines.append("## Java версия")
        lines.append(analysis.java_version)
        lines.append("")
    
    # Build tools
    if full_stack.build_tools:
        lines.append("## Инструменты сборки")
        lines.append(", ".join(full_stack.build_tools))
        lines.append("")
    
    # Cloud платформы
    if full_stack.cloud_platforms:
        lines.append("## Cloud платформы")
        lines.append(", ".join(full_stack.cloud_platforms))
        lines.append("")
    
    # CI/CD
    if full_stack.cicd:
        lines.append("## CI/CD")
        lines.append(", ".join(full_stack.cicd))
        lines.append("")
    
    return "\n".join(lines)

# Путь к корню проекта
# __file__ = core-service/app/cli.py
# parents[0] = core-service/app/
# parents[1] = core-service/
# parents[2] = T1/ (корень проекта)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def init_db():
    """Инициализировать базу данных."""
    Base.metadata.create_all(bind=engine)


@click.group()
def cli():
    """Self-Deploy CLI - управление проектами и генерация CI/CD пайплайнов."""
    pass


@cli.command()
@click.option("--name", required=True, help="Название проекта")
@click.option("--url", required=True, help="URL Git-репозитория")
@click.option("--token", default="", help="Токен для клонирования репозитория")
def add_project(name: str, url: str, token: str):
    """Добавить новый проект и проанализировать его стек."""
    click.echo(f"Анализ репозитория {url}...")
    
    try:
        # Анализ репозитория
        analysis = analyze_repository(url, token)
        
        # Создание проекта
        project_create = ProjectCreate(
            name=name,
            url=url,
            clone_token=token,
            analysis=analysis
        )
        
        db = next(get_db())
        project = storage.create_project(db, project_create)
        
        click.echo(f"✓ Проект '{project.name}' успешно добавлен (ID: {project.id})")
        click.echo(f"  Языки: {', '.join(analysis.languages) if analysis.languages else 'не определены'}")
        click.echo(f"  Фреймворки: {', '.join(analysis.frameworks) if analysis.frameworks else 'не определены'}")
        click.echo(f"  Docker: {'да' if analysis.docker else 'нет'}")
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_projects():
    """Показать список всех проектов."""
    db = next(get_db())
    projects = storage.list_projects(db)
    
    if not projects:
        click.echo("Проекты не найдены.")
        return
    
    click.echo(f"Найдено проектов: {len(projects)}\n")
    for project in projects:
        click.echo(f"ID: {project.id}")
        click.echo(f"  Название: {project.name}")
        click.echo(f"  URL: {project.url}")
        if project.analysis:
            click.echo(f"  Языки: {', '.join(project.analysis.languages) if project.analysis.languages else 'не определены'}")
        click.echo()


@cli.command()
@click.option("--project-id", type=int, required=True, help="ID проекта")
@click.option("--output", type=click.Path(), help="Путь для сохранения пайплайна (опционально)")
@click.option("--platform", default="gitlab", help="Платформа CI/CD (gitlab/jenkins)")
@click.option("--stages", help="Список стадий через запятую (опционально)")
def generate(project_id: int, output: Optional[str], platform: str, stages: Optional[str]):
    """Сгенерировать CI/CD пайплайн для проекта."""
    db = next(get_db())
    project = storage.get_project(db, project_id)
    
    if not project:
        click.echo(f"✗ Проект с ID {project_id} не найден", err=True)
        sys.exit(1)
    
    if not project.analysis:
        click.echo(f"✗ Для проекта {project_id} отсутствует анализ. Сначала выполните анализ.", err=True)
        sys.exit(1)
    
    click.echo(f"Генерация пайплайна для проекта '{project.name}'...")
    
    try:
        # Настройки генерации
        user_settings: Dict[str, Any] = {
            "platform": platform,
            "stages": stages.split(",") if stages else [],
            "triggers": {
                "on_push": ["main", "master"],
                "on_merge_request": False,
                "on_tags": "",
                "schedule": "",
                "manual": False,
            },
            "variables": {},
        }
        
        # Генерация пайплайна
        pipeline = generate_pipeline(project.analysis, user_settings)
        
        # Сохранение в БД
        create_dto = PipelineGenerationCreate(
            project_id=project_id,
            uml=pipeline,
        )
        generation = storage.create_pipeline_generation(db, create_dto)
        
        # Вывод или сохранение
        if output:
            Path(output).write_text(pipeline, encoding="utf-8")
            click.echo(f"✓ Пайплайн сохранен в {output}")
        else:
            click.echo("\n" + "="*80)
            click.echo(pipeline)
            click.echo("="*80)
        
        click.echo(f"✓ Пайплайн сгенерирован (ID генерации: {generation.id})")
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--url", required=True, help="URL Git-репозитория")
@click.option("--token", default="", help="Токен для клонирования репозитория")
@click.option("--output", type=click.Path(), help="Путь для сохранения пайплайна")
@click.option("--platform", default="gitlab", help="Платформа CI/CD (gitlab)")
@click.option("--stack-output", type=click.Path(), help="Путь для сохранения стека проекта (JSON)")
@click.option("--docker-compose/--no-docker-compose", default=None, help="Генерировать docker-compose.yml (по умолчанию: True если есть Docker и нет Kubernetes)")
@click.option("--stages", help="Список стадий через запятую (если не указано, используются все возможные стадии)")
@click.option("--on-push", help="Список веток для триггера push через запятую (например: main,master,develop)")
@click.option("--on-merge-request/--no-on-merge-request", default=None, help="Включить/выключить триггер на merge request")
@click.option("--on-tags", help="Паттерн для триггера на теги (regex, например: 'v.*')")
@click.option("--schedule", help="Включить запуск по расписанию (любое значение)")
@click.option("--manual/--no-manual", default=None, help="Разрешить/запретить ручной запуск пайплайна")
def generate_from_repo(
    url: str, 
    token: str, 
    output: Optional[str], 
    platform: str, 
    stack_output: Optional[str], 
    docker_compose: Optional[bool],
    stages: Optional[str],
    on_push: Optional[str],
    on_merge_request: Optional[bool],
    on_tags: Optional[str],
    schedule: Optional[str],
    manual: Optional[bool]
):
    """Сгенерировать CI/CD пайплайн напрямую из репозитория.
    
    Стадии: если --stages не указан, используются все возможные стадии.
    Триггеры: если флаги триггеров не указаны, используются значения по умолчанию.
    """
    start_time = time.time()
    click.echo(f"Анализ репозитория {url}...")
    
    try:
        # Получаем полный стек для сохранения
        full_stack = get_full_stack(url, token)
        
        # Анализ репозитория
        analysis = analyze_repository(url, token)
        
        # Сохраняем стек в файл, если указан
        if stack_output:
            import json
            # Извлекаем docker пути - все Dockerfile
            docker_context = None
            dockerfile_path = None
            dockerfile_paths = []
            
            docker_all = full_stack.files_detected.get("docker_all") if hasattr(full_stack, "files_detected") else None
            docker_files = full_stack.files_detected.get("docker") if hasattr(full_stack, "files_detected") else None
            
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
            
            # Убираем дубликаты
            seen = set()
            unique_paths = []
            for path in dockerfile_paths:
                if path not in seen:
                    seen.add(path)
                    unique_paths.append(path)
            dockerfile_paths = unique_paths
            
            if dockerfile_paths:
                dockerfile_path = dockerfile_paths[0]
                from pathlib import Path as PathLib
                context_path = str(PathLib(dockerfile_path).parent)
                docker_context = context_path if context_path != "." else ""
            
            stack_info = {
                "languages": full_stack.languages,
                "frameworks": full_stack.frameworks,
                "frontend_frameworks": full_stack.frontend_frameworks,
                "backend_frameworks": full_stack.backend_frameworks,
                "package_manager": full_stack.package_manager,
                "test_runner": full_stack.test_runner,
                "docker": full_stack.docker,
                "docker_context": docker_context,
                "dockerfile_path": dockerfile_path,
                "dockerfile_paths": dockerfile_paths,
                "kubernetes": full_stack.kubernetes,
                "terraform": full_stack.terraform,
                "databases": full_stack.databases,
                "cloud_platforms": full_stack.cloud_platforms,
                "build_tools": full_stack.build_tools,
                "cicd": full_stack.cicd,
            }
            Path(stack_output).write_text(json.dumps(stack_info, indent=2, ensure_ascii=False), encoding="utf-8")
            click.echo(f"✓ Стек проекта сохранен в {stack_output}")
        
        # Настройки стадий: если указаны, используем их, иначе пустой список (все возможные)
        stages_list = []
        if stages:
            stages_list = [s.strip() for s in stages.split(",") if s.strip()]
        
        # Настройки триггеров: если указаны, используем их, иначе значения по умолчанию
        triggers_config = {
            "on_push": ["main", "master"],
            "on_merge_request": False,
            "on_tags": "",
            "schedule": "",
            "manual": False,
        }
        
        # Обновляем триггеры, если указаны соответствующие флаги
        if on_push:
            triggers_config["on_push"] = [b.strip() for b in on_push.split(",") if b.strip()]
        
        if on_merge_request is not None:
            triggers_config["on_merge_request"] = on_merge_request
        
        if on_tags is not None:
            triggers_config["on_tags"] = on_tags
        
        if schedule is not None:
            triggers_config["schedule"] = schedule if schedule else ""
        
        if manual is not None:
            triggers_config["manual"] = manual
        
        # Настройки со всеми стадиями
        user_settings: Dict[str, Any] = {
            "platform": platform,
            "stages": stages_list,  # Пустой список означает "все возможные"
            "triggers": triggers_config,
            "variables": {},
            "docker_registry": "$CI_REGISTRY",
            "docker_image": "$CI_REGISTRY_IMAGE",
            "docker_context": analysis.docker_context if analysis.docker else ".",
            "dockerfile_path": analysis.dockerfile_path if analysis.docker else "Dockerfile",
            # use_docker_compose: только если флаг явно указан
            "use_docker_compose": docker_compose if docker_compose is not None else False,
        }
        
        # Генерация пайплайна
        pipeline = generate_pipeline(analysis, user_settings)
        
        # Сохранение или вывод
        if output:
            Path(output).write_text(pipeline, encoding="utf-8")
            click.echo(f"✓ Пайплайн сохранен в {output}")
        else:
            click.echo("\n" + "="*80)
            click.echo(pipeline)
            click.echo("="*80)
        
        # Сохранение стека в README с названием проекта
        # Извлекаем название проекта из URL (последняя часть после последнего слеша)
        project_name = url.rstrip('/').split('/')[-1]
        if project_name.endswith('.git'):
            project_name = project_name[:-4]
        # Очищаем название от специальных символов для использования в имени файла
        project_name = project_name.replace('/', '_').replace('\\', '_').replace(' ', '_')
        readme_filename = f"README-{project_name}.md"
        
        # Всегда сохраняем README в той же директории, что и output
        # Если output не указан, не сохраняем README (чтобы избежать перезаписи)
        if output:
            readme_path = Path(output).parent / readme_filename
            stack_markdown = format_stack_to_markdown(analysis, full_stack)
            readme_path.write_text(stack_markdown, encoding="utf-8")
            click.echo(f"✓ Стек проекта записан в {readme_path}")
        else:
            click.echo("ℹ️  README не сохранен (укажите --output для сохранения)")
        
        click.echo("✓ Пайплайн успешно сгенерирован")
        
        # Вывод времени выполнения
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        if minutes > 0:
            click.echo(f"⏱️  Время выполнения: {minutes} мин. {seconds} сек.")
        else:
            click.echo(f"⏱️  Время выполнения: {seconds} сек.")
        
        # Генерация docker-compose.yml только если флаг явно указан
        if docker_compose is True:
            try:
                # Импортируем генератор docker-compose
                COMPOSE_GENERATOR_PATH = PROJECT_ROOT / "docker_compose_generator"
                if str(COMPOSE_GENERATOR_PATH) not in sys.path:
                    sys.path.insert(0, str(COMPOSE_GENERATOR_PATH))
                
                # Используем прямой импорт через importlib
                import importlib.util
                compose_generator_path = COMPOSE_GENERATOR_PATH / "generator" / "compose_generator.py"
                spec = importlib.util.spec_from_file_location("compose_generator", compose_generator_path)
                compose_generator_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(compose_generator_module)
                generate_docker_compose = compose_generator_module.generate_docker_compose
                
                # Настройки для генерации docker-compose
                compose_settings: Dict[str, Any] = {
                    "use_gitlab_registry": True,
                    "project_name": "app",
                    "db_credentials": {},
                    "db_versions": {},
                    "environment": {}
                }
                
                # Генерируем docker-compose.yml
                compose_content = generate_docker_compose(analysis, compose_settings)
                
                # Сохраняем docker-compose.yml
                if output:
                    # Если указан output, сохраняем в той же директории, что и пайплайн
                    output_path = Path(output)
                    if output_path.is_absolute():
                        compose_output = output_path.parent / "docker-compose.yml"
                    else:
                        # Относительный путь - сохраняем относительно текущей директории (где запущен скрипт)
                        compose_output = output_path.parent / "docker-compose.yml" if output_path.parent != Path(".") else Path("docker-compose.yml")
                else:
                    # Если output не указан, сохраняем в текущей рабочей директории
                    compose_output = Path("docker-compose.yml")
                
                # Создаем директорию, если её нет
                compose_output.parent.mkdir(parents=True, exist_ok=True)
                
                compose_output.write_text(compose_content, encoding="utf-8")
                click.echo(f"✓ docker-compose.yml сохранен в {compose_output.absolute()}")
                
            except Exception as e:
                click.echo(f"⚠ Предупреждение: не удалось сгенерировать docker-compose.yml: {e}", err=True)
                import traceback
                traceback.print_exc()
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.option("--url", required=True, help="URL Git-репозитория")
@click.option("--token", default="", help="Токен для клонирования репозитория")
@click.option("--output", type=click.Path(), help="Путь для сохранения стека (JSON)")
def analyze_repo(url: str, token: str, output: Optional[str]):
    """Определить стек проекта и вывести его в консоль (или сохранить в файл)."""
    click.echo(f"Анализ репозитория {url}...")
    
    try:
        # Получаем полный стек
        stack = get_full_stack(url, token)
        
        # Формируем информацию о стеке
        # Извлекаем docker пути - все Dockerfile
        docker_context = None
        dockerfile_path = None
        dockerfile_paths = []
        
        docker_all = stack.files_detected.get("docker_all") if hasattr(stack, "files_detected") else None
        docker_files = stack.files_detected.get("docker") if hasattr(stack, "files_detected") else None
        
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
        
        # Убираем дубликаты
        seen = set()
        unique_paths = []
        for path in dockerfile_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        dockerfile_paths = unique_paths
        
        if dockerfile_paths:
            dockerfile_path = dockerfile_paths[0]
            from pathlib import Path as PathLib
            context_path = str(PathLib(dockerfile_path).parent)
            docker_context = context_path if context_path != "." else ""
        
        stack_info = {
            "languages": stack.languages,
            "frameworks": stack.frameworks,
            "frontend_frameworks": stack.frontend_frameworks,
            "backend_frameworks": stack.backend_frameworks,
            "package_manager": stack.package_manager,
            "test_runner": stack.test_runner,
            "docker": stack.docker,
            "docker_context": docker_context,
            "dockerfile_path": dockerfile_path,
            "dockerfile_paths": dockerfile_paths,
            "kubernetes": stack.kubernetes,
            "terraform": stack.terraform,
            "databases": stack.databases,
            "cloud_platforms": stack.cloud_platforms,
            "build_tools": stack.build_tools,
            "cicd": stack.cicd,
        }
        
        # Выводим в консоль
        click.echo("\n" + "="*80)
        click.echo("ТЕХНОЛОГИЧЕСКИЙ СТЕК ПРОЕКТА")
        click.echo("="*80)
        click.echo(f"Языки: {', '.join(stack.languages) if stack.languages else 'не определены'}")
        click.echo(f"Фреймворки: {', '.join(stack.frameworks) if stack.frameworks else 'не определены'}")
        click.echo(f"Frontend фреймворки: {', '.join(stack.frontend_frameworks) if stack.frontend_frameworks else 'не определены'}")
        click.echo(f"Backend фреймворки: {', '.join(stack.backend_frameworks) if stack.backend_frameworks else 'не определены'}")
        click.echo(f"Менеджер пакетов: {stack.package_manager or 'не определен'}")
        click.echo(f"Тестовые раннеры: {', '.join(stack.test_runner) if stack.test_runner else 'не определены'}")
        # Извлекаем docker пути для вывода - все Dockerfile
        dockerfile_paths = []
        docker_all = stack.files_detected.get("docker_all") if hasattr(stack, "files_detected") else None
        docker_files = stack.files_detected.get("docker") if hasattr(stack, "files_detected") else None
        
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
        
        # Убираем дубликаты
        seen = set()
        unique_paths = []
        for path in dockerfile_paths:
            if path not in seen:
                seen.add(path)
                unique_paths.append(path)
        dockerfile_paths = unique_paths
        
        click.echo(f"Docker: {'да' if stack.docker else 'нет'}")
        if stack.docker and dockerfile_paths:
            if len(dockerfile_paths) == 1:
                dockerfile_path = dockerfile_paths[0]
                click.echo(f"  Dockerfile: {dockerfile_path}")
                from pathlib import Path as PathLib
                context_path = str(PathLib(dockerfile_path).parent)
                if context_path != ".":
                    click.echo(f"  Docker context: {context_path}")
            else:
                click.echo(f"  Dockerfile файлов: {len(dockerfile_paths)}")
                for i, df_path in enumerate(dockerfile_paths, 1):
                    from pathlib import Path as PathLib
                    context_path = str(PathLib(df_path).parent)
                    click.echo(f"    {i}. {df_path} (context: {context_path if context_path != '.' else 'root'})")
        click.echo(f"Kubernetes: {'да' if stack.kubernetes else 'нет'}")
        click.echo(f"Terraform: {'да' if stack.terraform else 'нет'}")
        click.echo(f"Базы данных: {', '.join(stack.databases) if stack.databases else 'не определены'}")
        click.echo(f"Облачные платформы: {', '.join(stack.cloud_platforms) if stack.cloud_platforms else 'не определены'}")
        click.echo(f"Инструменты сборки: {', '.join(stack.build_tools) if stack.build_tools else 'не определены'}")
        click.echo(f"CI/CD: {', '.join(stack.cicd) if stack.cicd else 'не определены'}")
        click.echo("="*80)
        
        # Сохраняем в файл, если указан
        if output:
            import json
            Path(output).write_text(json.dumps(stack_info, indent=2, ensure_ascii=False), encoding="utf-8")
            click.echo(f"✓ Стек сохранен в {output}")
        
        click.echo("✓ Анализ завершен")
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def list_pipelines():
    """Показать историю генерации пайплайнов."""
    db = next(get_db())
    pipelines = storage.list_pipeline_generations(db)
    
    if not pipelines:
        click.echo("История генераций пуста.")
        return
    
    click.echo(f"Найдено генераций: {len(pipelines)}\n")
    for pipeline in pipelines:
        click.echo(f"ID: {pipeline.id}")
        click.echo(f"  Проект ID: {pipeline.project_id or 'N/A'}")
        click.echo(f"  Создан: {pipeline.generated_at}")
        click.echo(f"  Размер пайплайна: {len(pipeline.uml)} символов")
        click.echo()


@cli.command()
def init():
    """Инициализировать базу данных."""
    click.echo("Инициализация базы данных...")
    init_db()
    click.echo("✓ База данных инициализирована")


@cli.command()
@click.option("--url", required=True, help="URL GitLab репозитория")
@click.option("--token", required=True, help="GitLab токен для доступа к API")
@click.option("--file", required=True, type=click.Path(exists=True), help="Путь к файлу для отправки в Merge Request")
@click.option("--branch", default="main", help="Базовая ветка для создания Merge Request (по умолчанию: main)")
def auto_merge_request(
    url: str,
    token: str,
    file: str,
    branch: str
):
    """Автоматически создать Merge Request с указанным файлом в GitLab репозиторий.
    
    Команда читает указанный файл и автоматически создает Merge Request с этим файлом
    в указанном GitLab репозитории. Создается форк репозитория, файл добавляется в форк,
    и создается Merge Request из форка в оригинальный репозиторий.
    """
    click.echo(f"Подготовка Merge Request для репозитория {url}...")
    
    try:
        # Чтение файла
        file_path = Path(file)
        if not file_path.exists():
            click.echo(f"✗ Файл не найден: {file}", err=True)
            sys.exit(1)
        
        click.echo(f"Чтение файла: {file_path}")
        file_content = file_path.read_bytes()
        
        # Импорт модуля auto-merge-request
        AUTO_MERGE_REQUEST_PATH = PROJECT_ROOT / "auto-merge-request"
        if str(AUTO_MERGE_REQUEST_PATH) not in sys.path:
            sys.path.insert(0, str(AUTO_MERGE_REQUEST_PATH))
        
        try:
            from GitLabRepoService import GitLabRepoService
        except ImportError:
            click.echo("✗ Ошибка: не удалось импортировать модуль auto-merge-request", err=True)
            click.echo("  Убедитесь, что модуль auto-merge-request находится в корне проекта", err=True)
            sys.exit(1)
        
        # Создание Merge Request
        click.echo(f"Создание Merge Request в ветку '{branch}'...")
        service = GitLabRepoService()
        service.modify_repo(
            link=url,
            token=token,
            base_branch=branch,
            file_content=file_content
        )
        
        click.echo("✓ Merge Request успешно создан!")
        click.echo(f"  Репозиторий: {url}")
        click.echo(f"  Файл: {file_path.name}")
        click.echo(f"  Ветка: {branch}")
        
    except Exception as e:
        click.echo(f"✗ Ошибка: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()

