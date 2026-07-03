"""Narrator tests. The LLM client is mocked so this runs without API keys."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pydantic
import pytest

from markov_risk.chain import MarkovChain
from markov_risk.llm.client import (
    AnthropicClient,
    OpenAIClient,
    TokenUsage,
    CompletionResult,
)
from markov_risk.llm.narrator import NarrativeReport, RiskNarrator
from markov_risk.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from markov_risk.metrics import Obligor, Portfolio, RiskMetrics, RiskMetricsEngine
from markov_risk.states import Rating


@pytest.fixture
def tiny_portfolio() -> Portfolio:
    return Portfolio(
        [
            Obligor("Safe Inc", Rating.AAA, 1_000_000, 0.45),
            Obligor("Risky Co", Rating.B, 250_000, 0.60),
        ]
    )


def test_system_prompt_has_role_anchor():
    assert "credit risk analyst" in SYSTEM_PROMPT.lower()
    assert "json" in SYSTEM_PROMPT.lower()


def test_user_prompt_contains_portfolio_matrix_metrics(sample_matrix, tiny_portfolio):
    chain = MarkovChain(sample_matrix, seed=0)
    engine = RiskMetricsEngine(chain, tiny_portfolio)
    m = engine.compute(horizon=5, n_paths=500)
    user = build_user_prompt(
        portfolio=tiny_portfolio,
        transition=sample_matrix,
        metrics=m,
        analytical_pd=engine.analytical_pd(5),
    )
    # All three artifacts present.
    assert "Safe Inc" in user
    assert "Risky Co" in user
    assert "AAA" in user and "D" in user  # matrix rows
    assert "ECL" in user or "Expected Credit Loss" in user
    # Anti-injection note is in the system prompt (and possibly echoed).
    assert "prompt injection" in SYSTEM_PROMPT.lower()


class _FakeClient:
    """In-process stand-in for LLMClient."""

    def __init__(self, payload: dict[str, Any]):
        self._payload = payload
        self.last_system: str | None = None
        self.last_user: str | None = None
        self.last_schema: type[pydantic.BaseModel] | None = None
        self.calls = 0

    def complete_structured(self, system, user, schema, *, max_retries=3):
        self.calls += 1
        self.last_system = system
        self.last_user = user
        self.last_schema = schema
        return CompletionResult(
            parsed=schema.model_validate(self._payload),
            usage=TokenUsage(input_tokens=120, output_tokens=80),
            raw_text=json.dumps(self._payload),
        )


def test_narrator_validates_and_returns_report(sample_matrix, tiny_portfolio):
    chain = MarkovChain(sample_matrix, seed=0)
    engine = RiskMetricsEngine(chain, tiny_portfolio)
    m = engine.compute(horizon=5, n_paths=500)
    fake = _FakeClient(
        {
            "summary": "Portfolio is well-rated overall with one speculative name.",
            "key_risks": [
                "Risky Co carries 0.60 LGD and is the dominant default driver.",
                "Concentration in the B bucket above peer benchmark.",
            ],
            "recommendations": [
                "Cap single-obligor exposure to 5% of EAD.",
                "Place Risky Co on the watch list and review quarterly.",
            ],
            "confidence_notes": "Based on a 5-year horizon and 500 simulated paths.",
        }
    )
    narrator = RiskNarrator(fake)  # type: ignore[arg-type]
    report, usage = narrator.narrate(
        portfolio=tiny_portfolio,
        transition=sample_matrix,
        metrics=m,
        analytical_pd=engine.analytical_pd(5),
    )
    assert isinstance(report, NarrativeReport)
    assert len(report.key_risks) == 2
    assert len(report.recommendations) == 2
    assert fake.calls == 1
    assert fake.last_schema is NarrativeReport
    assert usage.input_tokens == 120
    assert "Risky Co" in (fake.last_user or "")


def test_narrator_rejects_invalid_payload(sample_matrix, tiny_portfolio):
    chain = MarkovChain(sample_matrix, seed=0)
    engine = RiskMetricsEngine(chain, tiny_portfolio)
    m = engine.compute(horizon=5, n_paths=500)
    # Missing required fields -> pydantic validation failure.
    fake = _FakeClient({"summary": "incomplete"})
    narrator = RiskNarrator(fake)  # type: ignore[arg-type]
    with pytest.raises(pydantic.ValidationError):
        narrator.narrate(
            portfolio=tiny_portfolio,
            transition=sample_matrix,
            metrics=m,
        )


def test_anthropic_client_force_tool_choice(monkeypatch):
    """Verify that AnthropicClient invokes tool_choice forcing."""
    anthropic = pytest.importorskip("anthropic")
    captured = {}

    class _FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            block = MagicMock()
            block.type = "tool_use"
            block.input = {
                "summary": "x",
                "key_risks": ["a"],
                "recommendations": ["b"],
                "confidence_notes": "c",
            }
            resp = MagicMock()
            resp.content = [block]
            resp.usage.input_tokens = 10
            resp.usage.output_tokens = 5
            return resp

    class _FakeAnthropicFactory:
        def __init__(self, api_key=None):
            self.messages = _FakeMessages()

    monkeypatch.setattr(anthropic, "Anthropic", _FakeAnthropicFactory)
    client = AnthropicClient(api_key="test")
    result = client.complete_structured("sys", "usr", NarrativeReport)
    assert captured["tool_choice"] == {"type": "tool", "name": "emit_report"}
    assert isinstance(result.parsed, NarrativeReport)


def test_openai_client_uses_json_mode(monkeypatch):
    openai = pytest.importorskip("openai")
    captured = {}

    class _FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            choice = MagicMock()
            choice.message.content = json.dumps(
                {
                    "summary": "x",
                    "key_risks": ["a"],
                    "recommendations": ["b"],
                    "confidence_notes": "c",
                }
            )
            resp = MagicMock()
            resp.choices = [choice]
            resp.usage.prompt_tokens = 7
            resp.usage.completion_tokens = 3
            return resp

    class _FakeOpenAI:
        def __init__(self, api_key=None):
            self.chat = MagicMock()
            self.chat.completions = _FakeCompletions()

    monkeypatch.setattr(openai, "OpenAI", _FakeOpenAI)
    client = OpenAIClient(api_key="test")
    result = client.complete_structured("sys", "usr", NarrativeReport)
    assert captured["response_format"] == {"type": "json_object"}
    assert isinstance(result.parsed, NarrativeReport)
