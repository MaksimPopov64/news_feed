"""
Модуль 4: Определение заинтересованных сторон («Кому выгодно?»)
NER + граф знаний NetworkX + LLM-анализ
"""

from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
import networkx as nx
from modules.analyzer import extract_entities
from utils.llm import ask_ollama

if TYPE_CHECKING:
    from modules.collector import Article

STAKEHOLDER_LABELS = {"PER", "ORG", "GPE", "LOC", "PERSON", "NORP", "FAC"}


def build_knowledge_graph(articles: list[Article]) -> nx.Graph:
    G = nx.Graph()
    for a in articles:
        text = f"{a.title}. {a.text}"
        ents = extract_entities(text)
        # Добавляем узел источника
        G.add_node(a.source, type="source")
        # Добавляем сущности и связи с источником
        for label, values in ents.items():
            if label not in STAKEHOLDER_LABELS:
                continue
            for v in values:
                if not G.has_node(v):
                    G.add_node(v, type=label)
                if G.has_edge(a.source, v):
                    G[a.source][v]["weight"] = G[a.source][v].get("weight", 0) + 1
                else:
                    G.add_edge(a.source, v, weight=1)
    return G


def get_top_entities(G: nx.Graph, top_n: int = 15) -> list[dict]:
    entities = []
    for node, data in G.nodes(data=True):
        if data.get("type") == "source":
            continue
        degree = G.degree(node)
        total_weight = sum(d.get("weight", 1) for _, _, d in G.edges(node, data=True))
        entities.append({
            "entity": node,
            "type": data.get("type", "?"),
            "mentions": total_weight,
            "connected_sources": degree,
        })
    return sorted(entities, key=lambda x: x["mentions"], reverse=True)[:top_n]


def graph_to_dict(G: nx.Graph) -> dict:
    return {
        "nodes": [
            {"id": n, "type": d.get("type", "?")}
            for n, d in G.nodes(data=True)
        ],
        "edges": [
            {"source": u, "target": v, "weight": d.get("weight", 1)}
            for u, v, d in G.edges(data=True)
        ],
    }


async def cui_bono_analysis(query: str, top_entities: list[dict]) -> str:
    if not top_entities:
        return "Недостаточно данных для анализа заинтересованных сторон."

    entities_text = "\n".join(
        f"- {e['entity']} ({e['type']}): упоминается {e['mentions']} раз"
        for e in top_entities
    )

    system = (
        "Ты аналитик СМИ и эксперт по медиа-анализу. "
        "Отвечай строго по-русски, кратко и аналитически. "
        "Избегай домыслов — только то, что следует из данных."
    )
    prompt = (
        f"Тема новостного запроса: «{query}»\n\n"
        f"Ключевые упомянутые акторы:\n{entities_text}\n\n"
        "Для каждого значимого актора из списка ответь:\n"
        "1. Какую выгоду он может получить от освещения этой темы?\n"
        "2. Какой ущерб ему угрожает?\n"
        "3. Какова его вероятная позиция?\n\n"
        "Завершинкратким выводом: кто, скорее всего, является основным бенефициаром "
        "информационной кампании вокруг этой темы и почему."
    )

    return await ask_ollama(prompt, system=system)


async def analyze(articles: list[Article], query: str) -> dict:
    G = build_knowledge_graph(articles)
    top_entities = get_top_entities(G)
    cui_bono = await cui_bono_analysis(query, top_entities)

    return {
        "graph": graph_to_dict(G),
        "top_entities": top_entities,
        "cui_bono": cui_bono,
    }
