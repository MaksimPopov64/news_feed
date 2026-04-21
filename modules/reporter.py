"""
Модуль 5: Генерация выводов и отчёта
Объединяет результаты всех модулей через LLM
"""

from __future__ import annotations
from utils.llm import ask_ollama


async def generate_report(
    query: str,
    articles_count: int,
    analysis: dict,
    sentiment: dict,
    stakeholders: dict,
) -> str:
    consensus_list = list(analysis.get("consensus_facts", {}).keys())[:10]
    disputed_list = list(analysis.get("disputed_facts", {}).keys())[:5]
    sentiment_summary = sentiment.get("summary", {})
    top_entities = stakeholders.get("top_entities", [])[:8]
    cui_bono = stakeholders.get("cui_bono", "")
    clusters = analysis.get("clusters", [])
    agreement_score = analysis.get("agreement_score", 0)

    system = (
        "Ты — аналитическая система верификации новостей. "
        "Создавай структурированные отчёты на русском языке. "
        "Будь точным, объективным, избегай оценочных суждений без фактической основы."
    )

    prompt = f"""На основе анализа {articles_count} статей по теме «{query}» составь аналитический отчёт.

=== ДАННЫЕ ===

Кластеры событий ({len(clusters)} групп):
{_format_clusters(clusters)}

Степень согласованности источников: {agreement_score * 100:.0f}%

Согласованные факты (упомянуты в большинстве источников):
{', '.join(consensus_list) if consensus_list else 'не выявлены'}

Спорные/уникальные утверждения (только один источник):
{', '.join(disputed_list) if disputed_list else 'не выявлены'}

Тональность публикаций:
- Позитивных: {sentiment_summary.get('позитивная', 0)}
- Нейтральных: {sentiment_summary.get('нейтральная', 0)}
- Негативных: {sentiment_summary.get('негативная', 0)}

Ключевые акторы:
{_format_entities(top_entities)}

Анализ «Кому выгодно»:
{cui_bono}

=== ТРЕБОВАНИЯ К ОТЧЁТУ ===

Напиши отчёт со следующими разделами:
1. **Тема и контекст** — кратко о чём запрос
2. **Анализ согласованности** — что подтверждается большинством, что вызывает сомнения
3. **Анализ тональности** — как разные типы СМИ освещают тему
4. **Заинтересованные стороны** — кто упомянут, чьи интересы затронуты
5. **Вывод** — итоговая оценка достоверности и рекомендация по интерпретации
"""

    return await ask_ollama(prompt, system=system)


def _format_clusters(clusters: list) -> str:
    if not clusters:
        return "  нет данных"
    lines = []
    for c in clusters:
        sources = ", ".join(c.get("sources", [])[:5])
        lines.append(f"  Группа {c['cluster_id']}: {sources}")
    return "\n".join(lines)


def _format_entities(entities: list) -> str:
    if not entities:
        return "  нет данных"
    lines = []
    for e in entities:
        lines.append(f"  - {e['entity']} ({e['type']}): {e['mentions']} упоминаний")
    return "\n".join(lines)
