"""Report assembly: JSON metrics + markdown narrative."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from markov_risk.llm.narrator import NarrativeReport
from markov_risk.metrics import Portfolio, RiskMetrics
from markov_risk.states import Rating
from markov_risk.transition import TransitionMatrix


def metrics_to_dict(
    portfolio: Portfolio,
    transition: TransitionMatrix,
    metrics: RiskMetrics,
    analytical_pd: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Serialize the full risk picture to a JSON-safe dict."""
    return {
        "horizon_years": metrics.horizon,
        "n_paths": metrics.n_paths,
        "portfolio": {
            "obligors": [
                {"name": o.name, "rating": o.rating.value, "ead": o.ead, "lgd": o.lgd}
                for o in portfolio.obligors
            ],
            "total_ead": metrics.portfolio_total_ead,
        },
        "transition_matrix": transition.to_dict(),
        "expected_credit_loss": {
            "total": metrics.ecl.total_ecl,
            "per_obligor": metrics.ecl.per_obligor,
        },
        "cumulative_pd": {
            "simulated": metrics.per_obligor_pd,
            **({"analytical": analytical_pd} if analytical_pd else {}),
        },
        "terminal_rating_distribution": {
            r.value: p for r, p in metrics.drift.probabilities().items()
        },
        "mean_rating_drift_buckets": metrics.mean_rating_drift_steps,
    }


def write_json_report(payload: dict[str, Any], path: str | Path) -> None:
    Path(path).write_text(json.dumps(payload, indent=2))


def build_markdown_report(
    portfolio: Portfolio,
    transition: TransitionMatrix,
    metrics: RiskMetrics,
    narrative: NarrativeReport | None,
    analytical_pd: dict[str, float] | None = None,
) -> str:
    """Compose a markdown report; narrative is optional (``--llm-provider none``)."""
    lines: list[str] = []
    lines.append(f"# Credit Risk Report ({metrics.horizon}-year horizon)")
    lines.append("")
    lines.append(f"**Total EAD**: {metrics.portfolio_total_ead:,.0f}  ")
    lines.append(f"**Expected Credit Loss (ECL)**: {metrics.ecl.total_ecl:,.0f}  ")
    lines.append(f"**Mean rating drift**: {metrics.mean_rating_drift_steps:.2f} buckets")
    lines.append("")
    # Portfolio
    lines.append("## Portfolio")
    lines.append("")
    lines.append("| Name | Rating | EAD | LGD |")
    lines.append("|---|---|---:|---:|")
    for o in portfolio.obligors:
        lines.append(f"| {o.name} | {o.rating.value} | {o.ead:,.0f} | {o.lgd:.2f} |")
    lines.append(f"| **Total** |  | **{portfolio.total_ead:,.0f}** |  |")
    lines.append("")
    # PD table
    lines.append("## Cumulative PD")
    lines.append("")
    lines.append("| Obligor | Simulated PD | Analytical PD |")
    lines.append("|---|---:|---:|")
    for o in portfolio.obligors:
        sim = metrics.per_obligor_pd[o.name]
        ana = analytical_pd.get(o.name) if analytical_pd else None
        ana_str = f"{ana:.2%}" if ana is not None else "—"
        lines.append(f"| {o.name} | {sim:.2%} | {ana_str} |")
    lines.append("")
    # Drift
    lines.append("## Terminal rating distribution")
    lines.append("")
    lines.append("| Rating | Probability |")
    lines.append("|---|---:|")
    for r, p in metrics.drift.probabilities().items():
        lines.append(f"| {r.value} | {p:.2%} |")
    lines.append("")
    # Transition matrix
    lines.append("## Annual transition matrix")
    lines.append("")
    arr = transition.array
    ratings = [r.value for r in Rating]
    header = "| from \\\\ to | " + " | ".join(ratings) + " |"
    sep = "|" + "---|" * (len(ratings) + 1)
    lines.append(header)
    lines.append(sep)
    for i, src in enumerate(ratings):
        cells = " | ".join(f"{arr[i, j]:.4f}" for j in range(len(ratings)))
        lines.append(f"| **{src}** | {cells} |")
    lines.append("")
    # Narrative
    if narrative is not None:
        lines.append("## Narrative (LLM-generated)")
        lines.append("")
        lines.append("### Executive summary")
        lines.append(narrative.summary)
        lines.append("")
        lines.append("### Key risks")
        for r in narrative.key_risks:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("### Recommendations")
        for r in narrative.recommendations:
            lines.append(f"- {r}")
        lines.append("")
        lines.append("### Confidence notes")
        lines.append(narrative.confidence_notes)
        lines.append("")
    else:
        lines.append("## Narrative")
        lines.append("")
        lines.append("_LLM narration was disabled (use `--llm-provider anthropic` to enable)._")
        lines.append("")
    return "\n".join(lines)


def write_markdown_report(md: str, path: str | Path) -> None:
    Path(path).write_text(md)
