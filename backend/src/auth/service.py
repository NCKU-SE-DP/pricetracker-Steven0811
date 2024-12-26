from passlib.context import CryptContext
from src.models import User
from datetime import datetime, timedelta
from fastapi import HTTPException
from jose import jwt
from src.config import Auth
from src.error_handler.logger import Logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def verify(plain_password, hashed_password):
    """
    Verify that a plain password matches a hashed password.

    :param plain_password: The plain text password provided by the user.
    :param hashed_password: The hashed password stored in the database.
    :return: True if the passwords match, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Password verification failed.")

def check_user_password_is_correct(user_db, username, password):
    """
    Check if the provided plain password matches the stored hashed password.

    :param plain_password: The plain text password provided by the user.
    :param hashed_password: The hashed password stored in the database.
    :return: True if the passwords match, False otherwise.
    """
    logger = Logger(__name__, "check_user_password_is_correct").get_logger()
    user = user_db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or invalid credentials.")
    
    if not verify(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    logger.info(f"User {user.username} authenticated successfully.")
    return user

def create_access_token(data, expires_delta=None):
    """
    Create a JWT access token.
    
    :param data: A dictionary containing the data to be encoded in the token.
    :param expires_delta: An optional timedelta for the token's expiration time.
                          If not provided, the token will expire in 15 minutes.
    :return: A JWT access token as a string.
    """
    logger = Logger(__name__, "create_access_token").get_logger()
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    try:
        encoded_jwt = jwt.encode(to_encode, Auth.JWT_SECRET_KEY, algorithm="HS256")
        logger.debug("Access token created successfully.")
        return encoded_jwt
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create access token.")