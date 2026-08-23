import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "orma-ai-secure-healthcare-key-v1"))
env_mode = os.getenv("ENVIRONMENT", os.getenv("ENV", "development")).strip().lower()
if env_mode == "production" and (SECRET_KEY == "orma-ai-secure-healthcare-key-v1" or len(SECRET_KEY) < 32):
    import logging
    logging.getLogger(__name__).critical("[SECURITY CRITICAL] Production deployment detected but JWT_SECRET_KEY is missing, weak (<32 chars), or using the default key! Set a strong random JWT_SECRET_KEY in production.")
    raise ValueError("Production mode requires a secure JWT_SECRET_KEY with at least 32 characters in environment variables.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 1 week

import bcrypt

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not plain_password or not hashed_password:
        return False
    try:
        if hashed_password.startswith("$2a$") or hashed_password.startswith("$2b$") or hashed_password.startswith("$2y$"):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
