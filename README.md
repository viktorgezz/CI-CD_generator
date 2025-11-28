# Self-Deploy

CLI приложение для автоматического анализа технологического стека репозиториев и генерации CI/CD пайплайнов для GitLab. 

Разработано для хакатона [Т1. Москва](https://impulse.t1.ru/event/mIadtUgt)

Команда: **Back2Back**

**Участики:**

Лулаков Даниил - Dev-ops, Team-Lead

Гезенцвей Виктор - Project Manager, Architect, Designer

Колесникова Лариса - Dev-ops, QA

Беляев Валерий - Buisnes Analiticts

Сорокина Полина - AI

## Структура проекта

```
T1/
├── core-service/              # Основное CLI приложение
├── stack_recognize/           # Модуль анализа технологического стека
├── ci_generator/              # Модуль генерации CI/CD пайплайнов
├── docker_compose_generator/  # Генератор docker-compose файлов
├── auto-merge-request/        # Модуль автоматического создания Merge Request
├── infra/                     # Инфраструктура для разработки (GitLab + Runner)
├── generated-pipelines/       # Примеры сгенерированных пайплайнов
├── CLI.md                     # Документация по использованию CLI
├── DOCKER.md                  # Документация по использованию через Docker
└── SUPPORTED_TECHNOLOGIES.md  # Документация по поддерживаемым технологиям
```

## Документация

- **[CLI.md](CLI.md)** - Полная документация по использованию CLI команд
- **[DOCKER.md](DOCKER.md)** - Документация по использованию через Docker Compose
- **[SUPPORTED_TECHNOLOGIES.md](SUPPORTED_TECHNOLOGIES.md)** - Документация по поддерживаемым языкам, фреймворкам и технологиям
- **[infra/README.md](infra/README.md)** - Инструкция по запуску локальной инфраструктуры GitLab
- **[https://disk.yandex.ru/i/PNgmMDO8eeh4Hg](TEST_REPORT.pdf)** - Отчет о тестировании пайплайнов

## Модули проекта

### core-service

Основное CLI приложение, предоставляющее интерфейс для работы со всеми модулями системы.

**Основные возможности:**
- Анализ репозиториев и определение технологического стека
- Генерация CI/CD пайплайнов для GitLab
- Управление проектами в базе данных
- Автоматическое создание Merge Request в GitLab
- Генерация docker-compose файлов

**Технологии:**
- Python 3.11
- Click (CLI интерфейс)
- SQLAlchemy (работа с БД)
- PostgreSQL

**Запуск:**
- Локально: `python3 cli.py [command]`
- Через Docker: см. [DOCKER.md](DOCKER.md)

---

### stack_recognize

Модуль для автоматического анализа технологического стека репозиториев.

**Функциональность:**
- Определение языков программирования (Python, Java, Go, TypeScript, JavaScript и др.)
- Обнаружение фреймворков (Django, Flask, Spring, React и др.)
- Определение менеджеров пакетов (pip, npm, maven, gradle и др.)
- Обнаружение тестовых раннеров (pytest, jest, junit и др.)
- Анализ DevOps инструментов (Docker, Kubernetes, Terraform)
- Определение баз данных (PostgreSQL, MySQL, MongoDB и др.)
- Обнаружение облачных платформ (AWS, GCP, Azure)

**Компоненты:**
- `analyzers/` - набор анализаторов для различных аспектов стека
- `detector.py` - основной детектор, координирующий работу анализаторов
- `models.py` - модели данных для представления стека

---

### ci_generator

Модуль генерации CI/CD пайплайнов на основе анализа технологического стека.

**Функциональность:**
- Генерация GitLab CI пайплайнов
- Поддержка различных языков программирования
- Настраиваемые стадии пайплайна
- Настройка триггеров (push, merge request, tags, schedule, manual)
- Плагинная архитектура для расширения функциональности

**Компоненты:**
- `generator/` - основная логика генерации
  - `stage_selector.py` - выбор стадий на основе анализа
  - `renderer.py` - рендеринг пайплайнов из шаблонов
- `pipelines/gitlab/` - шаблоны GitLab CI пайплайнов
  - `stages/` - шаблоны стадий для разных языков и технологий
- `plugins/` - плагины для языков и технологий
  - `languages/` - плагины для Python, Java, Go, TypeScript
  - `technologies/` - плагины для Docker, Kubernetes
  - `tests/` - плагины для тестирования

**Поддерживаемые стадии:**
- `pre_checks` - предварительные проверки
- `lint` - линтинг кода
- `type_check` - проверка типов
- `security` - проверка безопасности
- `test` - запуск тестов
- `build` - сборка проекта
- `docker_build` - сборка Docker образа
- `docker_push` - отправка образа в registry
- `integration` - интеграционные тесты
- `migration` - миграции БД
- `deploy` - развертывание
- `post_deploy` - пост-развертывание
- `cleanup` - очистка

---

### docker_compose_generator

Модуль генерации docker-compose файлов на основе анализа стека проекта.

**Функциональность:**
- Автоматическое определение необходимых сервисов
- Генерация конфигурации для баз данных (PostgreSQL, MySQL, MongoDB, Redis)
- Настройка сетей и volumes
- Поддержка различных конфигураций окружений

**Компоненты:**
- `generator/compose_generator.py` - основная логика генерации
- `templates/` - Jinja2 шаблоны для docker-compose
  - `base_compose.j2` - базовый шаблон
  - `services/` - шаблоны для различных сервисов

---

### auto-merge-request

Модуль автоматического создания Merge Request в GitLab репозиторий.

**Функциональность:**
- Автоматическое создание форка репозитория
- Создание ветки с изменениями
- Добавление/обновление файлов в форке
- Создание Merge Request из форка в оригинальный репозиторий

**Компоненты:**
- `GitLabRepoService.py` - сервис для работы с GitLab API
- `RunnerGitLab.py` - обертка для запуска процесса

**Использование:**
Через CLI команду `auto-merge-request` (см. [CLI.md](CLI.md))

---

### infra

Локальная инфраструктура для разработки и тестирования.

**Компоненты:**
- GitLab CE - локальный экземпляр GitLab
- GitLab Runner - runner для выполнения CI/CD пайплайнов

**Использование:**
См. [infra/README.md](infra/README.md)

---

### generated-pipelines

Директория с примерами сгенерированных пайплайнов для различных проектов.

**Структура:**
- `java/` - примеры для Java проектов (Keycloak, Kafka, Elasticsearch и др.)
- `go/` - примеры для Go проектов (Gitea, Minio, Vault и др.)
- `python/` - примеры для Python проектов (Home Assistant, Mastodon, Odoo и др.)
- `typescript/` - примеры для TypeScript проектов (Ghost, Strapi, n8n и др.)

Каждый проект содержит:
- `.gitlab-ci.yml` - сгенерированный пайплайн
- `README-*.md` - описание технологического стека проекта

---

## Быстрый старт

### Через Docker (рекомендуется)

```bash
cd core-service
docker-compose up -d
docker-compose run --rm cli init
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml
```

Подробнее: [DOCKER.md](DOCKER.md)

### Локально

```bash
cd core-service
pip install -r requirements.txt
python3 cli.py init
python3 cli.py generate-from-repo \
  --url "https://github.com/user/repo" \
  --output .gitlab-ci.yml
```

Подробнее: [CLI.md](CLI.md)

---

## Основные команды

### Анализ репозитория

```bash
docker-compose run --rm cli analyze-repo \
  --url "https://github.com/user/repo" \
  --output /output/stack.json
```

### Генерация пайплайна

```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/repo" \
  --output /output/.gitlab-ci.yml \
  --stages "lint,test,build" \
  --on-push "main" \
  --on-merge-request
```

### Автоматическое создание Merge Request

```bash
docker-compose run --rm cli auto-merge-request \
  --url "https://gitlab.com/user/repo" \
  --token "your-token" \
  --file /output/.gitlab-ci.yml \
  --branch main
```

Полный список команд: [CLI.md](CLI.md)

---

## Требования

- Python 3.8+ (для локального запуска)
- Docker 20.10+ и Docker Compose 2.0+ (для запуска через Docker)
- PostgreSQL (для работы с базой данных проектов)

---

## Лицензия

[Укажите лицензию проекта]
