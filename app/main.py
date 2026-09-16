from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.completions.router import history_router, router as completions_router
from app.habits.router import categories_router, router as habits_router
from app.stats.router import router as stats_router

app = FastAPI(title="Streak", version="0.1.0")

app.include_router(habits_router)
app.include_router(categories_router)
app.include_router(completions_router)
app.include_router(history_router)
app.include_router(stats_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


static_dir = Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
