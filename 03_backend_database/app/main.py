from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes import router


Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="CODYSSEY Urban Intelligence Platform",
    description="AI-powered mobile urban intelligence platform",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
def root():
    return {
        "system": "CODYSSEY",
        "platform": "Mobile Urban Intelligence",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }