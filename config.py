import os
from dotenv import load_dotenv

load_dotenv()

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY", "")
GNEWS_KEY = os.getenv("GNEWS_KEY", "")

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:14b")

SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "blanchefort/rubert-base-cased-sentiment")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
SPACY_MODEL = os.getenv("SPACY_MODEL", "ru_core_news_lg")

import torch
DEVICE = (
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)

RSS_FEEDS = {
    "РИА Новости": "https://ria.ru/export/rss2/archive/index.xml",
    "Коммерсантъ": "https://www.kommersant.ru/RSS/news.xml",
    "Meduza": "https://meduza.io/rss/all",
    "The Bell": "https://thebell.io/feed/",
    "Новая газета": "https://novayagazeta.ru/rss/all.xml",
    "Lenta.ru": "https://lenta.ru/rss/news",
    "Ведомости": "https://www.vedomosti.ru/rss/news",
    "BBC Русская служба": "https://feeds.bbci.co.uk/russian/rss.xml",
}
