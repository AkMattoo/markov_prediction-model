"""Markov chain operations: power, simulation, absorption analysis."""

from __future__ import annotations

from typing import Sequence

import numpy as np

from markov_risk.states import Rating
from markov_risk.transition import TransitionMatrix


class MarkovChain:
    """A discrete-time Markov chain over :class:`Rating` states."""

    def __init__(self, transition: TransitionMatrix, seed: int | None = None):
        self.P = transition
        self._rng = np.random.default_rng(seed)

    # ----- Forward propagation -------------------------------------------

    def n_step_matrix(self, k: int) -> np.ndarray:
        """``P^k`` -- probability of migrating i -> j in exactly k steps."""
        return self.P.power(k)

    def cumulative_default_probability(
        self, start: Rating, max_horizon: int
    ) -> np.ndarray:
        """``PD_cum[t] = P(start -> D within t steps)`` for t = 0..max_horizon.

        Returns a 1-D array of length ``max_horizon + 1`` where ``PD_cum[0] = 0``
        and ``PD_cum[t] = 1 - sum_j (P^t)[start, j]`` summed over transient
        states ``j``. This is the lifetime (by-horizon) form used in credit
        risk; for a chain with D absorbing it equals the eventual absorption
        probability as t -> infinity.
        """
        if max_horizon < 0:
            raise ValueError("max_horizon must be non-negative")
        idx = Rating.indices()
        d = idx[Rating.D]
        s = idx[start]
        transient = np.ones(self.P.N_STATES, dtype=bool)
        transient[d] = False
        out = np.zeros(max_horizon + 1)
        pk = np.eye(self.P.N_STATES)
        for t in range(1, max_horizon + 1):
            pk = pk @ self.P.array
            out[t] = 1.0 - pk[s, transient].sum()
        return out

    # ----- Simulation -----------------------------------------------------

    def simulate(
        self,
        starts: Sequence[Rating],
        horizon: int,
    ) -> np.ndarray:
        """Monte Carlo simulation. Returns ``(n_paths, horizon)`` int array.

        Each row is one path; each column is the state index at time t
        (t = 0 is the starting state, included). A draw of index 0 means AAA,
        index 7 means D, etc.
        """
        if horizon < 0:
            raise ValueError("horizon must be non-negative")
        idx = Rating.indices()
        P = self.P.array
        n = len(starts)
        # paths shape: (n, horizon+1) so columns 0..horizon inclusive.
        paths = np.zeros((n, horizon + 1), dtype=np.int64)
        paths[:, 0] = [idx[s] for s in starts]
        for t in range(1, horizon + 1):
            cur = paths[:, t - 1]
            # Vectorized categorical draw: uniform -> CDF lookup per row.
            u = self._rng.random(n)
            cdf = np.cumsum(P[cur], axis=1)  # (n, N)
            paths[:, t] = (u[:, None] < cdf).argmax(axis=1)
        return paths

    # ----- Absorption analysis -------------------------------------------

    def fundamental_matrix(self) -> np.ndarray:
        """``N = (I - Q)^(-1)`` where Q is the transient sub-matrix.

        ``N[i, j]`` is the expected number of visits to transient state ``j``
        when starting in transient state ``i``. Sum over a row gives the
        expected time to absorption (default).
        """
        transient = list(Rating.transient())
        idx = Rating.indices()
        Q = np.array([[self.P.row(t)[idx[t2]] for t2 in transient] for t in transient])
        return np.linalg.inv(np.eye(len(transient)) - Q)

    def expected_time_to_default(self, start: Rating) -> float:
        """Expected number of steps until default, starting in ``start``.

        Equals ``sum_j N[i, j]`` over the transient block.
        """
        if start is Rating.D:
            return 0.0
        transient = list(Rating.transient())
        i = transient.index(start)
        return float(self.fundamental_matrix()[i].sum())
