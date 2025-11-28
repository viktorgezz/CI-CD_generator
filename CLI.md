# CLI Документация

Документация по использованию командной строки для управления проектами и генерации CI/CD пайплайнов.

## Содержание

- [Установка и настройка](#установка-и-настройка)
- [Основные команды](#основные-команды)
  - [generate-from-repo](#generate-from-repo) ⭐
  - [analyze-repo](#analyze-repo)
  - [auto-merge-request](#auto-merge-request)
  - [init](#init)
  - [add-project](#add-project)
  - [list-projects](#list-projects)
  - [generate](#generate)
  - [list-pipelines](#list-pipelines)
- [Примеры использования](#примеры-использования)
- [Настройка стадий пайплайна](#настройка-стадий-пайплайна)
- [Настройка триггеров](#настройка-триггеров)

## Установка и настройка

### Требования

- Python 3.8+
- База данных SQLite (создается автоматически)

### Первоначальная настройка

1. Перейдите в директорию `core-service`:
```bash
cd core-service
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Выполните любую из команд:
```bash
python3 cli.py [command]
```

## Основные команды

### generate-from-repo

Генерирует CI/CD пайплайн и Markdown файл с описанием стека проекта напрямую из репозитория без сохранения проекта в базу данных. Это самая гибкая команда с множеством опций настройки.

**Использование:**
```bash
python3 cli.py generate-from-repo --url "https://github.com/user/repo" [опции]
```

**Основные параметры:**
- `--url` (обязательный) - URL Git-репозитория
- `--token` (опциональный) - Токен для доступа к приватному репозиторию
- `--output` (опциональный) - Путь для сохранения пайплайна. Если не указан, пайплайн выводится в консоль
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
python3 cli.py generate-from-repo --url "https://github.com/user/repo" --output ".gitlab-ci.yml"
```

С настройкой стадий:
```bash
python3 cli.py generate-from-repo \
  --url "https://github.com/user/repo" \
  --output ".gitlab-ci.yml" \
  --stages "lint,test,build"
```

С настройкой триггеров:
```bash
python3 cli.py generate-from-repo \
  --url "https://github.com/user/repo" \
  --output ".gitlab-ci.yml" \
  --on-push "main,develop" \
  --on-merge-request \
  --manual
```

Полная настройка:
```bash
python3 cli.py generate-from-repo \
  --url "https://github.com/user/repo" \
  --output ".gitlab-ci.yml" \
  --stack-output "stack.json" \
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

---

### analyze-repo

Анализирует репозиторий и определяет его технологический стек без сохранения в базу данных.

**Использование:**
```bash
python3 cli.py analyze-repo --url "https://github.com/user/repo" [--token "token"] [--output "stack.json"]
```

**Параметры:**
- `--url` (обязательный) - URL Git-репозитория
- `--token` (опциональный) - Токен для доступа к приватному репозиторию
- `--output` (опциональный) - Путь для сохранения стека в формате JSON

**Пример:**
```bash
python3 cli.py analyze-repo --url "https://github.com/user/repo" --output "project-stack.json"
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
python3 cli.py auto-merge-request --url "https://gitlab.com/user/repo" --token "token" --file ".gitlab-ci.yml" [--branch "main"]
```

**Параметры:**
- `--url` (обязательный) - URL GitLab репозитория
- `--token` (обязательный) - GitLab токен для доступа к API
- `--file` (обязательный) - Путь к файлу для отправки в Merge Request
- `--branch` (опциональный) - Базовая ветка для создания Merge Request (по умолчанию: `main`)

**Пример:**
```bash
python3 cli.py auto-merge-request \
  --url "https://gitlab.com/user/my-project" \
  --token "glpat-xxxxxxxxxxxx" \
  --file ".gitlab-ci.yml" \
  --branch "main"
```

**Что делает:**
1. Читает указанный файл с локального диска
2. Создает форк указанного GitLab репозитория (если форк еще не существует)
3. Создает ветку `pipeline_auto_branch` в форке
4. Добавляет или обновляет файл `.gitlab-ci.yml` в форке
5. Создает Merge Request из форка в оригинальный репозиторий

**Примечания:**
- Файл будет добавлен в корень репозитория с именем `.gitlab-ci.yml`
- Если Merge Request с таким файлом уже существует, команда выведет информацию о существующем MR
- Для работы требуется GitLab токен с правами на создание форков и Merge Request

---

### init

Инициализирует базу данных для хранения проектов и истории генерации пайплайнов.

**Использование:**
```bash
python3 cli.py init
```

**Описание:**
Создает необходимые таблицы в базе данных SQLite. Эту команду нужно выполнить один раз перед первым использованием системы.

---

### add-project

Добавляет новый проект в базу данных и автоматически анализирует его технологический стек.

**Использование:**
```bash
python3 cli.py add-project --name "Название проекта" --url "https://github.com/user/repo" [--token "token"]
```

**Параметры:**
- `--name` (обязательный) - Название проекта
- `--url` (обязательный) - URL Git-репозитория
- `--token` (опциональный) - Токен для доступа к приватному репозиторию

**Пример:**
```bash
python3 cli.py add-project --name "My Project" --url "https://github.com/user/my-project"
```

**Что делает:**
1. Клонирует репозиторий (временная директория)
2. Анализирует технологический стек проекта
3. Сохраняет проект и результаты анализа в базу данных
4. Выводит краткую информацию о найденных технологиях

---

### list-projects

Показывает список всех проектов, добавленных в базу данных.

**Использование:**
```bash
python3 cli.py list-projects
```

**Вывод:**
Отображает ID, название, URL и основные характеристики каждого проекта (языки программирования).

---

### generate

Генерирует CI/CD пайплайн для проекта, сохраненного в базе данных.

**Использование:**
```bash
python3 cli.py generate --project-id <ID> [--output "pipeline.yml"] [--platform "gitlab"] [--stages "stage1,stage2"]
```

**Параметры:**
- `--project-id` (обязательный) - ID проекта из базы данных
- `--output` (опциональный) - Путь для сохранения пайплайна. Если не указан, пайплайн выводится в консоль
- `--platform` (опциональный) - Платформа CI/CD: `gitlab` или `jenkins` (по умолчанию: `gitlab`)
- `--stages` (опциональный) - Список стадий через запятую. Если не указан, используются все возможные стадии

**Пример:**
```bash
python3 cli.py generate --project-id 1 --output ".gitlab-ci.yml" --stages "lint,test,build"
```

**Примечание:**
Пайплайн также сохраняется в базу данных с ID генерации для истории.

---

### list-pipelines

Показывает историю генерации пайплайнов.

**Использование:**
```bash
python3 cli.py list-pipelines
```

**Вывод:**
Отображает ID генерации, ID проекта, дату создания и размер каждого сгенерированного пайплайна.

---

## Примеры использования

### Сценарий 1: Быстрая генерация пайплайна

Если нужно быстро сгенерировать пайплайн для репозитория без сохранения в базу данных:

```bash
cd core-service
python3 cli.py generate-from-repo \
  --url "https://github.com/user/repo" \
  --output "../.gitlab-ci.yml"
```

### Сценарий 2: Работа с проектами в базе данных

1. Добавить проект:
```bash
python3 cli.py add-project --name "My Project" --url "https://github.com/user/repo"
```

2. Посмотреть список проектов:
```bash
python3 cli.py list-projects
```

3. Сгенерировать пайплайн:
```bash
python3 cli.py generate --project-id 1 --output "../.gitlab-ci.yml"
```

### Сценарий 3: Настройка пайплайна для production

```bash
python3 cli.py generate-from-repo \
  --url "https://github.com/user/repo" \
  --output ".gitlab-ci.yml" \
  --stages "lint,security,test,build,deploy" \
  --on-push "main" \
  --on-tags "v.*" \
  --manual
```

### Сценарий 4: Анализ стека без генерации пайплайна

```bash
python3 cli.py analyze-repo \
  --url "https://github.com/user/repo" \
  --output "stack.json"
```

---

## Настройка стадий пайплайна

### Доступные стадии

Система поддерживает следующие стадии (в порядке выполнения):

- `pre_checks` - Предварительные проверки
- `lint` - Линтинг кода
- `type_check` - Проверка типов
- `security` - Проверка безопасности
- `test` - Запуск тестов
- `build` - Сборка проекта
- `docker_build` - Сборка Docker образа
- `docker_push` - Отправка Docker образа в registry
- `integration` - Интеграционные тесты
- `migration` - Миграции базы данных
- `deploy` - Развертывание
- `post_deploy` - Пост-развертывание
- `cleanup` - Очистка

### Использование

Если параметр `--stages` не указан, система автоматически выберет все подходящие стадии на основе анализа проекта.

Для выбора конкретных стадий:
```bash
--stages "lint,test,build,deploy"
```

---

## Настройка триггеров

### Триггеры по умолчанию

Если триггеры не настроены, используются следующие значения по умолчанию:

- `on_push`: `["main", "master"]` - Пайплайн запускается при push в ветки main или master
- `on_merge_request`: `false` - Пайплайн не запускается для merge request
- `on_tags`: `""` - Пайплайн не запускается для тегов
- `schedule`: `""` - Пайплайн не запускается по расписанию
- `manual`: `false` - Ручной запуск запрещен

### Примеры настройки триггеров

**Только для main ветки:**
```bash
--on-push "main"
```

**Для нескольких веток:**
```bash
--on-push "main,develop,release/*"
```

**Включить триггер на merge request:**
```bash
--on-merge-request
```

**Запуск для тегов версий:**
```bash
--on-tags "v.*"
```

**Включить ручной запуск:**
```bash
--manual
```

**Полная настройка триггеров:**
```bash
--on-push "main,develop" \
--on-merge-request \
--on-tags "v.*" \
--schedule "enabled" \
--manual
```

---

## Использование через shell-скрипты

В корне проекта доступны удобные shell-скрипты:

### generate-from-repo.sh

Упрощенный способ генерации пайплайна:

```bash
./generate-from-repo.sh --url "https://github.com/user/repo" --output ".gitlab-ci.yml"
```

Все параметры команды `generate-from-repo` поддерживаются.

---

## Примечания

1. **Временные директории**: При анализе репозитории создаются временные директории в `/tmp`, которые автоматически удаляются после анализа.

2. **Токены доступа**: Для приватных репозиториев необходимо указать токен доступа через параметр `--token`.

3. **Формат вывода**: Пайплайны генерируются в формате YAML для GitLab CI.

4. **Автоматический README**: При использовании `generate-from-repo` с параметром `--output` автоматически создается файл README с описанием технологического стека проекта.

5. **Docker Compose**: Генерация docker-compose.yml доступна только через флаг `--docker-compose` в команде `generate-from-repo`.

---

## Получение справки

Для получения справки по любой команде используйте флаг `--help`:

```bash
python3 cli.py --help
python3 cli.py generate-from-repo --help
python3 cli.py add-project --help
```

