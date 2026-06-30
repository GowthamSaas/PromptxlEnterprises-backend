from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.models.application import Application
from app.models.user_application import UserApplication
from app.schemas.assignment import AssignmentCreate, AssignmentResponse
from app.auth.dependencies import require_admin_or_owner

router = APIRouter()

@router.get("/user/{user_id}", response_model=List[AssignmentResponse])
def get_user_assignments(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Get all application assignments for a user"""
    return db.query(UserApplication).filter(UserApplication.user_id == user_id).all()

@router.get("/application/{app_id}", response_model=List[AssignmentResponse])
def get_application_assignments(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Get all user assignments for an application"""
    return db.query(UserApplication).filter(UserApplication.application_id == app_id).all()

@router.post("/", response_model=List[AssignmentResponse])
def assign_applications(
    assignment: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Assign multiple applications to a user (must be in same tenant)"""
    # Verify user exists and is in the same tenant
    user = db.query(User).filter(User.id == assignment.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied: User not in your tenant")
    
    # Admin cannot assign apps to Owner
    if current_user.role == UserRole.ADMIN and user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot assign apps to Owner")
    
    created_assignments = []
    for app_id in assignment.application_ids:
        # Check if application exists and belongs to the tenant
        app = db.query(Application).filter(
            Application.id == app_id,
            Application.tenant_id == current_user.tenant_id
        ).first()
        if not app:
            continue
        
        # Check if assignment already exists
        existing = db.query(UserApplication).filter(
            UserApplication.user_id == assignment.user_id,
            UserApplication.application_id == app_id
        ).first()
        
        if not existing:
            db_assignment = UserApplication(
                user_id=assignment.user_id,
                application_id=app_id,
                assigned_by=current_user.id
            )
            db.add(db_assignment)
            created_assignments.append(db_assignment)
    
    db.commit()
    for a in created_assignments:
        db.refresh(a)
    
    return created_assignments

@router.delete("/{user_id}/{app_id}")
def remove_assignment(
    user_id: int,
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Remove application assignment from user"""
    assignment = db.query(UserApplication).filter(
        UserApplication.user_id == user_id,
        UserApplication.application_id == app_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    db.delete(assignment)
    db.commit()
    return {"message": "Assignment removed successfully"}
