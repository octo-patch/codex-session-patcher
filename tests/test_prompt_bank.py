import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_prompt_bank_regression.py"


def load_runner():
    spec = importlib.util.spec_from_file_location("prompt_bank_runner", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_default_prompt_satisfies_offline_prompt_bank():
    runner = load_runner()

    cases = runner.load_bank(runner.DEFAULT_BANK)
    errors = runner.validate_prompt_contract(runner.DEFAULT_PROMPT, cases)

    assert len(cases) == 12
    assert errors == []


def test_prompt_bank_rejects_missing_contract_text(tmp_path):
    runner = load_runner()
    prompt = tmp_path / "prompt.md"
    prompt.write_text("## Layer 1 — Universal Execution Rules\n", encoding="utf-8")

    cases = runner.load_bank(runner.DEFAULT_BANK)
    errors = runner.validate_prompt_contract(prompt, cases)

    assert errors
    assert any("web-api-chain" in error for error in errors)
