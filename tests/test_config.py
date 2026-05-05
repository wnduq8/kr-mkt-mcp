import os
import pytest

from kr_mkt_mcp.config import Config, load_config


def test_load_config_from_env(env_with_token, fake_token):
    cfg = load_config()
    assert cfg.access_token == fake_token
    assert cfg.api_version == "v25.0"


def test_load_config_missing_token(monkeypatch):
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="META_ACCESS_TOKEN"):
        load_config()


def test_load_config_version_override(env_with_token, monkeypatch):
    monkeypatch.setenv("META_API_VERSION", "v22.0")
    cfg = load_config()
    assert cfg.api_version == "v22.0"


def test_tier1_metrics_count():
    from kr_mkt_mcp.config import TIER1_METRICS
    assert len(TIER1_METRICS) == 10
    assert "purchase_roas" in TIER1_METRICS
    assert "cpc" in TIER1_METRICS


def test_pagination_cap():
    from kr_mkt_mcp.config import PAGINATION_HARD_CAP, TOP_N_DEFAULT
    assert PAGINATION_HARD_CAP == 200
    assert TOP_N_DEFAULT == 10
