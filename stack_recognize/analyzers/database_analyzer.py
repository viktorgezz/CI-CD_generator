"""Анализатор баз данных."""
import re
import logging
from pathlib import Path

from ..models import ProjectStack
from ..config import ConfigLoader, PatternConfig
from ..utils import get_relevant_files, read_file_sample, get_language_by_extension

logger = logging.getLogger(__name__)


class DatabaseAnalyzer:
    """Анализатор для определения используемых баз данных."""

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
        Анализ используемых баз данных.

        Args:
            repo_path: Путь к репозиторию
            stack: Объект ProjectStack для заполнения
        """
        # Анализ по конфигурационным файлам
        self._analyze_by_files(repo_path, stack)

        # Анализ по зависимостям и импортам
        self._analyze_by_content(repo_path, stack)

    def _analyze_by_files(self, repo_path: Path, stack: ProjectStack):
        """Анализ баз данных по наличию специфичных файлов."""
        database_files = {
            'postgresql': ['postgresql.conf', 'pg_hba.conf'],
            'mysql': ['my.cnf', 'my.ini'],
            'mongodb': ['mongod.conf'],
            'redis': ['redis.conf'],
            'sqlite': ['.db', '.sqlite', '.sqlite3'],
        }

        # Используем оптимизированный поиск файлов
        relevant_files = get_relevant_files(repo_path)
        for db, patterns in database_files.items():
            for pattern in patterns:
                matches = [f for f in relevant_files 
                          if f.name == pattern or f.suffix == pattern]
                if matches:
                    if db not in stack.databases:
                        stack.databases.append(db)
                    break

    def _analyze_by_content(self, repo_path: Path, stack: ProjectStack):
        """Анализ баз данных по содержимому файлов."""
        # Только расширения поддерживаемых языков: Python, TypeScript, Java/Kotlin, Go
        code_extensions = ['.py', '.pyw', '.ts', '.tsx', '.java', '.kt', '.kts', '.go']

        # Используем оптимизированную функцию для получения релевантных файлов
        relevant_files = get_relevant_files(repo_path, extensions=code_extensions, max_file_size=200 * 1024)

        for file_path in relevant_files:
            # Читаем только начало файла (достаточно для поиска паттернов БД)
            content = read_file_sample(file_path, max_lines=50, max_bytes=4096)

            if not content:
                continue

            # Определяем язык файла по расширению
            file_lang = get_language_by_extension(file_path.suffix)

            for db, patterns in self.pattern_config.DATABASE_PATTERNS.items():
                if db not in stack.databases:
                    # Проверяем паттерны с учетом языка файла
                    # Python-специфичные паттерны (psycopg2, pymysql и т.д.) применяются только к Python файлам
                    # TypeScript/JavaScript паттерны (require, import) применяются только к TypeScript файлам
                    # Go паттерны (redis.NewClient) применяются только к Go файлам
                    
                    for pattern in patterns:
                        # Фильтрация паттернов по языку
                        if file_lang == 'python':
                            # Для Python ищем Python-специфичные паттерны
                            if 'require(' in pattern or 'redis.NewClient' in pattern:
                                continue
                        elif file_lang == 'typescript':
                            # Для TypeScript ищем TypeScript/JavaScript паттерны
                            if 'psycopg2' in pattern or 'pymysql' in pattern or 'mysqldb' in pattern or \
                               'pymongo' in pattern or 'cx_Oracle' in pattern or 'pymssql' in pattern or \
                               'sqlite3' in pattern or 'redis.NewClient' in pattern:
                                continue
                        elif file_lang == 'go':
                            # Для Go ищем Go-специфичные паттерны (xorm, database/sql, драйверы)
                            # Разрешаем паттерны с xorm, database/sql, github.com, но блокируем Python/TS паттерны
                            if 'psycopg2' in pattern or 'pymysql' in pattern or 'mysqldb' in pattern or \
                               'pymongo' in pattern or 'cx_Oracle' in pattern or 'pymssql' in pattern or \
                               'require(' in pattern or 'mongoose' in pattern or 'import sqlite3' in pattern:
                                continue
                        elif file_lang == 'java':
                            # Для Java ищем Java-специфичные паттерны (пока нет специфичных, пропускаем Python/TS паттерны)
                            if 'psycopg2' in pattern or 'pymysql' in pattern or 'mysqldb' in pattern or \
                               'pymongo' in pattern or 'cx_Oracle' in pattern or 'pymssql' in pattern or \
                               'sqlite3' in pattern or 'require(' in pattern or 'mongoose' in pattern or \
                               'redis.NewClient' in pattern:
                                continue
                        else:
                            # Для неизвестного языка пропускаем специфичные паттерны
                            if 'psycopg2' in pattern or 'pymysql' in pattern or 'require(' in pattern or \
                               'redis.NewClient' in pattern:
                                continue
                        
                        if re.search(pattern, content, re.IGNORECASE):
                            stack.databases.append(db)
                            logger.info(f"Обнаружена БД {db} в файле {file_path.relative_to(repo_path)} по паттерну: {pattern}")
                            break


