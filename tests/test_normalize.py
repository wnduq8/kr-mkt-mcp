# tests/test_normalize.py
import json
from pathlib import Path

import pytest

from kr_mkt_mcp.normalize import flatten_insights, parse_metric_value, extract_action_value


FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_parse_metric_value_numeric_string():
    assert parse_metric_value("45000") == 45000
    assert parse_metric_value("1.25") == 1.25
    assert parse_metric_value("3.0") == 3.0


def test_parse_metric_value_passthrough_non_numeric():
    assert parse_metric_value("ACTIVE") == "ACTIVE"
    assert parse_metric_value(None) is None


def test_extract_action_value_purchase():
    actions = [
        {"action_type": "purchase", "value": "12"},
        {"action_type": "page_view", "value": "200"},
    ]
    assert extract_action_value(actions, "purchase") == 12.0


def test_extract_action_value_missing_returns_zero():
    assert extract_action_value([], "purchase") == 0


def test_flatten_insights_tier1():
    raw = load("insights_campaign_tier1.json")["data"]
    rows = flatten_insights(raw, requested_metrics=["spend", "ctr", "purchase_roas", "purchases"])
    assert len(rows) == 1
    row = rows[0]
    assert row["campaign_id"] == "c1"
    assert row["campaign_name"] == "봄세일"
    assert row["spend"] == 45000
    assert row["ctr"] == 1.25
    assert row["purchase_roas"] == 3.2
    assert row["purchases"] == 12
    assert row["date_start"] == "2026-04-28"
    assert row["date_stop"] == "2026-05-04"


def test_flatten_insights_with_breakdown():
    raw = load("insights_breakdown_age.json")["data"]
    rows = flatten_insights(raw, requested_metrics=["spend", "purchase_roas"])
    assert len(rows) == 2
    assert {r["age"] for r in rows} == {"25-34", "35-44"}
    assert rows[0]["spend"] == 20000
    assert rows[0]["purchase_roas"] == 3.5
