from fastapi import Depends, HTTPException
from jose import jwt, JWTError
from src.models import User
from src.database import session_opener
from fastapi.security import OAuth2PasswordBearer
from src.config import Auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=Auth.TOKER_URL)

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    user_db = Depends(session_opener)
):
    """
    Authenticate a user based on the provided JWT token.

    :param token: The JWT token provided by the user, injected by FastAPI.
    :param user_db: The database session dependency, injected by FastAPI.
    :return: The authenticated user object if the token is valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, Auth.JWT_SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token is invalid")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate token")
    
    user = user_db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user