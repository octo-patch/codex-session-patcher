#!/usr/bin/env python3
"""离线校验 Codex 默认提示词的结构和题型契约。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PROMPT = ROOT / "codex_session_patcher/ctf_config/prompts/ctf_optimized.md"
DEFAULT_BANK = ROOT / "tests/prompt_bank/cases.json"
REQUIRED_CATEGORIES = {
    "web-api",
    "pwn",
    "reverse",
    "crypto",
    "forensics",
    "mobile",
    "cloud",
    "universal",
    "workflow",
    "delivery",
}


def load_bank(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取提示词题库 {path}: {exc}") from exc

    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("提示词题库 schema_version 必须为 1")
    cases = data.get("cases")
    if not isinstance(cases, list) or len(cases) < 10:
        raise ValueError("提示词题库至少需要 10 个用例")

    seen_ids: set[str] = set()
    categories: set[str] = set()
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"用例 {index} 必须是对象")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip() or case_id in seen_ids:
            raise ValueError(f"用例 {index} 的 id 缺失或重复")
        seen_ids.add(case_id)

        category = case.get("category")
        if not isinstance(category, str) or not category.strip():
            raise ValueError(f"用例 {case_id} 缺少 category")
        categories.add(category)

        if not isinstance(case.get("input"), str) or not case["input"].strip():
            raise ValueError(f"用例 {case_id} 缺少 input")
        if not isinstance(case.get("prompt_section"), str) or not case["prompt_section"].strip():
            raise ValueError(f"用例 {case_id} 缺少 prompt_section")
        tokens = case.get("required_tokens")
        if not isinstance(tokens, list) or not tokens or not all(
            isinstance(token, str) and token for token in tokens
        ):
            raise ValueError(f"用例 {case_id} 的 required_tokens 无效")

    missing_categories = REQUIRED_CATEGORIES - categories
    if missing_categories:
        raise ValueError(f"提示词题库缺少分类: {', '.join(sorted(missing_categories))}")
    return cases


def validate_prompt_contract(prompt_path: Path, cases: list[dict]) -> list[str]:
    try:
        prompt = prompt_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"无法读取提示词 {prompt_path}: {exc}") from exc

    errors: list[str] = []
    for case in cases:
        section = case["prompt_section"]
        start = prompt.find(section)
        if start < 0:
            errors.append(f"{case['id']}: 缺少章节 {section}")
            continue

        heading_level = len(section) - len(section.lstrip("#"))
        section_end = len(prompt)
        for line in prompt[start + len(section):].splitlines(keepends=True):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                level = len(stripped) - len(stripped.lstrip("#"))
                if 0 < level <= heading_level:
                    section_end = prompt.find(line, start + len(section))
                    break
        section_text = prompt[start:section_end]
        for token in case["required_tokens"]:
            if token not in section_text:
                errors.append(f"{case['id']}: 章节内缺少契约文本 {token}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    parser.add_argument("--bank", type=Path, default=DEFAULT_BANK)
    args = parser.parse_args()

    try:
        cases = load_bank(args.bank)
        errors = validate_prompt_contract(args.prompt, cases)
    except ValueError as exc:
        parser.error(str(exc))

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print(f"PASS prompt bank: {len(cases)} offline contract cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
