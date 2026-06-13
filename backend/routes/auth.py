from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Dopasuj import get_db do swojej dokładnej ścieżki w core
from database.core import get_db
from database.User import User
from utils.schemas import UserCreate, UserCreateResponse
from utils.security import hash_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Użytkownik o podanej nazwie już istnieje."
        )

    hashed_pwd = hash_password(user_data.password)
    new_user = User(
        username=user_data.username,
        hashed_password=hashed_pwd
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Pobieramy m.in. wygenerowane ID z bazy

    return new_user