from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.models.application import Application
from app.models.user_application import UserApplication
from app.schemas.tenant import TenantBase, TenantCreate, TenantResponse
from app.auth.dependencies import require_owner, require_superadmin
from app.models.user import UserRole
from app.auth.security import get_password_hash

router = APIRouter()

@router.post("/", response_model=TenantResponse)
def create_tenant(
    tenant: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    """Create a new tenant and associate it with the owner who is creating it."""
    existing = db.query(Tenant).filter(Tenant.tenant_id == tenant.tenant_id).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant ID already exists")

    db_tenant = Tenant(
        tenant_id=tenant.tenant_id,
        company_name=tenant.company_name,
        contact_email=tenant.contact_email,
        contact_phone=tenant.contact_phone,
        address=tenant.address,
        created_by=current_user.id
    )
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    owner_user = User(
        email=tenant.owner_email,
        hashed_password=get_password_hash(tenant.owner_password),
        full_name=tenant.owner_full_name,
        role=UserRole.OWNER,
        is_active=True,
        created_by=current_user.id
    )
    # Set the tenant relationship
    owner_user.tenant = db_tenant
    
    db.add(owner_user)
    db.flush()  # Flush to ensure the user is created before commit
    db.commit()
    db.refresh(owner_user)
    
    # Verify tenant_id was assigned
    print(f"DEBUG: Created owner user {owner_user.email} with tenant_id={owner_user.tenant_id} (expected={db_tenant.id})")
    
    return db_tenant

@router.put("/{tenant_id}", response_model=TenantResponse)
def update_tenant(
    tenant_id: int,
    tenant: TenantBase,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    db_tenant.company_name = tenant.company_name
    db_tenant.contact_email = tenant.contact_email
    db_tenant.contact_phone = tenant.contact_phone
    db_tenant.address = tenant.address
    db.commit()
    db.refresh(db_tenant)
    return db_tenant

@router.delete("/{tenant_identifier}")
def delete_tenant(
    tenant_identifier: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    # Allow deletion by numeric DB id or by tenant_id string
    db_tenant = None
    # try numeric id first
    try:
        numeric_id = int(tenant_identifier)
        db_tenant = db.query(Tenant).filter(Tenant.id == numeric_id).first()
    except ValueError:
        numeric_id = None

    if not db_tenant:
        # try tenant_id string match
        db_tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_identifier).first()

    if not db_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    try:
        # Delete related records in proper order to avoid FK constraint errors:
        # 1) Remove user-application assignments for applications belonging to this tenant
        app_ids_subq = db.query(Application.id).filter(Application.tenant_id == db_tenant.id)
        db.query(UserApplication).filter(UserApplication.application_id.in_(app_ids_subq)).delete(synchronize_session=False)

        # 2) Remove assignments for users belonging to this tenant
        user_ids_subq = db.query(User.id).filter(User.tenant_id == db_tenant.id)
        db.query(UserApplication).filter(UserApplication.user_id.in_(user_ids_subq)).delete(synchronize_session=False)

        # 3) Remove applications belonging to this tenant
        db.query(Application).filter(Application.tenant_id == db_tenant.id).delete(synchronize_session=False)

        # 4) Remove users belonging to this tenant
        db.query(User).filter(User.tenant_id == db_tenant.id).delete(synchronize_session=False)

        # 5) Finally remove the tenant
        db.delete(db_tenant)
        db.commit()
        return {"detail": "Tenant deleted"}
    except Exception as exc:
        db.rollback()
        # Provide more informative error for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

@router.get("/", response_model=List[TenantResponse])
def list_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    return db.query(Tenant).all()
