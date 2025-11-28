# Docker Compose для CLI

Инструкция по запуску CLI приложения через Docker Compose.

## Требования

- Docker
- Docker Compose

## Быстрый старт

1. Перейдите в директорию `core-service`:
```bash
cd core-service
```

2. Запустите сервисы:
```bash
docker-compose up -d
```

3. Инициализируйте базу данных:
```bash
docker-compose run --rm cli init
```

## Использование CLI команд

### Базовые команды

```bash
# Показать справку
docker-compose run --rm cli --help

# Инициализация базы данных
docker-compose run --rm cli init

# Добавить проект
docker-compose run --rm cli add-project --name "My Project" --url "https://github.com/user/repo"

# Список проектов
docker-compose run --rm cli list-projects

# Анализ репозитория
docker-compose run --rm cli analyze-repo --url "https://github.com/user/repo" --output /output/stack.json

# Генерация пайплайна из репозитория
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml

# Создание Merge Request
docker-compose run --rm cli auto-merge-request \
  --url "https://gitlab.com/user/repo" \
  --token "your-token" \
  --file /output/.gitlab-ci.yml \
  --branch main
```

### Сохранение результатов

Результаты работы CLI сохраняются в директорию `core-service/output/`, которая монтируется в контейнер как `/output`.

Пример:
```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --stack-output /output/stack.json
```

После выполнения файлы будут доступны в `core-service/output/`.

## Остановка сервисов

```bash
# Остановить сервисы
docker-compose down

# Остановить и удалить volumes (удалит данные БД)
docker-compose down -v
```

## Переменные окружения

Вы можете настроить подключение к базе данных через переменные окружения в `docker-compose.yml`:

```yaml
environment:
  DATABASE_URL: postgresql+psycopg2://postgres:postgres@postgres:5432/self_deploy
```

## Порт PostgreSQL

По умолчанию PostgreSQL доступен на порту **5433** (чтобы не конфликтовать с локальным PostgreSQL на порту 5432).

Если нужно изменить порт, отредактируйте `docker-compose.yml`:
```yaml
ports:
  - "5433:5432"  # Измените 5433 на нужный порт
```

## Структура сервисов

- **postgres** - PostgreSQL база данных (порт 5432)
- **cli** - CLI приложение

## Troubleshooting

### Проблемы с подключением к БД

Убедитесь, что PostgreSQL запущен и готов:
```bash
docker-compose ps
```

Проверьте логи:
```bash
docker-compose logs postgres
docker-compose logs cli
```

### Проблемы с путями к модулям

Убедитесь, что все модули проекта (stack_recognize, ci_generator, auto-merge-request, docker_compose_generator) находятся в корне проекта и правильно смонтированы в контейнер.

