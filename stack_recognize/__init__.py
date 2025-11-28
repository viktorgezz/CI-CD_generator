"""Пакет для анализа технологического стека проекта."""
from .detector import ProjectStackDetector
from .models import ProjectStack, EntryPoint

__all__ = ['ProjectStackDetector', 'ProjectStack', 'EntryPoint']
__version__ = '1.0.0'

