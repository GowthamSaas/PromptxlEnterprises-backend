from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.auth.security import get_password_hash
from app.auth.dependencies import get_current_active_user, require_owner, require_admin_or_owner

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Get all users in the tenant (Owner and Admin only)"""
    # Filter by tenant_id
    tenant_filter = User.tenant_id == current_user.tenant_id
    
    if current_user.role == UserRole.OWNER:
        return db.query(User).filter(tenant_filter).all()
    else:
        # Admin can see Users and themselves, but not Owner, within their tenant
        return db.query(User).filter(
            tenant_filter,
            User.role != UserRole.OWNER
        ).all()

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Get user by ID (must be in same tenant)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user is in same tenant
    if user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied: User not in your tenant")
    
    # Admin cannot view Owner details
    if current_user.role == UserRole.ADMIN and user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot access Owner account")
    
    return user

@router.post("/", response_model=UserResponse)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Create new user (Owner can create Admins and Users, Admin can only create Users)"""
    # Check if email already exists
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Admins cannot create Admins or Owners
    if current_user.role == UserRole.ADMIN and user.role in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(status_code=403, detail="Admins can only create User accounts")
    
    # No one can create another Owner
    if user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot create Owner account")
    
    db_user = User(
        email=user.email,
        hashed_password=get_password_hash(user.password),
        full_name=user.full_name,
        role=user.role,
        is_active=True,
        created_by=current_user.id,
        tenant_id=current_user.tenant_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Update user (must be in same tenant)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user is in same tenant
    if db_user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied: User not in your tenant")
    
    # Admin cannot modify Owner
    if current_user.role == UserRole.ADMIN and db_user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot modify Owner account")
    
    # Admin cannot promote to Admin or Owner
    if current_user.role == UserRole.ADMIN and user_update.role in [UserRole.ADMIN, UserRole.OWNER]:
        raise HTTPException(status_code=403, detail="Cannot promote to Admin or Owner")
    
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):
    """Delete user (must be in same tenant)"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify user is in same tenant
    if db_user.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied: User not in your tenant")
    
    # Cannot delete Owner
    if db_user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot delete Owner account")
    
    # Admin cannot delete other Admins
    if current_user.role == UserRole.ADMIN and db_user.role == UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admins cannot delete other Admins")
    
    db.delete(db_user)
    db.commit()
    return {"message": "User deleted successfully"}
