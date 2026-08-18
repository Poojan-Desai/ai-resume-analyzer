"""
Application tracking CRUD.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application
from app.schemas import ApplicationCreate, ApplicationOut, ApplicationUpdate

router = APIRouter(prefix="/applications", tags=["applications"])


@router.post("", response_model=ApplicationOut)
def create_application(body: ApplicationCreate, db: Session = Depends(get_db)):
    row = Application(
        company_name=body.company_name,
        role_title=body.role_title,
        status=body.status,
        notes=body.notes,
        job_url=body.job_url,
        resume_id=body.resume_id,
        job_posting_id=body.job_posting_id,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[ApplicationOut])
def list_applications(db: Session = Depends(get_db)):
    return db.query(Application).order_by(Application.updated_at.desc()).all()


@router.get("/{app_id}", response_model=ApplicationOut)
def get_application(app_id: int, db: Session = Depends(get_db)):
    row = db.get(Application, app_id)
    if not row:
        raise HTTPException(status_code=404, detail="Application not found.")
    return row


@router.patch("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: int, body: ApplicationUpdate, db: Session = Depends(get_db)
):
    row = db.get(Application, app_id)
    if not row:
        raise HTTPException(status_code=404, detail="Application not found.")

    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{app_id}", status_code=204)
def delete_application(app_id: int, db: Session = Depends(get_db)):
    row = db.get(Application, app_id)
    if not row:
        raise HTTPException(status_code=404, detail="Application not found.")
    db.delete(row)
    db.commit()
    return None
