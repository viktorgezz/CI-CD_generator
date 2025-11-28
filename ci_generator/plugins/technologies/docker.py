"""
plugins/technologies/docker.py
"""

DOCKER_STAGES = [
    "docker_build",
    "docker_push",
    "cleanup",
    "integration",   # integration often uses docker-compose
]

def enabled(analysis: dict) -> bool:
    return bool(analysis.get("docker"))

def get_stages(analysis: dict, user_settings: dict):
    stages = list(DOCKER_STAGES)
    # only include push if registry provided
    registry = user_settings.get("docker_registry") or user_settings.get("docker_image") or ""
    if not registry and "docker_push" in stages:
        stages.remove("docker_push")
    # include integration only if entry_points include docker-compose
    has_compose = any((e.get("type") and "docker-compose" in str(e.get("type"))) for e in analysis.get("entry_points",[]))
    if not has_compose and "integration" in stages:
        stages.remove("integration")
    # include deploy stage if:
    # 1. use_docker_compose is explicitly enabled, OR
    # 2. docker is present and kubernetes is NOT present (default to docker-compose deploy)
    has_kubernetes = analysis.get("kubernetes", False)
    use_docker_compose = user_settings.get("use_docker_compose", False)
    should_add_deploy = use_docker_compose or (not has_kubernetes)
    if should_add_deploy and "deploy" not in stages:
        stages.append("deploy")
    return stages
