"""
working_memory.py — Reference implementation of the Harness-1 stateful search harness.

Reproduces the WORKINGMEMORY state machine described in:
  "Harness-1: Reinforcement Learning For Search Agents With State-Externalizing Harnesses"
  Jiang, Shi, Hong, Xu, Sun, Sun, Bashir, Han (UIUC / UC Berkeley / Chroma, 2026)
  https://github.com/pat-jj/harness-1

This is a runnable, stdlib-only reference harness (not the paper's production code) built
to accompany Vector & Loop video 005. It implements the seven state variables (P_t,
C_t/I_t, D_t, G_t, V_t, H_t, B_t) and the mechanisms named in the video:
  - curate() as the central state-editing action, with importance tags and the harness-
    side eviction that keeps the curated set at cap (never the policy's job)
  - auto-seeding for the cold-start problem
  - sentence-BM25 compression (top-K sentences per result)
  - two-level deduplication (exact chunk ID + content-fingerprint Jaccard)
  - an evidence graph over entities and documents (frequent / bridge / singleton)
  - verify() with the verify-before-promote norm
  - a budget-safe progressive-degradation renderer

Swap the corpus-search results you feed into ingest_search_results(), and the verify_fn
you pass to the constructor, for a real retriever + real LLM client to run this against
your own corpus and model. All constants are loaded from ../configs/harness_config.yaml.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable

IMPORTANCE_LEVELS = ("very high", "high", "fair", "low")
_IMPORTANCE_RANK = {lvl: i for i, lvl in enumerate(IMPORTANCE_LEVELS)}  # 0 = highest


@dataclass
class Document:
    doc_id: str
    text: str
    source_query: str = ""


class WorkingMemory:
    """Per-episode stateful harness. Instantiate one per search episode."""

    def __init__(self, config: dict, verify_fn: Callable[[str, list[str]], dict] | None = None):
        self.cfg = config
        self.verify_fn = verify_fn or self._default_verify_stub

        # P_t — candidate pool, after compression + dedup
        self.candidate_pool: dict[str, Document] = {}
        # C_t, I_t — curated output set + importance tags
        self.curated: dict[str, str] = {}
        # D_t — full-text memory of every chunk ever retrieved
        self.full_text_memory: dict[str, Document] = {}
        # G_t — evidence graph (entity <-> doc maps)
        self.entity_to_docs: dict[str, set] = defaultdict(set)
        self.doc_to_entities: dict[str, set] = defaultdict(set)
        # V_t — verification records
        self.verification_store: list[dict] = []
        # H_t — search history
        self.search_history: list[str] = []
        # B_t — budget marker (approx tokens of the last render)
        self.tokens_rendered = 0

        self._seen_fingerprints: set[str] = set()
        self._seen_chunk_ids: set[str] = set()
        self._auto_seeded = False

    # ---------------- Retrieval-side actions ----------------

    def ingest_search_results(self, query: str, raw_docs: list[Document]) -> list[Document]:
        """Every retrieval tool (fan_out_search / search_corpus / grep_corpus) funnels
        its raw output through here: dedup -> compress -> update P_t and D_t. Retrieval
        outputs are never simply appended to the prompt."""
        self.search_history.append(query)
        fresh = []
        for doc in raw_docs:
            if doc.doc_id in self._seen_chunk_ids:
                continue
            fp = self._content_fingerprint(doc.text)
            if self._is_near_duplicate(fp):
                # hidden from the rendered state, but NOT from reward accounting — a
                # trainer scoring this episode should still credit this doc if it's gold.
                continue
            self._seen_chunk_ids.add(doc.doc_id)
            self._seen_fingerprints.add(fp)
            self.full_text_memory[doc.doc_id] = doc
            compressed = self._compress(doc, query)
            self.candidate_pool[doc.doc_id] = compressed
            self._extract_entities(compressed)
            fresh.append(compressed)

        if not self._auto_seeded and not self.curated and fresh:
            self._auto_seed(fresh)
        return fresh

    def _auto_seed(self, fresh_results: list[Document]) -> None:
        """Cold-start fix: a blank curated set gives near-zero learning signal on hard
        queries. Seed C_t with the top-k reranked results, tagged 'fair' — this changes
        the starting point from 'build from scratch' to 'refine what's here'; it does not
        decide relevance for the policy."""
        k = self.cfg["auto_seed"]["k"]
        tag = self.cfg["auto_seed"]["tag"]
        for doc in fresh_results[:k]:
            self.curated[doc.doc_id] = tag
        self._auto_seeded = True

    def review_docs(self, doc_ids: list[str]) -> list[Document]:
        """Re-render documents already in memory — no corpus call."""
        return [self.full_text_memory[d] for d in doc_ids if d in self.full_text_memory]

    # ---------------- Curation ----------------

    def curate(self, doc_id: str, action: str, importance: str | None = None) -> None:
        """The central state-editing action: add, remove, or importance-tag a document."""
        if action == "remove":
            self.curated.pop(doc_id, None)
            return
        if action != "add":
            raise ValueError(f"unknown curate action: {action!r}")
        if importance not in IMPORTANCE_LEVELS:
            raise ValueError(f"importance must be one of {IMPORTANCE_LEVELS}")
        if importance == "very high" and not self._has_passed_verify(doc_id):
            raise PermissionError(
                "verify-before-promote: doc must pass verify() before it can be 'very high'"
            )

        self.curated[doc_id] = importance
        self._evict_if_over_capacity()

    def _has_passed_verify(self, doc_id: str) -> bool:
        return any(v["doc_id"] == doc_id and v["verdict"] for v in self.verification_store)

    def _evict_if_over_capacity(self) -> None:
        """The harness — never the policy — enforces the capacity constraint, evicting
        the lowest-importance documents first."""
        cap = self.cfg["curate"]["cap"]
        if len(self.curated) <= cap:
            return
        ranked = sorted(self.curated.items(), key=lambda kv: _IMPORTANCE_RANK[kv[1]], reverse=True)
        while len(self.curated) > cap:
            worst_id, _ = ranked.pop(0)
            del self.curated[worst_id]

    # ---------------- Verification ----------------

    def verify(self, claim: str, doc_ids: list[str]) -> dict:
        """Strict per-document entailment call — see
        ../system_prompts/verify_entailment_prompt.md for the prompt this backs."""
        texts = [self.full_text_memory[d].text for d in doc_ids if d in self.full_text_memory]
        result = self.verify_fn(claim, texts)
        for doc_id in doc_ids:
            self.verification_store.append({
                "doc_id": doc_id, "claim": claim,
                "verdict": result["verdict"], "rationale": result["rationale"],
            })
        return result

    @staticmethod
    def _default_verify_stub(claim: str, texts: list[str]) -> dict:
        """Offline stand-in for the real LLM entailment call — substring match only.
        Replace with a client that sends system_prompts/verify_entailment_prompt.md to
        your model of choice and parses its {"verdict", "rationale"} JSON."""
        supported = any(claim.lower() in t.lower() for t in texts)
        return {"verdict": supported, "rationale": "stub: substring match — replace with a real LLM call"}

    # ---------------- Derived-state rendering ----------------

    def _compress(self, doc: Document, query: str) -> Document:
        """Sentence-BM25 compression: keep only the top-K sentences scored against the
        query, so a single result can't dominate the context window."""
        k = self.cfg["compression"]["top_k_sentences"]
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", doc.text.strip()) if s]
        if len(sentences) <= k:
            return doc
        scored = sorted(sentences, key=lambda s: self._term_overlap_score(s, query), reverse=True)[:k]
        order = {s: i for i, s in enumerate(sentences)}
        kept = sorted(scored, key=lambda s: order.get(s, 0))
        return Document(doc.doc_id, " ".join(kept), doc.source_query)

    @staticmethod
    def _term_overlap_score(sentence: str, query: str) -> float:
        """Minimal BM25-style term-saturation score (k1=1.5, no corpus IDF term since
        this scores one sentence at a time against the query, not a corpus)."""
        q_terms = Counter(re.findall(r"\w+", query.lower()))
        s_terms = Counter(re.findall(r"\w+", sentence.lower()))
        k1 = 1.5
        score = 0.0
        for term, qf in q_terms.items():
            f = s_terms.get(term, 0)
            if f:
                score += qf * ((f * (k1 + 1)) / (f + k1))
        return score

    def _content_fingerprint(self, text: str, shingle_size: int = 5) -> str:
        """MinHash-style fingerprint: hash all word-shingles, keep the smallest 32 as a
        sketch. Swap for `datasketch.MinHash` at production scale."""
        words = re.findall(r"\w+", text.lower())
        if len(words) < shingle_size:
            shingles = {" ".join(words)} if words else set()
        else:
            shingles = {" ".join(words[i:i + shingle_size]) for i in range(len(words) - shingle_size + 1)}
        hashes = sorted(hashlib.md5(s.encode()).hexdigest() for s in shingles)[:32]
        return "|".join(hashes)

    def _is_near_duplicate(self, fingerprint: str) -> bool:
        threshold = self.cfg["dedup"]["jaccard_threshold"]
        new_set = set(fingerprint.split("|")) if fingerprint else set()
        if not new_set:
            return False
        for seen in self._seen_fingerprints:
            seen_set = set(seen.split("|"))
            if not seen_set:
                continue
            jaccard = len(new_set & seen_set) / len(new_set | seen_set)
            if jaccard >= threshold:
                return True
        return False

    def _extract_entities(self, doc: Document) -> None:
        """Evidence graph G_t: lightweight regex extractor for three entity types —
        multi-word proper nouns, four-digit years, numeric dates."""
        proper_nouns = re.findall(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", doc.text)
        years = re.findall(r"\b(?:19|20)\d{2}\b", doc.text)
        dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", doc.text)
        for ent in [*proper_nouns, *years, *dates]:
            self.entity_to_docs[ent].add(doc.doc_id)
            self.doc_to_entities[doc.doc_id].add(ent)

    def evidence_graph_summary(self) -> dict:
        """Renders frequent entities, bridge documents (>= N frequent entities, natural
        candidates for verify/promotion), and singleton entities (follow-up leads)."""
        min_freq = self.cfg["evidence_graph"]["bridge_doc_min_frequent_entities"]
        frequent = {e for e, docs in self.entity_to_docs.items() if len(docs) >= min_freq}
        bridges = {
            doc_id for doc_id, ents in self.doc_to_entities.items()
            if len(ents & frequent) >= min_freq
        }
        singletons = {e for e, docs in self.entity_to_docs.items() if len(docs) == 1}
        return {
            "frequent_entities": sorted(frequent),
            "bridge_documents": sorted(bridges),
            "singleton_entities": sorted(singletons),
        }

    # ---------------- Budget-safe rendering ----------------

    def render_prompt_state(self, token_budget: int) -> str:
        """B_t: progressive-degradation renderer. Drops oldest search-history entries
        first; the curated set and recent history are the last things cut, so a rollout
        never fails outright from context overflow."""
        graph = self.evidence_graph_summary()

        def build(history: list[str]) -> str:
            return "\n".join([
                f"CURATED SET ({len(self.curated)}/{self.cfg['curate']['cap']}):",
                *[f"  [{tag}] {doc_id}" for doc_id, tag in self.curated.items()],
                f"EVIDENCE GRAPH: {len(graph['frequent_entities'])} frequent entities, "
                f"{len(graph['bridge_documents'])} bridge docs, {len(graph['singleton_entities'])} singletons",
                f"VERIFICATION RECORDS: {len(self.verification_store)}",
                f"SEARCH HISTORY ({len(history)} queries): {history[-3:]}",
            ])

        history = list(self.search_history)
        rendered = build(history)
        while self._approx_tokens(rendered) > token_budget and history:
            history = history[1:]
            rendered = build(history)
        self.tokens_rendered = self._approx_tokens(rendered)
        return rendered

    @staticmethod
    def _approx_tokens(text: str) -> int:
        return max(1, len(text) // 4)
