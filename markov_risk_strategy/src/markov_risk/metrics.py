"""Credit-risk metrics derived from a Markov chain."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

import numpy as np

from markov_risk.chain import MarkovChain
from markov_risk.states import Rating


@dataclass(frozen=True)
class Obligor:
    """A single credit exposure: current rating, exposure at default, loss given default."""

    name: str
    rating: Rating
    ead: float  # Exposure at default, in portfolio currency units
    lgd: float  # Loss given default, in [0, 1]


@dataclass(frozen=True)
class Portfolio:
    obligors: Sequence[Obligor]

    def __post_init__(self) -> None:
        if not self.obligors:
            raise ValueError("Portfolio must contain at least one obligor")
        for o in self.obligors:
            if not 0.0 <= o.lgd <= 1.0:
                raise ValueError(f"LGD for {o.name!r} must be in [0, 1], got {o.lgd}")
            if o.ead < 0:
                raise ValueError(f"EAD for {o.name!r} must be non-negative")

    @property
    def total_ead(self) -> float:
        return float(sum(o.ead for o in self.obligors))


@dataclass(frozen=True)
class ECLResult:
    horizon: int
    total_ecl: float
    per_obligor: dict[str, float]
    per_obligor_pd: dict[str, float]


@dataclass(frozen=True)
class PortfolioDrift:
    """Empirical distribution of ending ratings from Monte Carlo paths."""

    horizon: int
    counts: dict[Rating, int]  # counts of paths ending in each rating
    n_paths: int

    def probabilities(self) -> dict[Rating, float]:
        if self.n_paths == 0:
            return {r: 0.0 for r in Rating}
        return {r: self.counts.get(r, 0) / self.n_paths for r in Rating}


@dataclass(frozen=True)
class RiskMetrics:
    """Computed risk metrics for a portfolio + Markov chain.

    All horizons share the same underlying chain; the LLM narrates from
    these structured numbers.
    """

    horizon: int
    n_paths: int
    ecl: ECLResult
    per_obligor_pd: dict[str, float]
    drift: PortfolioDrift
    portfolio_total_ead: float
    mean_rating_drift_steps: float  # avg # of rating buckets migrated (in either direction)


class RiskMetricsEngine:
    """Compute :class:`RiskMetrics` from a chain + portfolio + Monte Carlo paths."""

    def __init__(self, chain: MarkovChain, portfolio: Portfolio):
        self.chain = chain
        self.portfolio = portfolio

    def compute(
        self,
        horizon: int,
        n_paths: int = 10_000,
    ) -> RiskMetrics:
        if horizon < 1:
            raise ValueError("horizon must be >= 1")
        starts = [o.rating for o in self.portfolio.obligors]
        # Run n_paths Monte Carlo paths PER obligor. Concatenate the starting
        # list so a single vectorized simulate call produces (n_obligors *
        # n_paths, horizon+1) samples.
        d_idx = Rating.indices()[Rating.D]
        all_starts = []
        for s in starts:
            all_starts.extend([s] * n_paths)
        paths = self.chain.simulate(all_starts, horizon)  # (N*paths, h+1)
        n_obligors = len(starts)
        # Reshape so each obligor's block is contiguous, then aggregate.
        paths = paths.reshape(n_obligors, n_paths, horizon + 1)
        # Per-obligor empirical PD = fraction of that obligor's paths that
        # hit D at any time up to horizon.
        hit_default = (paths == d_idx).any(axis=2)  # (n_obligors, n_paths)
        per_obligor_pd = {
            o.name: float(hit_default[i].mean()) for i, o in enumerate(self.portfolio.obligors)
        }
        per_obligor_ecl = {
            o.name: o.ead * o.lgd * per_obligor_pd[o.name] for o in self.portfolio.obligors
        }
        ecl = ECLResult(
            horizon=horizon,
            total_ecl=sum(per_obligor_ecl.values()),
            per_obligor=per_obligor_ecl,
            per_obligor_pd=per_obligor_pd,
        )
        # Drift distribution: aggregate terminal states across ALL paths,
        # all obligors (each path is one sample).
        terminal = paths[:, :, -1].reshape(-1)
        counts: dict[Rating, int] = {r: 0 for r in Rating}
        for s_idx in terminal:
            counts[Rating.from_index(int(s_idx))] += 1
        drift = PortfolioDrift(
            horizon=horizon,
            counts=counts,
            n_paths=n_obligors * n_paths,
        )
        # Mean rating drift (in bucket-steps): per-path |final - start|,
        # averaged across all paths.
        rating_to_idx = Rating.indices()
        start_idx = np.array([rating_to_idx[o.rating] for o in self.portfolio.obligors])
        # Broadcast start to each path.
        start_idx_full = np.repeat(start_idx, n_paths)  # (N*paths,)
        mean_drift = float(np.abs(terminal - start_idx_full).mean())
        return RiskMetrics(
            horizon=horizon,
            n_paths=n_paths,
            ecl=ecl,
            per_obligor_pd=per_obligor_pd,
            drift=drift,
            portfolio_total_ead=self.portfolio.total_ead,
            mean_rating_drift_steps=mean_drift,
        )

    def analytical_pd(self, horizon: int) -> dict[str, float]:
        """Closed-form lifetime (by-horizon) cumulative PD per obligor.

        Equivalent to ``chain.cumulative_default_probability(rating, horizon)[horizon]``.
        """
        return {
            o.name: float(self.chain.cumulative_default_probability(o.rating, horizon)[horizon])
            for o in self.portfolio.obligors
        }
