"""
Модуль 2: Анализ и сравнение источников
Кластеризация статей, извлечение NER, семантическое сравнение
"""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import spacy
from sentence_transformers import SentenceTransformer
from config import EMBEDDING_MODEL, SPACY_MODEL, DEVICE

if TYPE_CHECKING:
    from modules.collector import Article

_embedder: SentenceTransformer | None = None
_nlp: spacy.Language | None = None


def _get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(EMBEDDING_MODEL, device=DEVICE)
    return _embedder


def _get_nlp() -> spacy.Language:
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load(SPACY_MODEL)
        except OSError:
            # Fallback to small model
            _nlp = spacy.load("ru_core_news_sm")
    return _nlp


def embed_articles(articles: list[Article]) -> np.ndarray:
    texts = [f"{a.title}. {a.text}" for a in articles]
    embedder = _get_embedder()
    return embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False)


def cluster_articles(embeddings: np.ndarray, n_clusters: int | None = None) -> list[int]:
    n = len(embeddings)
    if n < 2:
        return [0] * n
    k = n_clusters or max(2, min(8, n // 3))
    km = KMeans(n_clusters=k, random_state=42, n_init="auto")
    return km.fit_predict(embeddings).tolist()


def extract_entities(text: str) -> dict[str, list[str]]:
    nlp = _get_nlp()
    doc = nlp(text[:5000])
    entities: dict[str, list[str]] = {}
    for ent in doc.ents:
        label = ent.label_
        value = ent.text.strip()
        if len(value) > 2:
            entities.setdefault(label, [])
            if value not in entities[label]:
                entities[label].append(value)
    return entities


def compare_articles(a1: Article, a2: Article) -> dict:
    """Сравнивает две статьи: семантика + пересечение NER."""
    embedder = _get_embedder()
    t1 = f"{a1.title}. {a1.text}"
    t2 = f"{a2.title}. {a2.text}"
    emb = embedder.encode([t1, t2], normalize_embeddings=True)
    sim = float(cosine_similarity([emb[0]], [emb[1]])[0][0])

    ents1 = extract_entities(t1)
    ents2 = extract_entities(t2)
    all_labels = set(ents1) | set(ents2)
    entity_overlap = {}
    for label in all_labels:
        s1 = set(ents1.get(label, []))
        s2 = set(ents2.get(label, []))
        entity_overlap[label] = {
            "common": list(s1 & s2),
            "only_in_first": list(s1 - s2),
            "only_in_second": list(s2 - s1),
        }

    return {"semantic_similarity": round(sim, 3), "entity_overlap": entity_overlap}


def analyze(articles: list[Article]) -> dict:
    if not articles:
        return {"clusters": [], "embeddings_shape": [0, 0], "entities_per_source": {}}

    embeddings = embed_articles(articles)
    labels = cluster_articles(embeddings)

    # Группировка по кластерам
    clusters: dict[int, list[str]] = {}
    for i, label in enumerate(labels):
        clusters.setdefault(label, [])
        clusters[label].append(articles[i].source)

    # NER для каждой статьи
    entities_per_source: dict[str, dict] = {}
    for a in articles:
        entities_per_source[a.source] = extract_entities(f"{a.title}. {a.text}")

    # Консенсус фактов — ищем сущности, упомянутые в большинстве источников
    fact_frequency: dict[str, int] = {}
    for ents in entities_per_source.values():
        for label, values in ents.items():
            for v in values:
                key = f"{label}:{v}"
                fact_frequency[key] = fact_frequency.get(key, 0) + 1

    n_sources = len(articles)
    consensus_facts = {
        k: v for k, v in fact_frequency.items()
        if v >= max(2, n_sources * 0.4)
    }
    disputed_facts = {
        k: v for k, v in fact_frequency.items()
        if v == 1 and n_sources >= 3
    }

    return {
        "total_articles": n_sources,
        "clusters": [
            {"cluster_id": cid, "sources": srcs, "size": len(srcs)}
            for cid, srcs in clusters.items()
        ],
        "entities_per_source": entities_per_source,
        "consensus_facts": consensus_facts,
        "disputed_facts": disputed_facts,
        "agreement_score": round(
            len(consensus_facts) / max(1, len(fact_frequency)), 3
        ),
    }
