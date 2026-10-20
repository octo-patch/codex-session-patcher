# -*- coding: utf-8 -*-
"""
会话清理逻辑 — 支持 Codex CLI 和 Claude Code 两种格式
"""

import json
import copy
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass

from .constants import MOCK_RESPONSE
from .detector import RefusalDetector
from .formats import SessionFormat, get_format_strategy
from ..file_ops import atomic_write_text


@dataclass
class ChangeDetail:
    """修改详情"""
    line_num: int
    change_type: str  # 'replace', 'delete', 'remove_thinking'
    original_content: Optional[str] = None
    new_content: Optional[str] = None
    line_nums: Optional[List[int]] = None  # 所有关联行号（含冗余副本）
    item_ids: Optional[List[str]] = None  # 桌面端投影中的 item id



def group_refusal_messages(
    lines: List[Dict[str, Any]],
    detector: RefusalDetector,
    session_format: SessionFormat = SessionFormat.CODEX,
    selected_lines: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """把同一条拒绝回复的主记录和冗余副本分成一组。

    桌面端同一条助手回复会同时出现在 response_item 和
    event_msg/item_completed/AgentMessage 中，二者共享 item id。
    旧版没有 id 的 event_msg 只有在文本完全一致时才挂到上一组。
    """
    strategy = get_format_strategy(session_format)
    selected_set = set(selected_lines) if selected_lines else None
    groups: List[Dict[str, Any]] = []
    by_id: Dict[str, Dict[str, Any]] = {}

    for msg_idx, msg in strategy.get_assistant_messages(lines):
        content = strategy.extract_text_content(msg)
        if not content or not detector.detect(content):
            continue
        item_id = strategy.message_item_id(msg)
        if item_id and item_id in by_id:
            group = by_id[item_id]
            if lines[group["primary"]].get("type") == "event_msg" and msg.get("type") != "event_msg":
                group["companions"].append(group["primary"])
                group["primary"] = msg_idx
            else:
                group["companions"].append(msg_idx)
            if item_id not in group["item_ids"]:
                group["item_ids"].append(item_id)
            continue

        if msg.get("type") == "event_msg" and not item_id and groups:
            previous = groups[-1]
            previous_text = strategy.extract_text_content(lines[previous["primary"]])
            if previous_text == content:
                previous["companions"].append(msg_idx)
                continue

        group = {
            "primary": msg_idx,
            "companions": [],
            "item_ids": [item_id] if item_id else [],
            "text": content,
        }
        groups.append(group)
        if item_id:
            by_id[item_id] = group

    if selected_set is not None:
        groups = [group for group in groups if (group["primary"] + 1) in selected_set]
    return groups


def count_refusal_groups(
    lines: List[Dict[str, Any]],
    detector: RefusalDetector,
    session_format: SessionFormat = SessionFormat.CODEX,
) -> int:
    """按拒绝分组计数，避免同一条回复的冗余副本被重复计算。"""
    return len(group_refusal_messages(lines, detector, session_format))


def clean_session_jsonl(
    lines: List[Dict[str, Any]],
    detector: RefusalDetector,
    show_content: bool = False,
    mock_response: Optional[str] = None,
    session_format: SessionFormat = SessionFormat.CODEX,
    selected_lines: Optional[List[int]] = None,
    clean_reasoning: bool = True,
) -> Tuple[List[Dict[str, Any]], bool, List[ChangeDetail]]:
    """
    清洗 JSONL 会话数据

    Args:
        lines: JSONL 行列表
        detector: 拒绝检测器
        show_content: 是否返回详细内容
        mock_response: 替换文本
        session_format: 会话格式
        selected_lines: 只清理选中的行号列表（None 表示全部清理）
        clean_reasoning: 是否清理推理内容（thinking/reasoning blocks）

    Returns:
        (清洗后的行列表, 是否进行了修改, 修改详情列表)
    """
    modified = False
    changes = []

    if mock_response is None:
        mock_response = MOCK_RESPONSE


    strategy = get_format_strategy(session_format)

    # 1. 替换拒绝的助手消息。同一 item id 的 response_item / item_completed 只算一组。
    refusal_groups = group_refusal_messages(
        lines, detector, session_format, selected_lines,
    )

    for group in refusal_groups:
        primary_idx = group["primary"]
        companion_idxs = group["companions"]
        primary_msg = lines[primary_idx]
        content = strategy.extract_text_content(primary_msg)
        all_line_nums = sorted([primary_idx + 1] + [i + 1 for i in companion_idxs])

        change = ChangeDetail(
            line_num=primary_idx + 1,
            change_type='replace',
            line_nums=all_line_nums,
            item_ids=list(group["item_ids"]),
        )
        if show_content:
            change.original_content = content[:500] + ('...' if len(content) > 500 else '')
            change.new_content = mock_response
        changes.append(change)

        # 替换 primary 行
        lines[primary_idx] = strategy.update_text_content(primary_msg, mock_response)
        # 替换所有 companion 行
        for cidx in companion_idxs:
            lines[cidx] = strategy.update_text_content(lines[cidx], mock_response)
        modified = True

    # 2. 删除独立的 thinking/reasoning 行（Codex 格式）- 可选
    if clean_reasoning:
        thinking_items = strategy.get_thinking_items(lines)
        if thinking_items:
            for idx, item in thinking_items:
                item_id = strategy.reasoning_item_id(lines[idx])
                change = ChangeDetail(
                    line_num=idx + 1,
                    change_type='delete',
                    item_ids=[item_id] if item_id else [],
                )
                if show_content:
                    payload = lines[idx].get('payload', {})
                    summary = payload.get('summary', [])
                    if isinstance(summary, list):
                        texts = [s.get('text', '') for s in summary if isinstance(s, dict)]
                        content_preview = ' '.join(texts)[:100]
                    else:
                        content_preview = str(summary)[:100]
                    if not content_preview:
                        content_preview = '推理内容'
                    change.original_content = content_preview + ('...' if len(content_preview) >= 100 else '')
                changes.append(change)
                lines[idx] = None
                modified = True

    # 3. 移除嵌入在消息 content[] 中的 thinking 块（Claude Code 格式）- 可选
    if clean_reasoning:
        for idx, line in enumerate(lines):
            if line is None:
                continue
            updated, removed_count = strategy.remove_thinking_from_message(line)
            if removed_count > 0:
                change = ChangeDetail(
                    line_num=idx + 1,
                    change_type='remove_thinking'
                )
                if show_content:
                    change.original_content = f'移除 {removed_count} 个 thinking block'
                changes.append(change)
                lines[idx] = updated
                modified = True

    # 4. 过滤掉标记为 None 的行
    lines = [line for line in lines if line is not None]

    return lines, modified, changes


def serialize_session_jsonl(lines: List[Dict[str, Any]]) -> str:
    """把会话行序列化成与落盘完全一致的 JSONL 文本。"""
    serialized = []
    for line in lines:
        line_copy = {k: v for k, v in line.items() if not k.startswith('_')}
        serialized.append(json.dumps(line_copy, ensure_ascii=False))
    content = "\n".join(serialized)
    if serialized:
        content += "\n"
    return content


def save_session_jsonl(lines: List[Dict[str, Any]], file_path: str) -> None:
    """保存 JSONL 会话数据"""
    try:
        atomic_write_text(file_path, serialize_session_jsonl(lines))
    except PermissionError as e:
        raise ValueError(f"写入文件失败，权限不足: {file_path}\n{e}")
    except Exception as e:
        raise ValueError(f"写入文件失败: {file_path}\n{e}")


def publish_cleaned_codex_session(
    file_path: str,
    lines: List[Dict[str, Any]],
    changes: List[ChangeDetail],
    *,
    old_size: int,
    backup_path: Optional[str] = None,
    db_path: Optional[str] = None,
) -> None:
    """写入 Codex JSONL，并同步桌面端 thread_history 投影。"""
    from .thread_history import sync_cleaned_codex_session

    content = serialize_session_jsonl(lines)
    try:
        sync_cleaned_codex_session(
            file_path,
            content,
            changes,
            lines,
            old_size=old_size,
            backup_path=backup_path,
            db_path=db_path,
        )
    except PermissionError as e:
        raise ValueError(f"写入文件失败，权限不足: {file_path}\n{e}")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"写入文件失败: {file_path}\n{e}")
