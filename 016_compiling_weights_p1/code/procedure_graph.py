"""
procedure_graph.py -- a runnable implementation of the paper's own
procedure formalism (§2): F = (N, E, n0, T). N = nodes tagged with a role
(agent/user) and a prompt template; E is edges carrying optional
conditions; n0 is the single start node; T is the set of terminal nodes
(the paper is explicit these are not success-only -- success, abandonment,
and escalation are all terminal).

The paper does not publish the exact node/edge structure of its travel,
Zoom, or insurance flowcharts -- only their aggregate node/hub/path counts
(reproduced in data_tables.py). So the example graph built below is a
small ILLUSTRATIVE flowchart, built only to demonstrate the formalism and
the acyclic-path-enumeration mechanics step 2 of the compile pipeline
uses -- it is NOT a reconstruction of any of the paper's actual
procedures, and its path count is computed by the code below, not
asserted anywhere as a paper fact.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class Node:
    name: str
    role: str  # "agent" or "user" (paper: N = nodes with a role + prompt template)
    prompt_template: str


@dataclass
class Edge:
    src: str
    dst: str
    condition: Optional[Callable[[dict], bool]] = None  # None = unconditional (paper: E subset of NxNxC)


@dataclass
class ProcedureGraph:
    """F = (N, E, n0, T), exactly as defined in the paper's Section 2."""
    nodes: dict = field(default_factory=dict)
    edges: list = field(default_factory=list)
    start: str = ""
    terminals: set = field(default_factory=set)

    def add_node(self, name: str, role: str, prompt_template: str) -> None:
        self.nodes[name] = Node(name, role, prompt_template)

    def add_edge(self, src: str, dst: str, condition=None) -> None:
        self.edges.append(Edge(src, dst, condition))

    def outgoing(self, node_name: str):
        return [e for e in self.edges if e.src == node_name]

    def enumerate_acyclic_paths(self, scenario: dict | None = None):
        """DFS enumeration of every acyclic path from n0 to any terminal
        node, respecting edge conditions when a scenario dict is supplied
        -- the same traversal step 2 of the compile pipeline uses to
        generate synthetic training conversations (here it returns node
        paths instead of dialogue)."""
        scenario = scenario or {}
        paths: list[list[str]] = []

        def dfs(node_name: str, path: list[str], visited: set) -> None:
            if node_name in self.terminals:
                paths.append(list(path))
                return
            for edge in self.outgoing(node_name):
                if edge.dst in visited:
                    continue  # acyclic paths only, per the paper's own constraint
                if edge.condition is not None and not edge.condition(scenario):
                    continue
                dfs(edge.dst, path + [edge.dst], visited | {edge.dst})

        dfs(self.start, [self.start], {self.start})
        return paths


def build_illustrative_example() -> ProcedureGraph:
    """A small toy graph shaped like a miniature travel-booking flow (one
    decision hub, three terminal outcomes matching the paper's
    success/abandonment/escalation design) -- NOT the paper's real
    14-node/86-path travel domain, which isn't published node-by-node."""
    g = ProcedureGraph(start="greet")
    g.add_node("greet", "agent", "Greet the customer, ask what they need.")
    g.add_node("collect_prefs", "user", "Customer states destination and budget.")
    g.add_node("present_options", "agent", "Agent presents matching options.")
    g.add_node("confirm", "user", "Customer accepts an option.")
    g.add_node("reject", "user", "Customer rejects the options offered.")
    g.add_node("book", "agent", "Agent confirms the booking.")           # terminal: success
    g.add_node("abandon", "agent", "Customer leaves without booking.")   # terminal: abandonment
    g.add_node("escalate", "agent", "Agent hands off to a human.")       # terminal: escalation

    g.terminals = {"book", "abandon", "escalate"}

    g.add_edge("greet", "collect_prefs")
    g.add_edge("collect_prefs", "present_options")
    g.add_edge("present_options", "confirm", condition=lambda s: s.get("accepts", True))
    g.add_edge("present_options", "reject", condition=lambda s: not s.get("accepts", True))
    g.add_edge("confirm", "book")
    g.add_edge("reject", "abandon")
    g.add_edge("reject", "escalate")
    return g


if __name__ == "__main__":
    graph = build_illustrative_example()
    for scenario_name, scenario in [("accepts", {"accepts": True}), ("rejects", {"accepts": False})]:
        found = graph.enumerate_acyclic_paths(scenario)
        print(f"{scenario_name}: {len(found)} acyclic path(s)")
        for p in found:
            print("  ", " -> ".join(p))
