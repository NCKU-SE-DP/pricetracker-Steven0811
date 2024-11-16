from passlib.context import CryptContext
from src.models import User
from datetime import datetime, timedelta
from jose import jwt
from src.config import Auth

class AuthService:
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify(self, plain_password, hashed_password):
        """
        Verify that a plain password matches a hashed password.

        :param plain_password: The plain text password provided by the user.
        :param hashed_password: The hashed password stored in the database.
        :return: True if the passwords match, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def check_user_password_is_correct(self, user_db, username, password):
        """
        Check if the provided plain password matches the stored hashed password.

        :param plain_password: The plain text password provided by the user.
        :param hashed_password: The hashed password stored in the database.
        :return: True if the passwords match, False otherwise.
        """
        user = user_db.query(User).filter(User.username == username).first()
        if not self.verify(password, user.hashed_password):
            return False
        return user

    def create_access_token(self, data, expires_delta=None):
        """
        Create a JWT access token.
        
        :param data: A dictionary containing the data to be encoded in the token.
        :param expires_delta: An optional timedelta for the token's expiration time.
                            If not provided, the token will expire in 15 minutes.
        :return: A JWT access token as a string.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=Auth.DEFAULT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        print(to_encode)
        encoded_jwt = jwt.encode(to_encode, Auth.JWT_SECRET_KEY, algorithm="HS256")
        return encoded_jwt