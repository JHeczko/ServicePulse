from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import Check, Incident
from database.core import get_db
from database.Service import Service
from database.User import User
from utils.schemas import ServiceCreate, ServiceResponse, ServiceUpdate, CheckResponse, IncidentResponse
from utils.security import get_current_user
from utils.logger import logger
from tasks import scheduler, push_to_queue
router = APIRouter(prefix="/services", tags=["Services"])


# ===== SERVICE ENDPOINTS =====
@router.post("/", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(service_data: ServiceCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    new_service = Service()
    new_service.name = service_data.name
    new_service.url = str(service_data.url)
    new_service.interval = service_data.interval
    new_service.user_id = current_user.id

    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    try:
        scheduler.add_job(
            push_to_queue,
            trigger="interval",
            seconds=new_service.interval,
            id=f"service_{new_service.id}",
            args=[new_service.id],
            replace_existing=True
        )

    except Exception as e:
        logger.error(
            "Failed to add job to scheduler for service",
            service_id=new_service.id,
            error=str(e)
        )

    logger.info(
        "Service created successfully and scheduled",
        service_id=new_service.id,
        user_id=current_user.id,
        interval=new_service.interval
    )

    return new_service


@router.get("/", response_model=List[ServiceResponse])
def get_services(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    services = db.query(Service).filter(Service.user_id == current_user.id).all()

    # logger.info(
    #     "Fetched user services",
    #     user_id=current_user.id,
    #     count=len(services)
    # )
    return services


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service = (db.query(Service).
               filter(Service.id == service_id, Service.user_id == current_user.id).
               first())

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    # logger.info(
    #     "Fetched specific service details",
    #     service_id=service_id,
    #     user_id=current_user.id
    # )
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(service_id: int, service_data: ServiceUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service_data.name is not None:
        service.name = service_data.name

    if service_data.url is not None:
        service.url = str(service_data.url)

    if service_data.interval is not None:
        service.interval = service_data.interval

    db.commit()
    db.refresh(service)

    try:
        scheduler.add_job(
            push_to_queue,
            trigger="interval",
            seconds=service.interval,
            id=f"service_{service.id}",
            args=[service.id],
            replace_existing=True
        )
    except Exception as e:
        logger.error(
            "Failed to update scheduler job for service",
            service_id=service.id,
            error=str(e)
        )

    logger.info(
        "Service updated successfully and scheduler reloaded",
        service_id=service.id,
        user_id=current_user.id
    )

    return service


@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(service_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.user_id == current_user.id
    ).first()

    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    db.delete(service)
    db.commit()

    try:
        scheduler.remove_job(f"service_{service_id}")
    except Exception as e:
        logger.warning(
            "Could not remove job from scheduler or job did not exist",
            service_id=service_id,
            error=str(e)
        )

    logger.info(
        "Service deleted successfully and removed from scheduler",
        service_id=service_id,
        user_id=current_user.id
    )

    return None


# ===== CHECKS ENDPOINTS =====
@router.get("/{service_id}/checks", response_model=List[CheckResponse])
def get_service_checks(service_id: int, limit: int = 50, db: Session = Depends(get_db),
                       current_user=Depends(get_current_user)):
    checks = db.query(Check).filter(
        Check.service_id == service_id,
        Check.user_id == current_user.id
    ).order_by(Check.created_at.desc()).limit(limit).all()

    # logger.info(
    #     "Fetched history checks for service",
    #     service_id=service_id,
    #     user_id=current_user.id,
    #     limit=limit,
    #     count=len(checks)
    # )
    return checks


# ===== INCIDENTS ENDPOINTS =====
@router.get("/{service_id}/incidents", response_model=List[IncidentResponse])
def get_service_incidents(service_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    incidents = db.query(Incident).filter(
        Incident.service_id == service_id,
        Incident.user_id == current_user.id
    ).order_by(Incident.started_at.desc()).all()

    # logger.info(
    #     "Fetched all incidents for service",
    #     service_id=service_id,
    #     user_id=current_user.id,
    #     count=len(incidents)
    # )
    return incidents


@router.get("/incidents/active", response_model=List[IncidentResponse])
def get_active_incidents(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    active_incidents = db.query(Incident).filter(
        Incident.user_id == current_user.id,
        Incident.ended_at.is_(None)
    ).order_by(Incident.started_at.desc()).all()

    # logger.info(
    #     "Fetched active incidents",
    #     user_id=current_user.id,
    #     count=len(active_incidents)
    # )
    return active_incidents