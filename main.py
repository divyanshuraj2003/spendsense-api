from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, UserSchema
from auth import hash_pwd

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
