from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from database.core import get_db
from database.User import User
from utils.schemas.schema import UserCreate, UserCreateResponse, Token
from utils.security import hash_password, verify_password, create_access_token
from utils.logger import logger

router = APIRouter(prefix="/auth", tags=["Auth"])


# === REGISTER ===
@router.post("/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        logger.warning(
            "Registration failed: Username already taken",
            username=user_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists."
        )

    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        "User registered successfully",
        user_id=new_user.id,
        username=new_user.username
    )
    return new_user


# === LOGIN ===
@router.post("/login", response_model=Token)
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(
            "Failed login attempt",
            username=form_data.username
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.username})

    logger.info(
        "User logged in successfully",
        user_id=user.id,
        username=user.username
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }