"""Runtime configuration via pydantic-settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_prefix="INDIA_ATE_")

    sqlite_path: Path = Path("data/india_ate.db")
    snapshot_dir: Path = Path("data/snapshots")
    log_level: str = "INFO"
