# -*- coding: utf-8 -*-
"""共享的安全文件写入与备份工具。"""

from __future__ import annotations

import json
import os
import stat
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union


PathLike = Union[str, os.PathLike]


class UnsafeFileError(ValueError):
    """目标节点不是可安全管理的普通文件。"""


def require_regular_or_missing(path: PathLike) -> Optional[os.stat_result]:
    """确认目标不存在或是普通文件，不跟随符号链接。"""
    target = Path(path)
    try:
        info = os.lstat(str(target))
    except FileNotFoundError:
        return None

    if not stat.S_ISREG(info.st_mode):
        raise UnsafeFileError(f"目标不是普通文件: {target}")
    return info


def _fsync_directory(directory: Path) -> None:
    """尽力刷新目录元数据；不支持目录 fsync 的平台直接跳过。"""
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        fd = os.open(str(directory), flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def atomic_write_bytes(path: PathLike, data: bytes, mode: Optional[int] = None) -> None:
    """在同目录完整写入临时文件后原子替换目标。"""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    current = require_regular_or_missing(target)
    final_mode = mode if mode is not None else (
        stat.S_IMODE(current.st_mode) if current is not None else 0o600
    )

    fd, temp_name = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent)
    )
    temp_path = Path(temp_name)
    try:
        if hasattr(os, "fchmod"):
            os.fchmod(fd, final_mode)
        with os.fdopen(fd, "wb") as stream:
            fd = -1
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(str(temp_path), str(target))
        if os.name != "nt":
            os.chmod(str(target), final_mode)
        _fsync_directory(target.parent)
    finally:
        if fd >= 0:
            os.close(fd)
        try:
            temp_path.unlink()
        except FileNotFoundError:
            pass


def atomic_write_text(
    path: PathLike,
    content: str,
    *,
    encoding: str = "utf-8",
    mode: Optional[int] = None,
) -> None:
    atomic_write_bytes(path, content.encode(encoding), mode=mode)


def atomic_write_json(
    path: PathLike,
    data: Any,
    *,
    ensure_ascii: bool = False,
    indent: int = 2,
    mode: Optional[int] = None,
) -> None:
    payload = json.dumps(data, ensure_ascii=ensure_ascii, indent=indent) + "\n"
    atomic_write_text(path, payload, mode=mode)


def create_unique_backup(path: PathLike) -> str:
    """创建不覆盖既有文件的时间戳备份并返回路径。"""
    source = Path(path)
    source_info = require_regular_or_missing(source)
    if source_info is None:
        raise FileNotFoundError(f"源文件不存在: {source}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    attempt = 0
    while True:
        extra = "" if attempt == 0 else f".{attempt}"
        backup = Path(f"{source}.{timestamp}{extra}.bak")
        try:
            out_fd = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            break
        except FileExistsError:
            attempt += 1

    in_flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        in_flags |= os.O_NOFOLLOW
    in_fd = -1
    try:
        in_fd = os.open(str(source), in_flags)
        with os.fdopen(in_fd, "rb") as src, os.fdopen(out_fd, "wb") as dst:
            in_fd = -1
            out_fd = -1
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if os.name != "nt":
            os.chmod(str(backup), stat.S_IMODE(source_info.st_mode))
        _fsync_directory(source.parent)
        return str(backup)
    except Exception:
        try:
            backup.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        if in_fd >= 0:
            os.close(in_fd)
        if out_fd >= 0:
            os.close(out_fd)


def reserve_unique_backup_path(path: PathLike) -> str:
    """为需要自行写入的备份独占预留一个空文件。"""
    source = Path(path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    attempt = 0
    while True:
        extra = "" if attempt == 0 else f".{attempt}"
        backup = Path(f"{source}.{timestamp}{extra}.bak")
        try:
            fd = os.open(str(backup), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            attempt += 1
            continue
        os.close(fd)
        return str(backup)
