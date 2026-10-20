# -*- coding: utf-8 -*-
"""
CTF 提示词 CRUD 测试
"""
from __future__ import annotations

import json
import os
import tempfile
import asyncio

import pytest


PROFILE_MARKER = '# Codex CTF profile managed by codex-session-patcher'
PROMPT_MARKER = '<!-- managed-by: codex-session-patcher:ctf -->'


def managed_prompt(content: str) -> str:
    return f"{PROMPT_MARKER}\n{content}"


class TestCTFPromptTemplates:
    """验证模板内容基本正确"""

    def test_codex_template_exists(self):
        from codex_session_patcher.ctf_config.templates import SECURITY_MODE_PROMPT
        assert 'CTF' in SECURITY_MODE_PROMPT
        assert len(SECURITY_MODE_PROMPT) > 100

    def test_codex_template_has_three_layer_structure(self):
        from codex_session_patcher.ctf_config.templates import SECURITY_MODE_PROMPT_OPTIMIZED

        headings = [
            "## Layer 1 — Universal Execution Rules",
            "## Layer 2 — CTF Workflow",
            "## Layer 3 — Task-Specific Playbooks",
        ]
        positions = [SECURITY_MODE_PROMPT_OPTIMIZED.index(heading) for heading in headings]
        assert positions == sorted(positions)

    def test_codex_template_keeps_placeholder_and_exploit_contracts(self):
        from codex_session_patcher.ctf_config.templates import SECURITY_MODE_PROMPT_OPTIMIZED

        required = {
            "TARGET", "HOST", "PORT", "TOKEN", "OFFSET", "PATCH_BYTE",
            "PAYLOAD", "SERIAL", "CHECK_FN", "LICENSE_BLOB", "ENCRYPT_KEY",
            "C2_ADDR", "target configuration", "send/receive logic", "flag extraction",
        }
        assert all(token in SECURITY_MODE_PROMPT_OPTIMIZED for token in required)

    def test_codex_template_covers_ctf_playbooks_only(self):
        from codex_session_patcher.ctf_config.templates import SECURITY_MODE_PROMPT_OPTIMIZED

        required_headings = {
            "### Web, API, and browser targets",
            "### Pwn and native binaries",
            "### Reverse engineering and anti-analysis",
            "### Cryptography",
            "### Forensics and steganography",
            "### Mobile applications",
            "### Cloud, containers, Kubernetes, Active Directory, and Windows hosts",
        }
        assert all(heading in SECURITY_MODE_PROMPT_OPTIMIZED for heading in required_headings)
        lowered = SECURITY_MODE_PROMPT_OPTIMIZED.lower()
        assert "adult fiction" not in lowered
        assert "pharmacology" not in lowered
        assert "weapons guide" not in lowered

    def test_claude_template_exists(self):
        from codex_session_patcher.ctf_config.templates import CLAUDE_CODE_SECURITY_MODE_PROMPT
        assert 'managed-by: codex-session-patcher:ctf' in CLAUDE_CODE_SECURITY_MODE_PROMPT

    def test_opencode_template_exists(self):
        from codex_session_patcher.ctf_config.templates import OPENCODE_SECURITY_MODE_PROMPT
        assert 'managed-by: codex-session-patcher:ctf' in OPENCODE_SECURITY_MODE_PROMPT
        assert '# Security Testing Mode' in OPENCODE_SECURITY_MODE_PROMPT

    def test_opencode_config_is_valid_json(self):
        from codex_session_patcher.ctf_config.templates import OPENCODE_CTF_CONFIG
        data = json.loads(OPENCODE_CTF_CONFIG)
        assert 'instructions' in data
        assert 'AGENTS.md' in data['instructions']

    def test_opencode_readme_exists(self):
        from codex_session_patcher.ctf_config.templates import OPENCODE_CTF_README
        assert 'opencode' in OPENCODE_CTF_README.lower()
        assert 'codex-patcher' in OPENCODE_CTF_README


class TestCustomPromptParameter:
    """验证 install() 方法的 custom_prompt 参数"""

    def test_codex_installer_accepts_custom_prompt(self, tmp_path):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        installer = CTFConfigInstaller()
        installer.codex_dir = str(tmp_path / ".codex")
        installer.config_path = os.path.join(installer.codex_dir, "config.toml")
        installer.profile_config_path = os.path.join(installer.codex_dir, "ctf.config.toml")
        installer.prompts_dir = os.path.join(installer.codex_dir, "prompts")

        custom = "# My Custom Codex Prompt"
        success, _ = installer.install(custom_prompt=custom)
        assert success

        # install() 写入的文件由 _get_prompt_file() 决定，默认为 ctf_optimized.md
        prompt_file = installer._get_prompt_file()
        actual_path = os.path.join(installer.prompts_dir, prompt_file)
        with open(actual_path, 'r') as f:
            content = f.read()
        assert content == managed_prompt(custom)

    def test_codex_installer_uses_prompt_saved_in_shared_config(self, tmp_path, monkeypatch):
        from codex_session_patcher.config import save_config
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        (codex_dir / "config.toml").write_text('model = "auto"\n', encoding="utf-8")
        save_config({
            "ctf_prompts": {
                "codex": {
                    "file": "custom-ctf.md",
                    "prompt": "# Saved Custom CTF",
                }
            }
        })

        installer = CTFConfigInstaller()
        success, message = installer.install()

        assert success, message
        assert (codex_dir / "prompts" / "custom-ctf.md").read_text(
            encoding="utf-8"
        ) == managed_prompt("# Saved Custom CTF")
        assert "# Saved Custom CTF" in (codex_dir / "ctf.config.toml").read_text(
            encoding="utf-8"
        )

    def test_codex_installer_rejects_prompt_filename_outside_prompts(self, tmp_path, monkeypatch):
        from codex_session_patcher.config import save_config
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        save_config({
            "ctf_prompts": {
                "codex": {
                    "file": "../outside.md",
                    "prompt": "# Invalid path",
                }
            }
        })

        success, message = CTFConfigInstaller().install()

        assert success is False
        assert "prompts 目录内" in message
        assert not (tmp_path / "outside.md").exists()

    def test_codex_installer_stops_when_config_backup_fails(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config import installer as installer_module
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        config_path = codex_dir / "config.toml"
        original = 'model = "existing"\n'
        config_path.write_text(original, encoding="utf-8")

        def fail_backup(_path):
            raise OSError("backup failed")

        monkeypatch.setattr(installer_module, "create_unique_backup", fail_backup)

        success, message = CTFConfigInstaller().install()

        assert success is False
        assert "backup failed" in message
        assert config_path.read_text(encoding="utf-8") == original
        assert not (codex_dir / "ctf.config.toml").exists()
        assert not (codex_dir / "prompts" / "ctf_optimized.md").exists()

    def test_codex_install_refuses_unmanaged_profile_instructions(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        profile_path = codex_dir / "ctf.config.toml"
        original = 'developer_instructions = """\nUSER OWNED\n"""\nmodel = "keep"\n'
        profile_path.write_text(original, encoding="utf-8")

        success, message = CTFConfigInstaller().install(custom_prompt="# New CTF")

        assert success is False
        assert "未受管理" in message
        assert profile_path.read_text(encoding="utf-8") == original
        assert not (codex_dir / "prompts" / "ctf_optimized.md").exists()

    def test_codex_uninstall_refuses_unmanaged_profile_instructions(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        profile_path = codex_dir / "ctf.config.toml"
        original = 'developer_instructions = """\nUSER OWNED\n"""\nmodel = "keep"\n'
        profile_path.write_text(original, encoding="utf-8")

        success, message = CTFConfigInstaller().uninstall()

        assert success is False
        assert "没有本工具管理标记" in message
        assert profile_path.read_text(encoding="utf-8") == original

    def test_codex_install_refuses_unmanaged_prompt_file(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        prompt_path = tmp_path / ".codex" / "prompts" / "ctf_optimized.md"
        prompt_path.parent.mkdir(parents=True)
        prompt_path.write_text("USER OWNED", encoding="utf-8")

        success, message = CTFConfigInstaller().install(custom_prompt="# New CTF")

        assert success is False
        assert "没有本工具管理标记" in message
        assert prompt_path.read_text(encoding="utf-8") == "USER OWNED"
        assert list(prompt_path.parent.glob("*.bak")) == []
        assert not (tmp_path / ".codex" / "ctf.config.toml").exists()

    def test_codex_reinstall_backs_up_managed_prompt(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# First")
        assert success, message

        success, message = installer.install(custom_prompt="# Second")

        assert success, message
        prompt_path = tmp_path / ".codex" / "prompts" / "ctf_optimized.md"
        assert prompt_path.read_text(encoding="utf-8") == managed_prompt("# Second")
        backups = list(prompt_path.parent.glob("ctf_optimized.md.*.bak"))
        assert len(backups) == 1
        assert backups[0].read_text(encoding="utf-8") == managed_prompt("# First")

    def test_codex_profile_install_stops_when_global_uninstall_fails(self, tmp_path, monkeypatch):
        from types import SimpleNamespace
        from codex_session_patcher.ctf_config import installer as installer_module
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(
            installer_module,
            "check_ctf_status",
            lambda: SimpleNamespace(global_installed=True),
        )
        installer = CTFConfigInstaller()
        monkeypatch.setattr(installer, "uninstall_global", lambda: (False, "simulated failure"))

        success, message = installer.install(custom_prompt="# New CTF")

        assert success is False
        assert "simulated failure" in message
        assert not (tmp_path / ".codex" / "ctf.config.toml").exists()
        assert not (tmp_path / ".codex" / "prompts" / "ctf_optimized.md").exists()

    def test_codex_installer_writes_developer_instructions_and_cleans_legacy_entries(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller
        from codex_session_patcher.ctf_config.status import check_ctf_status

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        base_config = codex_dir / "config.toml"
        base_config.write_text(
            '\n'.join([
                'model = "auto"',
                'profile = "ctf"',
                '',
                '# 安全测试模式（由 codex-session-patcher 添加）',
                '[profiles.ctf]',
                'model_instructions_file = "~/.codex/prompts/old.md"',
                'model = "gpt-5.1-codex-max"',
                'sandbox = "danger-full-access"',
                'approval_policy = "never"',
                '',
                '[profiles.ctf.features]',
                'js_repl = false',
                'guardian_approval = false',
                'prevent_idle_sleep = false',
                '',
                '[projects."/tmp/work"]',
                'trust_level = "trusted"',
                '',
            ]),
            encoding="utf-8",
        )

        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# Custom CTF")

        assert success, message
        profile_config = codex_dir / "ctf.config.toml"
        assert profile_config.exists()
        profile_content = profile_config.read_text(encoding="utf-8")
        assert "[profiles.ctf]" not in profile_content
        assert 'model_instructions_file' not in profile_content
        assert 'developer_instructions = """' in profile_content
        assert "# Custom CTF" in profile_content
        assert 'model = "gpt-5.1-codex-max"' in profile_content
        assert 'sandbox = "danger-full-access"' in profile_content
        assert 'approval_policy = "never"' in profile_content
        assert '[features]' in profile_content
        assert 'js_repl = false' not in profile_content
        assert 'guardian_approval = false' in profile_content
        assert 'prevent_idle_sleep = false' in profile_content

        cleaned_base = base_config.read_text(encoding="utf-8")
        assert 'profile = "ctf"' not in cleaned_base
        assert "[profiles.ctf]" not in cleaned_base
        assert "[profiles.ctf.features]" not in cleaned_base
        assert 'model = "auto"' in cleaned_base
        assert '[projects."/tmp/work"]' in cleaned_base
        assert 'trust_level = "trusted"' in cleaned_base

        status = check_ctf_status()
        assert status.installed is True
        assert status.profile_available is True
        assert status.config_path == str(profile_config)

    def test_codex_installer_preserves_existing_v2_profile_settings(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            '\n'.join([
                '# Existing profile settings',
                'model = "gpt-5.1-codex-max"',
                'sandbox = "workspace-write"',
                '',
                '[tools]',
                'web_search = true',
                '',
            ]),
            encoding="utf-8",
        )

        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# Custom CTF")

        assert success, message
        profile_content = profile_config.read_text(encoding="utf-8")
        assert '# Existing profile settings' in profile_content
        assert 'model = "gpt-5.1-codex-max"' in profile_content
        assert 'sandbox = "workspace-write"' in profile_content
        assert '[tools]' in profile_content
        assert 'web_search = true' in profile_content
        assert 'developer_instructions = """' in profile_content
        assert "# Custom CTF" in profile_content

    def test_codex_installer_updates_existing_developer_instructions_once(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            '\n'.join([
                PROFILE_MARKER,
                'developer_instructions = """',
                '# Old CTF',
                '"""',
                'model = "gpt-5.1-codex-max"',
                '',
            ]),
            encoding="utf-8",
        )

        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# New CTF")

        assert success, message
        profile_content = profile_config.read_text(encoding="utf-8")
        assert profile_content.count('developer_instructions = """') == 1
        assert "# New CTF" in profile_content
        assert "# Old CTF" not in profile_content
        assert 'model = "gpt-5.1-codex-max"' in profile_content

    def test_codex_installer_can_replace_builtin_instructions_with_prompt_file(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller
        from codex_session_patcher.ctf_config.status import check_ctf_status

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# Replace CTF", injection_mode="replace")

        assert success, message
        profile_config = tmp_path / ".codex" / "ctf.config.toml"
        profile_content = profile_config.read_text(encoding="utf-8")
        assert 'developer_instructions' not in profile_content
        assert 'model_instructions_file = "~/.codex/prompts/ctf_optimized.md"' in profile_content
        assert (tmp_path / ".codex" / "prompts" / "ctf_optimized.md").read_text(
            encoding="utf-8"
        ) == managed_prompt("# Replace CTF")

        status = check_ctf_status()
        assert status.installed is True
        assert status.injection_mode == "replace"
        assert status.prompt_path == str(tmp_path / ".codex" / "prompts" / "ctf_optimized.md")

        success, message = installer.uninstall()
        assert success, message
        assert not (tmp_path / ".codex" / "prompts" / "ctf_optimized.md").exists()

    def test_codex_installer_switches_replace_profile_back_to_append(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# Replace CTF", injection_mode="replace")
        assert success, message

        success, message = installer.install(custom_prompt="# Append CTF", injection_mode="append")
        assert success, message
        profile_content = (tmp_path / ".codex" / "ctf.config.toml").read_text(encoding="utf-8")
        assert 'developer_instructions = """' in profile_content
        assert "# Append CTF" in profile_content
        assert 'model_instructions_file' not in profile_content

    def test_codex_append_status_reports_prompt_file_written_by_installer(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller
        from codex_session_patcher.ctf_config.status import check_ctf_status

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install(custom_prompt="# Append CTF", injection_mode="append")

        assert success, message
        status = check_ctf_status()
        assert status.injection_mode == "append"
        assert status.prompt_path == str(tmp_path / ".codex" / "prompts" / "ctf_optimized.md")
        assert status.prompt_exists is True

    def test_codex_installer_uninstall_removes_v2_profile_and_legacy_entries(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "ctf_optimized.md").write_text(
            managed_prompt("# Custom CTF"), encoding="utf-8"
        )
        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            f'{PROFILE_MARKER}\ndeveloper_instructions = """\n{managed_prompt("# Custom CTF")}\n"""\n',
            encoding="utf-8",
        )
        base_config = codex_dir / "config.toml"
        base_config.write_text(
            '\n'.join([
                'model = "auto"',
                'profile = "ctf"',
                '',
                '# 安全测试模式（由 codex-session-patcher 添加）',
                '[profiles.ctf]',
                'model_instructions_file = "~/.codex/prompts/ctf_optimized.md"',
                '',
                '[profiles.ctf.features]',
                'js_repl = false',
                '',
                '[projects."/tmp/work"]',
                'trust_level = "trusted"',
                '',
            ]),
            encoding="utf-8",
        )

        installer = CTFConfigInstaller()
        success, message = installer.uninstall()

        assert success, message
        assert not profile_config.exists()
        assert not (prompts_dir / "ctf_optimized.md").exists()
        cleaned_base = base_config.read_text(encoding="utf-8")
        assert 'profile = "ctf"' not in cleaned_base
        assert "[profiles.ctf]" not in cleaned_base
        assert "[profiles.ctf.features]" not in cleaned_base
        assert '[projects."/tmp/work"]' in cleaned_base

    def test_codex_status_reads_v2_profile_config_without_base_config(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.status import check_ctf_status

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        prompt_path = prompts_dir / "ctf_optimized.md"
        prompt_path.write_text(managed_prompt("# Custom CTF"), encoding="utf-8")
        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            f'{PROFILE_MARKER}\ndeveloper_instructions = """\n{managed_prompt("# Custom CTF")}\n"""\n',
            encoding="utf-8",
        )

        status = check_ctf_status()

        assert status.installed is True
        assert status.config_exists is True
        assert status.profile_available is True
        assert status.config_path == str(profile_config)
        assert status.prompt_path == str(prompt_path)
        assert status.prompt_exists is True

    def test_codex_status_ignores_commented_instruction_keys(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.status import check_ctf_status

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        prompt_path = prompts_dir / "ctf_optimized.md"
        prompt_path.write_text(managed_prompt("# Replace CTF"), encoding="utf-8")
        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            '\n'.join([
                PROFILE_MARKER,
                '# developer_instructions = "old"',
                'model_instructions_file = "~/.codex/prompts/ctf_optimized.md"',
                '',
            ]),
            encoding="utf-8",
        )

        status = check_ctf_status()

        assert status.installed is True
        assert status.injection_mode == "replace"
        assert status.prompt_path == str(prompt_path)

    def test_codex_global_install_cleans_legacy_profile_entries(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            f'{PROFILE_MARKER}\ndeveloper_instructions = """\n{managed_prompt("# Custom CTF")}\n"""\n',
            encoding="utf-8",
        )
        base_config = codex_dir / "config.toml"
        base_config.write_text(
            '\n'.join([
                'model = "auto"',
                'profile = "ctf" # legacy selector',
                '',
                '# 安全测试模式（由 codex-session-patcher 添加）',
                '[profiles.ctf]',
                'model_instructions_file = "~/.codex/prompts/ctf_optimized.md"',
                '',
                '[profiles.ctf.features]',
                'js_repl = false',
                '',
                '[projects."/tmp/work"]',
                'trust_level = "trusted"',
                '',
            ]),
            encoding="utf-8",
        )

        installer = CTFConfigInstaller()
        success, message = installer.install_global()

        assert success, message
        assert not profile_config.exists()
        cleaned_base = base_config.read_text(encoding="utf-8")
        assert 'profile = "ctf"' not in cleaned_base
        assert "[profiles.ctf]" not in cleaned_base
        assert "[profiles.ctf.features]" not in cleaned_base
        assert '[projects."/tmp/work"]' in cleaned_base
        assert 'model_instructions_file' not in cleaned_base
        assert 'developer_instructions = """' in cleaned_base
        assert 'CTF' in cleaned_base

    def test_codex_global_install_can_replace_builtin_instructions_with_prompt_file(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller
        from codex_session_patcher.ctf_config.status import GLOBAL_MARKER, check_ctf_status

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install_global(injection_mode="replace")

        assert success, message
        base_config = tmp_path / ".codex" / "config.toml"
        config_content = base_config.read_text(encoding="utf-8")
        assert GLOBAL_MARKER in config_content
        assert 'developer_instructions' not in config_content
        assert 'model_instructions_file = "~/.codex/prompts/ctf_optimized.md"' in config_content

        status = check_ctf_status()
        assert status.global_installed is True
        assert status.global_injection_mode == "replace"

    def test_codex_global_install_switches_replace_back_to_append(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install_global(injection_mode="replace")
        assert success, message

        success, message = installer.install_global(injection_mode="append")
        assert success, message
        config_content = (tmp_path / ".codex" / "config.toml").read_text(encoding="utf-8")
        assert 'developer_instructions = """' in config_content
        assert 'model_instructions_file' not in config_content

    def test_codex_global_install_refuses_unmanaged_developer_instructions(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller
        from codex_session_patcher.ctf_config.status import GLOBAL_MARKER

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        base_config = codex_dir / "config.toml"
        original = '\n'.join([
            'developer_instructions = "existing"',
            '',
            '[features]',
            'guardian_approval = false',
            '',
        ])
        base_config.write_text(original, encoding="utf-8")

        installer = CTFConfigInstaller()
        success, message = installer.install_global(injection_mode="append")

        assert success is False
        assert "顶层已有 developer_instructions" in message
        assert base_config.read_text(encoding="utf-8") == original
        assert GLOBAL_MARKER not in base_config.read_text(encoding="utf-8")

    def test_codex_global_install_refuses_unmanaged_model_instructions_file(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        base_config = codex_dir / "config.toml"
        original = '\n'.join([
            'model_instructions_file = "~/.codex/prompts/existing.md"',
            '',
            '[features]',
            'guardian_approval = false',
            '',
        ])
        base_config.write_text(original, encoding="utf-8")

        installer = CTFConfigInstaller()
        success, message = installer.install_global(injection_mode="replace")

        assert success is False
        assert "顶层已有 model_instructions_file" in message
        assert base_config.read_text(encoding="utf-8") == original

    def test_codex_uninstall_preserves_unmanaged_legacy_profile(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        base_config = codex_dir / "config.toml"
        original = '\n'.join([
            'profile = "ctf"',
            '',
            '[profiles.ctf]',
            'model = "user-owned"',
            '',
        ])
        base_config.write_text(original, encoding="utf-8")

        success, message = CTFConfigInstaller().uninstall()

        assert success, message
        assert base_config.read_text(encoding="utf-8") == original

    def test_codex_install_refuses_unmanaged_legacy_profile(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        base_config = codex_dir / "config.toml"
        original = '\n'.join([
            'profile = "ctf"',
            '',
            '[profiles.ctf]',
            'model = "user-owned"',
            '',
        ])
        base_config.write_text(original, encoding="utf-8")

        success, message = CTFConfigInstaller().install(custom_prompt="# New CTF")

        assert success is False
        assert "没有本工具历史标记" in message
        assert base_config.read_text(encoding="utf-8") == original
        assert not (codex_dir / "ctf.config.toml").exists()

    def test_codex_global_uninstall_removes_managed_developer_instructions_block(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller
        from codex_session_patcher.ctf_config.status import GLOBAL_MARKER

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        codex_dir.mkdir()
        base_config = codex_dir / "config.toml"
        base_config.write_text(
            '\n'.join([
                'model = "auto"',
                f'{GLOBAL_MARKER} 安全测试模式（由 codex-session-patcher 管理）',
                'developer_instructions = """',
                '# Custom CTF',
                '"""',
                '',
                '[projects."/tmp/work"]',
                'trust_level = "trusted"',
                '',
            ]),
            encoding="utf-8",
        )

        installer = CTFConfigInstaller()
        success, message = installer.uninstall_global()

        assert success, message
        cleaned_base = base_config.read_text(encoding="utf-8")
        assert GLOBAL_MARKER not in cleaned_base
        assert 'developer_instructions = """' not in cleaned_base
        assert '# Custom CTF' not in cleaned_base
        assert 'model = "auto"' in cleaned_base
        assert '[projects."/tmp/work"]' in cleaned_base

    def test_codex_prompt_save_updates_profile_developer_instructions(self, tmp_path, monkeypatch):
        from web.backend import api

        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(tmp_path / ".codex-patcher" / "config.json"))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        prompt_path = prompts_dir / "ctf_optimized.md"
        prompt_path.write_text(managed_prompt("# Old Prompt"), encoding="utf-8")
        monkeypatch.setitem(api._CTF_PROMPT_PATHS, "codex", str(prompt_path))

        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            '\n'.join([
                PROFILE_MARKER,
                'developer_instructions = """',
                managed_prompt('# Old Prompt'),
                '"""',
                'model = "gpt-5.1-codex-max"',
                '',
            ]),
            encoding="utf-8",
        )

        asyncio.run(api.save_ctf_prompt("codex", {"prompt": "# New Prompt"}))

        profile_content = profile_config.read_text(encoding="utf-8")
        assert "# New Prompt" in profile_content
        assert "# Old Prompt" not in profile_content
        assert 'model = "gpt-5.1-codex-max"' in profile_content
        assert prompt_path.read_text(encoding="utf-8") == managed_prompt("# New Prompt")

    def test_prompt_save_does_not_overwrite_unmanaged_workspace_file(self, tmp_path, monkeypatch):
        from web.backend import api

        monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(tmp_path / "config.json"))
        prompt_path = tmp_path / "opencode" / "AGENTS.md"
        prompt_path.parent.mkdir()
        prompt_path.write_text("USER OWNED", encoding="utf-8")
        monkeypatch.setitem(api._CTF_PROMPT_PATHS, "opencode", str(prompt_path))

        result = asyncio.run(api.save_ctf_prompt("opencode", {"prompt": "# Saved for later"}))

        assert result["success"] is True
        assert prompt_path.read_text(encoding="utf-8") == "USER OWNED"
        saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
        assert saved["ctf_prompts"]["opencode"]["prompt"] == "# Saved for later"

    def test_codex_prompt_get_reads_profile_developer_instructions(self, tmp_path, monkeypatch):
        from web.backend import api

        monkeypatch.setenv("HOME", str(tmp_path))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        prompt_path = prompts_dir / "ctf_optimized.md"
        prompt_path.write_text("# Stale File Prompt", encoding="utf-8")
        monkeypatch.setitem(api._CTF_PROMPT_PATHS, "codex", str(prompt_path))

        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            f'{PROFILE_MARKER}\ndeveloper_instructions = """\n# Effective Prompt\n"""\n',
            encoding="utf-8",
        )

        result = asyncio.run(api.get_ctf_prompt("codex"))

        assert result["prompt"] == "# Effective Prompt"
        assert result["is_installed"] is True

    def test_codex_prompt_save_updates_global_developer_instructions(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.status import GLOBAL_MARKER
        from web.backend import api

        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(tmp_path / ".codex-patcher" / "config.json"))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        prompt_path = prompts_dir / "ctf_optimized.md"
        prompt_path.write_text("# Old Prompt", encoding="utf-8")
        monkeypatch.setitem(api._CTF_PROMPT_PATHS, "codex", str(prompt_path))

        base_config = codex_dir / "config.toml"
        base_config.write_text(
            '\n'.join([
                'model = "auto"',
                f'{GLOBAL_MARKER} 安全测试模式（由 codex-session-patcher 管理）',
                'developer_instructions = """',
                '# Old Prompt',
                '"""',
                '',
                '[projects."/tmp/work"]',
                'trust_level = "trusted"',
                '',
            ]),
            encoding="utf-8",
        )

        asyncio.run(api.save_ctf_prompt("codex", {"prompt": "# New Global Prompt"}))

        config_content = base_config.read_text(encoding="utf-8")
        assert "# New Global Prompt" in config_content
        assert "# Old Prompt" not in config_content
        assert '[projects."/tmp/work"]' in config_content
        assert prompt_path.read_text(encoding="utf-8") == managed_prompt("# New Global Prompt")

    def test_codex_prompt_reset_updates_profile_developer_instructions(self, tmp_path, monkeypatch):
        from web.backend import api

        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(tmp_path / ".codex-patcher" / "config.json"))
        codex_dir = tmp_path / ".codex"
        prompts_dir = codex_dir / "prompts"
        prompts_dir.mkdir(parents=True)
        prompt_path = prompts_dir / "ctf_optimized.md"
        prompt_path.write_text(managed_prompt("# Old Prompt"), encoding="utf-8")
        monkeypatch.setitem(api._CTF_PROMPT_PATHS, "codex", str(prompt_path))

        profile_config = codex_dir / "ctf.config.toml"
        profile_config.write_text(
            f'{PROFILE_MARKER}\ndeveloper_instructions = """\n{managed_prompt("# Old Prompt")}\n"""\n',
            encoding="utf-8",
        )

        default_prompt = api._get_default_prompt("codex")
        asyncio.run(api.reset_ctf_prompt("codex"))

        assert api._read_codex_developer_instructions() == default_prompt
        profile_content = profile_config.read_text(encoding="utf-8")
        assert "# Old Prompt" not in profile_content
        assert prompt_path.read_text(encoding="utf-8") == default_prompt

    def test_codex_installer_uses_default_without_custom(self, tmp_path):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        installer = CTFConfigInstaller()
        installer.codex_dir = str(tmp_path / ".codex")
        installer.config_path = os.path.join(installer.codex_dir, "config.toml")
        installer.profile_config_path = os.path.join(installer.codex_dir, "ctf.config.toml")
        installer.prompts_dir = os.path.join(installer.codex_dir, "prompts")

        success, _ = installer.install()
        assert success

        # install() 写入的文件由 _get_prompt_file() 决定，默认为 ctf_optimized.md
        prompt_file = installer._get_prompt_file()
        actual_path = os.path.join(installer.prompts_dir, prompt_file)
        with open(actual_path, 'r') as f:
            content = f.read()
        # 默认内容应来自 BUILTIN_TEMPLATES 中标记为 default 的模板
        assert len(content) > 100

    def test_claude_installer_accepts_custom_prompt(self, tmp_path):
        from codex_session_patcher.ctf_config.installer import ClaudeCodeCTFInstaller

        installer = ClaudeCodeCTFInstaller()
        installer.workspace_dir = str(tmp_path / "claude-ctf")
        installer.claude_dir = os.path.join(installer.workspace_dir, ".claude")
        installer.prompt_path = os.path.join(installer.claude_dir, "CLAUDE.md")
        installer.readme_path = os.path.join(installer.workspace_dir, "README.md")
        installer.settings_local = str(tmp_path / "settings.local.json")

        custom = "# My Custom Claude Prompt"
        success, _ = installer.install(custom_prompt=custom)
        assert success

        with open(installer.prompt_path, 'r') as f:
            content = f.read()
        assert content == managed_prompt(custom)

        success, message = installer.uninstall()
        assert success, message
        assert not os.path.exists(installer.prompt_path)

    def test_claude_install_refuses_unmanaged_prompt(self, tmp_path):
        from codex_session_patcher.ctf_config.installer import ClaudeCodeCTFInstaller

        installer = ClaudeCodeCTFInstaller()
        installer.workspace_dir = str(tmp_path / "claude-ctf")
        installer.claude_dir = os.path.join(installer.workspace_dir, ".claude")
        installer.prompt_path = os.path.join(installer.claude_dir, "CLAUDE.md")
        installer.readme_path = os.path.join(installer.workspace_dir, "README.md")
        installer.settings_local = str(tmp_path / "settings.local.json")
        os.makedirs(installer.claude_dir)
        with open(installer.prompt_path, "w", encoding="utf-8") as stream:
            stream.write("USER OWNED")

        success, message = installer.install(custom_prompt="# Custom")

        assert success is False
        assert "没有本工具管理标记" in message
        assert open(installer.prompt_path, encoding="utf-8").read() == "USER OWNED"

    def test_codex_uninstall_preserves_unrelated_markdown(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install()
        assert success, message

        unrelated = tmp_path / ".codex" / "prompts" / "notes.md"
        unrelated.write_text("# User notes", encoding="utf-8")

        success, message = installer.uninstall()

        assert success, message
        assert unrelated.read_text(encoding="utf-8") == "# User notes"

    def test_codex_uninstall_preserves_other_profile_settings(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install()
        assert success, message

        profile_path = tmp_path / ".codex" / "ctf.config.toml"
        profile_path.write_text(
            profile_path.read_text(encoding="utf-8")
            + 'model = "gpt-test"\n\n[features]\nweb_search = true\n',
            encoding="utf-8",
        )

        success, message = installer.uninstall()

        assert success, message
        remaining = profile_path.read_text(encoding="utf-8")
        assert 'model = "gpt-test"' in remaining
        assert "[features]" in remaining
        assert "web_search = true" in remaining
        assert "developer_instructions" not in remaining

    def test_codex_uninstall_preserves_drifted_managed_prompt(self, tmp_path, monkeypatch):
        from codex_session_patcher.ctf_config.installer import CTFConfigInstaller

        monkeypatch.setenv("HOME", str(tmp_path))
        installer = CTFConfigInstaller()
        success, message = installer.install()
        assert success, message

        prompt_path = tmp_path / ".codex" / "prompts" / "ctf_optimized.md"
        prompt_path.write_text("# User changed prompt", encoding="utf-8")

        success, message = installer.uninstall()

        assert success, message
        assert "已保留" in message
        assert prompt_path.read_text(encoding="utf-8") == "# User changed prompt"

    def test_claude_uninstall_preserves_modified_readme(self, tmp_path):
        from codex_session_patcher.ctf_config.installer import ClaudeCodeCTFInstaller

        installer = ClaudeCodeCTFInstaller()
        installer.workspace_dir = str(tmp_path / "claude-ctf")
        installer.claude_dir = os.path.join(installer.workspace_dir, ".claude")
        installer.prompt_path = os.path.join(installer.claude_dir, "CLAUDE.md")
        installer.readme_path = os.path.join(installer.workspace_dir, "README.md")
        installer.settings_local = str(tmp_path / "settings.local.json")
        success, message = installer.install()
        assert success, message

        modified = "# User README\n"
        with open(installer.readme_path, "w", encoding="utf-8") as stream:
            stream.write(modified)

        success, message = installer.uninstall()

        assert success, message
        assert "README 已被修改，已保留" in message
        assert open(installer.readme_path, encoding="utf-8").read() == modified

    def test_opencode_uninstall_preserves_modified_config(self, tmp_path):
        from codex_session_patcher.ctf_config.installer import OpenCodeCTFInstaller

        installer = OpenCodeCTFInstaller()
        installer.workspace_dir = str(tmp_path / "opencode-ctf")
        installer.agents_md_path = os.path.join(installer.workspace_dir, "AGENTS.md")
        installer.config_path = os.path.join(installer.workspace_dir, "opencode.json")
        installer.readme_path = os.path.join(installer.workspace_dir, "README.md")
        success, message = installer.install()
        assert success, message

        modified = '{"user": true}\n'
        with open(installer.config_path, "w", encoding="utf-8") as stream:
            stream.write(modified)

        success, message = installer.uninstall()

        assert success, message
        assert "opencode.json 已被修改，已保留" in message
        assert open(installer.config_path, encoding="utf-8").read() == modified


class TestCTFStatus:
    """验证 CTFStatus 包含 OpenCode 字段"""

    def test_status_has_opencode_fields(self):
        from codex_session_patcher.ctf_config.status import CTFStatus
        status = CTFStatus()
        assert hasattr(status, 'opencode_installed')
        assert hasattr(status, 'opencode_workspace_exists')
        assert hasattr(status, 'opencode_prompt_exists')
        assert hasattr(status, 'opencode_workspace_path')
        assert hasattr(status, 'opencode_prompt_path')
        assert status.opencode_installed is False
