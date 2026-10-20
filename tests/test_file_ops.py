import os

import pytest

from codex_session_patcher import file_ops
from codex_session_patcher.file_ops import (
    UnsafeFileError,
    atomic_write_text,
    create_unique_backup,
)


class FrozenDatetime:
    @classmethod
    def now(cls):
        return cls()

    def strftime(self, _format):
        return "20260802_120000"


def test_atomic_write_preserves_original_when_replace_fails(tmp_path, monkeypatch):
    target = tmp_path / "session.jsonl"
    target.write_text("original\n", encoding="utf-8")

    def fail_replace(_source, _target):
        raise OSError("replace failed")

    monkeypatch.setattr(file_ops.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        atomic_write_text(target, "new\n")

    assert target.read_text(encoding="utf-8") == "original\n"
    assert list(tmp_path.glob(".session.jsonl.*.tmp")) == []


def test_atomic_write_rejects_symlink_target(tmp_path):
    actual = tmp_path / "actual.txt"
    actual.write_text("original", encoding="utf-8")
    target = tmp_path / "target.txt"
    try:
        target.symlink_to(actual)
    except (OSError, NotImplementedError):
        pytest.skip("当前平台不支持测试符号链接")

    with pytest.raises(UnsafeFileError):
        atomic_write_text(target, "new")

    assert actual.read_text(encoding="utf-8") == "original"


def test_backups_created_in_same_second_do_not_overwrite(tmp_path, monkeypatch):
    source = tmp_path / "config.toml"
    source.write_text("first", encoding="utf-8")
    monkeypatch.setattr(file_ops, "datetime", FrozenDatetime)

    first = create_unique_backup(source)
    source.write_text("second", encoding="utf-8")
    second = create_unique_backup(source)

    assert first != second
    assert open(first, encoding="utf-8").read() == "first"
    assert open(second, encoding="utf-8").read() == "second"


def test_backup_rejects_symlink_source(tmp_path):
    actual = tmp_path / "actual.txt"
    actual.write_text("content", encoding="utf-8")
    source = tmp_path / "source.txt"
    try:
        source.symlink_to(actual)
    except (OSError, NotImplementedError):
        pytest.skip("当前平台不支持测试符号链接")

    with pytest.raises(UnsafeFileError):
        create_unique_backup(source)
