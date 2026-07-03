"""Rating state definitions.

The state space mirrors the standard 8-bucket rating scale used by major
credit rating agencies. ``D`` (default) is the only absorbing state.
"""

from __future__ import annotations

from enum import Enum


class Rating(str, Enum):
    """Standard 8-bucket credit rating. Order matters: lower index = safer."""

    AAA = "AAA"
    AA = "AA"
    A = "A"
    BBB = "BBB"
    BB = "BB"
    B = "B"
    CCC = "CCC"
    D = "D"  # Default (absorbing)

    @classmethod
    def transient(cls) -> tuple["Rating", ...]:
        """All non-default ratings. Used to build the transient sub-matrix Q."""
        return (cls.AAA, cls.AA, cls.A, cls.BBB, cls.BB, cls.B, cls.CCC)

    @property
    def is_absorbing(self) -> bool:
        return self is Rating.D

    @classmethod
    def indices(cls) -> dict["Rating", int]:
        """Mapping from rating to its row/column index in the transition matrix."""
        return {r: i for i, r in enumerate(cls)}

    @classmethod
    def from_index(cls, idx: int) -> "Rating":
        return list(cls)[idx]
