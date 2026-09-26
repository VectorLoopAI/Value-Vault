"""
metrics.py -- the formulas the paper uses (and the ones the videos derive
from its raw tables): percent-of-in-context quality, per-token self-hosting
cost, cost-per-conversation savings multiples, and break-even conversation
counts. Every function is a straightforward transcription of arithmetic
named in the paper / backlog note (see data_tables.py for the source
numbers each is applied to). Nothing here is a paper-stated formula except
where noted -- most of these are just "how do you get from the raw tables
to the headline percentages named in the video."
"""

from __future__ import annotations


def pct_of_in_context(score: float, in_context_score: float) -> float:
    """What Part 1/Part 2 call 'X% of in-context/frontier quality' for a
    single criterion. E.g. travel info-accuracy: 4.75 / 4.64 = 102.4%,
    which the video rounds to the paper's own quoted 102%."""
    return round(100.0 * score / in_context_score, 1)


def savings_multiplier(baseline_cost: float, subterranean_cost: float) -> float:
    """baseline_cost / subterranean_cost -- the 128x / 296x / 462x figures
    in Part 2's cost section (Table 6: in-context cost / subterranean cost)."""
    return round(baseline_cost / subterranean_cost, 1)


def per_token_cost(hourly_rate_usd: float, tokens_per_sec: float) -> float:
    """USD per token for a self-hosted model, given a GPU's hourly rental
    rate and a served-tokens-per-second figure. Multiply by 1_000_000 to
    get USD per million tokens, the unit the paper quotes."""
    tokens_per_hour = tokens_per_sec * 3600
    return hourly_rate_usd / tokens_per_hour


def per_million_token_cost(hourly_rate_usd: float, tokens_per_sec: float) -> float:
    return per_token_cost(hourly_rate_usd, tokens_per_sec) * 1_000_000


def breakeven_conversations(one_time_compile_cost: float, baseline_cost_per_convo: float,
                             subterranean_cost_per_convo: float) -> float:
    """How many conversations before the one-time compile cost is repaid by
    the per-conversation savings versus the in-context baseline. Part 2:
    'break-even against the in-context baseline arrives within 500
    conversations on every domain they tested.'"""
    savings_per_convo = baseline_cost_per_convo - subterranean_cost_per_convo
    if savings_per_convo <= 0:
        raise ValueError("subterranean cost must be lower than baseline cost")
    return one_time_compile_cost / savings_per_convo


def failure_rate_pct(failures: int, total: int) -> float:
    return round(100.0 * failures / total, 1)


def delta(a: float, b: float) -> float:
    """a - b, rounded to 2 decimals -- used to sanity-check the paper's own
    stated deltas against the individual table cells (see the README's
    rounding-discrepancy note)."""
    return round(a - b, 2)
