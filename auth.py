import os
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
