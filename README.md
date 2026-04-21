# NewsTriangulator

Инструмент для анализа новостей: собирает статьи из множества источников, кластеризует их, сравнивает тональность, строит граф знаний и генерирует аналитический отчёт через LLM.

## Что делает

1. **Сбор** — параллельно опрашивает NewsAPI, GNews и RSS-ленты 8 изданий
2. **Кластеризация** — группирует статьи по семантической близости (multilingual-e5-large)
3. **NER** — извлекает именованные сущности через spaCy (`ru_core_news_lg`)
4. **Тональность** — классифицирует каждый материал (rubert-base-cased-sentiment)
5. **Граф знаний** — строит NetworkX-граф акторов и связей
6. **Cui Bono** — LLM-анализ заинтересованных сторон через Qwen
7. **Отчёт** — итоговый Markdown-доклад, сгенерированный Qwen

---

## Требования

- Python 3.10+
- [Ollama](https://ollama.com/) (локальный LLM-сервер)
- ~12 ГБ свободного места (модели HuggingFace + Qwen)

---

## Быстрый старт

### 1. Клонировать / перейти в папку проекта

```bash
cd news_feed
```

### 2. Установить зависимости и скачать модели

```bash
./setup.sh
```

Скрипт делает:
- `pip install -r requirements.txt`
- `python -m spacy download ru_core_news_lg`
- создаёт `.env` из `.env.example`
- устанавливает Ollama (если не установлен) и скачивает `qwen2.5:14b`

Или вручную по шагам:

```bash
pip install -r requirements.txt
python -m spacy download ru_core_news_lg
cp .env.example .env
./run_qwen.sh        # установка Ollama + скачивание qwen2.5:14b
```

### 3. Запустить

**Веб-интерфейс** (рекомендуется):

```bash
python app.py
# открыть http://localhost:8000
```

**CLI**:

```bash
python main.py "санкции против российского СПГ"
```

---

## Конфигурация (.env)

Скопируйте `.env.example` в `.env` и заполните нужные поля:

```env
# Опционально — без них работают только RSS-ленты
NEWSAPI_KEY=your_key_here
GNEWS_KEY=your_key_here

# Ollama (менять не нужно при локальном запуске)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b

# HuggingFace-модели (скачиваются автоматически при первом запуске)
SENTIMENT_MODEL=blanchefort/rubert-base-cased-sentiment
EMBEDDING_MODEL=intfloat/multilingual-e5-large
SPACY_MODEL=ru_core_news_lg
```

Получить API-ключи:
- **NewsAPI** — [newsapi.org](https://newsapi.org/) (бесплатный тариф: 100 запросов/сутки)
- **GNews** — [gnews.io](https://gnews.io/) (бесплатный тариф: 100 запросов/сутки)

Без ключей приложение работает через RSS-ленты:

| Источник | URL |
|---|---|
| РИА Новости | ria.ru |
| Коммерсантъ | kommersant.ru |
| Meduza | meduza.io |
| The Bell | thebell.io |
| Новая газета | novayagazeta.ru |
| Lenta.ru | lenta.ru |
| Ведомости | vedomosti.ru |
| BBC Русская служба | bbcrussian.com |

---

## Управление Qwen / Ollama

Отдельный скрипт для установки и запуска Ollama + модели:

```bash
./run_qwen.sh
```

Он:
1. Устанавливает Ollama (через Homebrew на macOS или официальный installer на Linux), если не установлен
2. Запускает `ollama serve` в фоне, если сервер ещё не работает
3. Скачивает модель (`qwen2.5:14b`, ~9 ГБ), если её нет локально

Использовать другую модель:

```bash
OLLAMA_MODEL=qwen2.5:7b ./run_qwen.sh
```

Или поменяйте `OLLAMA_MODEL` в `.env`.

---

## Структура проекта

```
news_feed/
├── app.py              # Веб-сервер FastAPI + SSE
├── main.py             # CLI-интерфейс
├── config.py           # Переменные окружения и настройки
├── requirements.txt    # Python-зависимости
├── setup.sh            # Первоначальная установка
├── run_qwen.sh         # Запуск Ollama + скачивание Qwen
├── .env.example        # Шаблон конфигурации
├── modules/
│   ├── collector.py    # Сбор статей (NewsAPI, GNews, RSS)
│   ├── analyzer.py     # Кластеризация, NER, сравнение источников
│   ├── sentiment.py    # Анализ тональности (rubert)
│   ├── stakeholders.py # Граф знаний, Cui Bono (NetworkX + LLM)
│   └── reporter.py     # Генерация итогового отчёта (LLM)
├── utils/
│   └── llm.py          # HTTP-клиент к Ollama API
└── static/
    └── index.html      # Веб-интерфейс
```

---

## Устранение неполадок

**`ModuleNotFoundError`** — зависимости не установлены:
```bash
pip install -r requirements.txt
```

**`OSError: [E050] Can't find model 'ru_core_news_lg'`** — spaCy-модель не скачана:
```bash
python -m spacy download ru_core_news_lg
```

**`Статьи не найдены`** — без API-ключей RSS-ленты возвращают результаты только если запрос совпадает со словами в заголовках. Попробуйте более конкретный запрос на русском.

**Ollama не отвечает** — сервер не запущен:
```bash
./run_qwen.sh
# или вручную:
ollama serve &
```

**Первый запрос медленный** — HuggingFace-модели (`e5-large`, `rubert`) скачиваются автоматически при первом обращении (~1-2 ГБ суммарно).
