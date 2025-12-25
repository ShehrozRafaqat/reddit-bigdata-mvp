from pymongo import MongoClient

from app.core.config import get_settings


def get_client() -> MongoClient:
    settings = get_settings()
    return MongoClient(settings.mongo_url)


def get_database():
    settings = get_settings()
    client = get_client()
    return client.get_database(settings.mongo_url.rsplit("/", 1)[-1])


def check_mongo() -> None:
    client = get_client()
    client.admin.command("ping")
