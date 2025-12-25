from sqlalchemy.orm import Session
from models import Transaction

def save_transaction(db: Session, data: dict):
    t = Transaction(
        amount=data["amount"],
        category=data["category"],
        date=data["date"],
        description=data["description"]
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def get_all_transactions(db: Session):
    return db.query(Transaction).all()
