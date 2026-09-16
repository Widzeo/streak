from fastapi import FastAPI

from app.habits.router import router as habits_router

app = FastAPI(title="Streak", version="0.1.0")

app.include_router(habits_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
