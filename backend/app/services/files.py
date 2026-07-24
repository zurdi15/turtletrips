import shutil
import uuid
from pathlib import Path

import aiofiles
from fastapi import UploadFile

from ..config import get_settings

ALLOWED_CONTENT_TYPES = {"application/pdf"}
ALLOWED_PREFIXES = ("image/",)
MAX_SIZE_BYTES = 25 * 1024 * 1024


class FileValidationError(Exception):
    pass


def is_allowed_content_type(content_type: str | None) -> bool:
    if not content_type:
        return False
    return content_type in ALLOWED_CONTENT_TYPES or content_type.startswith(ALLOWED_PREFIXES)


def _trip_dir(trip_id: int) -> Path:
    return get_settings().uploads_dir / str(trip_id)


async def save_upload(trip_id: int, upload: UploadFile) -> tuple[str, int]:
    """Guarda el fichero subido y devuelve (stored_name, size_bytes)."""
    if not is_allowed_content_type(upload.content_type):
        raise FileValidationError("Solo se admiten PDFs e imágenes")

    suffix = Path(upload.filename or "").suffix.lower()[:10]
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    target_dir = _trip_dir(trip_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / stored_name

    size = 0
    try:
        async with aiofiles.open(target, "wb") as out:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_SIZE_BYTES:
                    raise FileValidationError("El fichero supera el tamaño máximo (25 MB)")
                await out.write(chunk)
    except FileValidationError:
        target.unlink(missing_ok=True)
        raise
    return stored_name, size


def resolve_stored_file(trip_id: int, stored_name: str) -> Path:
    """Ruta absoluta de un fichero guardado, a prueba de path traversal."""
    base = _trip_dir(trip_id).resolve()
    path = (base / stored_name).resolve()
    if not path.is_relative_to(base):
        raise FileValidationError("Ruta de fichero inválida")
    return path


def delete_stored_file(trip_id: int, stored_name: str) -> None:
    try:
        resolve_stored_file(trip_id, stored_name).unlink(missing_ok=True)
    except FileValidationError:
        pass


def delete_trip_files(trip_id: int) -> None:
    shutil.rmtree(_trip_dir(trip_id), ignore_errors=True)
