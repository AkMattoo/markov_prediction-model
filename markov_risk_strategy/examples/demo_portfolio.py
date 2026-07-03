"""End-to-end demo: load a portfolio, simulate, write metrics + markdown report.

This script is the hermetic smoke test. It does NOT call an LLM -- set
``--with-llm`` to enable narration (requires ANTHROPIC_API_KEY or OPENAI_API_KEY).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from markov_risk.chain import MarkovChain
from markov_risk.metrics import RiskMetricsEngine
from markov_risk.reporting import (
    build_markdown_report,
    metrics_to_dict,
    write_json_report,
    write_markdown_report,
)
from markov_risk.transition import TransitionMatrix

# Reuse the CLI helpers for portfolio loading.
from markov_risk.cli import _load_portfolio  # type: ignore


def run(
    matrix_path: str,
    portfolio_path: str,
    horizon: int,
    n_paths: int,
    seed: int,
    out_dir: str,
    with_llm: bool,
    llm_provider: str,
) -> int:
    matrix = TransitionMatrix.from_json(matrix_path)
    portfolio = _load_portfolio(portfolio_path)
    chain = MarkovChain(matrix, seed=seed)
    engine = RiskMetricsEngine(chain, portfolio)
    metrics = engine.compute(horizon=horizon, n_paths=n_paths)
    analytical_pd = engine.analytical_pd(horizon=horizon)

    narrative = None
    token_usage = None
    if with_llm:
        from markov_risk.llm.client import make_client
        from markov_risk.llm.narrator import RiskNarrator

        client = make_client(llm_provider)
        narrator = RiskNarrator(client)
        narrative, token_usage = narrator.narrate(
            portfolio=portfolio,
            transition=matrix,
            metrics=metrics,
            analytical_pd=analytical_pd,
        )

    payload = metrics_to_dict(portfolio, matrix, metrics, analytical_pd=analytical_pd)
    if token_usage is not None:
        payload["llm_token_usage"] = {
            "input": token_usage.input_tokens,
            "output": token_usage.output_tokens,
        }

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "demo_metrics.json"
    md_path = out / "demo_report.md"
    write_json_report(payload, json_path)
    md = build_markdown_report(
        portfolio, matrix, metrics, narrative, analytical_pd=analytical_pd
    )
    write_markdown_report(md, md_path)

    print(f"Metrics written to: {json_path}")
    print(f"Report written to:  {md_path}")
    print(
        f"Horizon={horizon}y  EAD={metrics.portfolio_total_ead:,.0f}  "
        f"ECL={metrics.ecl.total_ecl:,.0f}"
    )
    if token_usage is not None:
        print(
            f"LLM tokens used: in={token_usage.input_tokens} "
            f"out={token_usage.output_tokens}"
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    here = Path(__file__).parent
    p = argparse.ArgumentParser(description="End-to-end demo of the credit-risk simulator.")
    p.add_argument("--matrix", default=str(here.parent / "tests" / "fixtures" / "sample_matrix.json"))
    p.add_argument("--portfolio", default=str(here / "demo_portfolio.json"))
    p.add_argument("--horizon", type=int, default=5)
    p.add_argument("--paths", type=int, default=10_000)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out-dir", default=str(here.parent / "reports"))
    p.add_argument("--with-llm", action="store_true")
    p.add_argument("--llm-provider", default="anthropic", choices=("anthropic", "openai"))
    args = p.parse_args(argv)
    return run(
        matrix_path=args.matrix,
        portfolio_path=args.portfolio,
        horizon=args.horizon,
        n_paths=args.paths,
        seed=args.seed,
        out_dir=args.out_dir,
        with_llm=args.with_llm,
        llm_provider=args.llm_provider,
    )


if __name__ == "__main__":
    sys.exit(main())