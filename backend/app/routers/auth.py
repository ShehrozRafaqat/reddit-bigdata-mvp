from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import insert, select
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.db.postgres import get_engine, users_table

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):
    engine = get_engine()
    password_hash = hash_password(request.password)
    try:
        with engine.begin() as connection:
            result = connection.execute(
                insert(users_table).values(
                    username=request.username,
                    email=request.email,
                    password_hash=password_hash,
                )
            )
    except IntegrityError as exc:
        raise HTTPException(status_code=400, detail="Username or email already exists") from exc

    user_id = result.inserted_primary_key[0]
    return {"id": str(user_id), "username": request.username, "email": request.email}


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest):
    engine = get_engine()
    with engine.connect() as connection:
        user = connection.execute(
            select(users_table).where(users_table.c.email == request.email)
        ).mappings().first()

    if user is None or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(str(user["id"]))
    return TokenResponse(access_token=token)
