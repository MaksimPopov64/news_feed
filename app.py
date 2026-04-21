"""
Веб-интерфейс: FastAPI + SSE для стриминга прогресса
"""

import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from modules import collector, analyzer, sentiment, stakeholders, reporter
from utils.llm import check_ollama

app = FastAPI(title="NewsTriangulator", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


class AnalyzeRequest(BaseModel):
    query: str
    lang: str = "ru"


@app.get("/", response_class=HTMLResponse)
async def root():
    return (Path("static") / "index.html").read_text(encoding="utf-8")


@app.get("/api/status")
async def status():
    ollama_ok = await check_ollama()
    return {"ollama": ollama_ok, "status": "ready" if ollama_ok else "ollama_offline"}


@app.post("/api/analyze/stream")
async def analyze_stream(req: AnalyzeRequest):
    async def event_generator() -> AsyncGenerator[str, None]:
        async def send(event: str, data: dict) -> str:
            payload = json.dumps(data, ensure_ascii=False)
            return f"event: {event}\ndata: {payload}\n\n"

        try:
            yield await send("progress", {"step": 1, "message": "Собираю статьи из источников..."})
            articles = await collector.collect(req.query, req.lang)

            if not articles:
                yield await send("error", {"message": "Статьи не найдены. Проверьте запрос или API-ключи."})
                return

            yield await send("progress", {
                "step": 1, "done": True,
                "message": f"Собрано {len(articles)} статей из {len({a.source for a in articles})} источников"
            })

            yield await send("progress", {"step": 2, "message": "Кластеризую и сравниваю источники..."})
            analysis = await asyncio.get_event_loop().run_in_executor(
                None, analyzer.analyze, articles
            )
            yield await send("progress", {"step": 2, "done": True, "message": "Анализ источников завершён"})

            yield await send("progress", {"step": 3, "message": "Анализирую тональность публикаций..."})
            sent_result = await asyncio.get_event_loop().run_in_executor(
                None, sentiment.analyze, articles
            )
            yield await send("progress", {"step": 3, "done": True, "message": "Анализ тональности завершён"})

            yield await send("progress", {"step": 4, "message": "Строю граф знаний, ищу заинтересованных акторов..."})
            stake_result = await stakeholders.analyze(articles, req.query)
            yield await send("progress", {"step": 4, "done": True, "message": "Анализ заинтересованных сторон завершён"})

            yield await send("progress", {"step": 5, "message": "Генерирую итоговый отчёт через LLM..."})
            report_text = await reporter.generate_report(
                query=req.query,
                articles_count=len(articles),
                analysis=analysis,
                sentiment=sent_result,
                stakeholders=stake_result,
            )
            yield await send("progress", {"step": 5, "done": True, "message": "Отчёт готов"})

            result = {
                "query": req.query,
                "timestamp": datetime.now().isoformat(),
                "articles": [a.model_dump() for a in articles[:30]],
                "analysis": analysis,
                "sentiment": sent_result,
                "stakeholders": {
                    "top_entities": stake_result["top_entities"],
                    "cui_bono": stake_result["cui_bono"],
                    "graph": stake_result["graph"],
                },
                "report": report_text,
            }
            yield await send("result", result)

        except Exception as e:
            yield await send("error", {"message": str(e)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
