from functools import lru_cache
from pydantic import BaseModel
from dotenv import load_dotenv
import os


class Settings(BaseModel):
    postgres_url: str
    mongo_url: str
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str
    jwt_secret: str
    jwt_algorithm: str
    jwt_expire_minutes: int


@lru_cache
def get_settings() -> Settings:
    load_dotenv()
    return Settings(
        postgres_url=os.getenv("POSTGRES_URL", ""),
        mongo_url=os.getenv("MONGO_URL", ""),
        minio_endpoint=os.getenv("MINIO_ENDPOINT", ""),
        minio_access_key=os.getenv("MINIO_ACCESS_KEY", ""),
        minio_secret_key=os.getenv("MINIO_SECRET_KEY", ""),
        minio_bucket=os.getenv("MINIO_BUCKET", ""),
        jwt_secret=os.getenv("JWT_SECRET", ""),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_expire_minutes=int(os.getenv("JWT_EXPIRE_MINUTES", "60")),
    )
