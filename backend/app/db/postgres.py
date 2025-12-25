from sqlalchemy import create_engine, text

from app.core.config import get_settings


def get_engine():
    settings = get_settings()
    return create_engine(settings.postgres_url, pool_pre_ping=True)


def check_postgres() -> None:
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
