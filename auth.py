import bcrypt

def hash_pwd(password: str):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def check_pwd(plain: str, hashed: str):
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
