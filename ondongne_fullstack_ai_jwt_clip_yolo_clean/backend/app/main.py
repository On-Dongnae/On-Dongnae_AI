from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="온동네 API", version="0.3.0")
app.include_router(router, prefix="/api/v1")
