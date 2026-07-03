"""Structured-output narrator for risk reports."""

from __future__ import annotations

from typing import Any

import pydantic

from markov_risk.llm.client import LLMClient, TokenUsage
from markov_risk.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from markov_risk.metrics import Portfolio, RiskMetrics
from markov_risk.transition import TransitionMatrix


class NarrativeReport(pydantic.BaseModel):
    """The narrator's structured output. Guaranteed-schema via the LLM client."""

    summary: str = pydantic.Field(..., description="2-4 sentence CRO-facing summary.")
    key_risks: list[str] = pydantic.Field(
        ..., min_length=1, max_length=10, description="Specific, grounded risks."
    )
    recommendations: list[str] = pydantic.Field(
        ..., min_length=1, max_length=10, description="Concrete risk-reduction actions."
    )
    confidence_notes: str = pydantic.Field(
        ..., description="Notes on data quality and horizon uncertainty."
    )


class RiskNarrator:
    """Coordinates the LLM call: builds prompts, calls client, returns report."""

    def __init__(self, client: LLMClient):
        self.client = client

    def narrate(
        self,
        portfolio: Portfolio,
        transition: TransitionMatrix,
        metrics: RiskMetrics,
        analytical_pd: dict[str, float] | None = None,
    ) -> tuple[NarrativeReport, TokenUsage]:
        user_prompt = build_user_prompt(
            portfolio=portfolio,
            transition=transition,
            metrics=metrics,
            analytical_pd=analytical_pd,
        )
        result = self.client.complete_structured(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=NarrativeReport,
        )
        # result.parsed is guaranteed to be NarrativeReport because the client
        # validates. We assert for the type checker.
        assert isinstance(result.parsed, NarrativeReport)
        return result.parsed, result.usage
