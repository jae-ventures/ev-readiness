from fastapi import FastAPI
from routers import score

app = FastAPI(
    title="EV Readiness Score API",
    description="Scores locations on EV adoption readiness",
    version="0.1.0"
)

app.include_router(score.router)

@app.get("/health")
async def health():
    return {"status": "ok"}