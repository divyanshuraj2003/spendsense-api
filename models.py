from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    transactions = relationship("Transaction", back_populates="owner")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, index=True, nullable=False)
    tx_type = Column(String, default="EXPENSE")  # EXPENSE or INCOME
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="transactions")


# Pydantic schemas for request/response validation
class UserSchema(BaseModel):
    username: str
    password: str


class TransactionIn(BaseModel):
    title: str
    amount: float
    category: str
    tx_type: Optional[str] = "EXPENSE"


class TransactionOut(TransactionIn):
    id: int
    created_at: datetime

    class Config:
        # needed in pydantic v2 to read orm models directly
        from_attributes = True