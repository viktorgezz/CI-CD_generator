# Инфраструктура для разработки и тестирования

Инструкция по запуску локальной инфраструктуры GitLab и GitLab Runner для разработки и тестирования CI/CD пайплайнов.

## Требования

- Docker 20.10+
- Docker Compose 2.0+
- Минимум 4GB свободной RAM (рекомендуется 8GB)
- Минимум 20GB свободного места на диске

### Проверка требований

```bash
docker --version
docker compose version
```

## Быстрый старт

### 1. Перейдите в директорию infra

```bash
cd infra
```

### 2. Настройте hostname (опционально)

По умолчанию используется `gitlab.local`. Если нужно изменить:

1. Отредактируйте `docker-compose.yml`:
```yaml
hostname: 'your-domain.local'
external_url 'http://your-domain.local'
```

2. Добавьте в `/etc/hosts` (Linux/Mac) или `C:\Windows\System32\drivers\etc\hosts` (Windows):
```
127.0.0.1 gitlab.local
```

### 3. Запустите сервисы

```bash
docker-compose up -d
```

### 4. Дождитесь запуска GitLab

GitLab запускается долго (обычно 2-5 минут). Проверьте статус:

```bash
# Проверка статуса контейнеров
docker-compose ps

# Просмотр логов GitLab
docker-compose logs -f gitlab
```

Дождитесь сообщения в логах: `gitlab Reconfigured!` или `gitlab started`.

### 5. Получите root пароль

```bash
# Пароль для пользователя root будет в логах
docker-compose logs gitlab | grep "Password:"
```

Или выполните:

```bash
docker exec -it gitlab grep 'Password:' /etc/gitlab/initial_root_password
```

### 6. Откройте GitLab в браузере

```
http://gitlab.local
```

Войдите с учетными данными:
- **Username:** `root`
- **Password:** (из шага 5)

---

## Настройка GitLab

### Первоначальная настройка

1. **Войдите в GitLab** (root / пароль из логов)

2. **Создайте проект:**
   - Нажмите "New project" или "Create project"
   - Выберите "Create blank project"
   - Укажите название проекта
   - Нажмите "Create project"

3. **Настройте SSH ключ** (опционально):
   - Перейдите в Settings → SSH Keys
   - Добавьте ваш публичный SSH ключ

### Настройка для работы с CLI

Для использования команды `auto-merge-request` из CLI:

1. **Создайте Personal Access Token:**
   - Перейдите в Preferences → Access Tokens
   - Создайте токен с правами:
     - `api` - для работы с API
     - `write_repository` - для создания форков и MR
   - Скопируйте токен (он показывается только один раз!)

2. **Используйте токен в CLI:**
```bash
cd ../core-service
docker-compose run --rm cli auto-merge-request \
  --url "http://gitlab.local/username/project" \
  --token "your-token-here" \
  --file /output/.gitlab-ci.yml
```

---

## Настройка GitLab Runner

### Автоматическая регистрация (рекомендуется)

1. **Получите registration token:**
   - В GitLab перейдите в Settings → CI/CD → Runners
   - Скопируйте "Registration token"

2. **Зарегистрируйте runner:**
```bash
docker-compose exec gitlab-runner gitlab-runner register \
  --url http://gitlab \
  --registration-token YOUR_REGISTRATION_TOKEN \
  --executor docker \
  --docker-image alpine:latest \
  --description "docker-runner" \
  --tag-list "docker,linux" \
  --run-untagged=true \
  --locked=false
```

### Ручная настройка

1. **Отредактируйте `runner/config.toml`:**
```toml
[[runners]]
  name = "runner-1"
  url = "http://gitlab"  # Внутренний URL GitLab
  token = "YOUR_REGISTRATION_TOKEN"  # Замените на ваш токен
  executor = "docker"
  [runners.docker]
    image = "alpine:latest"
    privileged = true
```

2. **Перезапустите runner:**
```bash
docker-compose restart gitlab-runner
```

### Проверка регистрации

```bash
# Проверить статус runner
docker-compose exec gitlab-runner gitlab-runner verify

# Список зарегистрированных runners
docker-compose exec gitlab-runner gitlab-runner list
```

---

## Использование

### Тестирование сгенерированных пайплайнов

1. **Сгенерируйте пайплайн через CLI:**
```bash
cd ../core-service
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml
```

2. **Создайте проект в GitLab** (если еще не создан)

3. **Добавьте файл `.gitlab-ci.yml` в проект:**
   - Скопируйте содержимое из `core-service/output/.gitlab-ci.yml`
   - В GitLab перейдите в ваш проект
   - Создайте файл `.gitlab-ci.yml` в корне проекта
   - Вставьте содержимое и закоммитьте

4. **Запустите пайплайн:**
   - Пайплайн запустится автоматически при push
   - Или запустите вручную: CI/CD → Pipelines → Run pipeline

### Автоматическое создание Merge Request

```bash
cd ../core-service

# Сгенерировать пайплайн
docker-compose run --rm cli generate-from-repo \
  --url "http://gitlab.local/username/project" \
  --output /output/.gitlab-ci.yml

# Создать Merge Request автоматически
docker-compose run --rm cli auto-merge-request \
  --url "http://gitlab.local/username/project" \
  --token "your-gitlab-token" \
  --file /output/.gitlab-ci.yml \
  --branch main
```

---

## Управление сервисами

### Запуск

```bash
# Запустить все сервисы
docker-compose up -d

# Запустить с выводом логов
docker-compose up
```

### Остановка

```bash
# Остановить сервисы
docker-compose stop

# Остановить и удалить контейнеры
docker-compose down
```

### Перезапуск

```bash
# Перезапустить все сервисы
docker-compose restart

# Перезапустить конкретный сервис
docker-compose restart gitlab
docker-compose restart gitlab-runner
```

### Просмотр логов

```bash
# Все логи
docker-compose logs

# Логи GitLab
docker-compose logs gitlab

# Логи GitLab Runner
docker-compose logs gitlab-runner

# Логи в реальном времени
docker-compose logs -f gitlab

# Последние 100 строк
docker-compose logs --tail=100 gitlab
```

### Проверка статуса

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats gitlab gitlab-runner
```

---

## Конфигурация

### Изменение портов

Если порты 80, 443 или 22 заняты, измените их в `docker-compose.yml`:

```yaml
ports:
  - '8080:80'    # HTTP
  - '8443:443'   # HTTPS
  - '2222:22'    # SSH
```

После изменения перезапустите:
```bash
docker-compose down
docker-compose up -d
```

### Изменение hostname

1. Отредактируйте `docker-compose.yml`:
```yaml
hostname: 'your-domain.local'
environment:
  GITLAB_OMNIBUS_CONFIG: |
    external_url 'http://your-domain.local'
```

2. Обновите `/etc/hosts`:
```
127.0.0.1 your-domain.local
```

3. Пересоздайте контейнер:
```bash
docker-compose down
docker-compose up -d
```

### Настройка объема данных

Данные GitLab сохраняются в volumes:
- `./gitlab/config` - конфигурация
- `./gitlab/logs` - логи
- `./gitlab/data` - данные (проекты, БД и т.д.)

Для изменения расположения отредактируйте `docker-compose.yml`:

```yaml
volumes:
  - /path/to/gitlab/config:/etc/gitlab
  - /path/to/gitlab/logs:/var/log/gitlab
  - /path/to/gitlab/data:/var/opt/gitlab
```

---

## Примечания

- **Первый запуск:** GitLab запускается долго (2-5 минут). Дождитесь сообщения `gitlab Reconfigured!` в логах.
- **Память:** GitLab требует минимум 4GB RAM. Для production рекомендуется 8GB+.
- **Диск:** GitLab занимает много места. Регулярно очищайте неиспользуемые данные.
- **Безопасность:** Это локальная инфраструктура для разработки. Не используйте в production без дополнительной настройки безопасности.

