from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.security import get_current_user
from app.db.mongo import get_database

router = APIRouter(prefix="/posts", tags=["posts"])


class PostCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(..., min_length=1)
    media_keys: List[str] = []


class CommentCreateRequest(BaseModel):
    body: str = Field(..., min_length=1)
    parent_comment_id: Optional[str] = None


def _serialize_id(value: ObjectId) -> str:
    return str(value)


def _serialize_datetime(value: datetime) -> str:
    return value.isoformat()


def _serialize_post(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": _serialize_id(doc["_id"]),
        "title": doc["title"],
        "body": doc["body"],
        "media_keys": doc.get("media_keys", []),
        "author_id": doc["author_id"],
        "created_at": _serialize_datetime(doc["created_at"]),
    }


def _serialize_comment(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": _serialize_id(doc["_id"]),
        "post_id": _serialize_id(doc["post_id"]),
        "body": doc["body"],
        "author_id": doc["author_id"],
        "parent_comment_id": (
            _serialize_id(doc["parent_comment_id"]) if doc.get("parent_comment_id") else None
        ),
        "created_at": _serialize_datetime(doc["created_at"]),
    }


def _parse_object_id(value: str, label: str) -> ObjectId:
    if not ObjectId.is_valid(value):
        raise HTTPException(status_code=400, detail=f"Invalid {label}")
    return ObjectId(value)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_post(
    request: PostCreateRequest,
    current_user=Depends(get_current_user),
):
    db = get_database()
    post = {
        "title": request.title,
        "body": request.body,
        "media_keys": request.media_keys,
        "author_id": str(current_user["id"]),
        "created_at": datetime.utcnow(),
    }
    result = db.posts.insert_one(post)
    post["_id"] = result.inserted_id
    return _serialize_post(post)


@router.get("")
def list_posts() -> List[Dict[str, Any]]:
    db = get_database()
    cursor = db.posts.find().sort("created_at", -1).limit(50)
    return [_serialize_post(doc) for doc in cursor]


@router.get("/{post_id}")
def get_post(post_id: str) -> Dict[str, Any]:
    db = get_database()
    object_id = _parse_object_id(post_id, "post_id")
    doc = db.posts.find_one({"_id": object_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return _serialize_post(doc)


@router.post("/{post_id}/comments", status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: str,
    request: CommentCreateRequest,
    current_user=Depends(get_current_user),
):
    db = get_database()
    post_object_id = _parse_object_id(post_id, "post_id")
    post = db.posts.find_one({"_id": post_object_id})
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    parent_comment_id = None
    if request.parent_comment_id:
        parent_comment_id = _parse_object_id(request.parent_comment_id, "parent_comment_id")
        existing = db.comments.find_one({"_id": parent_comment_id, "post_id": post_object_id})
        if existing is None:
            raise HTTPException(status_code=400, detail="Parent comment not found")

    comment = {
        "post_id": post_object_id,
        "body": request.body,
        "author_id": str(current_user["id"]),
        "parent_comment_id": parent_comment_id,
        "created_at": datetime.utcnow(),
    }
    result = db.comments.insert_one(comment)
    comment["_id"] = result.inserted_id
    return _serialize_comment(comment)


@router.get("/{post_id}/comments")
def list_comments(post_id: str) -> List[Dict[str, Any]]:
    db = get_database()
    post_object_id = _parse_object_id(post_id, "post_id")
    post = db.posts.find_one({"_id": post_object_id})
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    cursor = db.comments.find({"post_id": post_object_id}).sort("created_at", 1)
    return [_serialize_comment(doc) for doc in cursor]
