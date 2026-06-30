from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse ,ChangePasswordRequest
from app.schemas.token import Token
from app.auth.security import verify_password, get_password_hash, create_access_token
from app.auth.dependencies import get_current_active_user
from app.config import settings

router = APIRouter()

@router.post("/register", response_model=UserResponse, include_in_schema=False)
def register_owner(user: UserCreate, db: Session = Depends(get_db)):
    """Manual registration is disabled for this application."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Registration is disabled. Set SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD in .env and restart the backend."
    )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login and get access token"""
    user = db.query(User).filter(User.email == form_data.username).first()
    print(f"DEBUG: Login attempt for {form_data.username}, user found: {user is not None}")
    if user:
        pwd_match = verify_password(form_data.password, user.hashed_password)
        print(f"DEBUG: Password match: {pwd_match}")
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user cannot login"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token)

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current logged-in user info"""
    return current_user


@router.put("/change-password")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # Verify old password
    if not verify_password(
        data.old_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Old password is incorrect"
        )

    # Prevent same password
    if verify_password(
        data.new_password,
        current_user.hashed_password
    ):
        raise HTTPException(
            status_code=400,
            detail="New password cannot be same as old password"
        )

    current_user.hashed_password = get_password_hash(
        data.new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully"
    }
