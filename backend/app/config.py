from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TT_")

    data_dir: Path = Path("/data")
    nominatim_url: str = "https://nominatim.openstreetmap.org"
    rates_url: str = "https://api.frankfurter.dev/v1"
    default_currency: str = "EUR"
    # en dev (dev.sh) se pone a 0 para que :8000 no sirva una SPA compilada obsoleta
    serve_static: bool = True

    @property
    def db_path(self) -> Path:
        return self.data_dir / "app.db"

    @property
    def db_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()
