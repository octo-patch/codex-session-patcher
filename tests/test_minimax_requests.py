"""Exercise the real rewrite callers through serialized, offline HTTP requests."""

import asyncio
import copy
import json

import httpx
import pytest

from web.backend import api, llm_client
from web.backend.ai_service import call_llm
from web.backend.main import app
from web.backend.prompt_rewriter import rewrite_prompt
from web.backend.schemas import Settings


@pytest.fixture
def outgoing_requests(monkeypatch):
    requests = []
    real_client = httpx.AsyncClient

    def respond(request):
        requests.append(request)
        return httpx.Response(200, json={
            "choices": [{"message": {"content": "A concise answer."}}]
        })

    monkeypatch.setattr(
        llm_client.httpx, "AsyncClient",
        lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    return requests


@pytest.mark.parametrize("endpoint", [
    "https://api.minimax.io/v1",
    "https://api.minimaxi.com/v1/",
    "https://api.minimax.io/v1/chat/completions",
])
@pytest.mark.parametrize("caller", ["session", "prompt"])
def test_flash_rewrite_request(endpoint, caller, outgoing_requests):
    messages = [{"role": "user", "content": "Summarize this local project."}]
    if caller == "session":
        result = asyncio.run(call_llm(
            Settings(ai_endpoint=endpoint, ai_model="MiniMax-M3.1-Flash"), messages
        ))
    else:
        result, _ = asyncio.run(rewrite_prompt(
            messages[0]["content"], endpoint, "", "MiniMax-M3.1-Flash"
        ))
    assert result == "A concise answer."
    assert len(outgoing_requests) == 1
    request = outgoing_requests[0]
    assert str(request.url) == llm_client.build_chat_completions_endpoint(endpoint)
    body = json.loads(request.content)
    assert set(body) == {"model", "messages", "max_completion_tokens", "reasoning_effort"}
    assert body["model"] == "MiniMax-M3.1-Flash"
    assert body["max_completion_tokens"] == 16384
    assert body["reasoning_effort"] == "low"
    if caller == "session":
        assert body["messages"] == messages
    else:
        assert [message["role"] for message in body["messages"]] == ["system", "user"]
        assert messages[0]["content"] in body["messages"][1]["content"]


@pytest.mark.parametrize("endpoint,model", [
    ("https://api.minimax.io/v1", "MiniMax-M3"),
    ("https://api.minimaxi.com/v1", "MiniMax-M3"),
    ("https://api.minimaxi.com/v1", "MiniMax-M2.7"),
    ("https://api.minimax.io/v1", "MiniMax-M2.7-highspeed"),
    ("https://api.minimax.io/v1", "saved-custom-model"),
    ("https://gateway.example/v1", "MiniMax-M3.1-Flash"),
    ("https://api.minimax.io.example/v1", "MiniMax-M3.1-Flash"),
    ("https://api.minimax.io/custom/v1", "MiniMax-M3.1-Flash"),
    ("https://gateway.example/v1", "custom-model"),
])
@pytest.mark.parametrize("caller", ["session", "prompt"])
def test_saved_and_custom_requests_keep_existing_parameters(
    endpoint, model, caller, outgoing_requests
):
    messages = [{"role": "user", "content": "Summarize this local project."}]
    if caller == "session":
        asyncio.run(call_llm(Settings(ai_endpoint=endpoint, ai_model=model), messages))
    else:
        asyncio.run(rewrite_prompt(messages[0]["content"], endpoint, "", model))
    request = outgoing_requests[0]
    assert str(request.url) == endpoint + "/chat/completions"
    body = json.loads(request.content)
    assert set(body) == {"model", "messages", "max_tokens", "temperature"}
    assert body["model"] == model
    assert body["max_tokens"] == 1024
    assert body["temperature"] == 0.7


def test_flash_preserves_multimodal_tool_and_reasoning_history(outgoing_requests):
    messages = [
        {"role": "user", "content": [
            {"type": "text", "text": "Summarize these inputs."},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.png"}},
            {"type": "video_url", "video_url": {"url": "mm_file://example"}},
        ]},
        {"role": "assistant", "content": "", "reasoning_content": "Inspect the inputs.",
         "tool_calls": [{"id": "call_1", "type": "function",
                         "function": {"name": "inspect", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "call_1", "content": "Inspection complete."},
    ]
    original = copy.deepcopy(messages)
    asyncio.run(call_llm(Settings(
        ai_endpoint="https://api.minimax.io/v1", ai_model="MiniMax-M3.1-Flash"
    ), messages))
    assert json.loads(outgoing_requests[0].content)["messages"] == original
    assert messages == original


@pytest.mark.parametrize("model", ["MiniMax-M3.1-Flash", "MiniMax-M3", "MiniMax-M2.7", "custom-model"])
def test_saved_model_survives_settings_round_trip(model, monkeypatch, tmp_path, asgi_client_factory):
    config = tmp_path / "config.json"
    saved = {"ai_endpoint": "https://api.minimaxi.com/v1", "ai_model": model}
    config.write_text(json.dumps(saved), encoding="utf-8")
    monkeypatch.setattr(api, "DEFAULT_CONFIG_FILE", str(config))
    client = asgi_client_factory(app)
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert response.json()["ai_model"] == model
    assert response.json()["ai_endpoint"] == saved["ai_endpoint"]
    assert client.put("/api/settings", json=response.json()).status_code == 200
    stored = json.loads(config.read_text(encoding="utf-8"))
    assert stored["ai_model"] == model
    assert stored["ai_endpoint"] == saved["ai_endpoint"]
