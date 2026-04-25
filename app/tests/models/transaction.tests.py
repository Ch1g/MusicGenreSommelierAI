from unittest.mock import patch

from sqlmodel import Session

from music_genre_sommelier.models.transaction import Transaction
from music_genre_sommelier.models.user import User
from music_genre_sommelier.utils.enum.transaction import TransactionStatus


def _seed_user(session: Session) -> User:
    user = User(email="tx@example.com", username="txuser", encrypted_password="h")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_get_balance_counts_only_success(test_session: Session, test_engine):
    user = _seed_user(test_session)
    rows = [
        Transaction(user_id=user.id, amount=75.0, status=TransactionStatus.SUCCESS),
        Transaction(user_id=user.id, amount=25.0, status=TransactionStatus.SUCCESS),
        Transaction(user_id=user.id, amount=200.0, status=TransactionStatus.PENDING),
        Transaction(user_id=user.id, amount=300.0, status=TransactionStatus.FAIL_CANCELED),
        Transaction(user_id=user.id, amount=400.0, status=TransactionStatus.FAIL_INSUFFICIENT_FUNDS),
    ]
    for row in rows:
        test_session.add(row)
    test_session.commit()

    with patch("music_genre_sommelier.models.transaction.engine", test_engine):
        balance = Transaction.get_balance(user.id)

    assert balance == 100.0


def test_check_funds_insufficient_sets_status():
    tx = Transaction(user_id=1, amount=-10.0)
    with patch(
        "music_genre_sommelier.models.transaction.Transaction.get_balance",
        return_value=5.0,
    ):
        tx.check_funds()
    assert tx.status == TransactionStatus.FAIL_INSUFFICIENT_FUNDS


def test_check_funds_sufficient_leaves_status_pending():
    tx = Transaction(user_id=1, amount=-10.0)
    with patch(
        "music_genre_sommelier.models.transaction.Transaction.get_balance",
        return_value=100.0,
    ):
        tx.check_funds()
    assert tx.status == TransactionStatus.PENDING
