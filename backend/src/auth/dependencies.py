from fastapi import Depends
from jose import jwt
from src.models import User
from src.database import session_opener
from fastapi.security import OAuth2PasswordBearer
from src.config import Auth

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=Auth.TOKER_URL)

def authenticate_user_token(
    token = Depends(oauth2_scheme),
    user_db = Depends(session_opener)
):
    payload = jwt.decode(token, Auth.JWT_SECRET_KEY, algorithms=["HS256"])
    return user_db.query(User).filter(User.username == payload.get("sub")).first()