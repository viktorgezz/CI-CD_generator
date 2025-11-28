# Поддерживаемые технологии

Документация по всем языкам программирования, фреймворкам, инструментам и технологиям, которые поддерживает система анализа и генерации CI/CD пайплайнов.

---

## Языки программирования

Система поддерживает анализ и генерацию пайплайнов для следующих языков:

### Python
- **Расширения файлов:** `.py`, `.pyw`, `.pyx`, `.pxd`, `.pyi`
- **Менеджеры пакетов:** pip, poetry, setuptools
- **Фреймворки:** Django, Flask, FastAPI
- **Тестовые раннеры:** pytest, unittest
- **Стадии CI/CD:** lint, type_check, security, build, migration

### TypeScript / JavaScript
- **Расширения файлов:** `.ts`, `.tsx`, `.js`, `.jsx`
- **Менеджеры пакетов:** npm, yarn, pnpm
- **Фреймворки:**
  - Backend: Express, NestJS
  - Frontend: React, Vue, Angular, Next.js
- **Тестовые раннеры:** jest, mocha, jasmine, karma, cypress, playwright, vitest
- **Стадии CI/CD:** lint, type_check, security, build, migration

### Java / Kotlin
- **Расширения файлов:** `.java`, `.kt`, `.kts`, `.jar`, `.war`, `.class`
- **Менеджеры пакетов:** Maven, Gradle, Ant
- **Фреймворки:** Spring, Spring Boot, Quarkus, Micronaut, Vert.x
- **Тестовые раннеры:** JUnit, TestNG
- **Стадии CI/CD:** lint, type_check, security, build, migration

### Go
- **Расширения файлов:** `.go`
- **Менеджеры пакетов:** go mod
- **Фреймворки:** Gin, Echo, Fiber, Beego
- **Тестовые раннеры:** go-testing (встроенный)
- **Стадии CI/CD:** lint, type_check, security, build, migration

---

## Менеджеры пакетов

### Python
- **pip** - определяется по файлу `requirements.txt`
- **poetry** - определяется по файлу `pyproject.toml` (секция `tool.poetry`)
- **setuptools** - определяется по файлу `setup.py`

### TypeScript / JavaScript
- **npm** - определяется по файлу `package.json` и `package-lock.json`
- **yarn** - определяется по файлу `yarn.lock`
- **pnpm** - определяется по файлу `pnpm-lock.yaml`

### Java / Kotlin
- **Maven** - определяется по файлу `pom.xml`
- **Gradle** - определяется по файлам `build.gradle` или `build.gradle.kts`
- **Ant** - определяется по файлу `build.xml`

### Go
- **go mod** - определяется по файлу `go.mod`

### Другие (обнаруживаются, но не используются в генерации пайплайнов)
- **Cargo** (Rust) - `Cargo.toml`
- **Bundler** (Ruby) - `Gemfile`
- **Composer** (PHP) - `composer.json`
- **Mix** (Elixir) - `mix.exs`
- **Pub** (Dart) - `pubspec.yaml`
- **CocoaPods** (iOS) - `Podfile`
- **Carthage** (iOS) - `Cartfile`
- **Swift Package Manager** - `Package.swift`

---

## Фреймворки

### Python

#### Django
- **Определение:** наличие файла `manage.py` или импорты `from django`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

#### Flask
- **Определение:** наличие файлов `app.py` или `application.py`, или импорты `from flask import`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

#### FastAPI
- **Определение:** импорты `from fastapi` или `FastAPI()`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

### Java / Kotlin

#### Spring Boot
- **Определение:** аннотации `@SpringBootApplication` или зависимости `org.springframework.boot`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД, имеет приоритет над Spring

#### Spring
- **Определение:** зависимости `org.springframework` (без Spring Boot)
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

#### Quarkus
- **Определение:** зависимости `io.quarkus` или аннотации `@QuarkusTest`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД, не используется вместе с Spring Boot

#### Micronaut
- **Определение:** наличие файла `micronaut-cli.yml` или зависимости `io.micronaut`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

#### Vert.x
- **Определение:** зависимости `io.vertx`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

### TypeScript / JavaScript

#### Backend фреймворки

**Express**
- **Определение:** зависимости `express` в `package.json` или импорты `require('express')`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

**NestJS**
- **Определение:** наличие файла `nest-cli.json` или зависимости `@nestjs/core`
- **Тип:** Backend
- **Особенности:** Поддерживаются миграции БД

#### Frontend фреймворки

**React**
- **Определение:** зависимости `react` в `package.json`
- **Тип:** Frontend

**Vue**
- **Определение:** зависимости `vue` в `package.json` или использование `createApp`
- **Тип:** Frontend

**Angular**
- **Определение:** зависимости `@angular/core` в `package.json`
- **Тип:** Frontend

**Next.js**
- **Определение:** наличие файла `next.config.js` или зависимости `next`
- **Тип:** Frontend/Backend (Full-stack)
- **Особенности:** Поддерживаются миграции БД

### Go

#### Gin
- **Определение:** зависимости `github.com/gin-gonic/gin` или использование `gin.`
- **Тип:** Backend

#### Echo
- **Определение:** зависимости `github.com/labstack/echo` или использование `echo.`
- **Тип:** Backend

#### Fiber
- **Определение:** зависимости `github.com/gofiber/fiber` или использование `fiber.`
- **Тип:** Backend

#### Beego
- **Определение:** зависимости `github.com/astaxie/beego` или использование `beego.`
- **Тип:** Backend

---

## Базы данных

### Реляционные БД

#### PostgreSQL
- **Определение:** 
  - Python: импорты `psycopg2`
  - TypeScript: зависимости `pg` или `pg.connect`
  - Go: драйверы `xorm` или `database/sql` с PostgreSQL
- **Поддержка:** Полная поддержка в docker-compose генераторе

#### MySQL
- **Определение:**
  - Python: импорты `pymysql` или `mysqldb`
  - TypeScript: зависимости `mysql` или `mysql.createConnection`
  - Go: драйверы `github.com/go-sql-driver/mysql` или `xorm` с MySQL
- **Поддержка:** Полная поддержка в docker-compose генераторе

#### SQLite
- **Определение:**
  - Python: импорты `sqlite3`
  - Go: драйверы `github.com/mattn/go-sqlite3` или файлы `.db`, `.sqlite`
- **Поддержка:** Обнаруживается, но не генерируется в docker-compose

#### Oracle
- **Определение:** Python: импорты `cx_Oracle`
- **Поддержка:** Обнаруживается, но не генерируется в docker-compose

#### SQL Server
- **Определение:**
  - Python: импорты `pymssql`
  - Go: драйверы `github.com/microsoft/go-mssqldb` или `xorm` с MSSQL
- **Поддержка:** Обнаруживается, но не генерируется в docker-compose

### NoSQL БД

#### MongoDB
- **Определение:**
  - Python: импорты `pymongo`
  - TypeScript: зависимости `mongodb` или `mongoose`
- **Поддержка:** Полная поддержка в docker-compose генераторе

#### Redis
- **Определение:**
  - Python: импорты `redis`
  - TypeScript: зависимости `redis` или `redis.createClient`
  - Go: драйверы `github.com/go-redis/redis` или `redis.NewClient`
- **Поддержка:** Полная поддержка в docker-compose генераторе

#### Cassandra
- **Определение:** Python: импорты `cassandra` или `cassandra.cluster`
- **Поддержка:** Обнаруживается, но не генерируется в docker-compose

#### Elasticsearch
- **Определение:** Python: импорты `elasticsearch` или TypeScript зависимости `@elastic/elasticsearch`
- **Поддержка:** Обнаруживается, но не генерируется в docker-compose

---

## Тестовые раннеры

### Python

#### pytest
- **Определение:** наличие файлов `pytest.ini`, `tox.ini`, `conftest.py` или импорты `import pytest`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### unittest
- **Определение:** импорты `import unittest`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

### TypeScript / JavaScript

#### Jest
- **Определение:** наличие файлов `jest.config.js/ts/json` или импорты `jest`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### Mocha
- **Определение:** наличие файлов `.mocharc.js/json/yaml` или импорты `mocha`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### Jasmine
- **Определение:** наличие файла `jasmine.json` или импорты `jasmine`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### Karma
- **Определение:** наличие файлов `karma.conf.js/ts` или импорты `karma`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### Cypress
- **Определение:** наличие файлов `cypress.json`, `cypress.config.js` или использование `cy.visit`, `cy.get`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### Playwright
- **Определение:** наличие файлов `playwright.config.js/ts` или импорты `@playwright/test`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### Vitest
- **Определение:** наличие файлов `vitest.config.js/ts/mjs` или импорты `vitest`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

### Java / Kotlin

#### JUnit
- **Определение:** аннотации `@Test` или зависимости `org.junit`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

#### TestNG
- **Определение:** зависимости `org.testng`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

### Go

#### go-testing
- **Определение:** импорты `import "testing"` или функции `func Test`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах

---

## Инструменты сборки

### Frontend сборщики

#### Webpack
- **Определение:** наличие файлов `webpack.config.js/ts`
- **Поддержка:** Обнаруживается

#### Vite
- **Определение:** наличие файлов `vite.config.js/ts`
- **Поддержка:** Обнаруживается

#### Rollup
- **Определение:** наличие файла `rollup.config.js`
- **Поддержка:** Обнаруживается

#### Parcel
- **Определение:** наличие файлов `.parcelrc` или `parcel.json`
- **Поддержка:** Обнаруживается

#### Gulp
- **Определение:** наличие файлов `gulpfile.js/ts`
- **Поддержка:** Обнаруживается

#### Grunt
- **Определение:** наличие файла `Gruntfile.js`
- **Поддержка:** Обнаруживается

### Транспайлеры и компиляторы

#### Babel
- **Определение:** наличие файлов `.babelrc`, `babel.config.js/json`
- **Поддержка:** Обнаруживается

#### esbuild
- **Определение:** наличие файлов `esbuild.js` или `esbuild.config.js`
- **Поддержка:** Обнаруживается

#### SWC
- **Определение:** наличие файлов `.swcrc` или `swc.config.js`
- **Поддержка:** Обнаруживается

### Системы сборки

#### Make
- **Определение:** наличие файла `Makefile`
- **Поддержка:** Обнаруживается

#### CMake
- **Определение:** наличие файла `CMakeLists.txt`
- **Поддержка:** Обнаруживается

#### Gradle
- **Определение:** наличие файлов `build.gradle` или `build.gradle.kts`
- **Поддержка:** Обнаруживается и используется в CI/CD пайплайнах

#### Maven
- **Определение:** наличие файла `pom.xml`
- **Поддержка:** Обнаруживается и используется в CI/CD пайплайнах

#### Ant
- **Определение:** наличие файла `build.xml`
- **Поддержка:** Обнаруживается и используется в CI/CD пайплайнах

---

## DevOps инструменты

### Контейнеризация

#### Docker
- **Определение:** наличие файлов `Dockerfile`, `Dockerfile.*` или `*.dockerfile`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах (стадии `docker_build`, `docker_push`)
- **Особенности:** 
  - Поддерживается категоризация Dockerfile для монорепозиториев (frontend/backend)
  - Автоматический выбор основного Dockerfile по приоритету

#### Docker Compose
- **Определение:** наличие файлов `docker-compose.yml/yaml`
- **Поддержка:** 
  - Обнаруживается в анализе
  - Генерируется автоматически на основе обнаруженных БД и сервисов

### Оркестрация

#### Kubernetes
- **Определение:** наличие файлов в директориях `k8s/`, `manifests/`, `kubernetes/` или файлов `*.k8s.yaml/yml`
- **Поддержка:** Полная поддержка в CI/CD пайплайнах (стадии `deploy`, `post_deploy`)

#### Helm
- **Определение:** наличие файла `Chart.yaml`
- **Поддержка:** Обнаруживается, указывает на использование Kubernetes

### Infrastructure as Code

#### Terraform
- **Определение:** наличие файлов `*.tf`, `.terraform.lock.hcl`, `*.tfvars`, `terraform.tfstate`
- **Поддержка:** Обнаруживается

#### Ansible
- **Определение:** наличие файлов `ansible.cfg`, `inventory`, `playbook.yml`
- **Поддержка:** Обнаруживается

#### Pulumi
- **Определение:** наличие файла `Pulumi.yaml`
- **Поддержка:** Обнаруживается

#### Vagrant
- **Определение:** наличие файла `Vagrantfile`
- **Поддержка:** Обнаруживается

---

## Облачные платформы

### AWS
- **Определение:** наличие директории `.aws/`, файлов `aws.yml/yaml` или использование `boto3`, `aws-sdk`
- **Поддержка:** Обнаруживается

### Azure
- **Определение:** наличие директории `.azure/`, файла `azure-pipelines.yml` или использование `azure-sdk`
- **Поддержка:** Обнаруживается

### Google Cloud Platform (GCP)
- **Определение:** наличие директории `.gcp/`, файлов `gcp.yaml`, `app.yaml` или использование `google.cloud`
- **Поддержка:** Обнаруживается

### DigitalOcean
- **Определение:** использование `digitalocean` или `do-spaces`
- **Поддержка:** Обнаруживается

### Heroku
- **Определение:** наличие файла `Procfile` или `app.json`
- **Поддержка:** Обнаруживается

---

## Стадии CI/CD пайплайнов

Система генерирует следующие стадии для GitLab CI:

### Общие стадии

#### pre_checks
- **Описание:** Предварительные проверки перед началом пайплайна
- **Когда используется:** Всегда, если включена

#### test
- **Описание:** Запуск тестов с использованием обнаруженных тестовых раннеров
- **Когда используется:** Всегда, если обнаружены тесты

#### integration
- **Описание:** Интеграционные тесты
- **Когда используется:** Если включена пользователем

### Стадии для языков программирования

#### lint
- **Описание:** Проверка кода линтерами
- **Поддержка:** Python (ruff, pylint), TypeScript (ESLint), Java (Checkstyle), Go (golangci-lint)

#### type_check
- **Описание:** Проверка типов
- **Поддержка:** Python (mypy), TypeScript (tsc), Java (компилятор), Go (компилятор)

#### security
- **Описание:** Проверка безопасности зависимостей
- **Поддержка:** Python (safety), TypeScript (npm audit), Java (OWASP Dependency-Check), Go (gosec)

#### build
- **Описание:** Сборка проекта
- **Поддержка:** 
  - Python: создание пакетов (wheel, sdist)
  - TypeScript: компиляция TypeScript, сборка фронтенда
  - Java: сборка JAR/WAR файлов
  - Go: компиляция бинарников
- **Особенности:** Не добавляется, если есть Docker (кроме Go)

#### migration
- **Описание:** Запуск миграций базы данных
- **Поддержка:** 
  - Python: Django, Flask, FastAPI миграции
  - TypeScript: Express, NestJS, Next.js миграции
  - Java: Spring Boot, Quarkus, Micronaut миграции
  - Go: миграции при наличии БД
- **Когда используется:** Только если обнаружен поддерживаемый фреймворк и БД

### Стадии для Docker

#### docker_build
- **Описание:** Сборка Docker образа
- **Когда используется:** Если обнаружен Dockerfile

#### docker_push
- **Описание:** Отправка Docker образа в registry
- **Когда используется:** Если включена стадия `docker_build`

#### cleanup
- **Описание:** Очистка Docker образов и артефактов
- **Когда используется:** После `docker_push`

### Стадии для развертывания

#### deploy
- **Описание:** Развертывание приложения
- **Поддержка:** 
  - Kubernetes: развертывание через kubectl или Helm
  - Общие: развертывание через SSH, API и т.д.
- **Когда используется:** Если обнаружен Kubernetes или включена пользователем

#### post_deploy
- **Описание:** Пост-развертывание (проверки здоровья, smoke-тесты)
- **Когда используется:** После `deploy`, если включена

---

## Особенности анализа

### Монорепозитории

Система автоматически определяет структуру монорепозиториев:

- **Frontend директории:** `frontend`, `web`, `client`, `ui`, `app`
- **Backend директории:** `backend`, `server`, `api`, `services`
- **Apps директории:** `apps`, `applications`

Для монорепозиториев:
- Dockerfile категоризируются по назначению (frontend/backend/root)
- Тесты анализируются отдельно для каждой части
- Генерируются соответствующие стадии для каждой части

### Приоритеты менеджеров пакетов

При обнаружении нескольких менеджеров пакетов используется следующий приоритет:

1. `go.mod` (высший приоритет)
2. `build.gradle` / `build.gradle.kts`
3. `pom.xml`
4. `build.xml` (Ant)
5. `Gemfile` (Ruby)
6. `composer.json` (PHP)
7. `pyproject.toml` (Poetry) - только если нет более приоритетных
8. `requirements.txt` (pip)
9. `package.json` (npm/yarn/pnpm)

### Ограничения

- **Поддерживаются только 4 языка:** Python, TypeScript/JavaScript, Java/Kotlin, Go
- **JavaScript файлы** (`.js`, `.jsx`) определяются как TypeScript для унификации
- **Kotlin файлы** (`.kt`, `.kts`) определяются как Java для унификации
- **PHP, Ruby, Rust и другие языки** обнаруживаются, но не используются в генерации пайплайнов

---

## Примеры использования

### Python проект с Django и PostgreSQL

```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/django-project" \
  --output /output/.gitlab-ci.yml
```

**Обнаружится:**
- Язык: Python
- Менеджер пакетов: pip/poetry
- Фреймворк: Django
- БД: PostgreSQL
- Тесты: pytest

**Сгенерируются стадии:**
- lint, type_check, security, test, migration, docker_build, docker_push

### Java проект с Spring Boot и MySQL

```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/spring-project" \
  --output /output/.gitlab-ci.yml
```

**Обнаружится:**
- Язык: Java
- Менеджер пакетов: Maven/Gradle
- Фреймворк: Spring Boot
- БД: MySQL
- Тесты: JUnit

**Сгенерируются стадии:**
- lint, type_check, security, build, test, migration, docker_build, docker_push

### TypeScript проект с React и Express

```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/fullstack-project" \
  --output /output/.gitlab-ci.yml
```

**Обнаружится:**
- Язык: TypeScript
- Менеджер пакетов: npm/yarn/pnpm
- Фреймворки: React (frontend), Express (backend)
- Тесты: Jest

**Сгенерируются стадии:**
- lint, type_check, security, build, test, docker_build, docker_push

### Go проект с Gin и Redis

```bash
docker-compose run --rm cli generate-from-repo \
  --url "https://github.com/user/go-project" \
  --output /output/.gitlab-ci.yml
```

**Обнаружится:**
- Язык: Go
- Менеджер пакетов: go mod
- Фреймворк: Gin
- БД: Redis
- Тесты: go-testing

**Сгенерируются стадии:**
- lint, type_check, security, build, test, migration, docker_build, docker_push

---

## Дополнительная информация

- Подробная документация по использованию CLI: [CLI.md](CLI.md)
- Документация по использованию через Docker: [DOCKER.md](DOCKER.md)
- Инструкция по запуску инфраструктуры: [infra/README.md](infra/README.md)

