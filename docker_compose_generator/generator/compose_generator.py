"""Генератор docker-compose.yml файлов."""
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader

# Добавляем путь к корню проекта
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _get_default_ports(analysis, service_name: str = "app") -> List[int]:
    """Определить порты по умолчанию на основе языка и фреймворка."""
    languages = [l.lower() for l in analysis.languages]
    frameworks = [f.lower() for f in analysis.frameworks]
    backend_frameworks = [f.lower() for f in analysis.backend_frameworks]
    
    # Определяем основной язык
    main_language = languages[0] if languages else "python"
    
    # Маппинг портов
    port_map = {
        'python': {
            'django': 8000,
            'flask': 5000,
            'fastapi': 8000,
            'default': 8000
        },
        'java': {
            'spring': 8080,
            'default': 8080
        },
        'go': {
            'default': 8080
        },
        'typescript': {
            'next': 3000,
            'react': 3000,
            'default': 3000
        },
        'javascript': {
            'next': 3000,
            'react': 3000,
            'default': 3000
        }
    }
    
    # Проверяем фреймворки
    all_frameworks = frameworks + backend_frameworks
    for fw in all_frameworks:
        if main_language in port_map and fw in port_map[main_language]:
            return [port_map[main_language][fw]]
    
    # Возвращаем порт по умолчанию для языка
    if main_language in port_map:
        return [port_map[main_language].get('default', 8080)]
    
    return [8080]


def _build_database_environment(db: str, db_name: str, settings: Dict[str, Any]) -> Dict[str, str]:
    """Построить переменные окружения для подключения к БД."""
    db_creds = settings.get('db_credentials', {}).get(db.lower(), {})
    
    user = db_creds.get('user', 'appuser')
    password = db_creds.get('password', 'changeme')
    db_name_value = db_creds.get('db_name', 'appdb')
    
    env = {}
    
    if db.lower() == 'postgresql':
        env['DATABASE_URL'] = f"postgresql://{user}:{password}@{db_name}:5432/{db_name_value}"
        env['POSTGRES_DB'] = db_name_value
        env['POSTGRES_USER'] = user
        env['POSTGRES_PASSWORD'] = password
    elif db.lower() == 'mysql':
        env['DATABASE_URL'] = f"mysql://{user}:{password}@{db_name}:3306/{db_name_value}"
        env['MYSQL_DATABASE'] = db_name_value
        env['MYSQL_USER'] = user
        env['MYSQL_PASSWORD'] = password
        env['MYSQL_ROOT_PASSWORD'] = db_creds.get('root_password', password)
    elif db.lower() == 'mongodb':
        env['DATABASE_URL'] = f"mongodb://{user}:{password}@{db_name}:27017/{db_name_value}"
        env['MONGO_INITDB_DATABASE'] = db_name_value
        if user and password:
            env['MONGO_INITDB_ROOT_USERNAME'] = user
            env['MONGO_INITDB_ROOT_PASSWORD'] = password
    elif db.lower() == 'redis':
        env['REDIS_URL'] = f"redis://{db_name}:6379"
    
    return env


def _build_app_environment(analysis, settings: Dict[str, Any], databases: List[str]) -> Dict[str, str]:
    """Построить переменные окружения для приложения."""
    env = {}
    
    # Добавляем connection strings для баз данных
    for db in databases:
        db_env = _build_database_environment(db, db.lower(), settings)
        env.update(db_env)
    
    # Добавляем пользовательские переменные
    user_env = settings.get('environment', {}).get('app', {})
    env.update(user_env)
    
    return env


def build_app_services(analysis, settings: Dict[str, Any]) -> Dict[str, Dict]:
    """Построить сервисы приложений."""
    dockerfile_paths = analysis.dockerfile_paths or []
    use_registry = settings.get('use_gitlab_registry', True)
    project_name = settings.get('project_name', 'app')
    
    services = {}
    
    if not dockerfile_paths and analysis.dockerfile_path:
        dockerfile_paths = [analysis.dockerfile_path]
    
    if len(dockerfile_paths) == 0:
        # Нет Dockerfile - создаем базовый сервис
        services['app'] = {
            'name': 'app',
            'template': 'app',
            'use_gitlab_registry': use_registry,
            'service_suffix': None,
            'docker_context': analysis.docker_context or '.',
            'dockerfile_path': 'Dockerfile',
            'ports': _get_default_ports(analysis),
            'environment': _build_app_environment(analysis, settings, analysis.databases),
            'depends_on': [db.lower() for db in analysis.databases],
            'networks': ['app_network']
        }
    elif len(dockerfile_paths) == 1:
        # Один Dockerfile
        dockerfile_path = dockerfile_paths[0]
        docker_context = analysis.docker_context or str(Path(dockerfile_path).parent) if '/' in dockerfile_path else '.'
        
        services['app'] = {
            'name': 'app',
            'template': 'app',
            'use_gitlab_registry': use_registry,
            'service_suffix': None,
            'docker_context': docker_context,
            'dockerfile_path': dockerfile_path,
            'ports': _get_default_ports(analysis),
            'environment': _build_app_environment(analysis, settings, analysis.databases),
            'depends_on': [db.lower() for db in analysis.databases],
            'networks': ['app_network']
        }
    else:
        # Несколько Dockerfile (монорепозиторий)
        for dockerfile_path in dockerfile_paths:
            # Определяем имя сервиса из пути
            dockerfile_dir = str(Path(dockerfile_path).parent)
            if dockerfile_dir == '.':
                service_name = 'main'
            else:
                service_name = dockerfile_dir.split('/')[-1].lower()
            
            service_suffix = service_name if service_name != 'main' else None
            
            services[service_name] = {
                'name': service_name,
                'template': 'app',
                'use_gitlab_registry': use_registry,
                'service_suffix': service_suffix,
                'docker_context': dockerfile_dir if dockerfile_dir != '.' else '.',
                'dockerfile_path': dockerfile_path,
                'ports': _get_default_ports(analysis, service_name),
                'environment': _build_app_environment(analysis, settings, analysis.databases),
                'depends_on': [db.lower() for db in analysis.databases],
                'networks': ['app_network']
            }
    
    return services


def build_database_services(analysis, settings: Dict[str, Any]) -> Dict[str, Dict]:
    """Построить сервисы баз данных."""
    services = {}
    
    db_versions = settings.get('db_versions', {})
    
    for db in analysis.databases:
        db_lower = db.lower()
        db_creds = settings.get('db_credentials', {}).get(db_lower, {})
        
        service_config = {
            'name': db_lower,
            'template': db_lower,
            'version': db_versions.get(db_lower, _get_default_db_version(db_lower)),
            'user': db_creds.get('user', 'appuser'),
            'password': db_creds.get('password', 'changeme'),
            'db_name': db_creds.get('db_name', 'appdb'),
            'networks': ['app_network'],
            'volumes': [f'{db_lower}_data:/var/lib/{db_lower}/data']
        }
        
        # Специфичные настройки для разных БД
        if db_lower == 'postgresql':
            service_config['ports'] = ['5432:5432']
        elif db_lower == 'mysql':
            service_config['ports'] = ['3306:3306']
            service_config['root_password'] = db_creds.get('root_password', db_creds.get('password', 'changeme'))
        elif db_lower == 'mongodb':
            service_config['ports'] = ['27017:27017']
        elif db_lower == 'redis':
            service_config['ports'] = ['6379:6379']
            service_config['volumes'] = []
        
        services[db_lower] = service_config
    
    return services


def _get_default_db_version(db: str) -> str:
    """Получить версию БД по умолчанию."""
    versions = {
        'postgresql': '15',
        'mysql': '8.0',
        'mongodb': '7',
        'redis': '7-alpine'
    }
    return versions.get(db.lower(), 'latest')


def generate_docker_compose(analysis, settings: Dict[str, Any]) -> str:
    """Сгенерировать docker-compose.yml файл."""
    templates_root = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(loader=FileSystemLoader(str(templates_root)), trim_blocks=True, lstrip_blocks=True)
    
    # Строим сервисы
    app_services = build_app_services(analysis, settings)
    db_services = build_database_services(analysis, settings)
    
    # Объединяем все сервисы
    all_services = {**app_services, **db_services}
    
    # Строим volumes
    volumes = {}
    for db in analysis.databases:
        db_lower = db.lower()
        if db_lower != 'redis':  # Redis обычно не требует volume
            volumes[f'{db_lower}_data'] = {}
    
    # Строим networks
    networks = {
        'app_network': {
            'driver': 'bridge'
        }
    }
    
    # Контекст для шаблона
    ctx = {
        'services': all_services,
        'volumes': volumes,
        'networks': networks,
        'project_name': settings.get('project_name', 'app')
    }
    
    # Рендерим шаблон
    template = env.get_template('base_compose.j2')
    return template.render(**ctx)

