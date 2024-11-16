from fastapi import Depends
from jose import jwt
from src.models import User
from src.database import session_opener
from fastapi.security import OAuth2PasswordBearer
from src.config import Auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=Auth.TOKER_URL)
class AuthDependency(Auth):
    def __init__(self):
        super().__init__()

    def authenticate_user_token(
        self,
        token = Depends(oauth2_scheme),
        user_db = Depends(session_opener)
    ):
        """
        Authenticate a user based on the provided JWT token.

        :param token: The JWT token provided by the user, injected by FastAPI.
        :param user_db: The database session dependency, injected by FastAPI.
        :return: The authenticated user object if the token is valid, None otherwise.
        """
        payload = jwt.decode(token, self.JWT_SECRET_KEY, algorithms=["HS256"])
        return user_db.query(User).filter(User.username == payload.get("sub")).first()