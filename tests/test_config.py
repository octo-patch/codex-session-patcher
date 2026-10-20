from __future__ import annotations

import json
import os

import pytest

from codex_session_patcher.config import ConfigError, load_config, save_config


def test_shared_config_round_trip_and_permissions(tmp_path):
    path = tmp_path / "config" / "config.json"
    save_config({"ai_enabled": True, "ctf_prompts": {"codex": {"prompt": "CTF"}}}, path)

    assert load_config(path)["ctf_prompts"]["codex"]["prompt"] == "CTF"
    if os.name != "nt":
        assert path.stat().st_mode & 0o777 == 0o600
        assert path.parent.stat().st_mode & 0o777 == 0o700


def test_shared_config_rejects_invalid_json(tmp_path):
    path = tmp_path / "config.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigError, match="读取配置失败"):
        load_config(path)


def test_shared_config_rejects_non_object_root(tmp_path):
    path = tmp_path / "config.json"
    path.write_text(json.dumps(["invalid"]), encoding="utf-8")

    with pytest.raises(ConfigError, match="根节点必须是对象"):
        load_config(path)


def test_shared_config_rejects_symlink(tmp_path):
    target = tmp_path / "target.json"
    target.write_text("{}", encoding="utf-8")
    link = tmp_path / "config.json"
    try:
        link.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"当前平台不能创建符号链接: {exc}")

    with pytest.raises(ConfigError, match="不是普通文件"):
        load_config(link)
