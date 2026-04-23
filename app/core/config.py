from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Project Collision Avoidance System"
    app_env: str = "development"
    app_debug: bool = True
    database_url: str = "sqlite:///./pcas.db"
    dataset_csv: str = "./data/projects.csv"
    default_top_n: int = 5
    max_top_n: int = 10

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

