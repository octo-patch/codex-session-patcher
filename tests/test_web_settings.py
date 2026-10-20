import json

from web.backend import api
from web.backend.main import app


def write_config(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def read_config(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_get_settings_redacts_api_key(monkeypatch, tmp_path, asgi_client_factory):
    config_file = tmp_path / "config.json"
    write_config(config_file, {"ai_key": "secret-key", "ai_model": "test-model"})
    monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(config_file))

    response = asgi_client_factory(app).get("/api/settings")

    assert response.status_code == 200
    assert response.json()["ai_key"] == ""
    assert response.json()["ai_key_configured"] is True


def test_blank_api_key_preserves_existing_secret(monkeypatch, tmp_path, asgi_client_factory):
    config_file = tmp_path / "config.json"
    write_config(config_file, {"ai_key": "secret-key", "ctf_prompts": {"codex": "custom.md"}})
    monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(config_file))

    response = asgi_client_factory(app).put("/api/settings", json={"ai_key": ""})

    assert response.status_code == 200
    saved = read_config(config_file)
    assert saved["ai_key"] == "secret-key"
    assert saved["ctf_prompts"] == {"codex": "custom.md"}
    assert "ai_key_configured" not in saved
    assert "clear_ai_key" not in saved


def test_explicit_clear_removes_existing_secret(monkeypatch, tmp_path, asgi_client_factory):
    config_file = tmp_path / "config.json"
    write_config(config_file, {"ai_key": "secret-key"})
    monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(config_file))

    response = asgi_client_factory(app).put(
        "/api/settings",
        json={"ai_key": "", "clear_ai_key": True},
    )

    assert response.status_code == 200
    assert read_config(config_file)["ai_key"] == ""


def test_invalid_config_is_not_overwritten(monkeypatch, tmp_path, asgi_client_factory):
    config_file = tmp_path / "config.json"
    config_file.write_text("{invalid", encoding="utf-8")
    monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(config_file))

    response = asgi_client_factory(app).put("/api/settings", json={"ai_model": "new-model"})

    assert response.status_code == 500
    assert config_file.read_text(encoding="utf-8") == "{invalid"
