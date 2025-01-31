#!/bin/bash

# Получаем количество CPU ядер
CORES=$(nproc)
WORKERS=$(( 2 * CORES + 1 ))

# Запускаем Gunicorn с оптимизированными настройками
gunicorn main:app \
    --bind 0.0.0.0:8080 \
    --workers $WORKERS \
    --worker-class uvicorn.workers.UvicornWorker \
    --timeout 45 \
    --keep-alive 10 \
    --backlog 2048 \
    --worker-connections 2000 \
    --max-requests 20000 \
    --max-requests-jitter 1000 \
    --graceful-timeout 30 \
    --log-level info \
    --worker-tmp-dir /dev/shm \
    --preload