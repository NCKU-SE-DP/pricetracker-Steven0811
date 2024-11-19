from datetime import timedelta
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from src.models import User
from src.database import session_opener
from src.auth.service import AuthService
from src.auth.schemas import UserAuthSchema
from fastapi import APIRouter
from src.auth.dependencies import AuthDependency
from src.config import Auth

class UsersRouter(AuthService, AuthDependency):
    def __init__(self):
        super().__init__()

        self.users_router = APIRouter(
            prefix="/users",
            tags=["users"],
            responses={404: {"description": "Not found"}},
        )
        
        @self.users_router.post("/login")
        async def login_for_access_token(
                form_data: OAuth2PasswordRequestForm = Depends(), user_db: Session = Depends(session_opener)
        ):
            """
            Authenticate the user and return an access token.

            :param form_data: The form data containing the user's login credentials,
                            injected by FastAPI.
            :return: A dictionary containing the access token and token type.
            """
            user = self.check_user_password_is_correct(user_db, form_data.username, form_data.password)
            access_token = self.create_access_token(
                data={"sub": str(user.username)}, expires_delta=timedelta(minutes=Auth.ACCESS_TOKEN_EXPIRE_MINUTES)
            )
            return {"access_token": access_token, "token_type": "bearer"}


        @self.users_router.post("/register")
        def create_user(user: UserAuthSchema, user_db: Session = Depends(session_opener)):
            """
            Create a new user in the database.
            
            :param user: The user details for creating a new user.
            :param db: The database session dependency, injected by FastAPI.
            :return: The created user object.
            """
            hashed_password = self.pwd_context.hash(user.password)
            new_user = User(username=user.username, hashed_password=hashed_password)
            user_db.add(new_user)
            user_db.commit()
            user_db.refresh(new_user)
            return new_user

        @self.users_router.get("/me")
        def read_users_me(user=Depends(self.authenticate_user_token)):
            return {"username": user.username}