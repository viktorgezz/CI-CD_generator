import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from GitLabRepoService import GitLabRepoService
except ImportError:
    logger.error("Ошибка: файл gitlab_service.py не найден в текущей директории.")


##!!!! Важно метод считывает файл из корня если надо по другому то {Использовать метод string_to_yaml_file}
def run_process(repo_link, repo_token, branch, yaml_content_str):
    # 1. Конфигурация
    # Ссылка на репозиторий (куда будем делать MR)
    # repo_link = "https://gitlab.com/viktorgezz/git-service-1"

    # Токен доступа (лучше брать из переменных окружения для безопасности)
    # export GITLAB_TOKEN=your_token_here
    # repo_token = os.getenv("GITLAB_TOKEN")
    # Базовая ветка в оригинальном репозитории (обычно main или master)
    # base_branch = "main"

    # 2. Подготовка файла (эмуляция чтения байтов)
    # Пытаемся прочитать реальный файл,
    # file_name_on_disk = "pipeline.yml"

    # 1. Проверка токена
    if not repo_token:
        logger.error("Токен не передан. Укажите токен.")
        return

    if yaml_content_str:
        logger.info("Конвертация YAML-строки в байты для отправки...")
        file_bytes = yaml_content_str.encode('utf-8')
    else:
        logger.error("Передан пустой контент для файла pipeline.yml")
        return

    # 3. Инициализация и запуск сервиса
    runner = GitLabRepoService()

    logger.info(f"Запуск процесса для репозитория: {repo_link}")

    try:
        runner.modify_repo(
            link=repo_link,
            token=repo_token,
            base_branch=branch,
            file_content=file_bytes
        )
        logger.info("Готово! Процесс завершен успешно.")

    except Exception as e:
        logger.error(f"Произошла ошибка при выполнении: {e}")


## ! Пример .yml
#     my_pipeline_config = """
# stages:
#     - build
#     - test
#     - deploy
#
# build_job:
#     stage: build
#     script:
#         - echo "Compiling the code..."
#         - echo "Build complete."
#
# test_job:
#     stage: test
#     script:
#         - echo "Running unit tests..."
#
# deploy_job:
#     stage: deploy
#     script:
#     - echo "Deploying to production..."
# """