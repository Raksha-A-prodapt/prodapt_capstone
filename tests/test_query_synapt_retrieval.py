import numpy as np
import pandas as pd

from agents.query_synapt_agent import QuerySynaptAgent


ROWS = [
    {"incident_id": "INC-A", "city": "Alpha", "state": "MN", "season": "Winter", "weather": "Snow", "issue_reported": "latency", "latency_ms": 180, "throughput_mbps": 200, "signal_strength_dbm": -120},
    {"incident_id": "INC-B", "city": "Alpha", "state": "MN", "season": "Winter", "weather": "Snow", "issue_reported": "latency", "latency_ms": 140, "throughput_mbps": 500, "signal_strength_dbm": -95},
    {"incident_id": "INC-C", "city": "Beta", "state": "CA", "season": "Summer", "weather": "Clear", "issue_reported": "throughput", "latency_ms": 60, "throughput_mbps": 100, "signal_strength_dbm": -110},
    {"incident_id": "INC-D", "city": "Beta", "state": "CA", "season": "Summer", "weather": "Clear", "issue_reported": "normal", "latency_ms": 40, "throughput_mbps": 900, "signal_strength_dbm": -70},
]


class FakeEmbeddingModel:
    def encode(self, query):
        lowered = query.lower()
        return np.array([
            1.0 if "latency" in lowered else 0.0,
            1.0 if "throughput" in lowered else 0.0,
            1.0 if "signal" in lowered else 0.0,
        ])


class FakeCollection:
    embeddings = {
        "INC-A": [1, 0, 0],
        "INC-B": [0.8, 0, 0],
        "INC-C": [0, 1, 0],
        "INC-D": [0, 0.2, 1],
    }

    def get(self, ids, include=None):
        return {
            "ids": ids,
            "embeddings": [self.embeddings[item] for item in ids],
        }


def make_agent():
    agent = QuerySynaptAgent.__new__(QuerySynaptAgent)
    agent.df = pd.DataFrame(ROWS)
    agent.metadata_values = {
        field: sorted(agent.df[field].astype(str).str.lower().unique().tolist())
        for field in ("city", "state", "season", "weather", "issue_reported")
    }
    agent.metric_thresholds = {
        "latency_ms": {"low_upper": 50, "high_lower": 150},
        "throughput_mbps": {"low_upper": 250, "high_lower": 800},
        "signal_strength_dbm": {"low_upper": -105, "high_lower": -75},
    }
    agent.embedding_model = FakeEmbeddingModel()
    agent.collection = FakeCollection()
    agent._build_bm25()
    return agent


def retrieve(agent, query):
    plan = agent._validate_query_plan(agent._fallback_parser(query, 15), query)
    soft_hints = agent._apply_severity_bands(query, plan)
    metadata_ids = agent.get_metadata_candidates(plan.metadata_filters)
    eligible_ids = agent.apply_numeric_conditions(metadata_ids, plan.numeric_conditions)
    semantic = agent.semantic_search(
        plan.search_query,
        plan.metadata_filters,
        len(eligible_ids),
        eligible_ids,
    )
    bm25 = agent.bm25_search(plan.search_query, eligible_ids, len(eligible_ids))
    metric = agent.metric_relevance_scores(query, eligible_ids, plan.numeric_conditions)
    ranked = agent.hybrid_rank(bm25, semantic, min(plan.top_k, len(eligible_ids)), metric)
    return plan, soft_hints, eligible_ids, ranked


def test_explicit_metadata_and_numeric_conditions_are_hard_filters():
    plan, soft, eligible, ranked = retrieve(
        make_agent(), "Find Alpha incidents with latency above 150 ms"
    )
    assert plan.metadata_filters == {"city": "alpha"}
    assert [condition.field for condition in plan.numeric_conditions] == ["latency_ms"]
    assert eligible == ["INC-A"]
    assert [item["incident_id"] for item in ranked] == ["INC-A"]
    assert soft == []


def test_qualitative_metric_is_soft_ranking_signal():
    plan, soft, eligible, ranked = retrieve(make_agent(), "Find incidents with high latency")
    assert plan.numeric_conditions == []
    assert plan.metadata_filters == {}
    assert soft == [{"field": "latency_ms", "band": "high", "mode": "soft_ranking"}]
    assert set(eligible) == {"INC-A", "INC-B", "INC-C", "INC-D"}
    assert [item["incident_id"] for item in ranked[:2]] == ["INC-A", "INC-B"]


def test_no_filters_searches_the_full_candidate_pool():
    _, _, eligible, ranked = retrieve(make_agent(), "Find relevant network incidents")
    assert len(eligible) == 4
    assert len(ranked) == 4


def test_empty_hard_filter_returns_no_results():
    _, _, eligible, ranked = retrieve(
        make_agent(), "Find Alpha incidents with latency above 300 ms"
    )
    assert eligible == []
    assert ranked == []
