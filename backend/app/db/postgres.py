import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.config import get_settings


def get_engine():
    settings = get_settings()
    return create_engine(settings.postgres_url, pool_pre_ping=True)


metadata = MetaData()

users_table = Table(
    "users",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("username", String(50), unique=True, nullable=False),
    Column("email", String(255), unique=True, nullable=False),
    Column("password_hash", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), default=datetime.utcnow, nullable=False),
)


def init_db() -> None:
    engine = get_engine()
    metadata.create_all(engine)


def check_postgres() -> None:
    engine = get_engine()
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
