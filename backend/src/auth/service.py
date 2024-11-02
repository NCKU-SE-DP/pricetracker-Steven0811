from passlib.context import CryptContext
from src.models import User
from datetime import datetime, timedelta
from jose import jwt
from src.config import Auth

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def check_user_password_is_correct(user_db, username, password):
    user = user_db.query(User).filter(User.username == username).first()
    if not verify(password, user.hashed_password):
        return False
    return user

def create_access_token(user_data, expires_delta=None):
    """create access token"""
    to_encode = user_data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Auth.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    print(to_encode)
    encoded_jwt = jwt.encode(to_encode, Auth.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt