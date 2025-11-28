"""
plugins/technologies/kubernetes.py
"""

K8S_STAGES = [
    "deploy",
    "post_deploy",
]

def enabled(analysis: dict) -> bool:
    return bool(analysis.get("kubernetes"))

def get_stages(analysis: dict, user_settings: dict):
    stages = list(K8S_STAGES)
    # Если use_docker_compose включен, не добавляем deploy (будет использован docker-compose deploy)
    if user_settings.get("use_docker_compose", False) and "deploy" in stages:
        stages.remove("deploy")
    return stages
