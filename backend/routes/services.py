from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database.core import get_db
from database.Service import Service
from database.User import User
from utils.schemas.schema import ServiceCreate, ServiceResponse, ServiceUpdate
from utils.security import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])

@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_service = Service(**service_data.model_dump(), user_id=current_user.id)
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service


@router.get("/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Service).filter(Service.user_id == current_user.id).all()


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Serwis nie został znaleziony.")
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(service_id: int, service_data: ServiceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Serwis nie został znaleziony.")

    update_data = service_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "url":
            value = str(value)
        setattr(service, key, value)

    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Serwis nie został znaleziony.")

    db.delete(service)
    db.commit()
    return None