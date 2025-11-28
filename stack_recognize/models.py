"""Модели данных для проекта анализа технологического стека."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class EntryPoint:
    """Структура для хранения информации о точке входа."""
    type: str  # 'app', 'server', 'main', 'config'
    file_path: str
    framework: Optional[str] = None
    language: Optional[str] = None
    confidence: float = 0.0  # Уверенность в определении (0.0 - 1.0)
    description: Optional[str] = None


@dataclass
class ProjectStack:
    """Структура для хранения информации о технологическом стеке проекта."""
    languages: List[str] = field(default_factory=list)
    frameworks: List[str] = field(default_factory=list)
    frontend_frameworks: List[str] = field(default_factory=list)
    backend_frameworks: List[str] = field(default_factory=list)
    mobile_frameworks: List[str] = field(default_factory=list)
    package_manager: Optional[str] = None
    test_runner: List[str] = field(default_factory=list)
    docker: bool = False
    kubernetes: bool = False
    terraform: bool = False
    cicd: List[str] = field(default_factory=list)
    databases: List[str] = field(default_factory=list)
    cloud_platforms: List[str] = field(default_factory=list)
    build_tools: List[str] = field(default_factory=list)
    entry_points: List[EntryPoint] = field(default_factory=list)
    main_entry_point: Optional[EntryPoint] = None
    hints: List[str] = field(default_factory=list)
    files_detected: Dict[str, Any] = field(default_factory=dict)

