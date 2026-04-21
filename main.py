"""CLI-запуск: python main.py "ваш запрос" """

import asyncio
import sys
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from modules import collector, analyzer, sentiment, stakeholders, reporter

console = Console()


async def run(query: str, lang: str = "ru"):
    console.print(Panel(f"[bold]Запрос:[/] {query}", title="NewsTriangulator"))

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as p:

        t = p.add_task("Сбор статей...", total=None)
        articles = await collector.collect(query, lang)
        p.update(t, description=f"[green]✓[/] Собрано {len(articles)} статей из {len({a.source for a in articles})} источников")
        p.stop_task(t)

        if not articles:
            console.print("[red]Статьи не найдены. Проверьте запрос или добавьте API-ключи в .env[/]")
            return

        t2 = p.add_task("Анализ источников...", total=None)
        loop = asyncio.get_event_loop()
        analysis = await loop.run_in_executor(None, analyzer.analyze, articles)
        p.update(t2, description="[green]✓[/] Анализ источников завершён")
        p.stop_task(t2)

        t3 = p.add_task("Анализ тональности...", total=None)
        sent_result = await loop.run_in_executor(None, sentiment.analyze, articles)
        p.update(t3, description="[green]✓[/] Тональность проанализирована")
        p.stop_task(t3)

        t4 = p.add_task("Граф знаний и Cui Bono...", total=None)
        stake_result = await stakeholders.analyze(articles, query)
        p.update(t4, description="[green]✓[/] Заинтересованные стороны определены")
        p.stop_task(t4)

        t5 = p.add_task("Генерация отчёта...", total=None)
        report = await reporter.generate_report(
            query=query,
            articles_count=len(articles),
            analysis=analysis,
            sentiment=sent_result,
            stakeholders=stake_result,
        )
        p.update(t5, description="[green]✓[/] Отчёт готов")
        p.stop_task(t5)

    console.print()
    console.print(Markdown(report))


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or "последние новости"
    asyncio.run(run(query))
