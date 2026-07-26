from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import (
    SESSION_COOKIE,
    CurrentUser,
    clear_session_cookie,
    create_session,
    dummy_password_check,
    hash_password,
    revoke_other_sessions,
    revoke_session,
    set_session_cookie,
    verify_password,
)
from ..db import get_db
from ..models import Family, Traveler, User
from ..schemas.auth import (
    AuthStatus,
    BootstrapRequest,
    LoginRequest,
    MeRead,
    PasswordChange,
    UserSettingsUpdate,
)
from ..services.categories import ensure_default_categories

router = APIRouter(tags=["auth"])


def _me(user: User) -> dict:
    return {"user": user, "traveler": user.traveler, "family": user.traveler.family}


def _find_user(db: Session, username: str) -> User | None:
    return db.scalar(
        select(User).where(func.lower(User.username) == username.strip().lower())
    )


@router.get("/auth/status", response_model=AuthStatus)
def auth_status(db: Session = Depends(get_db)):
    """Público: la pantalla de login decide si ofrecer el alta del primer admin."""
    count = db.scalar(select(func.count(User.id)))
    return {"bootstrapped": bool(count)}


@router.post("/auth/bootstrap", response_model=MeRead, status_code=201)
def bootstrap(payload: BootstrapRequest, response: Response, db: Session = Depends(get_db)):
    """Crea la cuenta admin inicial (solo con la instancia sin usuarios).

    Reutiliza la familia existente (instancia migrada) o crea una por defecto,
    y reutiliza el viajero por nombre para poder reclamar uno pre-existente.
    """
    if db.scalar(select(func.count(User.id))):
        raise HTTPException(status_code=409, detail="La instancia ya tiene usuarios")
    family = db.scalar(select(Family).order_by(Family.id).limit(1))
    if family is None:
        family = Family(name="Familia")
        db.add(family)
        db.flush()
    traveler = db.scalar(
        select(Traveler).where(
            func.lower(Traveler.name) == payload.traveler_name.lower()
        )
    )
    if traveler is None:
        traveler = Traveler(name=payload.traveler_name, family_id=family.id)
        db.add(traveler)
        db.flush()
    elif traveler.family_id is None:
        traveler.family_id = family.id
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_admin=True,
        traveler_id=traveler.id,
        language=payload.language or "en",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    ensure_default_categories(db, family.id)
    set_session_cookie(response, create_session(db, user))
    return _me(user)


@router.post("/auth/login", response_model=MeRead)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = _find_user(db, payload.username)
    if user is None:
        dummy_password_check(payload.password)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    set_session_cookie(response, create_session(db, user))
    return _me(user)


@router.post("/auth/logout", status_code=204)
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        revoke_session(db, token)
    clear_session_cookie(response)


@router.get("/auth/me", response_model=MeRead)
def me(user: CurrentUser):
    return _me(user)


@router.patch("/auth/me/settings", response_model=MeRead)
def update_settings(
    payload: UserSettingsUpdate, user: CurrentUser, db: Session = Depends(get_db)
):
    for key, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return _me(user)


@router.post("/auth/me/password", status_code=204)
def change_password(
    payload: PasswordChange,
    request: Request,
    user: CurrentUser,
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    # cerrar las demás sesiones abiertas (posible robo de sesión) conservando esta
    revoke_other_sessions(db, user.id, request.cookies.get(SESSION_COOKIE))
