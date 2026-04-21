from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session

from music_genre_sommelier.services.registration_service import RegistrationService
from music_genre_sommelier.utils.auth import create_token
from music_genre_sommelier.utils.database.db import engine

router = APIRouter(prefix="/api/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    username: str
    password: str


class SigninRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    id: int
    email: str
    jwt_token: str


@router.post(
    "/signup",
    status_code=201,
    response_model=AuthResponse,
    responses={
        409: {"description": "Email already taken"},
        422: {"description": "Invalid input"},
        500: {"description": "Internal server error"},
    },
)
def sign_up(body: SignupRequest):
    with Session(engine) as session:
        user = RegistrationService(session).register(body.email, body.username, body.password)
        return JSONResponse(
            status_code=201,
            content={"id": user.id, "email": user.email, "jwt_token": create_token(user.id)},
        )


@router.post(
    "/signin",
    status_code=200,
    response_model=AuthResponse,
    responses={
        401: {"description": "Invalid email or password"},
        500: {"description": "Internal server error"},
    },
)
def sign_in(body: SigninRequest):
    with Session(engine) as session:
        user = RegistrationService(session).verify_password(body.email, body.password)
        return JSONResponse(
            status_code=200,
            content={"id": user.id, "email": user.email, "jwt_token": create_token(user.id)},
        )
