import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.errors.errors import AppError, NotFoundError, ValidationError

router = APIRouter(prefix="/transactions", tags=["transactions"])


class AddFundsRequest(BaseModel):
    amount: float


def _get_user(session: Session, user_id: int) -> User:
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise NotFoundError(f"User with id {user_id} is not found")
    return user


@router.get(
    "/{user_id}/balance",
    status_code=200,
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    }
)
def get_balance(user_id: int):
    with Session(engine) as session:
        try:
            user = _get_user(session, user_id)
            return JSONResponse(status_code=200, content={"balance": user.get_balance()})
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@router.get(
    "/{user_id}",
    status_code=200,
    response_model=list[Transaction],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    }
)
def list_transactions(user_id: int):
    with Session(engine) as session:
        try:
            user = _get_user(session, user_id)
            return JSONResponse(
                status_code=200,
                content=[t.model_dump(mode="json") for t in user.transactions]
            )
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@router.post(
    "/{user_id}/funds",
    status_code=201,
    response_model=Transaction,
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    }
)
def add_funds(user_id: int, body: AddFundsRequest):
    with Session(engine) as session:
        try:
            if body.amount <= 0:
                raise ValidationError("amount must be positive")

            user = _get_user(session, user_id)

            transaction = Transaction(user_id=user.id, amount=body.amount)
            transaction.approve()

            session.add(transaction)
            session.commit()
            session.refresh(transaction)

            return JSONResponse(status_code=201, content=transaction.model_dump(mode="json"))
        except AppError as e:
            return JSONResponse(status_code=e.status_code, content={"detail": str(e)})
        except Exception as e:
            logging.exception(str(e))
            return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})
