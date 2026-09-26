"""
ledger.py — the per-event ledger both parts of this episode build toward.
Part 1: "a trajectory isn't one blob of spend, it's a ledger, and each
entry has to earn its credit." Part 2 / EFC-ADAPTER: the ledger stops
being read after the fact and starts driving the agent loop in real time
("same invoice, different ledger — and now the ledger runs the agent").

Schema, per the source note's L(tau): (event, credit earned, cost
incurred, running normalized score).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LedgerRow:
    event_id: str
    credit: float  # EFC_hat_t^nr for this event
    cost: float  # delta C_raw for this event
    running_score: float  # running X_hat_t^nr = cumulative credit / D_task so far


@dataclass
class Ledger:
    rows: list[LedgerRow] = field(default_factory=list)
    d_task: float = 1.0  # frozen for the run once task demand is estimated

    def log(self, event_id: str, credit: float, cost: float) -> LedgerRow:
        cumulative_credit = sum(r.credit for r in self.rows) + credit
        running_score = cumulative_credit / max(self.d_task, 1e-9)
        row = LedgerRow(event_id=event_id, credit=credit, cost=cost, running_score=running_score)
        self.rows.append(row)
        return row

    @property
    def total_credit(self) -> float:
        return sum(r.credit for r in self.rows)

    @property
    def total_cost(self) -> float:
        return sum(r.cost for r in self.rows)

    def to_table(self) -> str:
        header = f"{'event':30s} {'credit':>8s} {'cost':>8s} {'running X':>10s}"
        lines = [header, "-" * len(header)]
        for r in self.rows:
            lines.append(f"{r.event_id:30s} {r.credit:8.3f} {r.cost:8.3f} {r.running_score:10.3f}")
        return "\n".join(lines)


if __name__ == "__main__":
    ledger = Ledger(d_task=2.4)
    ledger.log("checker_fired", credit=3.6, cost=1.1)
    ledger.log("unread_critique", credit=0.05, cost=0.9)
    ledger.log("verified_fix_stored", credit=4.2, cost=1.4)
    print(ledger.to_table())
    print(f"\ntotal credit={ledger.total_credit:.3f}  total cost={ledger.total_cost:.3f}")
