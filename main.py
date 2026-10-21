from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
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
