FROM python:3.11-slim

# Системные зависимости (asyncpg)
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/*

# Непривилегированный пользователь
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

WORKDIR /app

# Зависимости отдельным слоем (кэширование Docker layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Код приложения
COPY --chown=appuser:appuser . .

# Отдаем права на саму директорию /app нашему юзеру
RUN chown appuser:appuser /app

USER appuser

CMD ["python", "main.py"]