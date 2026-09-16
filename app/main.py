from fastapi import FastAPI

from app.completions.router import router as completions_router
from app.habits.router import router as habits_router
from app.stats.router import router as stats_router

app = FastAPI(title="Streak", version="0.1.0")

app.include_router(habits_router)
app.include_router(completions_router)
app.include_router(stats_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
