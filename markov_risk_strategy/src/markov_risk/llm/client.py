"""LLM client abstraction.

Two backends -- Anthropic (primary) and OpenAI-compatible -- share the
``LLMClient`` protocol. The narrator uses ``complete_structured`` with a
pydantic schema so the response is guaranteed to validate.

Provider choice is by environment / constructor; no live API key is needed
for tests because the client is mocked.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

import pydantic


class LLMError(RuntimeError):
    """Raised when an LLM call fails after retries."""


@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class CompletionResult:
    """The LLM's reply, already parsed into the requested pydantic model."""

    parsed: pydantic.BaseModel
    usage: TokenUsage
    raw_text: str


class LLMClient(Protocol):
    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[pydantic.BaseModel],
        *,
        max_retries: int = 3,
    ) -> CompletionResult: ...


# ----- Anthropic backend --------------------------------------------------


class AnthropicClient:
    """Wrapper around the Anthropic Python SDK with retry + structured output.

    Uses the SDK's tool-use / structured-output feature so the model is
    forced to produce JSON matching the supplied pydantic schema.
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        client: Any | None = None,
    ):
        self.model = model
        if client is not None:
            self._client = client
        else:
            try:
                from anthropic import Anthropic  # type: ignore[import-not-found]
            except ImportError as e:
                raise LLMError(
                    "anthropic SDK is not installed. pip install anthropic"
                ) from e
            self._client = Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[pydantic.BaseModel],
        *,
        max_retries: int = 3,
    ) -> CompletionResult:
        schema_json = json.dumps(schema.model_json_schema())
        # System instructions + a tool definition the model is forced to use.
        tool_name = "emit_report"
        tool_desc = (
            f"Emit the final report as JSON conforming to the {schema.__name__} schema."
        )
        messages = [{"role": "user", "content": user}]
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    system=system,
                    tools=[
                        {
                            "name": tool_name,
                            "description": tool_desc,
                            "input_schema": json.loads(schema_json),
                        }
                    ],
                    tool_choice={"type": "tool", "name": tool_name},
                    messages=messages,
                )
                break
            except Exception as e:  # network / rate-limit; retry with backoff
                if attempt >= max_retries:
                    raise LLMError(f"Anthropic call failed after {max_retries} retries: {e}") from e
                time.sleep(2 ** (attempt - 1))
        # Extract the tool-use block.
        tool_block = next(
            (b for b in resp.content if getattr(b, "type", None) == "tool_use"),
            None,
        )
        if tool_block is None:
            raise LLMError("Anthropic response did not contain a tool_use block")
        raw = tool_block.input  # dict matching the schema
        parsed = schema.model_validate(raw)
        usage = TokenUsage(
            input_tokens=getattr(resp.usage, "input_tokens", 0),
            output_tokens=getattr(resp.usage, "output_tokens", 0),
        )
        return CompletionResult(parsed=parsed, usage=usage, raw_text=json.dumps(raw))


# ----- OpenAI backend -----------------------------------------------------


class OpenAIClient:
    """OpenAI-compatible client using JSON mode + pydantic validation."""

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        client: Any | None = None,
    ):
        self.model = model
        if client is not None:
            self._client = client
        else:
            try:
                from openai import OpenAI  # type: ignore[import-not-found]
            except ImportError as e:
                raise LLMError("openai SDK is not installed. pip install openai") from e
            self._client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    def complete_structured(
        self,
        system: str,
        user: str,
        schema: type[pydantic.BaseModel],
        *,
        max_retries: int = 3,
    ) -> CompletionResult:
        schema_json = json.dumps(schema.model_json_schema())
        sys_with_schema = (
            f"{system}\n\nYou MUST respond with JSON matching this schema:\n{schema_json}"
        )
        attempt = 0
        while True:
            attempt += 1
            try:
                resp = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": sys_with_schema},
                        {"role": "user", "content": user},
                    ],
                    response_format={"type": "json_object"},
                )
                break
            except Exception as e:
                if attempt >= max_retries:
                    raise LLMError(f"OpenAI call failed after {max_retries} retries: {e}") from e
                time.sleep(2 ** (attempt - 1))
        raw_text = resp.choices[0].message.content or ""
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError as e:
            raise LLMError(f"OpenAI returned non-JSON response: {raw_text!r}") from e
        parsed = schema.model_validate(data)
        usage = TokenUsage(
            input_tokens=getattr(resp.usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(resp.usage, "completion_tokens", 0) or 0,
        )
        return CompletionResult(parsed=parsed, usage=usage, raw_text=raw_text)


def make_client(provider: str, **kwargs: Any) -> LLMClient:
    """Factory: ``"anthropic"`` / ``"openai"`` / ``"mock"`` (raises -- for tests)."""
    p = provider.lower()
    if p == "anthropic":
        return AnthropicClient(**kwargs)
    if p == "openai":
        return OpenAIClient(**kwargs)
    raise LLMError(f"Unknown provider: {provider!r}")
