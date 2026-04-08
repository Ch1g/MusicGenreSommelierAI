import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlmodel import Session
from music_genre_sommelier.services.registration_service import AuthError, RegistrationService
from music_genre_sommelier.utils.database.db import engine
from pydantic import BaseModel

router = APIRouter()

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupResponse(BaseModel):
    id: int
    email: str
    jwt_token: str

@router.post(
    "/signup",
    status_code=201,
    response_model=SignupResponse,
    responses={
        409: {"description": "Email already taken"},
        422: {"description": "Invalid input"},
        500: {"description": "Internal server error"},
    }
)
def sign_up(email: str, username: str, password: str):
    with Session(engine) as session:
        try:
            registration_service = RegistrationService(session)
            user = registration_service.register(email, username, password)

            return JSONResponse(
                status_code=201,
                content={
                    "id": user.id,
                    "email": user.email,
                    "jwt_token": "placeholder"
                }
            )
        except AuthError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


class SigninResponse(BaseModel):
    id: int
    email: str
    jwt_token: str

@router.post(
    "/signin",
    status_code=200,
    response_model=SigninResponse,
    responses={
        401: {"description": "Invalid email or password"},
        500: {"description": "Internal server error"},
    }
)
def sign_in(email: str, password: str):
    with Session(engine) as session:
        try:
            registration_service = RegistrationService(session)
            user = registration_service.verify_password(email, password)

            return JSONResponse(
                status_code=200,
                content={
                    "id": user.id,
                    "email": user.email,
                    "jwt_token": "placeholder"
                }
            )
        except AuthError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
