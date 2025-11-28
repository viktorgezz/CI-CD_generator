import gitlab
import base64
import time
import logging
from urllib.parse import urlparse

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GitLabRepoService:
    # Константы
    TARGET_BRANCH_NAME = "pipeline_auto_branch"
    COMMIT_MESSAGE = "Add pipeline configuration file"
    UPDATE_MESSAGE = "Update pipeline configuration file"
    MR_TITLE = "Add pipeline configuration file"
    MR_DESCRIPTION = "Automated Merge Request adding pipeline.yml configuration"
    FILE_NAME = ".gitlab-ci.yml"

    def modify_repo(self, link: str, token: str, base_branch: str, file_content: bytes):
        """
        Главный метод, выполняющий весь процесс.
        """
        try:
            # Инициализация клиента
            gl = gitlab.Gitlab("https://gitlab.com", private_token=token.strip())
            gl.auth()

            logger.info(f"Starting repository processing: {link}")

            # 1. Получаем оригинальный проект
            project_path = self._extract_project_path(link)
            original_project = gl.projects.get(project_path)
            current_user = gl.user

            # 2. Получаем или создаем форк
            forked_project = self._get_or_create_fork(original_project, current_user)
            logger.info(f"Working with fork ID: {forked_project.id}")

            # 3. Создаем ветку в форке
            self._create_or_get_branch(forked_project, base_branch)

            # 4. Заливаем файл в форк
            self._create_or_update_file(forked_project, file_content)

            # 5. Создаем Merge Request
            self._create_or_get_merge_request(forked_project, original_project, base_branch)

        except gitlab.GitlabError as e:
            logger.error(f"GitLab API error: {e}")
            raise RuntimeError(f"GitLab operation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise RuntimeError(f"Unexpected error: {e}")

    def _extract_project_path(self, link: str) -> str:
        parsed = urlparse(link)
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        return path

    def _get_or_create_fork(self, original_project, user):
        fork_path = f"{user.username}/{original_project.path}"

        try:
            # Пытаемся найти через глобальный менеджер проектов
            return original_project.manager.gitlab.projects.get(fork_path)
        except gitlab.GitlabGetError:
            logger.info("Fork not found. Creating new fork...")
            fork = original_project.forks.create({})

            # Ждем завершения
            self._wait_for_fork_completion(fork)

            # Важно: возвращаем "свежий" объект проекта через глобальный менеджер
            return original_project.manager.gitlab.projects.get(fork.id)

    def _wait_for_fork_completion(self, fork_project):
        """Ждет завершения импорта форка."""
        attempts = 0
        max_attempts = 30

        # Получаем доступ к глобальному объекту gitlab для запросов
        gl_instance = fork_project.manager.gitlab

        while attempts < max_attempts:
            # ИСПРАВЛЕНИЕ ЗДЕСЬ: используем глобальный менеджер проектов (gl.projects.get),
            # а не менеджер форков (fork_project.manager.get), у которого нет метода get.
            current_project_state = gl_instance.projects.get(fork_project.id)
            status = current_project_state.import_status

            if status in ['finished', 'none', None]:
                return

            logger.info(f"Waiting for fork... Status: {status}")
            time.sleep(2)
            attempts += 1

        logger.warning("Fork wait time exceeded")

    def _create_or_get_branch(self, project, original_base_branch):
        try:
            project.branches.get(self.TARGET_BRANCH_NAME)
            logger.info(f"Branch {self.TARGET_BRANCH_NAME} already exists in fork")
        except gitlab.GitlabGetError:
            logger.info(f"Creating branch {self.TARGET_BRANCH_NAME} from {original_base_branch}")
            project.branches.create({
                'branch': self.TARGET_BRANCH_NAME,
                'ref': original_base_branch
            })

    def _create_or_update_file(self, project, content: bytes):
        b64_content = base64.b64encode(content).decode('utf-8')

        file_action_data = {
            'file_path': self.FILE_NAME,
            'branch': self.TARGET_BRANCH_NAME,
            'content': b64_content,
            'encoding': 'base64'
        }

        try:
            f = project.files.get(file_path=self.FILE_NAME, ref=self.TARGET_BRANCH_NAME)
            logger.info("File exists. Updating...")
            file_action_data['commit_message'] = self.UPDATE_MESSAGE
            f.content = b64_content
            f.encoding = 'base64'
            f.save(branch=self.TARGET_BRANCH_NAME, commit_message=self.UPDATE_MESSAGE)
        except gitlab.GitlabGetError:
            logger.info("File not found. Creating...")
            file_action_data['commit_message'] = self.COMMIT_MESSAGE
            project.files.create(file_action_data)

    def _create_or_get_merge_request(self, source_project, target_project, target_branch):
        logger.info(f"Attempting to create Merge Request from Fork (ID: {source_project.id}) "
                    f"to Original (ID: {target_project.id})...")

        mr_data = {
            'source_branch': self.TARGET_BRANCH_NAME,
            'target_branch': target_branch,
            'title': self.MR_TITLE,
            'description': self.MR_DESCRIPTION,
            'target_project_id': target_project.id,
            'remove_source_branch': True
        }

        try:
            mr = source_project.mergerequests.create(mr_data)
            logger.info(f"Merge Request created successfully: {mr.web_url}")

        except gitlab.GitlabCreateError as e:
            if e.response_code == 409 or "already exists" in str(e):
                logger.info("Merge Request creation failed: it already exists. Searching for it...")
                mrs = target_project.mergerequests.list(
                    source_branch=self.TARGET_BRANCH_NAME,
                    target_branch=target_branch,
                    state='opened',
                    get_all=False
                )
                if mrs:
                    logger.info(f"Found existing Merge Request: {mrs[0].web_url}")
                else:
                    logger.warning("GitLab says MR exists, but search returned empty list. Check permissions.")
            else:
                raise e