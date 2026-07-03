"""CLI entry point: ``python -m markov_risk``.

Run a credit-risk Markov simulation on a portfolio and write JSON metrics +
markdown report. Optionally narrate via an LLM (Anthropic or OpenAI).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from markov_risk.chain import MarkovChain
from markov_risk.metrics import Obligor, Portfolio, RiskMetricsEngine
from markov_risk.reporting import (
    build_markdown_report,
    metrics_to_dict,
    write_json_report,
    write_markdown_report,
)
from markov_risk.states import Rating
from markov_risk.transition import TransitionMatrix


def _load_portfolio(path: str | Path) -> Portfolio:
    data = json.loads(Path(path).read_text())
    obligors = [
        Obligor(
            name=o["name"],
            rating=Rating(o["rating"]),
            ead=float(o["ead"]),
            lgd=float(o["lgd"]),
        )
        for o in data["obligors"]
    ]
    return Portfolio(obligors)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="markov-risk",
        description="Credit-risk Markov simulator with optional LLM narration.",
    )
    p.add_argument("--matrix", required=True, help="Path to transition matrix JSON.")
    p.add_argument("--portfolio", required=True, help="Path to portfolio JSON.")
    p.add_argument("--horizon", type=int, default=5, help="Risk horizon in years.")
    p.add_argument("--paths", type=int, default=10_000, help="Monte Carlo path count.")
    p.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility.")
    p.add_argument(
        "--llm-provider",
        choices=("anthropic", "openai", "none"),
        default="none",
        help="LLM provider for narration; 'none' skips narrative.",
    )
    p.add_argument("--llm-model", default=None, help="Override the LLM model name.")
    p.add_argument(
        "--out",
        default="reports/report.md",
        help="Output path for markdown report.",
    )
    p.add_argument(
        "--out-json",
        default=None,
        help="Optional JSON metrics path. Defaults to <out>.json.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    matrix = TransitionMatrix.from_json(args.matrix)
    portfolio = _load_portfolio(args.portfolio)
    chain = MarkovChain(matrix, seed=args.seed)
    engine = RiskMetricsEngine(chain, portfolio)
    metrics = engine.compute(horizon=args.horizon, n_paths=args.paths)
    analytical_pd = engine.analytical_pd(horizon=args.horizon)

    narrative = None
    token_usage = None
    if args.llm_provider != "none":
        from markov_risk.llm.client import make_client
        from markov_risk.llm.narrator import RiskNarrator

        client_kwargs = {}
        if args.llm_model:
            client_kwargs["model"] = args.llm_model
        client = make_client(args.llm_provider, **client_kwargs)
        narrator = RiskNarrator(client)
        narrative, token_usage = narrator.narrate(
            portfolio=portfolio,
            transition=matrix,
            metrics=metrics,
            analytical_pd=analytical_pd,
        )

    payload = metrics_to_dict(
        portfolio, matrix, metrics, analytical_pd=analytical_pd
    )
    if token_usage is not None:
        payload["llm_token_usage"] = {
            "input": token_usage.input_tokens,
            "output": token_usage.output_tokens,
        }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json_path = Path(args.out_json) if args.out_json else out_path.with_suffix(".json")
    write_json_report(payload, json_path)
    md = build_markdown_report(
        portfolio, matrix, metrics, narrative, analytical_pd=analytical_pd
    )
    write_markdown_report(md, out_path)

    print(f"Report written to: {out_path}")
    print(f"Metrics written to: {json_path}")
    print(
        f"Horizon={args.horizon}y  EAD={metrics.portfolio_total_ead:,.0f}  "
        f"ECL={metrics.ecl.total_ecl:,.0f}"
    )
    if token_usage is not None:
        print(
            f"LLM tokens: in={token_usage.input_tokens} "
            f"out={token_usage.output_tokens}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
