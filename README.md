A production-ready credit-risk simulator built on a discrete-time Markov chain over standard rating states (AAA → D), with an LLM layer that narrates the resulting risk profile in plain English for executive consumption.

What it does
Models credit migration as a Markov chain over 8 rating buckets (AAA, AA, A, BBB, BB, B, CCC, D), where D is absorbing. Uses the standard industry formulation used by Moody's, S&P, and Basel IRB banks.
Computes real credit-risk quantities: cumulative multi-period default probabilities, expected time to default (fundamental matrix), expected credit loss (ECL), and rating-drift distributions.
Calibrates from either a published transition matrix or migration counts (with Laplace smoothing for cold-start matrices).
Narrates the results through an LLM (Anthropic Claude or OpenAI) using a structured output schema so the report is machine-validatable.
Install
pip install -e ".[dev]"
Quickstart (no API key)
python examples/demo_portfolio.py
Produces a JSON metrics file and a markdown report at reports/demo_report.md.

With an LLM narrator
export ANTHROPIC_API_KEY=sk-...
python -m markov_risk \
    --matrix tests/fixtures/sample_matrix.json \
    --portfolio examples/demo_portfolio.json \
    --horizon 5 \
    --paths 10000 \
    --llm-provider anthropic \
    --out reports/full_report.md
Math overview
Let P be the 8×8 transition matrix, e_i a one-hot row vector for state i.

Cumulative default probability: PD_cum(t | i) = e_i · P^t · e_D
Expected time to default: E[T_D | i] = sum_j N_ij, where N = (I − Q)^(-1) is the fundamental matrix and Q is the transient sub-matrix (D removed).
ECL for portfolio: Σ EAD_i · LGD_i · PD_cum(t | rating_i)
LLM prompt design
The narrator uses:

A system prompt that anchors the model as a senior credit risk analyst.
A user prompt containing the portfolio composition, transition matrix as a markdown table, and pre-computed metrics. The model is asked to produce an executive summary, key risks, and recommendations.
Structured output via pydantic (NarrativeReport) so the response is guaranteed-schema-valid.
All LLM-returned text is treated as data, never as instructions — there is no path through which portfolio CSV or matrix content can override the system prompt.

Layout
src/markov_risk/
  states.py       Rating enum
  transition.py   TransitionMatrix (validation, calibration)
  chain.py        MarkovChain (P^k, simulation, absorption)
  metrics.py      RiskMetrics (PD, ECL, drift)
  llm/            Anthropic/OpenAI clients + narrator
  reporting.py    Markdown/JSON assembly
  cli.py          python -m markov_risk
tests/            pytest suite + sample transition matrix fixture
examples/         demo_portfolio.py
Testing
pytest
The narrator test mocks the SDK, so the suite runs without API keys.
