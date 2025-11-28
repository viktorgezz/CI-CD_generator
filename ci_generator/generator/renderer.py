"""
renderer.py

Рендерит pipeline для GitLab и Jenkins.
Ищет шаблон стадии в директориях:
  templates_root/<platform>/stages/python/<stage>.<ext>
  templates_root/<platform>/stages/docker/<stage>.<ext>
  templates_root/<platform>/stages/kubernetes/<stage>.<ext>
  templates_root/<platform>/stages/shared/<stage>.<ext>

Если шаблона для стадии нет — стадия пропускается (маловероятно).
"""

import os
from jinja2 import Environment, FileSystemLoader
from typing import List, Dict

class PipelineRenderer:
    def __init__(self, templates_root: str = "pipelines"):
        self.templates_root = templates_root
        self.env = Environment(loader=FileSystemLoader(templates_root), trim_blocks=True, lstrip_blocks=True)

        # search order for stage templates
        # tests вынесены в отдельную директорию "tests"
        # языковые директории должны быть проверены перед общими
        self.stage_dirs = ["tests", "python", "java", "go", "typescript", "docker", "kubernetes", "shared"]

    def _find_stage_template(self, platform: str, stage: str, ext: str, ctx: Dict = None) -> str:
        """
        Возвращает относительный путь шаблона (от templates_root) или None.
        ext: 'gitlab.j2' or 'jenkins.j2' suffix.
        Сначала ищет в директории языка из ctx.language, затем в общих директориях.
        """
        base = os.path.join(platform, "stages")
        
        # Специальная логика для deploy: если use_docker_compose = True, используем shared/deploy
        if stage == "deploy" and ctx and ctx.get("use_docker_compose", False):
            candidate = os.path.join(base, "shared", f"{stage}.{ext}")
            if os.path.exists(os.path.join(self.templates_root, candidate)):
                return candidate
        
        # Определяем приоритетный язык из контекста
        language_dir = None
        if ctx:
            language = ctx.get("language", "").lower()
            # Маппинг языков на директории
            lang_to_dir = {
                "python": "python",
                "java": "java",
                "kotlin": "java",  # Kotlin использует Java шаблоны
                "go": "go",
                "golang": "go",
                "typescript": "typescript",
                "javascript": "typescript",  # JavaScript использует TypeScript шаблоны
            }
            language_dir = lang_to_dir.get(language)
        
        # Сначала проверяем директорию языка, если она определена
        if language_dir and language_dir in self.stage_dirs:
            candidate = os.path.join(base, language_dir, f"{stage}.{ext}")
            if os.path.exists(os.path.join(self.templates_root, candidate)):
                return candidate
        
        # Затем проверяем остальные директории в порядке приоритета
        # Для deploy: shared должен быть перед kubernetes
        search_dirs = self.stage_dirs.copy()
        if stage == "deploy":
            # Перемещаем shared перед kubernetes для deploy
            if "shared" in search_dirs and "kubernetes" in search_dirs:
                shared_idx = search_dirs.index("shared")
                k8s_idx = search_dirs.index("kubernetes")
                if shared_idx > k8s_idx:
                    search_dirs.remove("shared")
                    search_dirs.insert(k8s_idx, "shared")
        
        for d in search_dirs:
            # Пропускаем уже проверенную директорию языка
            if d == language_dir:
                continue
            candidate = os.path.join(base, d, f"{stage}.{ext}")
            if os.path.exists(os.path.join(self.templates_root, candidate)):
                return candidate
        return None

    def render_gitlab(self, stages: List[str], ctx: Dict) -> str:
        parts = []
        # base header (stages list + variables)
        header_tpl = self.env.get_template("gitlab/base_header.j2")
        parts.append(header_tpl.render(stages=stages, ctx=ctx))

        # append each stage template content
        for s in stages:
            tpl_path = self._find_stage_template("gitlab", s, "gitlab.j2", ctx)
            if tpl_path:
                tpl = self.env.get_template(tpl_path)
                parts.append(tpl.render(ctx=ctx))
            else:
                # skip silently if no template (extensible)
                parts.append(f"# NOTE: no template for stage: {s}\n")

        return "\n".join(parts)

    def render_jenkins(self, stages: List[str], ctx: Dict) -> str:
        parts = []
        header_tpl = self.env.get_template("jenkins/base_header.j2")
        parts.append(header_tpl.render(ctx=ctx))

        # include each stage snippet
        for s in stages:
            tpl_path = self._find_stage_template("jenkins", s, "jenkins.j2", ctx)
            if tpl_path:
                tpl = self.env.get_template(tpl_path)
                parts.append(tpl.render(ctx=ctx))
            else:
                parts.append(f"// NOTE: no template for stage: {s}\n")

        # close pipeline (header already includes closing)
        return "\n".join(parts)
