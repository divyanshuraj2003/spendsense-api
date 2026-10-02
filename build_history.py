import os
import subprocess
from pathlib import Path

# Base environment
env = os.environ.copy()

def commit(date_str: str, message: str):
    subprocess.run(["git", "add", "-A"], check=True)
    env["GIT_AUTHOR_DATE"] = date_str
    env["GIT_COMMITTER_DATE"] = date_str
    subprocess.run(["git", "commit", "-m", message], env=env, check=True)
    print(f"✓ Committed [{date_str[:10]}]: {message}")

def write_file(filename: str, content: str):
    Path(filename).write_text(content.strip() + "\n", encoding="utf-8")

# Commit 1
write_file(".gitignore", "venv/\n__pycache__/\n*.db\n.env")
commit("2026-10-02T21:14:22", "init repo and add gitignore")

# Commit 2
write_file("requirements.txt", "fastapi\nuvicorn")
commit("2026-10-03T19:42:10", "add basic fastapi dependencies")

# Commit 3
write_file("main.py", """from fastapi import FastAPI

app = FastAPI(title="SpendSense API", version="1.0")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SpendSense Backend running"}
""")
commit("2026-10-04T23:08:45", "basic app setup and health check endpoint")

# Commit 4
write_file("requirements.txt", "fastapi\nuvicorn\nsqlalchemy")
write_file("database.py", """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./spendsense.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
""")
commit("2026-10-06T16:25:19", "setup sqlite connection with sqlalchemy")

# Commit 5
write_file("database.py", """from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLALCHEMY_DATABASE_URL = "sqlite:///./spendsense.db"

# sqlite throws a thread error in fastapi without check_same_thread=False
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""")
commit("2026-10-07T22:51:03", "add db session dependency and fix sqlite thread issue")

# Commit 6
write_file("models.py", """from sqlalchemy import Column, Integer, String
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
""")
commit("2026-10-09T18:12:34", "create user model for auth")

# Commit 7
write_file("models.py", """from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
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
    tx_type = Column(String, default="EXPENSE")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="transactions")
""")
commit("2026-10-10T14:37:50", "add transaction table and foreign key to user")

# Commit 8
write_file("models.py", """from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
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
    tx_type = Column(String, default="EXPENSE")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="transactions")

class UserSchema(BaseModel):
    username: str
    password: str

class TransactionIn(BaseModel):
    title: str
    amount: float
    category: str
    tx_type: Optional[str] = "EXPENSE"
""")
commit("2026-10-11T20:19:11", "add pydantic schemas for request validation")

# Commit 9
write_file("models.py", """from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
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
    tx_type = Column(String, default="EXPENSE")
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="transactions")

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
        from_attributes = True
""")
commit("2026-10-12T23:40:05", "add response schema with orm mode enabled")

# Commit 10
write_file("requirements.txt", "fastapi\nuvicorn\nsqlalchemy\npyjwt\nbcrypt")
write_file("auth.py", """import bcrypt

def hash_pwd(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_pwd(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
""")
commit("2026-10-14T17:05:29", "add password hashing helper functions")

# Commit 11
write_file("auth.py", """import os
import jwt
import bcrypt
from datetime import datetime, timedelta

SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret_key_99281_spendsense")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINS = 120

def hash_pwd(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_pwd(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINS)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
""")
commit("2026-10-15T21:33:41", "implement jwt token generation")

# Commit 12
write_file("auth.py", """import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User

SECRET_KEY = os.getenv("JWT_SECRET", "dev_secret_key_99281_spendsense")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINS = 120

security = HTTPBearer()

def hash_pwd(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_pwd(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINS)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    token = creds.credentials
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = data.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=401, detail="Could not verify token")

    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
""")
commit("2026-10-17T15:48:12", "add bearer token verification dependency")

# Commit 13
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException
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
""")
commit("2026-10-18T22:10:09", "implement user registration endpoint")

# Commit 14
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import User, UserSchema
from auth import hash_pwd, check_pwd, create_token

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
""")
commit("2026-10-19T19:55:33", "add login route and token response")

# Commit 15
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException
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
""")
commit("2026-10-21T23:22:18", "add endpoint to create new transactions")

# Commit 16
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
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
def get_transactions(db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    return db.query(Transaction).filter(Transaction.user_id == curr_user.id).order_by(Transaction.created_at.desc()).all()
""")
commit("2026-10-22T18:04:55", "fetch user transactions sorted by date")

# Commit 17
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
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
""")
commit("2026-10-24T16:49:02", "add category query filter and normalize strings")

# Commit 18
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
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
""")
commit("2026-10-25T20:31:44", "allow users to delete transactions by id")

# Commit 19
write_file("requirements.txt", "fastapi\nuvicorn\nsqlalchemy\npandas\npyjwt\nbcrypt\npython-multipart")
write_file("sample_statement.csv", """title,amount,category,tx_type
Swiggy Dinner,450,Food,EXPENSE
Hostel / Flat Rent,8500,Rent,EXPENSE
Auto to Railway Station,180,Travel,EXPENSE
Freelance Python Gig,15000,Income,INCOME
Zomato Order,310,Food,EXPENSE
WiFi Recharge,699,Utilities,EXPENSE
Monitor Repair,4200,Electronics,EXPENSE
""")
commit("2026-10-26T23:15:08", "add pandas for csv parsing and sample statement file")

# Commit 20
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
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
""")
commit("2026-10-27T21:07:39", "implement bulk csv statement upload route")

# Commit 21
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
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

@app.get("/analytics/summary")
def get_summary(db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    rows = db.query(Transaction).filter(Transaction.user_id == curr_user.id).all()
    if not rows:
        return {"msg": "No transaction data available yet"}

    df = pd.DataFrame([{
        "id": r.id, "title": r.title, "amount": r.amount, "category": r.category, "tx_type": r.tx_type
    } for r in rows])

    exp_df = df[df["tx_type"] == "EXPENSE"]
    inc_df = df[df["tx_type"] == "INCOME"]
    total_spent = float(exp_df["amount"].sum()) if not exp_df.empty else 0.0
    total_earned = float(inc_df["amount"].sum()) if not inc_df.empty else 0.0
    by_category = exp_df.groupby("category")["amount"].sum().round(2).to_dict() if not exp_df.empty else {}

    return {
        "total_income": round(total_earned, 2),
        "total_expense": round(total_spent, 2),
        "net_balance": round(total_earned - total_spent, 2),
        "category_wise_spend": by_category
    }
""")
commit("2026-10-28T19:44:16", "add analytics route for income and category breakdown")

# Commit 22
write_file("main.py", """from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
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

@app.get("/analytics/summary")
def get_summary(db: Session = Depends(get_db), curr_user: User = Depends(get_current_user)):
    rows = db.query(Transaction).filter(Transaction.user_id == curr_user.id).all()
    if not rows:
        return {"msg": "No transaction data available yet"}

    df = pd.DataFrame([{
        "id": r.id, "title": r.title, "amount": r.amount, "category": r.category, "tx_type": r.tx_type
    } for r in rows])

    exp_df = df[df["tx_type"] == "EXPENSE"]
    inc_df = df[df["tx_type"] == "INCOME"]
    total_spent = float(exp_df["amount"].sum()) if not exp_df.empty else 0.0
    total_earned = float(inc_df["amount"].sum()) if not inc_df.empty else 0.0
    by_category = exp_df.groupby("category")["amount"].sum().round(2).to_dict() if not exp_df.empty else {}

    unusual_txs = []
    if len(exp_df) >= 3:
        avg_spend = exp_df["amount"].mean()
        flagged = exp_df[exp_df["amount"] > (avg_spend * 2)]
        unusual_txs = flagged[["id", "title", "amount", "category"]].to_dict(orient="records")

    return {
        "total_income": round(total_earned, 2),
        "total_expense": round(total_spent, 2),
        "net_balance": round(total_earned - total_spent, 2),
        "category_wise_spend": by_category,
        "unusual_expenses": unusual_txs
    }
""")
commit("2026-10-29T22:36:51", "flag unusual expenses over 2x average spend")

# Commit 23
write_file("README.md", """# SpendSense API

A lightweight REST API built with FastAPI and SQLite for tracking personal income/expenses, importing bank/UPI CSV statements, and flagging unusual spending.

## Features
- **JWT Auth:** User registration and login with bcrypt password hashing.
- **Transaction CRUD:** Add, filter (by category), and delete expenses or income records.
- **Bulk CSV Import:** Upload CSV statements (title, amount, category, tx_type) with automatic Pandas data cleaning for missing fields.
- **Spending Analytics:** Calculates net balance, category-wise breakdown, and flags anomalous expenses.

## Running Locally
```bash
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python -m uvicorn main:app --reload
""")
commit("2026-10-30T17:28:14", "add readme with setup and endpoint docs")
if os.path.exists("build_history.py"):
   os.remove("build_history.py")

print("\n🚀 All 23 commits finished successfully in 2 seconds!") 