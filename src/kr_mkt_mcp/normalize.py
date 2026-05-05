# src/kr_mkt_mcp/normalize.py
"""Meta API 응답을 flat list[dict]로 정규화.

핵심 변환:
- 숫자 string → int/float
- actions[] 중 특정 action_type → 평탄 메트릭 (예: purchases = actions[purchase].value)
- purchase_roas[] (list 형태) → scalar (첫 element value)
- nested 메트릭 → flat 키
"""
from __future__ import annotations

from typing import Any

# AI가 자연어로 요청할 수 있는 평탄 메트릭 → Meta API actions[].action_type 매핑
_ACTION_TYPE_BY_FLAT_METRIC = {
    "purchases": "purchase",
    "leads": "lead",
    "registrations": "complete_registration",
    "add_to_carts": "add_to_cart",
    "checkouts_initiated": "initiate_checkout",
    "page_views": "page_view",
}


def parse_metric_value(value: Any) -> Any:
    """숫자처럼 보이는 string을 int/float로 변환. 그 외엔 원본 그대로."""
    if value is None or not isinstance(value, str):
        return value
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def extract_action_value(actions: list[dict] | None, action_type: str) -> float | int:
    """actions[] 중 특정 action_type의 value를 number로 추출. 없으면 0."""
    if not actions:
        return 0
    for entry in actions:
        if entry.get("action_type") == action_type:
            return parse_metric_value(entry.get("value")) or 0
    return 0


def _flatten_purchase_roas(value: Any) -> float | None:
    """Meta API의 purchase_roas는 list[{action_type, value}] 형태. 첫 entry value를 scalar로."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        return parse_metric_value(value)
    if isinstance(value, list) and value:
        return parse_metric_value(value[0].get("value"))
    return None


def flatten_insights(
    raw_rows: list[dict],
    *,
    requested_metrics: list[str] | None = None,
) -> list[dict]:
    """Meta Insights API 응답을 평탄 list[dict]로 변환.

    - 숫자 string → number
    - actions[]에서 평탄 메트릭(purchases, leads 등) 추출
    - purchase_roas list → scalar
    - 식별 필드(campaign_id/campaign_name/adset_id/.../date_start/date_stop) 유지
    - breakdown 필드(age/gender 등) 그대로 유지
    """
    out: list[dict] = []
    for raw in raw_rows:
        flat: dict = {}
        for k, v in raw.items():
            if k == "actions":
                # actions는 평탄 메트릭으로 분해
                actions = v
                for flat_name, action_type in _ACTION_TYPE_BY_FLAT_METRIC.items():
                    if requested_metrics is None or flat_name in requested_metrics:
                        flat[flat_name] = extract_action_value(actions, action_type)
                continue
            if k == "purchase_roas":
                flat["purchase_roas"] = _flatten_purchase_roas(v)
                continue
            if k == "action_values":
                # purchase_value 등 평탄화 — actions와 동일 패턴
                for flat_name, action_type in _ACTION_TYPE_BY_FLAT_METRIC.items():
                    target_key = f"{flat_name.removesuffix('s')}_value"
                    if requested_metrics is None or target_key in requested_metrics:
                        flat[target_key] = extract_action_value(v, action_type)
                continue
            flat[k] = parse_metric_value(v)
        out.append(flat)
    return out
