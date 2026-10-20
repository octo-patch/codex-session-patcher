# -*- coding: utf-8 -*-
import json
import os
import sqlite3

from codex_session_patcher.core.detector import RefusalDetector
from codex_session_patcher.core.formats import SessionFormat
from codex_session_patcher.core.patcher import clean_session_jsonl, publish_cleaned_codex_session
from codex_session_patcher.core.thread_history import (
    restore_thread_history_sidecar,
    thread_id_from_path,
)


def _create_db(path, thread_id, text, file_size, ordinal):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE thread_items (
            thread_id TEXT NOT NULL,
            turn_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            rollout_ordinal INTEGER NOT NULL,
            created_at_ms INTEGER NOT NULL,
            item_json TEXT NOT NULL,
            item_type TEXT NOT NULL DEFAULT '',
            updated_at_ordinal INTEGER NOT NULL DEFAULT 0,
            started_at_ms INTEGER,
            completed_at_ms INTEGER,
            PRIMARY KEY (thread_id, turn_id, item_id)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE thread_history_projection_state (
            thread_id TEXT PRIMARY KEY,
            next_rollout_byte_offset INTEGER NOT NULL,
            next_rollout_ordinal INTEGER NOT NULL
        )
        """
    )
    agent = {
        "type": "agentMessage",
        "id": "msg_1",
        "text": text,
        "phase": None,
    }
    reasoning = {"type": "reasoning", "id": "rs_1", "summary": ["hidden"]}
    conn.execute(
        """
        INSERT INTO thread_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (thread_id, "turn_1", "msg_1", 2, 1, json.dumps(agent, ensure_ascii=False, separators=(",", ":")), "agentMessage", 2, 1, 2),
    )
    conn.execute(
        """
        INSERT INTO thread_items VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (thread_id, "turn_1", "rs_1", 1, 1, json.dumps(reasoning, ensure_ascii=False, separators=(",", ":")), "reasoning", 1, 1, 2),
    )
    conn.execute(
        "INSERT INTO thread_history_projection_state VALUES (?, ?, ?)",
        (thread_id, file_size, ordinal),
    )
    conn.commit()
    conn.close()


def test_thread_id_from_forked_rollout_uses_child_id():
    path = (
        "rollout-2026-10-03T18-23-48-01a0fcf1-f060-7633-9640-5b713f942c29_"
        "01a1014a-9acc-7ff3-a315-10dfce14b196.jsonl"
    )
    assert thread_id_from_path(path) == "01a1014a-9acc-7ff3-a315-10dfce14b196"
    assert thread_id_from_path(
        "rollout-2026-10-04T13-52-30-01a10578-916b-7dd3-be46-4d4ca2b7e4ff.jsonl"
    ) == "01a10578-916b-7dd3-be46-4d4ca2b7e4ff"


def test_publish_syncs_projected_agent_message_and_repairs_cursor(tmp_path):
    thread_id = "01a10578-916b-7dd3-be46-4d4ca2b7e4ff"
    session = tmp_path / f"rollout-2026-10-04T13-52-30-{thread_id}.jsonl"
    lines = [
        {
            "type": "event_msg",
            "payload": {
                "type": "item_completed",
                "item": {
                    "type": "AgentMessage",
                    "id": "msg_1",
                    "content": [{"type": "Text", "text": "不能继续做这件事。"}],
                },
            },
        },
        {
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "assistant",
                "id": "msg_1",
                "content": [{"type": "output_text", "text": "不能继续做这件事。"}],
            },
        },
        {
            "type": "response_item",
            "payload": {"type": "reasoning", "id": "rs_1", "summary": []},
        },
    ]
    raw = "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines)
    session.write_text(raw, encoding="utf-8", newline="\n")
    db = tmp_path / "thread_history.sqlite"
    original_size = session.stat().st_size
    _create_db(db, thread_id, "不能继续做这件事。", original_size, 3)

    cleaned, modified, changes = clean_session_jsonl(
        lines,
        RefusalDetector(),
        mock_response="已改为可继续的说明",
        session_format=SessionFormat.CODEX,
    )
    assert modified is True
    backup = str(session) + ".20261004_000000.bak"
    session.with_name(session.name + ".20261004_000000.bak").write_text(raw, encoding="utf-8")

    publish_cleaned_codex_session(
        str(session),
        cleaned,
        changes,
        old_size=session.stat().st_size,
        backup_path=backup,
        db_path=str(db),
    )

    conn = sqlite3.connect(db)
    agent = json.loads(conn.execute(
        "SELECT item_json FROM thread_items WHERE item_id='msg_1'"
    ).fetchone()[0])
    reasoning = conn.execute(
        "SELECT COUNT(*) FROM thread_items WHERE item_id='rs_1'"
    ).fetchone()[0]
    offset, ordinal = conn.execute(
        "SELECT next_rollout_byte_offset, next_rollout_ordinal FROM thread_history_projection_state"
    ).fetchone()
    conn.close()

    assert agent["text"] == "已改为可继续的说明"
    assert reasoning == 0
    assert offset == session.stat().st_size
    assert ordinal == 2
    assert "不能继续做这件事" not in session.read_text(encoding="utf-8")
    sidecar = backup + ".thread-history.json"
    assert os.path.exists(sidecar)

    restore_thread_history_sidecar(backup, db_path=str(db))
    conn = sqlite3.connect(db)
    restored = json.loads(conn.execute(
        "SELECT item_json FROM thread_items WHERE item_id='msg_1'"
    ).fetchone()[0])
    restored_reasoning = conn.execute(
        "SELECT COUNT(*) FROM thread_items WHERE item_id='rs_1'"
    ).fetchone()[0]
    restored_offset = conn.execute(
        "SELECT next_rollout_byte_offset FROM thread_history_projection_state"
    ).fetchone()[0]
    conn.close()
    assert restored["text"] == "不能继续做这件事。"
    assert restored_reasoning == 1
    assert restored_offset == original_size


def test_publish_without_projection_database_still_writes_jsonl(tmp_path, monkeypatch):
    session = tmp_path / "rollout-2026-10-04T13-52-30-01a10578-916b-7dd3-be46-4d4ca2b7e4ff.jsonl"
    lines = [{
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "assistant",
            "id": "msg_1",
            "content": [{"type": "output_text", "text": "不能继续做这件事。"}],
        },
    }]
    session.write_text(json.dumps(lines[0], ensure_ascii=False) + "\n", encoding="utf-8")
    cleaned, modified, changes = clean_session_jsonl(
        lines,
        RefusalDetector(),
        mock_response="已替换",
        session_format=SessionFormat.CODEX,
        clean_reasoning=False,
    )
    assert modified is True
    monkeypatch.setenv("CODEX_THREAD_HISTORY_DB", str(tmp_path / "missing.sqlite"))
    publish_cleaned_codex_session(
        str(session),
        cleaned,
        changes,
        old_size=session.stat().st_size,
    )
    assert "已替换" in session.read_text(encoding="utf-8")


def test_jsonl_write_failure_restores_cursor_and_keeps_projected_text(tmp_path, monkeypatch):
    """JSONL 写入失败时，投影游标必须回到原位，已替换的文本不能回退成拒绝。"""
    import pytest
    from codex_session_patcher.core import thread_history

    thread_id = "01a10578-916b-7dd3-be46-4d4ca2b7e4ff"
    session = tmp_path / f"rollout-2026-10-04T13-52-30-{thread_id}.jsonl"
    original = {
        "type": "response_item",
        "payload": {
            "type": "message",
            "role": "assistant",
            "id": "msg_1",
            "content": [{"type": "output_text", "text": '不能继续做这件事。'}],
        },
    }
    raw = json.dumps(original, ensure_ascii=False) + "\n"
    session.write_text(raw, encoding="utf-8", newline="\n")
    db = tmp_path / "thread_history.sqlite"
    original_size = session.stat().st_size
    _create_db(db, thread_id, '不能继续做这件事。', original_size, 1)
    cleaned, modified, changes = clean_session_jsonl(
        [original],
        RefusalDetector(),
        mock_response='已改为可继续的说明',
        session_format=SessionFormat.CODEX,
        clean_reasoning=False,
    )
    assert modified is True

    real_write = thread_history.atomic_write_text

    def fail_jsonl(path, content, **kwargs):
        if str(path).endswith(".jsonl"):
            raise PermissionError("simulated write failure")
        return real_write(path, content, **kwargs)

    monkeypatch.setattr(thread_history, "atomic_write_text", fail_jsonl)
    with pytest.raises(ValueError, match='权限不足'):
        publish_cleaned_codex_session(
            str(session),
            cleaned,
            changes,
            old_size=original_size,
            backup_path=str(session) + ".bak",
            db_path=str(db),
        )

    assert session.read_text(encoding="utf-8") == raw
    conn = sqlite3.connect(db)
    agent = json.loads(conn.execute(
        "SELECT item_json FROM thread_items WHERE item_id='msg_1'"
    ).fetchone()[0])
    offset, ordinal = conn.execute(
        "SELECT next_rollout_byte_offset, next_rollout_ordinal FROM thread_history_projection_state"
    ).fetchone()
    conn.close()
    assert agent["text"] == '已改为可继续的说明'
    assert offset == original_size
    assert ordinal == 1
