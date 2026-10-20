# -*- coding: utf-8 -*-
"""CLI、Web 与提示词安装器共享的配置存储。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .file_ops import atomic_write_json, require_regular_or_missing


PathLike = Union[str, os.PathLike]


class ConfigError(ValueError):
    """配置无法安全读取或保存。"""


def default_config_file() -> str:
    return os.path.expanduser("~/.codex-patcher/config.json")


DEFAULT_CONFIG_FILE = default_config_file()


def load_config(path: Optional[PathLike] = None) -> Dict[str, Any]:
    target = Path(path or default_config_file())
    try:
        info = require_regular_or_missing(target)
        if info is None:
            return {}
        with target.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ConfigError(f"读取配置失败: {target}: {exc}") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"配置根节点必须是对象: {target}")
    return data


def save_config(data: Dict[str, Any], path: Optional[PathLike] = None) -> None:
    if not isinstance(data, dict):
        raise ConfigError("配置根节点必须是对象")

    target = Path(path or default_config_file())
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            os.chmod(str(target.parent), 0o700)
        atomic_write_json(target, data, mode=0o600)
    except (OSError, TypeError, ValueError) as exc:
        raise ConfigError(f"保存配置失败: {target}: {exc}") from exc

