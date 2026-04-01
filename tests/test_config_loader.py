from pathlib import Path

from etl_sf.config.loader import load_environment_config


def test_load_environment_config():
    env = load_environment_config(Path("configs"), "dev")
    assert env.name == "DEV"
    assert "sqlite:///etl_sf_dev.db" == env.database.url
