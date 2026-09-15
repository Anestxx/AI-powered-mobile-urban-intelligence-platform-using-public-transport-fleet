from pathlib import Path
from fastapi import Request
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

Base = declarative_base()


def create_database(url):
    parsed = make_url(url)
    if parsed.get_backend_name() != "sqlite":
        raise ValueError("This prototype supports SQLite databases")
    memory = parsed.database in (None, "", ":memory:")
    if not memory:
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    options = {"poolclass": StaticPool} if memory else {}
    engine = create_engine(url, connect_args={"check_same_thread": False, "timeout": 15}, **options)

    @event.listens_for(engine, "connect")
    def configure_sqlite(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=15000")
        cursor.close()

    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def get_db(request: Request):
    with request.app.state.session_factory() as session:
        yield session
