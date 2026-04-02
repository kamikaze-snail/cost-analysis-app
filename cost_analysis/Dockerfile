FROM python:3.11-slim

WORKDIR /app

ARG VERSION=unknown
ENV APP_VERSION=$VERSION

# Копируем requirements.txt (он в папке app репозитория)
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем ВСЕ файлы из папки app репозитория в /app
COPY app/ ./

# Создаем пользователя
RUN useradd -m -s /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["python", "-m", "app"]
