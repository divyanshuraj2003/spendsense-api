from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io

from database import engine, Base, get_db
from models import User, Transaction, UserSchema, TransactionIn, TransactionOut
from auth import hash_pwd, check_pwd, create_token, get_current_user

Base.metadata.create_all(bind=engine)
app = FastAPI(title="SpendSense API", version="1.0")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SpendSense Backend running"}

@app.post("/register", status_code=201)
def register(user: UserSchema, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username taken")
    new_user = User(username=user.username, hashed_password=hash_pwd(user.password))
    db.add(new_user)
    db.commit()
    return {"msg": "Account created successfully"}

@app.post("/login")
def login(user: UserSchema, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not check_pwd(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Wrong credentials")
    return {"access_token": create_token(db_user.username), "token_type": "bearer"}

@app.post("/transactions", response_model=TransactionOut, status_code=201)
def add_transaction(tx: TransactionIn, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    item = Transaction(
        title=tx.title.strip(),
        amount=tx.amount,
        category=tx.category.strip().title(),
        tx_type=tx.tx_type.upper(),
        user_id=curr_user.id
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/transactions", response_model=List[TransactionOut])
def get_transactions(category: Optional[str] = None, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    q = db.query(Transaction).filter(Transaction.user_id == curr_user.id)
    if category:
        q = q.filter(Transaction.category == category.strip().title())
    return q.order_by(Transaction.created_at.desc()).all()

@app.delete("/transactions/{tx_id}")
def remove_transaction(tx_id: int, db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    tx = db.query(Transaction).filter(Transaction.id == tx_id, Transaction.user_id == curr_user.id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    db.delete(tx)
    db.commit()
    return {"msg": "Deleted", "id": tx_id}

@app.post("/transactions/import-csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")
    raw = await file.read()
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.dropna(subset=["title", "amount"])
    df["category"] = df["category"].fillna("Misc").astype(str).str.title()
    df["tx_type"] = df.get("tx_type", "EXPENSE").fillna("EXPENSE").astype(str).str.upper()

    count = 0
    for _, row in df.iterrows():
        db.add(Transaction(
            title=str(row["title"]).strip(),
            amount=float(row["amount"]),
            category=row["category"],
            tx_type=row["tx_type"],
            user_id=curr_user.id
        ))
        count += 1
    db.commit()
    return {"msg": "CSV imported", "rows_added": count}
