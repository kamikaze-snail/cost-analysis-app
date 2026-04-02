FROM python:3.11-slim

WORKDIR /app

# Устанавливаем версию приложения (будет подставлена при сборке)
ARG VERSION=unknown
ENV APP_VERSION=$VERSION

# Копируем зависимости
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY app/ ./app/

# Создаем непривилегированного пользователя
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

# Запускаем приложение напрямую (простой и надежный способ)
CMD ["python", "-m", "app.app"]