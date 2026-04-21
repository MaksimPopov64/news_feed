#!/bin/bash
set -e

echo "=== NewsTriangulator: первоначальная настройка ==="

# 1. Python-зависимости
echo ""
echo "[1/4] Устанавливаю Python-пакеты..."
pip install -r requirements.txt

# 2. Русская spaCy-модель
echo ""
echo "[2/4] Скачиваю spaCy ru_core_news_lg..."
python -m spacy download ru_core_news_lg

# 3. .env файл
echo ""
echo "[3/4] Создаю .env из примера..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  → .env создан. Добавьте API-ключи при необходимости."
else
  echo "  → .env уже существует, пропускаю."
fi

# 4. Ollama и модель
echo ""
echo "[4/4] Проверяю Ollama..."
if ! command -v ollama &> /dev/null; then
  echo "  Ollama не установлен. Установите с https://ollama.com/"
  echo "  Затем выполните: ollama pull qwen2.5:14b"
else
  echo "  Ollama найден. Скачиваю qwen2.5:14b (~9GB, один раз)..."
  ollama pull qwen2.5:14b
  echo "  ✓ Модель готова"
fi

echo ""
echo "=== Установка завершена ==="
echo ""
echo "Запуск веб-интерфейса:  python app.py"
echo "Запуск CLI:             python main.py \"ваш запрос\""
echo "Открыть браузер:        http://localhost:8000"
