FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВСЕ содержимое текущей директории (включая main.py, templates/, static/ и т.д.) 
# в рабочую директорию /app внутри контейнера.
# Это делается ПОСЛЕ установки зависимостей, чтобы использовать кэширование слоев Docker.
COPY . .

# Открыть порт, на котором будет работать Uvicorn
EXPOSE 8000

# Основная команда запуска (дополненная для продакшена)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]