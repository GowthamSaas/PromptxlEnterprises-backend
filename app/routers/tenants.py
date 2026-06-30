from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
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

@router.delete("/{tenant_id}")
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    db_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not db_tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    db.delete(db_tenant)
    db.commit()
    return {"detail": "Tenant deleted"}

@router.get("/", response_model=List[TenantResponse])
def list_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_superadmin)
):
    return db.query(Tenant).all()
