from fastapi import APIRouter, HTTPException

from app.db.mongo import check_mongo
from app.db.postgres import check_postgres
from app.db.s3 import check_s3

router = APIRouter()


@router.get("/health")
def health_check():
    try:
        check_postgres()
        check_mongo()
        check_s3()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ok"}
