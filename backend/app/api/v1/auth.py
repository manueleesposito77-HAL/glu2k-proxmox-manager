from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import LoginRequest, TokenResponse, UserCreate, UserResponse, UserUpdate, UserBase
from app.core.security import verify_password, create_access_token, hash_password, get_current_user, require_admin
from typing import List

router = APIRouter()

VALID_ROLES = {"admin", "operator", "viewer"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenziali non valide")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Utente disattivato")
    token = create_access_token({"sub": str(user.id), "role": user.role, "username": user.username})
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


# --- User management (solo admin) ---
@router.get("/users", response_model=List[UserResponse])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    return db.query(User).all()


@router.post("/users", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    if payload.role not in VALID_ROLES:
        raise HTTPException(status_code=400, detail="Ruolo non valido")
    if db.query(User).filter(User.username == payload.username).first():
        raise HTTPException(status_code=400, detail="Username già esistente")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        role=payload.role,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), _admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    if payload.role is not None:
        if payload.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="Ruolo non valido")
        user.role = payload.role
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Non puoi eliminare te stesso")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utente non trovato")
    db.delete(user)
    db.commit()
    return {"status": "deleted"}
