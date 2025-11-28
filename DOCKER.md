# Docker Документация

Документация по использованию CLI приложения через Docker и Docker Compose.

## Содержание

- [Установка и настройка](#установка-и-настройка)
- [Быстрый старт](#быстрый-старт)
- [Основные команды через Docker](#основные-команды-через-docker)
  - [generate-from-repo](#generate-from-repo) ⭐
  - [analyze-repo](#analyze-repo)
  - [auto-merge-request](#auto-merge-request)
  - [init](#init)
  - [add-project](#add-project)
  - [list-projects](#list-projects)
  - [generate](#generate)
  - [list-pipelines](#list-pipelines)
- [Примеры использования](#примеры-использования)
- [Управление сервисами](#управление-сервисами)
- [Конфигурация](#конфигурация)
- [Troubleshooting](#troubleshooting)

## Установка и настройка

### Требования

- Docker 20.10+
- Docker Compose 2.0+ (или docker compose plugin)

### Проверка установки

```bash
docker --version
docker compose version
```

### Первоначальная настройка

1. Перейдите в директорию `core-service`:
```bash
cd core-service
```

2. Запустите сервисы:
```bash
docker-compose up -d
```

3. Дождитесь готовности PostgreSQL (обычно 5-10 секунд):
```bash
docker-compose ps
```

4. Инициализируйте базу данных:
```bash
docker-compose run --rm cli init
```

## Быстрый старт

### Минимальный пример

```bash
cd core-service

# Запустить сервисы
docker-compose up -d

# Инициализировать БД
docker-compose run --rm cli init

# Сгенерировать пайплайн
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml
```

## Основные команды через Docker

### generate-from-repo

**Генерирует CI/CD пайплайн и Markdown файл с описанием стека проекта напрямую из репозитория без сохранения проекта в базу данных. Это самая гибкая команда с множеством опций настройки.**

**Использование:**
```bash
docker-compose run --rm cli generate-from-repo --url "https://github.com/user/repo" [опции]
```

**Основные параметры:**
- `--url` (обязательный) - URL Git-репозитория
- `--token` (опциональный) - Токен для доступа к приватному репозиторию
- `--output` (опциональный) - Путь для сохранения пайплайна. Используйте `/output/` для сохранения в директорию `core-service/output/`
- `--platform` (опциональный) - Платформа CI/CD: `gitlab` (по умолчанию: `gitlab`)
- `--stack-output` (опциональный) - Путь для сохранения стека проекта в формате JSON
- `--docker-compose` / `--no-docker-compose` (опциональный) - Генерировать docker-compose.yml для деплоя

**Параметры настройки стадий:**
- `--stages` (опциональный) - Список стадий через запятую. Если не указан, используются все возможные стадии

**Параметры настройки триггеров:**
- `--on-push` (опциональный) - Список веток для триггера push через запятую (например: `main,master,develop`)
- `--on-merge-request` / `--no-on-merge-request` (опциональный) - Включить/выключить триггер на merge request
- `--on-tags` (опциональный) - Паттерн для триггера на теги (regex, например: `v.*`)
- `--schedule` (опциональный) - Включить запуск по расписанию (любое значение)
- `--manual` / `--no-manual` (опциональный) - Разрешить/запретить ручной запуск пайплайна

**Примеры:**

Базовое использование:
```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml
```

С настройкой стадий:
```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --stages "lint,test,build"
```

С настройкой триггеров:
```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --on-push "main,develop" \
  --on-merge-request \
  --manual
```

Полная настройка:
```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --stack-output /output/stack.json \
  --stages "lint,test,build,deploy" \
  --on-push "main,master" \
  --on-merge-request \
  --on-tags "v.*" \
  --manual
```

**Что делает:**
1. Клонирует репозиторий (временная директория)
2. Анализирует технологический стек
3. Генерирует CI/CD пайплайн на основе анализа
4. Сохраняет пайплайн в указанный файл (или выводит в консоль)
5. Автоматически создает README с описанием стека проекта (если указан `--output`)
6. Опционально сохраняет стек в JSON (если указан `--stack-output`)
7. Опционально генерирует docker-compose.yml (если указан `--docker-compose`)
8. Выводит время выполнения

**Примечание:** Все файлы сохраняются в директорию `core-service/output/` на хосте.

---

### analyze-repo

Анализирует репозиторий и определяет его технологический стек без сохранения в базу данных.

**Использование:**
```bash
docker-compose run --rm cli analyze-repo --url "https://github.com/user/repo" [--token "token"] [--output "/output/stack.json"]
```

**Параметры:**
- `--url` (обязательный) - URL Git-репозитория
- `--token` (опциональный) - Токен для доступа к приватному репозиторию
- `--output` (опциональный) - Путь для сохранения стека в формате JSON. Используйте `/output/` для сохранения в директорию `core-service/output/`

**Пример:**
```bash
docker-compose run --rm cli analyze-repo \
  --url "https://github.com/user/repo" \
  --output /output/project-stack.json
```

**Что анализируется:**
- Языки программирования
- Фреймворки (frontend и backend)
- Менеджер пакетов
- Тестовые раннеры
- Docker (Dockerfile и контекст)
- Kubernetes
- Terraform
- Базы данных
- Облачные платформы
- Инструменты сборки
- CI/CD системы

---

### auto-merge-request

Автоматически создает Merge Request с указанным файлом в GitLab репозиторий.

**Использование:**
```bash
docker-compose run --rm cli auto-merge-request --url "https://gitlab.com/user/repo" --token "token" --file "/output/.gitlab-ci.yml" [--branch "main"]
```

**Параметры:**
- `--url` (обязательный) - URL GitLab репозитория
- `--token` (обязательный) - GitLab токен для доступа к API
- `--file` (обязательный) - Путь к файлу для отправки в Merge Request. Используйте `/output/` для файлов из директории `core-service/output/`
- `--branch` (опциональный) - Базовая ветка для создания Merge Request (по умолчанию: `main`)

**Пример:**
```bash
docker-compose run --rm cli auto-merge-request \
  --url "https://gitlab.com/user/my-project" \
  --token "glpat-xxxxxxxxxxxx" \
  --file /output/.gitlab-ci.yml \
  --branch main
```

**Что делает:**
1. Читает указанный файл с локального диска
2. Создает форк указанного GitLab репозитория (если форк еще не существует)
3. Создает ветку `pipeline_auto_branch` в форке
4. Добавляет или обновляет файл `.gitlab-ci.yml` в форке
5. Создает Merge Request из форка в оригинальный репозиторий

---

### init

Инициализирует базу данных для хранения проектов и истории генерации пайплайнов.

**Использование:**
```bash
docker-compose run --rm cli init
```

**Описание:**
Создает необходимые таблицы в базе данных PostgreSQL. Эту команду нужно выполнить один раз перед первым использованием системы.

---

### add-project

Добавляет новый проект в базу данных и автоматически анализирует его технологический стек.

**Использование:**
```bash
docker-compose run --rm cli add-project --name "Название проекта" --url "https://github.com/user/repo" [--token "token"]
```

**Параметры:**
- `--name` (обязательный) - Название проекта
- `--url` (обязательный) - URL Git-репозитория
- `--token` (опциональный) - Токен для доступа к приватному репозиторию

**Пример:**
```bash
docker-compose run --rm cli add-project \
  --name "My Project" \
  --url "https://github.com/user/my-project"
```

---

### list-projects

Показывает список всех проектов, добавленных в базу данных.

**Использование:**
```bash
docker-compose run --rm cli list-projects
```

**Вывод:**
Отображает ID, название, URL и основные характеристики каждого проекта (языки программирования).

---

### generate

Генерирует CI/CD пайплайн для проекта, сохраненного в базе данных.

**Использование:**
```bash
docker-compose run --rm cli generate --project-id <ID> [--output "/output/pipeline.yml"] [--platform "gitlab"] [--stages "stage1,stage2"]
```

**Параметры:**
- `--project-id` (обязательный) - ID проекта из базы данных
- `--output` (опциональный) - Путь для сохранения пайплайна. Используйте `/output/` для сохранения в директорию `core-service/output/`. Если не указан, пайплайн выводится в консоль
- `--platform` (опциональный) - Платформа CI/CD: `gitlab` или `jenkins` (по умолчанию: `gitlab`)
- `--stages` (опциональный) - Список стадий через запятую. Если не указан, используются все возможные стадии

**Пример:**
```bash
docker-compose run --rm cli generate \
  --project-id 1 \
  --output /output/.gitlab-ci.yml \
  --stages "lint,test,build"
```

---

### list-pipelines

Показывает историю генерации пайплайнов.

**Использование:**
```bash
docker-compose run --rm cli list-pipelines
```

**Вывод:**
Отображает ID генерации, ID проекта, дату создания и размер каждого сгенерированного пайплайна.

---

## Примеры использования

### Сценарий 1: Быстрая генерация пайплайна

Если нужно быстро сгенерировать пайплайн для репозитория без сохранения в базу данных:

```bash
cd core-service
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml
```

Результат будет в `core-service/output/.gitlab-ci.yml`

### Сценарий 2: Работа с проектами в базе данных

1. Инициализировать БД:
```bash
docker-compose run --rm cli init
```

2. Добавить проект:
```bash
docker-compose run --rm cli add-project \
  --name "My Project" \
  --url "https://github.com/user/repo"
```

3. Посмотреть список проектов:
```bash
docker-compose run --rm cli list-projects
```

4. Сгенерировать пайплайн:
```bash
docker-compose run --rm cli generate \
  --project-id 1 \
  --output /output/.gitlab-ci.yml
```

### Сценарий 3: Настройка пайплайна для production

```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --stages "lint,security,test,build,deploy" \
  --on-push "main" \
  --on-tags "v.*" \
  --manual
```

### Сценарий 4: Анализ стека и генерация пайплайна с сохранением стека

```bash
# Анализ стека
docker-compose run --rm cli analyze-repo \
  --url "https://github.com/user/repo" \
  --output /output/stack.json

# Генерация пайплайна с сохранением стека
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --stack-output /output/stack.json
```

### Сценарий 5: Генерация и автоматическое создание Merge Request

```bash
# Генерация пайплайна
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml

# Создание Merge Request в GitLab
docker-compose run --rm cli auto-merge-request \
  --url "https://gitlab.com/user/repo" \
  --token "your-gitlab-token" \
  --file /output/.gitlab-ci.yml \
  --branch main
```

---

## Управление сервисами

### Запуск сервисов

```bash
# Запустить в фоновом режиме
docker-compose up -d

# Запустить с выводом логов
docker-compose up
```

### Остановка сервисов

```bash
# Остановить сервисы
docker-compose down

# Остановить и удалить volumes (удалит данные БД!)
docker-compose down -v
```

### Проверка статуса

```bash
# Статус контейнеров
docker-compose ps

# Логи PostgreSQL
docker-compose logs postgres

# Логи CLI (последние 50 строк)
docker-compose logs --tail=50 cli

# Логи в реальном времени
docker-compose logs -f
```

### Пересборка образа

```bash
# Пересобрать образ после изменений
docker-compose build cli

# Пересобрать без кэша
docker-compose build --no-cache cli
```

---

## Конфигурация

### Структура сервисов

- **postgres** - PostgreSQL база данных
  - Порт: `5433:5432` (внешний:внутренний)
  - База данных: `self_deploy`
  - Пользователь: `postgres`
  - Пароль: `postgres`
  - Данные сохраняются в volume `postgres_data`

- **cli** - CLI приложение
  - Рабочая директория: `/app/core-service`
  - Монтирование проекта: `/app` (read-only)
  - Директория вывода: `/output` → `core-service/output/`

### Переменные окружения

Вы можете настроить подключение к базе данных через переменные окружения в `docker-compose.yml`:

```yaml
environment:
  DATABASE_URL: postgresql+psycopg2://postgres:postgres@postgres:5432/self_deploy
```

### Изменение порта PostgreSQL

По умолчанию PostgreSQL доступен на порту **5433** (чтобы не конфликтовать с локальным PostgreSQL на порту 5432).

Для изменения порта отредактируйте `docker-compose.yml`:

```yaml
services:
  postgres:
    ports:
      - "5433:5432"  # Измените 5433 на нужный порт
```

### Пути к файлам

**Важно:** При работе через Docker используйте пути внутри контейнера:

- `/output/` - для сохранения результатов (соответствует `core-service/output/` на хосте)
- `/app/` - корень проекта (read-only, для доступа к модулям)

**Примеры правильных путей:**
```bash
# ✅ Правильно
--output /output/.gitlab-ci.yml
--stack-output /output/stack.json
--file /output/.gitlab-ci.yml

# ❌ Неправильно
--output .gitlab-ci.yml  # Файл не будет доступен на хосте
--output ./output/.gitlab-ci.yml  # Относительные пути не работают
```

---

## Troubleshooting

### Проблемы с подключением к БД

**Симптомы:** Ошибки подключения к базе данных

**Решение:**
1. Убедитесь, что PostgreSQL запущен:
```bash
docker-compose ps
```

2. Проверьте, что PostgreSQL готов:
```bash
docker-compose logs postgres | grep "ready to accept connections"
```

3. Проверьте переменную окружения `DATABASE_URL`:
```bash
docker-compose run --rm cli env | grep DATABASE_URL
```

### Проблемы с путями к модулям

**Симптомы:** Ошибки импорта модулей (stack_recognize, ci_generator и т.д.)

**Решение:**
1. Убедитесь, что все модули находятся в корне проекта:
```bash
ls -d ../stack_recognize ../ci_generator ../auto-merge-request ../docker_compose_generator
```

2. Проверьте монтирование в контейнере:
```bash
docker-compose run --rm cli ls -la /app/
```

### Проблемы с сохранением файлов

**Симптомы:** Файлы не сохраняются в `core-service/output/`

**Решение:**
1. Убедитесь, что используете путь `/output/`:
```bash
# ✅ Правильно
--output /output/.gitlab-ci.yml

# ❌ Неправильно
--output .gitlab-ci.yml
```

2. Проверьте права доступа к директории:
```bash
ls -la core-service/output/
chmod 755 core-service/output/
```

3. Проверьте монтирование volume:
```bash
docker-compose config | grep -A 2 output
```

### Порт 5432 уже занят

**Симптомы:** Ошибка `address already in use` при запуске PostgreSQL

**Решение:**
PostgreSQL в docker-compose использует порт 5433 по умолчанию. Если нужно использовать другой порт, измените `docker-compose.yml`:

```yaml
ports:
  - "5434:5432"  # Используйте свободный порт
```

### Контейнер не запускается

**Симптомы:** Контейнер сразу останавливается

**Решение:**
1. Проверьте логи:
```bash
docker-compose logs cli
```

2. Проверьте статус:
```bash
docker-compose ps -a
```

3. Запустите в интерактивном режиме для отладки:
```bash
docker-compose run --rm cli /bin/bash
```

### Медленная работа

**Симптомы:** Команды выполняются очень долго

**Решение:**
1. Это нормально для первого запуска (клонирование репозиториев может занять время)
2. Проверьте использование ресурсов:
```bash
docker stats
```
3. Увеличьте лимиты ресурсов в `docker-compose.yml` при необходимости

---

## Дополнительная информация

### Просмотр логов

```bash
# Все логи
docker-compose logs

# Логи конкретного сервиса
docker-compose logs postgres
docker-compose logs cli

# Последние 100 строк
docker-compose logs --tail=100

# Логи в реальном времени
docker-compose logs -f
```

### Очистка

```bash
# Остановить и удалить контейнеры
docker-compose down

# Удалить контейнеры и volumes (удалит данные БД!)
docker-compose down -v

# Удалить образы
docker-compose down --rmi all

# Полная очистка (контейнеры, volumes, образы, сети)
docker-compose down -v --rmi all
```

### Интерактивный режим

Для отладки можно запустить контейнер в интерактивном режиме:

```bash
# Запустить bash в контейнере
docker-compose run --rm cli /bin/bash

# Внутри контейнера можно выполнять команды
python3 cli.py --help
python3 cli.py list-projects
```

### Использование переменных окружения

Вы можете передавать переменные окружения в контейнер:

```bash
docker-compose run --rm -e GITLAB_TOKEN=your-token cli \
  auto-merge-request \
  --url "https://gitlab.com/user/repo" \
  --token "$GITLAB_TOKEN" \
  --file /output/.gitlab-ci.yml
```

---

## Получение справки

Для получения справки по любой команде используйте флаг `--help`:

```bash
docker-compose run --rm cli --help
docker-compose run --rm cli generate-from-repo --help
docker-compose run --rm cli add-project --help
```

