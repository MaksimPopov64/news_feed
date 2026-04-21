#!/bin/bash
set -e

MODEL="${OLLAMA_MODEL:-qwen2.5:14b}"
OLLAMA_URL="http://localhost:11434"

echo "=== Qwen через Ollama ==="
echo "Модель: $MODEL"
echo ""

# ── 1. Установка Ollama ──────────────────────────────────────────────────────
if ! command -v ollama &>/dev/null; then
  echo "[1/3] Ollama не найден — устанавливаю..."
  if [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &>/dev/null; then
      brew install --cask ollama
    else
      echo "  Homebrew не найден. Скачиваю установщик..."
      curl -fsSL https://ollama.com/install.sh | sh
    fi
  elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    curl -fsSL https://ollama.com/install.sh | sh
  else
    echo "  Неподдерживаемая ОС. Установите Ollama вручную: https://ollama.com/"
    exit 1
  fi
  echo "  ✓ Ollama установлен"
else
  echo "[1/3] Ollama уже установлен ($(ollama --version 2>/dev/null || echo 'версия неизвестна'))"
fi

# ── 2. Запуск Ollama-сервера ─────────────────────────────────────────────────
echo ""
echo "[2/3] Проверяю сервер Ollama..."

if curl -sf "$OLLAMA_URL/api/tags" &>/dev/null; then
  echo "  ✓ Сервер уже запущен на $OLLAMA_URL"
else
  echo "  Запускаю сервер в фоне..."
  ollama serve &>/tmp/ollama.log &
  OLLAMA_PID=$!
  echo "  PID: $OLLAMA_PID  (лог: /tmp/ollama.log)"

  echo -n "  Жду готовности"
  for i in $(seq 1 30); do
    if curl -sf "$OLLAMA_URL/api/tags" &>/dev/null; then
      echo " ✓"
      break
    fi
    echo -n "."
    sleep 1
    if [ "$i" -eq 30 ]; then
      echo ""
      echo "  ✗ Сервер не запустился за 30 секунд. Лог: /tmp/ollama.log"
      exit 1
    fi
  done
fi

# ── 3. Скачивание модели ─────────────────────────────────────────────────────
echo ""
echo "[3/3] Проверяю модель $MODEL..."

if ollama list 2>/dev/null | grep -q "^${MODEL}"; then
  echo "  ✓ Модель уже скачана"
else
  echo "  Скачиваю $MODEL (первый раз ~9 ГБ, может занять несколько минут)..."
  ollama pull "$MODEL"
  echo "  ✓ Модель скачана"
fi

# ── Готово ───────────────────────────────────────────────────────────────────
echo ""
echo "=== Всё готово ==="
echo ""
echo "  Модель:  $MODEL"
echo "  Сервер:  $OLLAMA_URL"
echo ""
echo "  Быстрый тест:"
echo "    ollama run $MODEL \"Привет!\""
echo ""
echo "  Запуск приложения:"
echo "    python app.py"
