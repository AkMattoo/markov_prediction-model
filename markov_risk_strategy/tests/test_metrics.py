"""Risk metrics (ECL, drift, PD) tests."""

from __future__ import annotations

import numpy as np
import pytest

from markov_risk.chain import MarkovChain
from markov_risk.metrics import Obligor, Portfolio, RiskMetricsEngine
from markov_risk.states import Rating
from markov_risk.transition import TransitionMatrix


@pytest.fixture
def sample_portfolio() -> Portfolio:
    return Portfolio(
        [
            Obligor("Acme Corp", Rating.A, 1_000_000, 0.45),
            Obligor("BBB Issuer", Rating.BBB, 500_000, 0.40),
            Obligor("Speculative Co", Rating.B, 250_000, 0.60),
            Obligor("Distressed LLC", Rating.CCC, 100_000, 0.75),
        ]
    )


def test_ecl_is_non_negative(sample_matrix, sample_portfolio):
    engine = RiskMetricsEngine(MarkovChain(sample_matrix, seed=1), sample_portfolio)
    m = engine.compute(horizon=5, n_paths=5000)
    assert m.ecl.total_ecl >= 0
    for v in m.ecl.per_obligor.values():
        assert v >= 0


def test_ecl_is_monotonic_in_horizon(sample_matrix, sample_portfolio):
    chain = MarkovChain(sample_matrix, seed=11)
    engine = RiskMetricsEngine(chain, sample_portfolio)
    e1 = engine.compute(horizon=1, n_paths=3000).ecl.total_ecl
    e3 = engine.compute(horizon=3, n_paths=3000).ecl.total_ecl
    e5 = engine.compute(horizon=5, n_paths=3000).ecl.total_ecl
    assert e1 <= e3 + 1e-6
    assert e3 <= e5 + 1e-6


def test_analytical_pd_matches_n_step_matrix(sample_matrix, sample_portfolio):
    chain = MarkovChain(sample_matrix, seed=2)
    engine = RiskMetricsEngine(chain, sample_portfolio)
    apd = engine.analytical_pd(horizon=5)
    # Compare against chain.cumulative_default_probability directly.
    for o in sample_portfolio.obligors:
        expected = chain.cumulative_default_probability(o.rating, 5)[5]
        assert apd[o.name] == pytest.approx(expected, abs=1e-10)


def test_drift_distribution_sums_to_one(sample_matrix, sample_portfolio):
    engine = RiskMetricsEngine(MarkovChain(sample_matrix, seed=4), sample_portfolio)
    m = engine.compute(horizon=10, n_paths=2000)
    probs = m.drift.probabilities()
    assert sum(probs.values()) == pytest.approx(1.0, abs=1e-9)


def test_high_rated_obligor_has_lower_simulated_pd_than_low_rated(sample_matrix):
    portfolio = Portfolio(
        [
            Obligor("Safe", Rating.AAA, 1_000_000, 0.45),
            Obligor("Risky", Rating.CCC, 1_000_000, 0.45),
        ]
    )
    engine = RiskMetricsEngine(MarkovChain(sample_matrix, seed=9), portfolio)
    m = engine.compute(horizon=10, n_paths=10_000)
    assert m.per_obligor_pd["Safe"] < m.per_obligor_pd["Risky"]


def test_portfolio_validates_lgd_range():
    with pytest.raises(ValueError, match="LGD"):
        Portfolio([Obligor("Bad", Rating.A, 1000, 1.5)])


def test_portfolio_validates_negative_ead():
    with pytest.raises(ValueError, match="EAD"):
        Portfolio([Obligor("Bad", Rating.A, -1, 0.5)])


def test_empty_portfolio_rejected():
    with pytest.raises(ValueError, match="at least one"):
        Portfolio([])
