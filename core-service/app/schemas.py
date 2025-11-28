from datetime import datetime
from typing import Any, List, Literal, Optional, Union

from pydantic import BaseModel, HttpUrl, Field, field_validator


# ---------- Проект и анализ репозитория ----------


class ProjectAnalysis(BaseModel):
    languages: List[str] = []
    frameworks: List[str] = []
    frontend_frameworks: List[str] = []
    backend_frameworks: List[str] = []
    package_manager: Optional[str] = None
    test_runner: Optional[str] = None
    java_version: Optional[str] = None  # Версия Java из pom.xml
    docker: bool = False
    docker_context: str = ""
    dockerfile_path: Optional[str] = None
    dockerfile_paths: List[str] = []  # Список всех Dockerfile
    kubernetes: bool = False
    terraform: bool = False
    databases: List[str] = []

    @field_validator("test_runner", mode="before")
    @classmethod
    def convert_test_runner_to_string(cls, v: Any) -> Optional[str]:
        """Конвертирует test_runner из списка в строку, если необходимо."""
        if v is None:
            return None
        if isinstance(v, list):
            # Берем первый элемент списка, если список не пустой
            return v[0] if v else None
        if isinstance(v, str):
            return v
        # Если это другой тип, конвертируем в строку
        return str(v) if v else None


class ProjectBase(BaseModel):
    name: str = Field(..., description="Название проекта в Self-Deploy")
    url: HttpUrl = Field(..., description="URL Git-репозитория")
    clone_token: str = Field(..., description="Токен для клонирования репозитория")


class ProjectCreate(ProjectBase):
    analysis: Optional[ProjectAnalysis] = None


class ProjectCreateRequest(ProjectBase):
    """
    Входная схема для создания проекта от клиента.
    Анализ репозитория заполняется автоматически через внешний сервис.
    """


class Project(ProjectBase):
    id: int
    analysis: Optional[ProjectAnalysis] = None

    class Config:
        from_attributes = True


# ---------- Генерация пайплайна ----------


class PipelineGenerationBase(BaseModel):
    project_id: Optional[int] = None
    uml: str = Field(..., description="Готовый пайплайн в UML-представлении или другом форматировании")


class PipelineGenerationCreate(PipelineGenerationBase):
    ...


class PipelineGeneration(PipelineGenerationBase):
    id: int
    generated_at: datetime

    class Config:
        from_attributes = True



# ---------- Пользовательские настройки для генерации пайплайна ----------


class TriggerSettings(BaseModel):
    on_push: List[str] = []
    on_merge_request: bool = False
    on_tags: str | None = ""
    schedule: str | None = ""
    manual: bool = False


class UserSettings(BaseModel):
    platform: str
    triggers: TriggerSettings
    stages: List[str] = []
    docker_registry: str | None = ""
    docker_image: str | None = ""
    docker_context: str | None = None
    dockerfile_path: str | None = None
    variables: dict = {}
    project_name: str | None = ""
    python_version: str | None = ""
    docker_tag: str | None = ""


class PipelineGenerationRequest(BaseModel):
    """
    Вход для генерации пайплайна:
    - project_id: из него берётся analysis из БД
    - user_settings: пользовательские настройки генерации
    """

    project_id: int
    user_settings: UserSettings


class PipelineGenerateFromRepoRequest(BaseModel):
    """
    Вход для генерации пайплайна напрямую из репозитория:
    - repo_url: URL Git-репозитория
    - token: токен для клонирования репозитория
    """

    repo_url: HttpUrl = Field(..., description="URL Git-репозитория")
    token: str = Field(..., description="Токен для клонирования репозитория")



