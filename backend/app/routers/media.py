import uuid
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.security import get_current_user
from app.db.s3 import get_s3_client
from app.core.config import get_settings

router = APIRouter(prefix="/media", tags=["media"])


class PresignResponse(BaseModel):
    media_key: str
    upload_url: str


@router.post("/presign", response_model=PresignResponse)
def presign_upload(_user=Depends(get_current_user)) -> PresignResponse:
    settings = get_settings()
    client = get_s3_client()
    media_key = f"media/{uuid.uuid4()}"
    upload_url = client.generate_presigned_url(
        "put_object",
        Params={"Bucket": settings.minio_bucket, "Key": media_key},
        ExpiresIn=900,
    )
    return PresignResponse(media_key=media_key, upload_url=upload_url)
