from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Project Collision Avoidance System"
    app_env: str = "development"
    app_debug: bool = True
    vercel: bool = False
    database_url: str | None = None
    dataset_csv: str | None = None
    default_top_n: int = 5
    max_top_n: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def model_post_init(self, __context) -> None:
        if self.database_url is None:
            if self.vercel:
                self.database_url = "sqlite:////tmp/pcas.db"
            else:
                self.database_url = f"sqlite:///{(BASE_DIR / 'pcas.db').as_posix()}"

        if self.dataset_csv is None:
            self.dataset_csv = str(BASE_DIR / "data" / "projects.csv")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
