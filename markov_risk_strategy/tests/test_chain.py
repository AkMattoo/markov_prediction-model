"""Markov chain power, simulation, and absorption tests."""

from __future__ import annotations

import numpy as np
import pytest

from markov_risk.chain import MarkovChain
from markov_risk.states import Rating


def test_n_step_matrix_matches_power(sample_matrix):
    chain = MarkovChain(sample_matrix, seed=0)
    np.testing.assert_allclose(chain.n_step_matrix(5), sample_matrix.power(5))


def test_cumulative_default_probability_is_monotonic(sample_matrix):
    chain = MarkovChain(sample_matrix, seed=0)
    for start in (Rating.AAA, Rating.A, Rating.BBB, Rating.CCC):
        pd = chain.cumulative_default_probability(start, max_horizon=20)
        assert pd[0] == 0.0
        assert np.all(np.diff(pd) >= -1e-12)  # non-decreasing
        # Long horizon mass approaches 1 for non-AAA starting ratings under a
        # well-mixed absorbing chain. AAA should still be << 1 at 20y.
        assert pd[-1] <= 1.0 + 1e-9


def test_analytical_5y_pd_in_plausible_range(sample_matrix):
    chain = MarkovChain(sample_matrix, seed=0)
    pd_5y = chain.cumulative_default_probability(Rating.BBB, 5)
    # Real 5y PD for Baa-rated issuers typically in 1-10% range.
    assert 0.005 < pd_5y[5] < 0.15
    pd_aaa_5y = chain.cumulative_default_probability(Rating.AAA, 5)
    # AAA 5y PD should be tiny.
    assert 0.0 < pd_aaa_5y[5] < 0.02


def test_simulation_shape_and_seed(sample_matrix):
    chain1 = MarkovChain(sample_matrix, seed=42)
    chain2 = MarkovChain(sample_matrix, seed=42)
    p1 = chain1.simulate([Rating.AA, Rating.BBB, Rating.CCC], horizon=10)
    p2 = chain2.simulate([Rating.AA, Rating.BBB, Rating.CCC], horizon=10)
    assert p1.shape == (3, 11)
    # Same seed -> identical paths.
    np.testing.assert_array_equal(p1, p2)


def test_simulation_stays_in_valid_states(sample_matrix):
    chain = MarkovChain(sample_matrix, seed=7)
    paths = chain.simulate([Rating.CCC] * 200, horizon=20)
    # Every value must be a valid rating index in [0, 7].
    assert paths.min() >= 0
    assert paths.max() <= 7


def test_simulation_default_path_terminates_in_default(sample_matrix):
    """Once a path hits D, the absorbing property keeps it there."""
    chain = MarkovChain(sample_matrix, seed=3)
    # Many paths from CCC, which has a high 1y default prob.
    paths = chain.simulate([Rating.CCC] * 500, horizon=15)
    d = Rating.indices()[Rating.D]
    for row in paths:
        first_d = np.where(row == d)[0]
        if first_d.size:
            assert np.all(row[first_d[0] :] == d)


def test_expected_time_to_default_ccc_is_smaller_than_aaa(sample_matrix):
    chain = MarkovChain(sample_matrix, seed=0)
    t_ccc = chain.expected_time_to_default(Rating.CCC)
    t_aaa = chain.expected_time_to_default(Rating.AAA)
    assert 0 < t_ccc < t_aaa


def test_expected_time_to_default_d_is_zero(sample_matrix):
    chain = MarkovChain(sample_matrix, seed=0)
    assert chain.expected_time_to_default(Rating.D) == 0.0
