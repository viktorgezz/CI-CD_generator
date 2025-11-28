FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Копирование requirements.txt из core-service
COPY core-service/requirements.txt /app/core-service/requirements.txt

# Установка зависимостей Python
RUN pip install --no-cache-dir -r /app/core-service/requirements.txt

# Копирование core-service
COPY core-service /app/core-service

# Рабочая директория - core-service
WORKDIR /app/core-service

# Точка входа
ENTRYPOINT ["python3", "cli.py"]

