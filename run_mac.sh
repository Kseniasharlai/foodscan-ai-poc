#!/bin/bash
set -e

echo "=== FoodScan AI: Налаштування та запуск на macOS ==="

if [ ! -d ".venv" ]; then
    echo "-> Створення віртуального середовища (.venv)..."
    python3 -m venv .venv
fi

source .venv/bin/activate
echo "-> Встановлення залежностей..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "-> Створено файл .env з шаблону .env.example (додайте свій GEMINI_API_KEY за бажанням)."
fi

echo "-> Запуск сервера FastAPI на http://127.0.0.1:8000 ..."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
