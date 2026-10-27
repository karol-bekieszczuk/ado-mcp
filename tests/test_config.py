import pytest
from pydantic import ValidationError

from ado_mcp import config


def test_settings_from_kwargs(monkeypatch):
    settings = config.Settings(
        _env_file=None, org="test_org", project="test_project", pat="test_pat"
    )

    assert settings.org == "test_org"
    assert settings.project == "test_project"
    assert settings.pat.get_secret_value() == "test_pat"


def test_pat_does_not_expose_pat():
    settings = config.Settings(
        _env_file=None, org="test_org", project="test_project", pat="secret123"
    )
    assert "secret123" not in str(settings)
    assert "secret123" not in repr(settings)
    assert "secret123" not in str(settings.model_dump_json())


def test_config_from_env_vars(monkeypatch):
    monkeypatch.setenv("ADO_ORG", "env_org")
    monkeypatch.setenv("ADO_PROJECT", "env_project")
    monkeypatch.setenv("ADO_PAT", "env_pat")

    settings = config.Settings(_env_file=None)

    assert settings.org == "env_org"
    assert settings.project == "env_project"
    assert settings.pat.get_secret_value() == "env_pat"


def test_config_validation(monkeypatch):
    monkeypatch.setenv("ADO_ORG", "")
    monkeypatch.setenv("ADO_PROJECT", "")
    monkeypatch.setenv("ADO_PAT", "")

    with pytest.raises(ValidationError) as exc:
        config.Settings(_env_file=None)

    error = str(exc.value)
    assert "org" in error
    assert "project" in error
    assert "pat" in error
    assert "String should have at least 1 character" in error


def test_required_config_fields(monkeypatch):
    for name in ("ADO_ORG", "ADO_PROJECT", "ADO_PAT"):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(ValidationError, match="org"):
        config.Settings(_env_file=None, project="p", pat="test_pat")

    with pytest.raises(ValidationError, match="project"):
        config.Settings(_env_file=None, org="o", pat="test_pat")

    with pytest.raises(ValidationError, match="pat"):
        config.Settings(_env_file=None, org="o", project="p")


def test_validation_error_does_not_leak_pat(monkeypatch):
    monkeypatch.setenv("ADO_ORG", "")
    monkeypatch.setenv("ADO_PROJECT", "test_project")
    monkeypatch.setenv("ADO_PAT", "pat-value-that-must-not-leak")

    with pytest.raises(ValidationError) as exc_info:
        config.Settings(_env_file=None)

    assert "pat-value-that-must-not-leak" not in str(exc_info.value)
