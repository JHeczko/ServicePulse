from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import Check, Incident
from database.core import get_db
from database.Service import Service
from database.User import User
from utils.schemas import ServiceCreate, ServiceResponse, ServiceUpdate, CheckResponse, IncidentResponse
from utils.security import get_current_user

router = APIRouter(prefix="/services", tags=["Services"])

# ===== SERVICE ENDPOINTS =====
@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Tworzymy nowy obiekt modelu i jawnie przypisujemy wartości
    new_service = Service()
    new_service.name = service_data.name
    new_service.url = str(service_data.url)      # Bezpieczna, jawna konwersja HttpUrl -> str
    new_service.interval = service_data.interval
    new_service.user_id = current_user.id

    # 2. Zapis do bazy danych
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    # 3. Rejestracja zadania w schedulerze
    from main import scheduler, push_to_queue
    try:
        scheduler.add_job(
            push_to_queue,
            trigger="interval",
            seconds=new_service.interval,
            id=f"service_{new_service.id}",
            args=[new_service.id],
            replace_existing=True  # Dobra praktyka, zapobiega konfliktom ID w pamięci
        )
    except Exception as e:
        # Log błędu schedulera, żeby w razie problemów z APSchedulerem nie blokować zapisu do bazy
        print(f"Błąd podczas dodawania jobu do schedulera dla serwisu {new_service.id}: {e}")

    return new_service


@router.get("/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Service).filter(Service.user_id == current_user.id).all()


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    service = (db.query(Service).
               filter(Service.id == service_id,Service.user_id == current_user.id).
               first())

    if not service:
        raise HTTPException(status_code=404, detail="Serwis nie został znaleziony.")

    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(service_id: int, service_data: ServiceUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Szukamy serwisu w bazie
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Serwis nie został znaleziony.")

    # 2. Ręczne, jawne przypisywanie parametrów po kolei
    if service_data.name is not None:
        service.name = service_data.name

    if service_data.url is not None:
        print(f"[INFO] {str(service_data.url)}")
        service.url = str(service_data.url)  # Od razu bezpiecznie rzutujemy obiekt HttpUrl na string

    if service_data.interval is not None:
        service.interval = service_data.interval

    # 3. Zapis zmian w bazie
    db.commit()
    db.refresh(service)

    # 4. Przeładowanie jobu w schedulerze z aktualnymi danymi serwisu
    from main import scheduler, push_to_queue
    try:
        scheduler.add_job(
            push_to_queue,
            trigger="interval",
            seconds=service.interval,  # Zawsze bierze aktualną wartość (nową lub starą)
            id=f"service_{service.id}",
            args=[service.id],
            replace_existing=True      # Bezwarunkowo nadpisuje konfigurację zadania
        )
    except Exception as e:
        print(f"Błąd podczas aktualizacji schedulera dla serwisu {service.id}: {e}")

    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from main import scheduler

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Serwis nie został znaleziony.")

    db.delete(service)
    db.commit()

    try:
        scheduler.remove_job(f"service_{service_id}")
    except Exception:
        pass

    return None

# ===== CHECKS ENDPOINTS =====
@router.get("/{service_id}/checks", response_model=List[CheckResponse])
def get_service_checks(service_id: int, limit: int = 50, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Zapytanie uderza prosto w Twój świetny kompozytowy indeks!
    checks = db.query(Check).filter(
        Check.service_id == service_id,
        Check.user_id == current_user.id  # Błyskawiczna weryfikacja uprawnień
    ).order_by(Check.created_at.desc()).limit(limit).all()

    return checks


# ===== INCIDENTS ENDPOINTS =====
@router.get("/{service_id}/incidents", response_model=List[IncidentResponse])
def get_service_incidents(    service_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Incident).filter(
        Incident.service_id == service_id,
        Incident.user_id == current_user.id
    ).order_by(Incident.started_at.desc()).all()

@router.get("/incidents/active", response_model=List[IncidentResponse])
def get_active_incidents(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Incident).filter(
        Incident.user_id == current_user.id,
        Incident.ended_at.is_(None)
    ).order_by(Incident.started_at.desc()).all()