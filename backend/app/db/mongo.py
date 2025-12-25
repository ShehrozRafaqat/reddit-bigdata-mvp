from pymongo import MongoClient

from app.core.config import get_settings


def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongo_url)


def check_mongo() -> None:
    client = get_client()
    client.admin.command("ping")
