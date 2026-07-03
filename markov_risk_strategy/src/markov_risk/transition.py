"""Transition matrix construction, validation, and calibration."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from markov_risk.states import Rating


class TransitionMatrixError(ValueError):
    """Raised when a transition matrix fails validation."""


class TransitionMatrix:
    """An 8x8 row-stochastic transition matrix over :class:`Rating`.

    Rows index the source rating, columns the destination. ``P[i, j]`` is
    the probability of migrating from rating ``i`` to rating ``j`` in one
    time step. The ``D`` (default) row must be a one-hot vector with all
    mass on ``D`` itself -- default is absorbing.
    """

    N_STATES = len(Rating)

    def __init__(self, matrix: np.ndarray):
        P = np.asarray(matrix, dtype=float)
        if P.shape != (self.N_STATES, self.N_STATES):
            raise TransitionMatrixError(
                f"Expected shape ({self.N_STATES}, {self.N_STATES}), got {P.shape}"
            )
        if np.any(P < 0):
            raise TransitionMatrixError("Transition probabilities must be non-negative.")
        row_sums = P.sum(axis=1)
        if not np.allclose(row_sums, 1.0, atol=1e-8):
            bad = np.where(~np.isclose(row_sums, 1.0, atol=1e-8))[0]
            raise TransitionMatrixError(
                f"Rows must sum to 1; offenders at indices {bad.tolist()} with sums "
                f"{row_sums[bad].tolist()}"
            )
        # Enforce absorbing default state: all mass on D, none elsewhere.
        d_idx = Rating.indices()[Rating.D]
        off_d = np.ones(self.N_STATES, dtype=bool)
        off_d[d_idx] = False
        if not (
            np.isclose(P[d_idx, d_idx], 1.0)
            and np.isclose(P[d_idx, off_d], 0.0).all()
        ):
            raise TransitionMatrixError(
                "Default (D) must be absorbing: P[D, D] = 1 and P[D, j] = 0 for j != D."
            )
        self._P = P

    # ----- Access ---------------------------------------------------------

    @property
    def array(self) -> np.ndarray:
        """Return a copy of the underlying matrix (defensive)."""
        return self._P.copy()

    def row(self, rating: Rating) -> np.ndarray:
        return self._P[Rating.indices()[rating]].copy()

    # ----- Calibration ----------------------------------------------------

    @classmethod
    def from_dict(cls, data: dict[str, list[float]]) -> "TransitionMatrix":
        """Build from ``{source_rating: [p_AAA, p_AA, ..., p_D]}``."""
        ratings = list(Rating)
        P = np.zeros((cls.N_STATES, cls.N_STATES))
        for i, src in enumerate(ratings):
            row = data.get(src.value)
            if row is None:
                raise TransitionMatrixError(f"Missing row for rating {src.value!r}")
            if len(row) != cls.N_STATES:
                raise TransitionMatrixError(
                    f"Row {src.value!r} has {len(row)} entries, expected {cls.N_STATES}"
                )
            P[i] = row
        return cls(P)

    @classmethod
    def from_counts(
        cls,
        migration_counts: dict[tuple[Rating, Rating], int],
        smoothing: float = 1.0,
    ) -> "TransitionMatrix":
        """Calibrate from observed (src, dst) -> count migration data.

        Uses maximum-likelihood estimation with additive (Laplace) smoothing
        ``smoothing`` so no zero-probability transitions remain. The ``D`` row
        is forced to its absorbing form after smoothing.
        """
        ratings = list(Rating)
        idx = Rating.indices()
        counts = np.zeros((cls.N_STATES, cls.N_STATES))
        for (src, dst), c in migration_counts.items():
            counts[idx[src], idx[dst]] = c
        counts += smoothing
        P = counts / counts.sum(axis=1, keepdims=True)
        d = idx[Rating.D]
        P[d, :] = 0.0
        P[d, d] = 1.0
        return cls(P)

    # ----- Serialization --------------------------------------------------

    def to_dict(self) -> dict[str, list[float]]:
        return {r.value: self._P[i].tolist() for i, r in enumerate(Rating)}

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def from_json(cls, path: str | Path) -> "TransitionMatrix":
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data)

    # ----- Algebra --------------------------------------------------------

    def power(self, k: int) -> np.ndarray:
        """Return ``P^k`` (the k-step transition matrix)."""
        if k < 0:
            raise ValueError("k must be non-negative")
        if k == 0:
            return np.eye(self.N_STATES)
        return np.linalg.matrix_power(self._P, k)

    def __matmul__(self, other: "TransitionMatrix | np.ndarray") -> np.ndarray:
        if isinstance(other, TransitionMatrix):
            return self._P @ other._P
        return self._P @ np.asarray(other)
