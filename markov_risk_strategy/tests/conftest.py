"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from markov_risk.transition import TransitionMatrix

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_matrix() -> TransitionMatrix:
    return TransitionMatrix.from_json(FIXTURE_DIR / "sample_matrix.json")
