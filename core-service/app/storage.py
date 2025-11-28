import json
from typing import List

from sqlalchemy.orm import Session

from app import models
from app.schemas import (
    Project,
    ProjectCreate,
    PipelineGeneration,
    PipelineGenerationCreate,
    ProjectAnalysis,
)


# ---------- Projects ----------


def _analysis_to_json(analysis: ProjectAnalysis | None) -> str | None:
    if analysis is None:
        return None
    return analysis.model_dump_json()


def _analysis_from_json(data: str | None) -> ProjectAnalysis | None:
    if not data:
        return None
    # Используем pydantic для восстановления объекта
    return ProjectAnalysis.model_validate(json.loads(data))


def create_project(db: Session, data: ProjectCreate) -> Project:
    try:
        project_orm = models.ProjectORM(
            name=data.name,
            url=str(data.url),
            clone_token=data.clone_token,
            analysis_json=_analysis_to_json(data.analysis),
        )
        db.add(project_orm)
        db.commit()
        db.refresh(project_orm)

        return Project(
            id=project_orm.id,
            name=project_orm.name,
            url=project_orm.url,
            clone_token=project_orm.clone_token,
            analysis=_analysis_from_json(project_orm.analysis_json),
        )
    except Exception as exc:
        db.rollback()
        raise


def list_projects(db: Session) -> List[Project]:
    projects = db.query(models.ProjectORM).all()
    result: List[Project] = []
    for p in projects:
        result.append(
            Project(
                id=p.id,
                name=p.name,
                url=p.url,
                clone_token=p.clone_token,
                analysis=_analysis_from_json(p.analysis_json),
            )
        )
    return result


def get_project(db: Session, project_id: int) -> Project | None:
    p = db.query(models.ProjectORM).filter(models.ProjectORM.id == project_id).first()
    if p is None:
        return None
    return Project(
        id=p.id,
        name=p.name,
        url=p.url,
        clone_token=p.clone_token,
        analysis=_analysis_from_json(p.analysis_json),
    )


# ---------- Pipeline generations ----------


def create_pipeline_generation(
    db: Session, data: PipelineGenerationCreate
) -> PipelineGeneration:
    pipeline_orm = models.PipelineGenerationORM(
        project_id=data.project_id,
        uml=data.uml,
    )
    db.add(pipeline_orm)
    db.commit()
    db.refresh(pipeline_orm)

    return PipelineGeneration(
        id=pipeline_orm.id,
        project_id=pipeline_orm.project_id,
        uml=pipeline_orm.uml,
        generated_at=pipeline_orm.generated_at,
    )


def list_pipeline_generations(db: Session) -> List[PipelineGeneration]:
    pipelines = db.query(models.PipelineGenerationORM).all()
    return [
        PipelineGeneration(
            id=p.id,
            project_id=p.project_id,
            uml=p.uml,
            generated_at=p.generated_at,
        )
        for p in pipelines
    ]


