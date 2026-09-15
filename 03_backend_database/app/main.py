from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router
from .config import Settings
from .database import Base, create_database
from .routes import router, health
from .models import ISSUE_LOCATION_INDEX


def create_app(settings=None):
    settings = settings or Settings.from_environment()

    @asynccontextmanager
    async def lifespan(app):
        settings.ensure_operator_password()
        engine, session_factory = create_database(settings.database_url)
        Base.metadata.create_all(engine)
        # create_all does not add a new index to an already-existing table.
        ISSUE_LOCATION_INDEX.create(bind=engine, checkfirst=True)
        app.state.engine = engine
        app.state.session_factory = session_factory
        yield
        engine.dispose()

    application = FastAPI(title="CODYSSEY Urban Intelligence", version="2.0.0", lifespan=lifespan)
    application.state.settings = settings
    application.state.sessions = {}
    application.state.login_failures = {}
    application.add_middleware(CORSMiddleware, allow_origins=list(settings.allowed_origins), allow_credentials=True,
                               allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"])
    application.include_router(router)
    application.include_router(auth_router)
    application.add_api_route("/health", health, methods=["GET"], include_in_schema=False)

    @application.get("/")
    def root():
        return {"system": "CODYSSEY", "status": "online", "contract_version": "2.0", "docs": "/docs"}

    return application


app = create_app()
