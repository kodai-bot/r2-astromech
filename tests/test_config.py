"""Configuration: the shipped config file loads and validates."""

from pathlib import Path

from src.core.config import Configuration

CONFIG = Path(__file__).resolve().parent.parent / "config" / "r2_config.yaml"


def test_shipped_config_is_valid():
    config = Configuration(str(CONFIG))
    assert config.validate()


def test_dot_notation_and_defaults():
    config = Configuration(str(CONFIG))
    assert isinstance(config.get("modules"), dict)
    assert config.get("does.not.exist", "fallback") == "fallback"
