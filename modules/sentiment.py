"""
Модуль 3: Анализ тональности и фрейминга
Модель: blanchefort/rubert-base-cased-sentiment
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from transformers import pipeline, Pipeline
from config import SENTIMENT_MODEL, DEVICE

if TYPE_CHECKING:
    from modules.collector import Article

_pipeline: Pipeline | None = None

LABEL_MAP = {
    "POSITIVE": "позитивная",
    "NEGATIVE": "негативная",
    "NEUTRAL": "нейтральная",
    "LABEL_0": "негативная",
    "LABEL_1": "нейтральная",
    "LABEL_2": "позитивная",
}


def _get_pipeline() -> Pipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = pipeline(
            "text-classification",
            model=SENTIMENT_MODEL,
            device=DEVICE if DEVICE != "mps" else -1,  # transformers pipeline: mps→cpu fallback
            truncation=True,
            max_length=512,
        )
    return _pipeline


def analyze_text(text: str) -> dict:
    pipe = _get_pipeline()
    result = pipe(text[:512])[0]
    label_raw = result["label"]
    label_ru = LABEL_MAP.get(label_raw, label_raw)
    return {
        "label": label_ru,
        "label_raw": label_raw,
        "score": round(result["score"], 3),
    }


def analyze(articles: list[Article]) -> dict:
    results_per_source: dict[str, dict] = {}
    for a in articles:
        text = f"{a.title}. {a.text}"
        results_per_source[a.source] = analyze_text(text)

    counts: dict[str, int] = {"позитивная": 0, "негативная": 0, "нейтральная": 0}
    for r in results_per_source.values():
        lbl = r["label"]
        counts[lbl] = counts.get(lbl, 0) + 1

    dominant = max(counts, key=counts.get) if counts else "нейтральная"

    return {
        "per_source": results_per_source,
        "summary": counts,
        "dominant_tone": dominant,
    }
