"""Transition matrix construction and validation tests."""

from __future__ import annotations

import json

import numpy as np
import pytest

from markov_risk.states import Rating
from markov_risk.transition import TransitionMatrix, TransitionMatrixError


def test_valid_matrix_loads(sample_matrix: TransitionMatrix):
    arr = sample_matrix.array
    assert arr.shape == (8, 8)
    assert np.allclose(arr.sum(axis=1), 1.0)
    # Default is absorbing.
    d = Rating.indices()[Rating.D]
    assert arr[d, d] == 1.0
    assert np.all(arr[d, :d] == 0) and np.all(arr[d, d + 1 :] == 0)


def test_rejects_wrong_shape():
    with pytest.raises(TransitionMatrixError, match="shape"):
        TransitionMatrix(np.eye(7))


def test_rejects_negative_entries():
    P = np.eye(8)
    P[0, 1] = -0.1
    with pytest.raises(TransitionMatrixError, match="non-negative"):
        TransitionMatrix(P)


def test_rejects_non_stochastic_rows():
    P = np.eye(8)
    P[0] = 0  # zero row
    with pytest.raises(TransitionMatrixError, match="sum to 1"):
        TransitionMatrix(P)


def test_rejects_non_absorbing_default():
    P = np.eye(8)  # all self-loops, including D -> D == 1, ok, but other rows are 0
    # Make D row point to C, so D is not absorbing.
    P[Rating.indices()[Rating.D], Rating.indices()[Rating.CCC]] = 0.5
    P[Rating.indices()[Rating.D], Rating.indices()[Rating.D]] = 0.5
    with pytest.raises(TransitionMatrixError, match="absorbing"):
        TransitionMatrix(P)


def test_from_dict_roundtrip(sample_matrix: TransitionMatrix):
    d = sample_matrix.to_dict()
    rebuilt = TransitionMatrix.from_dict(d)
    assert np.allclose(rebuilt.array, sample_matrix.array)


def test_calibration_from_counts_gives_stochastic_matrix():
    counts = {
        (Rating.AA, Rating.AA): 900,
        (Rating.AA, Rating.A): 80,
        (Rating.AA, Rating.D): 20,
    }
    P = TransitionMatrix.from_counts(counts)
    aa = P.row(Rating.AA)
    assert abs(aa.sum() - 1.0) < 1e-9
    # D row forced absorbing.
    d = P.row(Rating.D)
    assert d[-1] == 1.0


def test_power_zero_is_identity(sample_matrix: TransitionMatrix):
    assert np.allclose(sample_matrix.power(0), np.eye(8))


def test_power_one_equals_matrix(sample_matrix: TransitionMatrix):
    assert np.allclose(sample_matrix.power(1), sample_matrix.array)


def test_power_two_brute_force(sample_matrix: TransitionMatrix):
    P = sample_matrix.array
    assert np.allclose(sample_matrix.power(2), P @ P)
