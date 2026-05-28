FROM python:3.11-slim

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код
COPY . .

# Команда для запуска твоего бота
CMD ["python", "main.py"]