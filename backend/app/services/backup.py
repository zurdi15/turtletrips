"""Backup/restore completo: DB (snapshot consistente) + uploads en un ZIP.

El snapshot usa el API de backup de sqlite3 sobre la conexión del propio
engine — nunca se copia el fichero a pelo (WAL podría dejarlo corrupto).
"""

import json
import os
import re
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..config import get_settings
from ..db import make_engine, make_sessionmaker
from .categories import ensure_default_categories_all

BACKEND_DIR = Path(__file__).resolve().parents[2]
# formato 2 = multi-usuario (avatares en uploads/avatars/); los ZIP formato 1
# restauran igual: la compatibilidad real la marca la revisión de alembic
BACKUP_FORMAT = 2
MAX_RESTORE_BYTES = 1024**3  # 1 GiB comprimido
MAX_EXTRACTED_BYTES = 4 * 1024**3  # 4 GiB descomprimido (anti zip-bomb)
_UPLOAD_ENTRY = re.compile(r"^uploads/(\d+|avatars|world)/[^/\\]+$")


class BackupValidationError(Exception):
    pass


class BackupBusyError(Exception):
    pass


def _alembic_config() -> Config:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    return cfg


def _db_revision(db_path: Path) -> str | None:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        try:
            row = conn.execute("SELECT version_num FROM alembic_version").fetchone()
        except sqlite3.OperationalError:
            return None  # DB sin alembic (p. ej. creada con create_all)
        return row[0] if row else None
    finally:
        conn.close()


def snapshot_db(engine: Engine, target: Path) -> None:
    """Copia consistente de la DB del engine (correcta con WAL activo)."""
    raw = engine.raw_connection()
    try:
        dst = sqlite3.connect(target)
        try:
            raw.driver_connection.backup(dst)
        finally:
            dst.close()
    finally:
        raw.close()


def create_backup_zip(engine: Engine) -> Path:
    """Crea el ZIP de backup en data_dir y devuelve su ruta (temporal)."""
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=settings.data_dir, prefix="backup-", suffix=".zip")
    os.close(fd)
    zip_path = Path(tmp_name)

    with tempfile.TemporaryDirectory(dir=settings.data_dir) as workdir:
        db_snapshot = Path(workdir) / "app.db"
        snapshot_db(engine, db_snapshot)
        manifest = {
            "app": "turtle-trips",
            "format": BACKUP_FORMAT,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "alembic_revision": _db_revision(db_snapshot),
        }
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(db_snapshot, "app.db", compress_type=zipfile.ZIP_DEFLATED)
            zf.writestr("manifest.json", json.dumps(manifest))
            uploads = settings.uploads_dir
            if uploads.is_dir():
                for path in sorted(uploads.rglob("*")):
                    if path.is_file():
                        arcname = f"uploads/{path.relative_to(uploads)}"
                        # PDFs/imágenes ya comprimidos: STORED evita CPU inútil
                        zf.write(path, arcname, compress_type=zipfile.ZIP_STORED)
    return zip_path


def validate_backup_zip(zip_path: Path) -> str | None:
    """Valida el ZIP y devuelve la revisión alembic de su DB (o None)."""
    if not zipfile.is_zipfile(zip_path):
        raise BackupValidationError("El fichero no es un ZIP válido")
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        if "app.db" not in names:
            raise BackupValidationError("La copia no contiene app.db")
        total = 0
        for info in zf.infolist():
            name = info.filename
            if name.startswith("/") or ".." in name.split("/"):
                raise BackupValidationError(f"Ruta sospechosa en la copia: {name}")
            if name not in ("app.db", "manifest.json") and not _UPLOAD_ENTRY.match(name):
                raise BackupValidationError(f"Entrada inesperada en la copia: {name}")
            total += info.file_size
            if total > MAX_EXTRACTED_BYTES:
                raise BackupValidationError("La copia descomprimida es demasiado grande")

        with tempfile.TemporaryDirectory() as workdir:
            db_path = Path(workdir) / "app.db"
            with zf.open("app.db") as src, open(db_path, "wb") as dst:
                shutil.copyfileobj(src, dst)
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            try:
                result = conn.execute("PRAGMA quick_check").fetchone()
            except sqlite3.DatabaseError as exc:
                raise BackupValidationError("La base de datos de la copia está corrupta") from exc
            finally:
                conn.close()
            if result is None or result[0] != "ok":
                raise BackupValidationError("La base de datos de la copia está corrupta")
            revision = _db_revision(db_path)

    if revision is not None:
        script = ScriptDirectory.from_config(_alembic_config())
        try:
            script.get_revision(revision)
        except Exception as exc:
            raise BackupValidationError(
                "La copia es de una versión más nueva de la app "
                f"(revisión {revision} desconocida); actualiza antes de restaurar"
            ) from exc
    return revision


def _move_if_exists(src: Path, dst_dir: Path) -> None:
    if src.exists():
        shutil.move(str(src), str(dst_dir / src.name))


def restore_backup(app: FastAPI, zip_path: Path) -> dict:
    """Sustituye TODOS los datos por los del ZIP (ya validado).

    El estado anterior queda en data_dir/pre-restore como red de seguridad;
    si algo falla a mitad, se restaura y se relanza la excepción.
    """
    lock = app.state.backup_lock
    if not lock.acquire(blocking=False):
        raise BackupBusyError("Ya hay una restauración en curso")
    settings = get_settings()
    data_dir = settings.data_dir
    pre_restore = data_dir / "pre-restore"
    try:
        app.state.engine.dispose()

        if pre_restore.exists():
            shutil.rmtree(pre_restore)
        pre_restore.mkdir(parents=True)
        for name in ("app.db", "app.db-wal", "app.db-shm"):
            _move_if_exists(data_dir / name, pre_restore)
        _move_if_exists(settings.uploads_dir, pre_restore)

        try:
            with zipfile.ZipFile(zip_path) as zf:
                for info in zf.infolist():
                    name = info.filename
                    if name == "manifest.json" or name.endswith("/"):
                        continue
                    target = (
                        settings.db_path if name == "app.db" else data_dir / name
                    )
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(info) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            previous_revision = _db_revision(settings.db_path)
            cfg = _alembic_config()
            if previous_revision is None:
                # DB sin tabla alembic (backup de un entorno create_all): el
                # esquema ya es el actual, solo hay que marcarlo
                command.stamp(cfg, "head")
            else:
                command.upgrade(cfg, "head")

            engine = make_engine(settings.db_url)
            app.state.engine = engine
            app.state.sessionmaker = make_sessionmaker(engine)
            with app.state.sessionmaker() as session:
                ensure_default_categories_all(session)
                trips = session.execute(text("SELECT count(*) FROM trips")).scalar()
            return {
                "restored": True,
                "trips": int(trips or 0),
                "previous_revision": previous_revision,
            }
        except Exception:
            # deshacer: borrar lo extraído y devolver el estado anterior
            for name in ("app.db", "app.db-wal", "app.db-shm"):
                (data_dir / name).unlink(missing_ok=True)
            shutil.rmtree(settings.uploads_dir, ignore_errors=True)
            for child in pre_restore.iterdir():
                shutil.move(str(child), str(data_dir / child.name))
            engine = make_engine(settings.db_url)
            app.state.engine = engine
            app.state.sessionmaker = make_sessionmaker(engine)
            raise
    finally:
        lock.release()
