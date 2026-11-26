"""Unit tests for pydantic-settings configuration."""

from pathlib import Path

from india_ate.config import Settings


def test_settings_defaults_and_env_override(monkeypatch: object) -> None:
    defaults = Settings()
    assert defaults.sqlite_path == Path("data/india_ate.db")
    assert defaults.snapshot_dir == Path("data/snapshots")
    assert defaults.log_level == "INFO"

    monkeypatch.setenv("INDIA_ATE_LOG_LEVEL", "DEBUG")  # type: ignore[attr-defined]
    overridden = Settings()
    assert overridden.log_level == "DEBUG"
