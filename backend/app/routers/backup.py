import os
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from ..config import get_settings
from ..schemas.backup import RestoreResult
from ..services import backup

router = APIRouter(tags=["backup"])

CHUNK = 1024 * 1024


@router.get("/backup/export")
def export_backup(request: Request):
    lock = request.app.state.backup_lock
    if not lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Hay una restauración en curso")
    try:
        zip_path = backup.create_backup_zip(request.app.state.engine)
    finally:
        lock.release()
    filename = f"turtle-trips-backup-{datetime.now():%Y%m%d-%H%M}.zip"
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=filename,
        background=BackgroundTask(os.unlink, zip_path),
    )


@router.post("/backup/restore", response_model=RestoreResult)
async def restore_backup(request: Request, file: UploadFile):
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=settings.data_dir, prefix="restore-", suffix=".zip"
    )
    tmp_path = Path(tmp_name)
    size = 0
    try:
        with os.fdopen(fd, "wb") as out:
            while chunk := await file.read(CHUNK):
                size += len(chunk)
                if size > backup.MAX_RESTORE_BYTES:
                    raise HTTPException(
                        status_code=413, detail="La copia supera el tamaño máximo (1 GB)"
                    )
                out.write(chunk)

        try:
            backup.validate_backup_zip(tmp_path)
        except backup.BackupValidationError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        try:
            result = backup.restore_backup(request.app, tmp_path)
        except backup.BackupBusyError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail="No se pudo restaurar la copia; se conservan los datos anteriores",
            ) from exc
        return RestoreResult(**result)
    finally:
        tmp_path.unlink(missing_ok=True)
