# -*- coding: utf-8 -*-
"""Codex 桌面端 thread_history 投影同步。"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence

from ..file_ops import atomic_write_text


THREAD_ID_RE = re.compile(
    r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"
    r"(?:_([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}))?"
    r"\.jsonl$",
    re.IGNORECASE,
)
THREAD_ITEMS_COLUMNS = (
    "thread_id",
    "turn_id",
    "item_id",
    "rollout_ordinal",
    "created_at_ms",
    "item_json",
    "item_type",
    "updated_at_ordinal",
    "started_at_ms",
    "completed_at_ms",
)


def default_thread_history_db() -> str:
    override = os.environ.get("CODEX_THREAD_HISTORY_DB", "").strip()
    if override:
        return os.path.expanduser(override)
    return os.path.expanduser("~/.codex/thread_history_1.sqlite")


def thread_id_from_path(file_path: str) -> Optional[str]:
    """从 rollout 文件名提取当前文件对应的 thread id。

    分叉会话文件名是 ``<parent>_<child>.jsonl``。桌面端投影挂在子 id 上，
    不能用 session_meta 里的父 id。
    """
    match = THREAD_ID_RE.search(os.path.basename(file_path))
    if not match:
        return None
    return match.group(2) or match.group(1)


def resolve_thread_id(file_path: str, lines: Sequence[Dict[str, Any]]) -> Optional[str]:
    thread_id = thread_id_from_path(file_path)
    if thread_id:
        return thread_id
    for line in lines:
        if not isinstance(line, dict) or line.get("type") != "session_meta":
            continue
        payload = line.get("payload") or {}
        if isinstance(payload, dict):
            return payload.get("id") or payload.get("session_id")
    return None


@dataclass
class ThreadHistorySyncResult:
    updated: int = 0
    deleted: int = 0
    cursor_repaired: bool = False
    skipped: bool = False
    reason: str = ""
    backup_path: Optional[str] = None


@dataclass
class _ProjectionSnapshot:
    offset: int
    ordinal: int


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return row is not None


def _load_projection(conn: sqlite3.Connection, thread_id: str) -> Optional[_ProjectionSnapshot]:
    if not _table_exists(conn, "thread_history_projection_state"):
        return None
    row = conn.execute(
        """
        SELECT next_rollout_byte_offset, next_rollout_ordinal
        FROM thread_history_projection_state
        WHERE thread_id=?
        """,
        (thread_id,),
    ).fetchone()
    if row is None:
        return None
    return _ProjectionSnapshot(int(row[0]), int(row[1]))


def _restore_projection(conn: sqlite3.Connection, thread_id: str, snapshot: _ProjectionSnapshot) -> None:
    conn.execute(
        """
        UPDATE thread_history_projection_state
        SET next_rollout_byte_offset=?, next_rollout_ordinal=?
        WHERE thread_id=?
        """,
        (snapshot.offset, snapshot.ordinal, thread_id),
    )


def _item_rows(conn: sqlite3.Connection, thread_id: str, item_ids: Iterable[str]) -> List[sqlite3.Row]:
    ids = [item_id for item_id in item_ids if item_id]
    if not ids or not _table_exists(conn, "thread_items"):
        return []
    placeholders = ",".join("?" for _ in ids)
    return list(conn.execute(
        f"""
        SELECT {", ".join(THREAD_ITEMS_COLUMNS)}
        FROM thread_items
        WHERE thread_id=? AND item_id IN ({placeholders})
        """,
        (thread_id, *ids),
    ))


def _write_sidecar(backup_path: Optional[str], payload: Dict[str, Any]) -> Optional[str]:
    if not backup_path:
        return None
    sidecar = backup_path + ".thread-history.json"
    atomic_write_text(
        sidecar,
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
    )
    return sidecar


def _json_text(item_json: str) -> Dict[str, Any]:
    try:
        data = json.loads(item_json)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def sync_cleaned_codex_session(
    file_path: str,
    content: str,
    changes: Sequence[Any],
    cleaned_lines: Sequence[Dict[str, Any]],
    *,
    old_size: int,
    backup_path: Optional[str] = None,
    db_path: Optional[str] = None,
) -> ThreadHistorySyncResult:
    """把已清理的助手文本和推理删除同步到桌面端投影，再写 JSONL。"""
    from .formats import SessionFormat, get_format_strategy

    strategy = get_format_strategy(SessionFormat.CODEX)
    final_text: Dict[str, str] = {}
    for line in cleaned_lines:
        if not isinstance(line, dict):
            continue
        item_id = strategy.message_item_id(line)
        if not item_id:
            continue
        if item_id not in final_text or line.get("type") == "response_item":
            final_text[item_id] = strategy.extract_text_content(line)

    text_updates: Dict[str, str] = {}
    removed_ids: List[str] = []
    for change in changes:
        item_ids = list(getattr(change, "item_ids", None) or [])
        if getattr(change, "change_type", "") == "replace":
            for item_id in item_ids:
                if item_id in final_text:
                    text_updates[item_id] = final_text[item_id]
        elif getattr(change, "change_type", "") == "delete":
            removed_ids.extend(item_id for item_id in item_ids if item_id)

    new_size = len(content.encode("utf-8"))
    new_line_count = content.count("\n")
    db_path = db_path or default_thread_history_db()
    thread_id = resolve_thread_id(file_path, cleaned_lines)

    if not text_updates and not removed_ids:
        atomic_write_text(file_path, content)
        return ThreadHistorySyncResult(skipped=True, reason="no projection changes")

    if not thread_id or not os.path.exists(db_path):
        atomic_write_text(file_path, content)
        return ThreadHistorySyncResult(skipped=True, reason="thread history database unavailable")

    conn = _connect(db_path)
    cursor_before: Optional[_ProjectionSnapshot] = None
    cursor_changed = False
    try:
        if not _table_exists(conn, "thread_items"):
            atomic_write_text(file_path, content)
            return ThreadHistorySyncResult(skipped=True, reason="thread_items table missing")

        known = conn.execute(
            "SELECT 1 FROM thread_items WHERE thread_id=? LIMIT 1",
            (thread_id,),
        ).fetchone()
        projection = _load_projection(conn, thread_id)
        if known is None and projection is None:
            atomic_write_text(file_path, content)
            return ThreadHistorySyncResult(skipped=True, reason="thread is not projected")

        target_ids = list(dict.fromkeys([*text_updates.keys(), *removed_ids]))
        rows = _item_rows(conn, thread_id, target_ids)
        sidecar_rows = [dict(row) for row in rows]
        sidecar = {
            "thread_id": thread_id,
            "rows": sidecar_rows,
            "projection": None if projection is None else {
                "next_rollout_byte_offset": projection.offset,
                "next_rollout_ordinal": projection.ordinal,
            },
        }
        sidecar_path = _write_sidecar(backup_path, sidecar)

        updated = 0
        for row in rows:
            item_id = row["item_id"]
            if item_id not in text_updates:
                continue
            data = _json_text(row["item_json"])
            item_type = (row["item_type"] or data.get("type") or "")
            if item_type not in ("agentMessage", "AgentMessage") and "text" not in data:
                continue
            data["text"] = text_updates[item_id]
            conn.execute(
                """
                UPDATE thread_items
                SET item_json=?
                WHERE thread_id=? AND turn_id=? AND item_id=?
                """,
                (
                    json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                    row["thread_id"],
                    row["turn_id"],
                    item_id,
                ),
            )
            updated += 1

        deleted = 0
        for row in rows:
            item_id = row["item_id"]
            if item_id not in removed_ids:
                continue
            data = _json_text(row["item_json"])
            item_type = row["item_type"] or data.get("type") or ""
            if item_type not in ("reasoning", "Reasoning"):
                continue
            conn.execute(
                """
                DELETE FROM thread_items
                WHERE thread_id=? AND turn_id=? AND item_id=?
                """,
                (row["thread_id"], row["turn_id"], item_id),
            )
            deleted += 1

        cursor_before = projection
        if projection is not None and old_size > 0 and projection.offset >= old_size:
            conn.execute(
                """
                UPDATE thread_history_projection_state
                SET next_rollout_byte_offset=?, next_rollout_ordinal=?
                WHERE thread_id=?
                """,
                (new_size, new_line_count, thread_id),
            )
            cursor_changed = True

        conn.commit()
        try:
            atomic_write_text(file_path, content)
        except Exception:
            # JSONL 没写成功时文件长度没变，必须把游标放回原处。
            # 已提交的文本替换保留，避免桌面端继续显示拒绝。
            if cursor_changed and cursor_before is not None:
                try:
                    _restore_projection(conn, thread_id, cursor_before)
                    conn.commit()
                except sqlite3.Error:
                    conn.rollback()
            raise
        return ThreadHistorySyncResult(
            updated=updated,
            deleted=deleted,
            cursor_repaired=cursor_changed,
            backup_path=sidecar_path,
        )
    except sqlite3.OperationalError as exc:
        conn.rollback()
        raise ValueError(f"桌面端会话投影正在被占用，暂时无法同步: {exc}") from exc
    finally:
        conn.close()


def restore_thread_history_sidecar(backup_path: str, db_path: Optional[str] = None) -> bool:
    """还原清理时保存的投影行。没有 sidecar 时返回 False。"""
    sidecar = backup_path + ".thread-history.json"
    if not os.path.exists(sidecar):
        return False
    db_path = db_path or default_thread_history_db()
    if not os.path.exists(db_path):
        return False
    with open(sidecar, "r", encoding="utf-8") as stream:
        payload = json.load(stream)
    thread_id = payload.get("thread_id")
    rows = payload.get("rows") or []
    if not thread_id:
        return False

    conn = _connect(db_path)
    try:
        for row in rows:
            if not isinstance(row, dict) or not row.get("item_id"):
                continue
            conn.execute(
                f"""
                INSERT INTO thread_items ({", ".join(THREAD_ITEMS_COLUMNS)})
                VALUES ({", ".join("?" for _ in THREAD_ITEMS_COLUMNS)})
                ON CONFLICT(thread_id, turn_id, item_id) DO UPDATE SET
                    rollout_ordinal=excluded.rollout_ordinal,
                    created_at_ms=excluded.created_at_ms,
                    item_json=excluded.item_json,
                    item_type=excluded.item_type,
                    updated_at_ordinal=excluded.updated_at_ordinal,
                    started_at_ms=excluded.started_at_ms,
                    completed_at_ms=excluded.completed_at_ms
                """,
                tuple(row.get(column) for column in THREAD_ITEMS_COLUMNS),
            )
        projection = payload.get("projection") or None
        if isinstance(projection, dict) and _table_exists(conn, "thread_history_projection_state"):
            conn.execute(
                """
                INSERT INTO thread_history_projection_state (
                    thread_id, next_rollout_byte_offset, next_rollout_ordinal
                ) VALUES (?, ?, ?)
                ON CONFLICT(thread_id) DO UPDATE SET
                    next_rollout_byte_offset=excluded.next_rollout_byte_offset,
                    next_rollout_ordinal=excluded.next_rollout_ordinal
                """,
                (
                    thread_id,
                    int(projection.get("next_rollout_byte_offset") or 0),
                    int(projection.get("next_rollout_ordinal") or 0),
                ),
            )
        conn.commit()
        return True
    except sqlite3.OperationalError as exc:
        conn.rollback()
        raise ValueError(f"还原桌面端会话投影失败: {exc}") from exc
    finally:
        conn.close()
