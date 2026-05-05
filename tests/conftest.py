import pytest


@pytest.fixture
def fake_token() -> str:
    return "FAKE_META_TOKEN_FOR_TESTS"


@pytest.fixture
def env_with_token(monkeypatch, fake_token):
    monkeypatch.setenv("META_ACCESS_TOKEN", fake_token)
    yield fake_token
