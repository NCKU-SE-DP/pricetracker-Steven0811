from datetime import timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.models import User
from src.database import session_opener
from src.auth.service import check_user_password_is_correct, create_access_token, pwd_context
from src.auth.schemas import UserAuthSchema
from fastapi import APIRouter, HTTPException
from src.auth.dependencies import authenticate_user_token
from src.config import Auth
from src.error_handler.logger import Logger

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

@router.post("/login")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(), user_db: Session = Depends(session_opener)
):
    """
    Authenticate the user and return an access token.

    :param form_data: The form data containing the user's login credentials,
                      injected by FastAPI.
    :return: A dictionary containing the access token and token type.
    """
    logger = Logger(__name__, "login_for_access_token").get_logger()
    user = check_user_password_is_correct(user_db, form_data.username, form_data.password)   
    access_token = create_access_token(
        data={"sub": str(user.username)}, expires_delta=timedelta(minutes=Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    logger.debug(f"User {user.username} logged in successfully.")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
def create_user(user: UserAuthSchema, user_db: Session = Depends(session_opener)):
    """
    Create a new user in the database.
    
    :param user: The user details for creating a new user.
    :param db: The database session dependency, injected by FastAPI.
    :return: The created user object.
    """
    logger = Logger(__name__, "create_user").get_logger()
    existing_user = user_db.query(User).filter(User.username == user.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists.")
    
    hashed_password = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed_password)
    user_db.add(new_user)
    user_db.commit()
    user_db.refresh(new_user)
    logger.debug(f"User {new_user.username} created successfully.")
    return new_user

@router.get("/me")
def read_users_me(user=Depends(authenticate_user_token)):
    logger = Logger(__name__, "read_users_me").get_logger()
    logger.debug(f"User {user.username} accessed their profile)")
    return {"username": user.username}