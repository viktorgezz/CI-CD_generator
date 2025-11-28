"""Вспомогательные функции для проекта."""
import re
import os
from typing import Optional, List
from pathlib import Path


def get_language_by_extension(extension: str) -> Optional[str]:
    """Определение языка по расширению файла.
    
    Поддерживаются только 4 языка: Python, TypeScript, Java/Kotlin, Go.
    """
    language_map = {
        '.py': 'python',
        '.pyw': 'python',
        '.pyx': 'python',
        '.pxd': 'python',
        '.pyi': 'python',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.js': 'typescript',  # JavaScript файлы определяются как TypeScript
        '.jsx': 'typescript',  # JSX файлы определяются как TypeScript
        '.java': 'java',
        '.kt': 'java',  # Kotlin объединен с Java
        '.kts': 'java',
        '.go': 'go',
    }
    return language_map.get(extension)


def detect_language_from_command(command: str) -> str:
    """Определение языка из команды.
    
    Поддерживаются только 4 языка: Python, TypeScript, Java/Kotlin, Go.
    """
    if 'node' in command or 'ts-node' in command or 'tsx' in command:
        return 'typescript'
    elif 'python' in command:
        return 'python'
    elif 'java' in command or 'kotlin' in command:
        return 'java'
    elif 'go' in command:
        return 'go'
    return 'unknown'


def get_language_extensions() -> dict:
    """Получить словарь расширений файлов по языкам.
    
    Поддерживаются только 4 языка: Python, TypeScript/JavaScript, Java/Kotlin, Go.
    JavaScript файлы (.js, .jsx) определяются как TypeScript.
    """
    return {
        # Поддерживаемые языки
        'python': ['.py', '.pyw', '.pyx', '.pxd', '.pyi'],
        'typescript': ['.ts', '.tsx', '.js', '.jsx'],  # JavaScript файлы определяются как TypeScript
        'java': ['.java', '.kt', '.kts', '.jar', '.war', '.class'],
        'go': ['.go'],
    }


def should_ignore_path(path: Path) -> bool:
    """
    Проверка, нужно ли игнорировать путь при анализе.
    
    Игнорируются служебные директории, кэши, зависимости и т.д.
    
    Args:
        path: Путь к файлу или директории
        
    Returns:
        True если путь нужно игнорировать, False иначе
    """
    ignore_patterns = {
        # Системы контроля версий
        '.git', '.svn', '.hg', '.bzr',
        # Python
        '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache',
        'venv', '.venv', 'env', '.env', 'virtualenv',
        'dist', 'build', '.build', '*.egg-info',
        '.tox', '.coverage', 'htmlcov', '.pytest_cache',
        # Node.js
        'node_modules', '.node_modules', '.npm', '.yarn',
        '.next', '.nuxt', '.cache', '.parcel-cache',
        # IDE
        '.idea', '.vscode', '.vs', '.settings',
        # Сборка
        'target', 'bin', 'obj', 'out', '.gradle',
        # Зависимости
        'vendor', 'bower_components', 'packages',
        # Другое
        '.DS_Store', 'Thumbs.db', '.tmp',
        # Убрали 'tmp' и 'temp' - слишком общие имена, которые могут быть в проектах
        # и конфликтуют с системными путями типа /tmp/
    }
    
    # Получить все части пути
    parts = path.parts
    
    # Пропускаем системные части пути (корень файловой системы)
    # Если путь абсолютный и начинается с '/', пропускаем первую часть
    start_idx = 0
    if parts and parts[0] == '/':
        start_idx = 1
    
    # Важные конфигурационные файлы в корне, которые не нужно игнорировать
    important_root_files = {'.dockerignore', '.gitignore', '.env.example', '.github', '.gitlab', '.circleci'}
    
    # Проверить каждую часть пути (начиная с start_idx)
    for i, part in enumerate(parts[start_idx:], start=start_idx):
        # Игнорировать скрытые файлы/директории (начинающиеся с точки)
        # кроме важных конфигурационных файлов
        if part.startswith('.'):
            # Не игнорировать важные конфигурационные файлы/директории
            if part in important_root_files:
                continue
            # Не игнорировать файлы в корне репозитория, которые могут быть важными
            if i == start_idx and part in {'.dockerignore', '.gitignore', '.env.example', '.prettierrc', '.eslintrc'}:
                continue
            # Игнорировать остальные скрытые файлы/директории
            return True
        
        # Проверить паттерны игнорирования
        if part in ignore_patterns:
            return True
        
        # Игнорировать директории с типичными именами для зависимостей
        if part.endswith('_cache') or part.endswith('.cache'):
            return True
    
    return False


def get_relevant_files(
    repo_path: Path, 
    extensions: Optional[List[str]] = None, 
    max_file_size: int = 1024 * 1024,  # 1MB по умолчанию
    max_files: Optional[int] = None
) -> List[Path]:
    """
    Получить список релевантных файлов с фильтрацией.
    
    Игнорируются служебные директории, большие файлы и т.д.
    
    Args:
        repo_path: Корневой путь репозитория
        extensions: Список расширений для фильтрации (если None - все файлы)
        max_file_size: Максимальный размер файла в байтах
        max_files: Максимальное количество файлов (для раннего выхода)
        
    Returns:
        Список путей к релевантным файлам
    """
    relevant_files = []
    file_count = 0
    
    try:
        for file_path in repo_path.rglob('*'):
            # Проверка лимита файлов
            if max_files and file_count >= max_files:
                break
            
            if not file_path.is_file():
                continue
            
            # Пропустить игнорируемые пути
            if should_ignore_path(file_path):
                continue
            
            # Проверка размера файла
            try:
                file_size = file_path.stat().st_size
                if file_size > max_file_size:
                    continue
            except (OSError, ValueError):
                # Если не удалось получить размер, пропускаем
                continue
            
            # Фильтр по расширениям (если указан)
            if extensions:
                if file_path.suffix.lower() not in extensions:
                    continue
            
            relevant_files.append(file_path)
            file_count += 1
            
    except (OSError, PermissionError) as e:
        # Игнорируем ошибки доступа к файлам
        pass
    
    return relevant_files


def read_file_sample(
    file_path: Path, 
    max_lines: int = 100, 
    max_bytes: int = 8192
) -> str:
    """
    Читать только начало файла для быстрого анализа паттернов.
    
    Для большинства паттернов (импорты, объявления) достаточно первых строк.
    
    Args:
        file_path: Путь к файлу
        max_lines: Максимальное количество строк для чтения
        max_bytes: Максимальное количество байт для чтения
        
    Returns:
        Строка с содержимым начала файла
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = ''
            bytes_read = 0
            
            for line_num, line in enumerate(f):
                if line_num >= max_lines:
                    break
                
                line_bytes = len(line.encode('utf-8'))
                if bytes_read + line_bytes > max_bytes:
                    # Читаем только часть строки, чтобы не превысить лимит
                    remaining_bytes = max_bytes - bytes_read
                    if remaining_bytes > 0:
                        content += line[:remaining_bytes]
                    break
                
                content += line
                bytes_read += line_bytes
            
            return content
    except (UnicodeDecodeError, IOError, OSError):
        # Если файл бинарный или недоступен, возвращаем пустую строку
        return ''

