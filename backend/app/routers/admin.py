"""Gestión de usuarios (solo admin; el candado lo pone include_router)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import hash_password, revoke_other_sessions
from ..db import get_db
from ..models import Family, Traveler, User
from ..schemas.admin import PasswordReset, UserAdminRead, UserCreate, UserUpdate
from .common import get_or_404

router = APIRouter(tags=["admin"])


def _admin_count(db: Session) -> int:
    return db.scalar(select(func.count(User.id)).where(User.is_admin == True)) or 0  # noqa: E712


@router.get("/users", response_model=list[UserAdminRead])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.username)).all()


@router.post("/users", response_model=UserAdminRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    duplicate = db.scalar(
        select(User).where(func.lower(User.username) == payload.username.lower())
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Ya existe ese nombre de usuario")
    if payload.traveler_id is not None:
        traveler = get_or_404(db, Traveler, payload.traveler_id)
    else:
        name = (payload.traveler_name or "").strip()
        traveler = db.scalar(
            select(Traveler).where(func.lower(Traveler.name) == name.lower())
        )
        if traveler is None:
            traveler = Traveler(name=name)
            db.add(traveler)
            db.flush()
    if traveler.user is not None:
        raise HTTPException(status_code=409, detail="Ese viajero ya tiene una cuenta")
    if payload.family_id is not None:
        get_or_404(db, Family, payload.family_id)
        traveler.family_id = payload.family_id
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
        traveler_id=traveler.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserAdminRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = get_or_404(db, User, user_id)
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_admin") is False and user.is_admin and _admin_count(db) <= 1:
        raise HTTPException(
            status_code=409, detail="No puedes quitar el último administrador"
        )
    for key, value in data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/users/{user_id}/password", status_code=204)
def reset_password(user_id: int, payload: PasswordReset, db: Session = Depends(get_db)):
    user = get_or_404(db, User, user_id)
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    # el reset cierra todas sus sesiones abiertas
    revoke_other_sessions(db, user.id, None)


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Borra la cuenta; su viajero queda como virtual (conserva familia y avatar)."""
    user = get_or_404(db, User, user_id)
    if user.is_admin and _admin_count(db) <= 1:
        raise HTTPException(
            status_code=409, detail="No puedes borrar al último administrador"
        )
    db.delete(user)  # las sesiones caen por CASCADE
    db.commit()
