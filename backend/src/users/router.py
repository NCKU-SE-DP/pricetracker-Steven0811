from datetime import timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.models import User
from src.database import session_opener
from src.auth.service import check_user_password_is_correct, create_access_token, pwd_context
from src.auth.schemas import UserAuthSchema
from fastapi import APIRouter
from src.auth.dependencies import authenticate_user_token
from src.config import Auth


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)
@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), user_db: Session = Depends(session_opener)
):
    """login"""
    user = check_user_password_is_correct(user_db, form_data.username, form_data.password)
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def create_user(user: UserAuthSchema, user_db: Session = Depends(session_opener)):
    """create user"""
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    user_db.add(new_user)
    user_db.commit()
    user_db.refresh(new_user)
    return new_user

@router.get("/api/v1/users/me")
def read_users_me(user=Depends(authenticate_user_token)):
    return {"username": user.username}