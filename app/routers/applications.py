from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.models.application import Application
from app.models.user_application import UserApplication
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.auth.dependencies import get_current_active_user, require_admin_or_owner

router = APIRouter()

# @router.get("/", response_model=List[ApplicationResponse])
# def get_applications(
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_active_user)
# ):
#     """Get applications (Users see only assigned active apps, Admin/Owner see tenant apps)"""
#     if current_user.role in [UserRole.OWNER, UserRole.ADMIN]:
#         # Owner/Admin see applications they created within their tenant
#         return db.query(Application).filter(
#             Application.created_by == current_user.id
#         ).all()
#     else:
#         # User: only assigned active applications
#         return db.query(Application).join(UserApplication).filter(
#             UserApplication.user_id == current_user.id,
#             Application.is_active == True
#         ).all()


@router.get("/", response_model=List[ApplicationResponse])
def get_applications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Owner/Admin -> See all applications in same tenant
    User -> See only assigned applications
    """

    if current_user.role in [UserRole.OWNER, UserRole.ADMIN]:
        return db.query(Application).filter(
            Application.tenant_id == current_user.tenant_id
        ).all()

    return db.query(Application).join(UserApplication).filter(
        UserApplication.user_id == current_user.id,
        Application.is_active == True
    ).all()

@router.get("/{app_id}", response_model=ApplicationResponse)
def get_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get application by ID"""
    application = db.query(Application).filter(Application.id == app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Users can only see assigned apps
    if current_user.role == UserRole.USER:
        assignment = db.query(UserApplication).filter(
            UserApplication.user_id == current_user.id,
            UserApplication.application_id == app_id
        ).first()
        if not assignment or not application.is_active:
            raise HTTPException(status_code=403, detail="Access denied")
    
    return application

@router.post("/", response_model=ApplicationResponse)
def create_application(
    app: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Create new application (Owner and Admin only within their tenant)"""
    db_app = Application(
        name=app.name,
        description=app.description,
        icon_url=app.icon_url,
        launch_url=app.launch_url,
        is_active=True,
        created_by=current_user.id,
        tenant_id=current_user.tenant_id
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.put("/{app_id}", response_model=ApplicationResponse)
def update_application(
    app_id: int,
    app_update: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Update application"""
    db_app = db.query(Application).filter(Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    update_data = app_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_app, field, value)
    
    db.commit()
    db.refresh(db_app)
    return db_app

@router.delete("/{app_id}")
def delete_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Delete application"""
    db_app = db.query(Application).filter(Application.id == app_id).first()
    if not db_app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    db.delete(db_app)
    db.commit()
    return {"message": "Application deleted successfully"}
