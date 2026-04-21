from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.auth import get_current_user_id
from music_genre_sommelier.utils.database.db import engine
from music_genre_sommelier.utils.errors.errors import ForbiddenError, NotFoundError, ValidationError


def _require_self(path_user_id: int, current_user_id: int) -> None:
    if path_user_id != current_user_id:
        raise ForbiddenError("Cannot access another user's transactions")


router = APIRouter(prefix="/api/transactions", tags=["transactions"])


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
    },
)
def get_balance(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    _require_self(user_id, current_user_id)
    with Session(engine) as session:
        user = _get_user(session, user_id)
        return JSONResponse(status_code=200, content={"balance": user.get_balance()})


@router.get(
    "/{user_id}",
    status_code=200,
    response_model=list[Transaction],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def list_transactions(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
):
    _require_self(user_id, current_user_id)
    with Session(engine) as session:
        user = _get_user(session, user_id)
        return JSONResponse(
            status_code=200,
            content=[t.model_dump(mode="json") for t in user.transactions],
        )


@router.post(
    "/{user_id}/funds",
    status_code=201,
    response_model=Transaction,
    responses={
        404: {"description": "Not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"},
    },
)
def add_funds(
    user_id: int,
    body: AddFundsRequest,
    current_user_id: int = Depends(get_current_user_id),
):
    _require_self(user_id, current_user_id)
    with Session(engine) as session:
        if body.amount <= 0:
            raise ValidationError("amount must be positive")

        user = _get_user(session, user_id)

        transaction = Transaction(user_id=user.id, amount=body.amount)
        transaction.approve()

        session.add(transaction)
        session.commit()
        session.refresh(transaction)

        return JSONResponse(status_code=201, content=transaction.model_dump(mode="json"))
