import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..auth import (
    SESSION_COOKIE,
    CurrentUser,
    clear_password_resets,
    clear_session_cookie,
    create_password_reset,
    create_session,
    dummy_password_check,
    hash_password,
    resolve_reset_token,
    revoke_other_sessions,
    revoke_session,
    set_session_cookie,
    verify_password,
)
from ..config import get_settings
from ..db import get_db
from ..models import Family, Traveler, User
from ..schemas.auth import (
    AuthStatus,
    BootstrapRequest,
    LoginRequest,
    MeRead,
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetInfo,
    PasswordResetRequest,
    UserSettingsUpdate,
)
from ..services.categories import ensure_default_categories

router = APIRouter(tags=["auth"])
logger = logging.getLogger("tt.auth")

# el enlace de recuperación es la única "notificación" de la app y sale por los
# logs: enmarcado para encontrarlo de un vistazo en `docker logs`
_BANNER = "─" * 64


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


def _reset_link(request: Request, token: str) -> str:
    """URL absoluta del formulario de contraseña nueva.

    El Origin de la petición es la URL pública real con la que se está usando
    la app; detrás de un reverse proxy `base_url` solo conoce el puerto
    interno, así que queda de respaldo (peticiones sin cabecera).
    """
    origin = request.headers.get("origin") or str(request.base_url).rstrip("/")
    return f"{origin}/reset-password?token={token}"


def _log_reset_link(username: str, link: str, expires_at: datetime) -> None:
    logger.warning(
        "\n%s\n Turtle Trips · recuperación de contraseña\n"
        " Usuario: %s\n Enlace:  %s\n Caduca:  %s UTC (%d min)\n%s",
        _BANNER,
        username,
        link,
        expires_at.strftime("%Y-%m-%d %H:%M"),
        get_settings().password_reset_ttl_minutes,
        _BANNER,
    )


@router.post("/auth/forgot-password", status_code=204)
def forgot_password(
    payload: PasswordResetRequest, request: Request, db: Session = Depends(get_db)
):
    """Genera el enlace de recuperación y lo escribe EN LOS LOGS del servidor.

    No hay correo saliente: en una instancia self-hosted el admin lee el
    enlace (`docker logs`) y se lo pasa al usuario. La respuesta es siempre la
    misma exista o no la cuenta, para no filtrar qué usuarios hay.
    """
    user = _find_user(db, payload.username)
    if user is None:
        logger.info(
            "Recuperación de contraseña pedida para un usuario inexistente (%r)",
            payload.username.strip()[:50],
        )
        return
    token, expires_at = create_password_reset(db, user)
    _log_reset_link(user.username, _reset_link(request, token), expires_at)


@router.get("/auth/reset-password", response_model=PasswordResetInfo)
def check_reset_token(token: str, db: Session = Depends(get_db)):
    """Valida el enlace ANTES de pedir la contraseña nueva: uno caducado da un
    mensaje claro en vez de un formulario que falla al enviarlo."""
    entry = resolve_reset_token(db, token)
    if entry is None:
        raise HTTPException(
            status_code=400, detail="El enlace no es válido o ha caducado"
        )
    return {"username": entry.user.username}


@router.post("/auth/reset-password", response_model=MeRead)
def reset_password(
    payload: PasswordResetConfirm, response: Response, db: Session = Depends(get_db)
):
    """Estrena la contraseña y deja la sesión abierta (el usuario ya se ha
    identificado con el enlace: pedirle el login otra vez sobra)."""
    entry = resolve_reset_token(db, payload.token)
    if entry is None:
        raise HTTPException(
            status_code=400, detail="El enlace no es válido o ha caducado"
        )
    user = entry.user
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    clear_password_resets(db, user.id)
    # fuera TODAS las sesiones anteriores: quien recupera la contraseña puede
    # estar echando a alguien que le entró en la cuenta
    revoke_other_sessions(db, user.id, None)
    logger.info("Contraseña restablecida para %r", user.username)
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
