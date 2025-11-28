"""Анализатор DevOps инструментов."""
import logging
from pathlib import Path
from typing import List, Optional, Dict

from ..models import ProjectStack
from ..config import ConfigLoader
from ..utils import get_relevant_files, should_ignore_path

logger = logging.getLogger(__name__)


class DevOpsAnalyzer:
    """Анализатор для определения DevOps инструментов."""

    def __init__(self, config_loader: ConfigLoader):
        """
        Инициализация анализатора.

        Args:
            config_loader: Загрузчик конфигурации
        """
        self.config_loader = config_loader

    @staticmethod
    def _detect_monorepo_structure(repo_path: Path) -> Dict[str, List[Path]]:
        """Определить структуру монорепозитория.
        
        Returns:
            Словарь с ключами: 'frontend', 'backend', 'root', 'apps'
        """
        structure = {
            'frontend': [],
            'backend': [],
            'root': [],
            'apps': [],
            'packages': []
        }
        
        # Типичные структуры монорепозиториев
        frontend_dirs = ['frontend', 'web', 'client', 'ui', 'app']
        backend_dirs = ['backend', 'server', 'api', 'services']
        apps_dirs = ['apps', 'applications']
        packages_dirs = ['packages', 'libs', 'libraries']
        
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
            elif dir_name in packages_dirs:
                structure['packages'].append(item)
        
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

    @staticmethod
    def _categorize_dockerfiles(docker_files: List[Path], repo_path: Path, monorepo_structure: Dict[str, List[Path]]) -> Dict[str, List[Path]]:
        """Категоризировать Dockerfile по назначению (frontend, backend, root).
        
        Args:
            docker_files: Список всех найденных Dockerfile
            repo_path: Корневой путь репозитория
            monorepo_structure: Структура монорепозитория
            
        Returns:
            Словарь с категориями: 'frontend', 'backend', 'root', 'other'
        """
        categorized = {
            'frontend': [],
            'backend': [],
            'root': [],
            'other': []
        }
        
        for dockerfile in docker_files:
            rel_path = dockerfile.relative_to(repo_path)
            
            # Dockerfile в корне
            if len(rel_path.parts) == 1:
                categorized['root'].append(dockerfile)
                continue
            
            # Проверяем, находится ли Dockerfile в frontend или backend директории
            path_parts = rel_path.parts
            is_frontend = False
            is_backend = False
            
            for i, part in enumerate(path_parts[:-1]):  # Все части кроме имени файла
                part_lower = part.lower()
                
                # Проверяем прямые совпадения
                if part_lower in ['frontend', 'web', 'client', 'ui', 'app']:
                    is_frontend = True
                    break
                elif part_lower in ['backend', 'server', 'api', 'services']:
                    is_backend = True
                    break
                
                # Проверяем в apps/
                if part_lower == 'apps' and i + 1 < len(path_parts):
                    next_part = path_parts[i + 1].lower()
                    if next_part in ['frontend', 'web', 'client', 'ui', 'app']:
                        is_frontend = True
                        break
                    elif next_part in ['backend', 'server', 'api', 'services']:
                        is_backend = True
                        break
            
            # Также проверяем по имени файла
            dockerfile_name = dockerfile.name.lower()
            if 'frontend' in dockerfile_name or 'web' in dockerfile_name or 'client' in dockerfile_name:
                is_frontend = True
            elif 'backend' in dockerfile_name or 'server' in dockerfile_name or 'api' in dockerfile_name:
                is_backend = True
            
            if is_frontend:
                categorized['frontend'].append(dockerfile)
            elif is_backend:
                categorized['backend'].append(dockerfile)
            else:
                categorized['other'].append(dockerfile)
        
        return categorized

    @staticmethod
    def _select_main_dockerfile(docker_files: List[Path], repo_path: Path) -> Optional[Path]:
        """Выбрать основной Dockerfile из списка по приоритету.
        
        Приоритет:
        1. Dockerfile в корне проекта
        2. Dockerfile в любой директории
        3. Dockerfile.* файлы (Dockerfile.prod, Dockerfile.dev и т.д.)
        4. *.dockerfile файлы
        
        Args:
            docker_files: Список найденных Dockerfile файлов
            repo_path: Корневой путь репозитория
            
        Returns:
            Основной Dockerfile или None
        """
        if not docker_files:
            return None
        
        # Приоритет 1: Dockerfile в корне проекта
        for f in docker_files:
            rel_path = f.relative_to(repo_path)
            if rel_path.name == 'Dockerfile' and len(rel_path.parts) == 1:
                return f
        
        # Приоритет 2: Dockerfile в любой директории
        for f in docker_files:
            rel_path = f.relative_to(repo_path)
            if rel_path.name == 'Dockerfile':
                return f
        
        # Приоритет 3: Dockerfile.* файлы (Dockerfile.prod, Dockerfile.dev и т.д.)
        dockerfile_variants = []
        for f in docker_files:
            if f.name.startswith('Dockerfile.') or f.name.startswith('Dockerfile-'):
                dockerfile_variants.append(f)
        
        if dockerfile_variants:
            # Сортируем по имени, чтобы выбрать наиболее стандартный (например, Dockerfile.prod)
            dockerfile_variants.sort(key=lambda x: x.name)
            return dockerfile_variants[0]
        
        # Приоритет 4: *.dockerfile файлы
        dockerfile_ext = [f for f in docker_files if f.name.endswith('.dockerfile')]
        if dockerfile_ext:
            dockerfile_ext.sort(key=lambda x: x.name)
            return dockerfile_ext[0]
        
        # Если ничего не подошло, возвращаем первый
        return docker_files[0]

    def analyze(self, repo_path: Path, stack: ProjectStack):
        """
        Анализ DevOps инструментов.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        devops_files = {
            'docker': ['Dockerfile', '*.dockerfile'],
            'docker-compose': ['docker-compose.yml', 'docker-compose.yaml'],
            'kubernetes': ['k8s/**/*', 'manifests/**/*', 'kubernetes/**/*', '*.k8s.yaml', '*.k8s.yml'],
            'helm': ['Chart.yaml'],
            'terraform': ['*.tf', '.terraform.lock.hcl', '*.tfvars', 'terraform.tfstate'],
            'ansible': ['ansible.cfg', 'inventory', 'playbook.yml'],
            'pulumi': ['Pulumi.yaml'],
            'vagrant': ['Vagrantfile'],
        }

        detected_files = {}
        
        # Используем оптимизированный поиск файлов
        relevant_files = get_relevant_files(repo_path)
        logger.info(f"Найдено релевантных файлов для анализа DevOps: {len(relevant_files)}")
        
        # Дополнительный поиск Dockerfile и docker-compose через rglob (на случай, если они не попали в relevant_files)
        dockerfile_matches = list(repo_path.rglob('Dockerfile*'))
        dockerfile_matches = [f for f in dockerfile_matches if f.is_file() and not should_ignore_path(f)]
        logger.info(f"Найдено Dockerfile файлов через rglob: {len(dockerfile_matches)}")
        if dockerfile_matches:
            logger.info(f"Dockerfile файлы: {[str(f.relative_to(repo_path)) for f in dockerfile_matches]}")
            before_count = len(relevant_files)
            relevant_files.extend([f for f in dockerfile_matches if f not in relevant_files])
            after_count = len(relevant_files)
            logger.info(f"Добавлено Dockerfile файлов в relevant_files: {after_count - before_count}, всего файлов: {after_count}")
        
        docker_compose_matches = list(repo_path.rglob('docker-compose.*'))
        docker_compose_matches = [f for f in docker_compose_matches if f.is_file() and not should_ignore_path(f)]
        logger.info(f"Найдено docker-compose файлов через rglob: {len(docker_compose_matches)}")
        if docker_compose_matches:
            logger.info(f"docker-compose файлы: {[str(f.relative_to(repo_path)) for f in docker_compose_matches]}")
            relevant_files.extend([f for f in docker_compose_matches if f not in relevant_files])

        # Сначала проверяем Docker и docker-compose напрямую
        # Dockerfile может быть: Dockerfile, Dockerfile.prod, Dockerfile_backend, Dockerfile-frontend и т.д.
        docker_files = []
        for f in relevant_files:
            if f.name == 'Dockerfile' or f.name.startswith('Dockerfile') or f.name.endswith('.dockerfile'):
                docker_files.append(f)
        
        logger.info(f"Найдено потенциальных Dockerfile файлов в relevant_files: {len(docker_files)}")
        if docker_files:
            logger.info(f"Имена Dockerfile файлов: {[f.name for f in docker_files]}")
            stack.docker = True
            
            # Определяем структуру монорепозитория
            monorepo_structure = self._detect_monorepo_structure(repo_path)
            is_monorepo = any(len(v) > 0 for v in monorepo_structure.values() if isinstance(v, list))
            
            if is_monorepo and len(docker_files) > 1:
                # Для монорепозиториев категоризируем Dockerfile
                categorized = self._categorize_dockerfiles(docker_files, repo_path, monorepo_structure)
                
                # Сохраняем Dockerfile по категориям
                if categorized['root']:
                    detected_files['docker'] = [str(f.relative_to(repo_path)) for f in categorized['root']]
                elif categorized['backend']:
                    detected_files['docker'] = [str(f.relative_to(repo_path)) for f in categorized['backend']]
                else:
                    detected_files['docker'] = [str(f.relative_to(repo_path)) for f in docker_files]
                
                # Сохраняем все Dockerfile с категориями
                all_dockerfiles_by_category = {}
                for category, files in categorized.items():
                    if files:
                        all_dockerfiles_by_category[category] = [str(f.relative_to(repo_path)) for f in files]
                
                if len(all_dockerfiles_by_category) > 1:
                    detected_files['docker_by_category'] = all_dockerfiles_by_category
                    detected_files['docker_all'] = [str(f.relative_to(repo_path)) for f in docker_files]
                    logger.info(f"Монорепозиторий: Dockerfile по категориям: {all_dockerfiles_by_category}")
            else:
                # Для обычных репозиториев выбираем основной Dockerfile по приоритету
                main_dockerfile = self._select_main_dockerfile(docker_files, repo_path)
                if main_dockerfile:
                    # Сохраняем основной Dockerfile в ключе 'docker'
                    detected_files['docker'] = [str(main_dockerfile.relative_to(repo_path))]
                    # Все остальные Dockerfile сохраняем в 'docker_all' для справки
                    all_dockerfiles = [str(f.relative_to(repo_path)) for f in docker_files]
                    if len(all_dockerfiles) > 1:
                        detected_files['docker_all'] = all_dockerfiles
                    logger.info(f"Выбран основной Dockerfile: {main_dockerfile.relative_to(repo_path)}")
                else:
                    detected_files['docker'] = [str(f.relative_to(repo_path)) for f in docker_files]
            
            logger.info(f"Обнаружен Docker: {detected_files['docker']}")
        
        docker_compose_files = [f for f in relevant_files 
                               if f.name.startswith('docker-compose') and 
                               (f.name.endswith('.yml') or f.name.endswith('.yaml'))]
        if docker_compose_files:
            stack.docker = True  # docker-compose тоже указывает на Docker
            detected_files['docker-compose'] = [str(f.relative_to(repo_path)) for f in docker_compose_files]
            logger.info(f"Обнаружен docker-compose: {detected_files['docker-compose']}")
        
        # Обработка остальных инструментов
        for tool, patterns in devops_files.items():
            if tool in ['docker', 'docker-compose']:
                continue  # Уже обработали выше
            
            for pattern in patterns:
                matches = []
                
                # Обработка разных типов паттернов
                if pattern.startswith('*.') and pattern != '*.dockerfile':
                    # Файлы с определенным расширением (например, *.tf, *.tfvars)
                    ext = pattern[1:]  # убираем *
                    matches = [f for f in relevant_files 
                              if f.name.endswith(ext)]
                elif '**' in pattern:
                    # Паттерны с ** - ищем в поддиректориях (например, k8s/**/*)
                    dir_part = pattern.split('/')[0]
                    matches = [f for f in relevant_files 
                              if dir_part in str(f.relative_to(repo_path))]
                elif pattern.startswith('*.') and '.' in pattern and pattern.count('.') > 1:
                    # Паттерны типа *.k8s.yaml - ищем файлы с таким расширением
                    ext = pattern[1:]  # убираем *
                    matches = [f for f in relevant_files 
                              if f.name.endswith(ext) or str(f.relative_to(repo_path)).endswith(ext)]
                else:
                    # Точное совпадение имени файла
                    matches = [f for f in relevant_files if f.name == pattern]
                
                if matches:
                    if tool == 'kubernetes':
                        stack.kubernetes = True
                    elif tool == 'helm':
                        stack.kubernetes = True  # Helm тоже указывает на Kubernetes
                    elif tool == 'terraform':
                        stack.terraform = True

                    detected_files[tool] = detected_files.get(tool, []) + [str(m.relative_to(repo_path)) for m in matches]
                    # Не break, продолжаем поиск для других паттернов того же инструмента

        stack.files_detected.update(detected_files)

