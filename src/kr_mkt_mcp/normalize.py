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
    "landing_page_views": "landing_page_view",  # Meta v25에서 top-level 필드 deprecated, actions에서 추출
}

# action_values 분해 시 사용할 value 키 매핑 — 영어식 단수화 일괄 규칙은 깨지므로 명시
_VALUE_KEY_BY_FLAT_METRIC = {
    "purchases": "purchase_value",
    "leads": "lead_value",
    "registrations": "registration_value",
    "add_to_carts": "add_to_cart_value",
    "checkouts_initiated": "checkout_value",
    "page_views": "page_view_value",
    "landing_page_views": "landing_page_view_value",
}


def to_api_fields(metric_fields: list[str]) -> list[str]:
    """우리가 쓰는 flat metric 이름 → Meta API 실 필드 이름으로 번역.

    purchases/leads 등 → actions
    purchase_value/lead_value 등 → action_values
    그 외(impressions/spend/purchase_roas 등) → 그대로
    중복 제거 + 순서 유지.
    """
    flat_action_names = set(_ACTION_TYPE_BY_FLAT_METRIC.keys())
    flat_value_names = set(_VALUE_KEY_BY_FLAT_METRIC.values())
    out: list[str] = []
    seen: set[str] = set()
    for m in metric_fields:
        if m in flat_action_names:
            translated = "actions"
        elif m in flat_value_names:
            translated = "action_values"
        else:
            translated = m
        if translated not in seen:
            out.append(translated)
            seen.add(translated)
    return out


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
    - action_values[]에서 value 메트릭(purchase_value 등) 추출
    - purchase_roas list → scalar
    - 식별 필드(campaign_id/campaign_name/adset_id/.../date_start/date_stop) 유지
    - breakdown 필드(age/gender 등) 그대로 유지

    requested_metrics 동작:
        - actions[] / action_values[] 분해 시 어떤 flat 메트릭을 추출할지 필터.
          예: requested_metrics=["purchases"]면 actions에서 purchase만 추출.
        - 일반 필드(spend, ctr 등)와 purchase_roas는 항상 포함 — Meta API 호출 시
          fields 파라미터로 이미 통제됐다는 가정.
        - None이면 _ACTION_TYPE_BY_FLAT_METRIC / _VALUE_KEY_BY_FLAT_METRIC의 모든
          매핑을 추출.
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
                # purchase_value 등 평탄화 — _VALUE_KEY_BY_FLAT_METRIC로 키 명시
                for flat_name, action_type in _ACTION_TYPE_BY_FLAT_METRIC.items():
                    target_key = _VALUE_KEY_BY_FLAT_METRIC[flat_name]
                    if requested_metrics is None or target_key in requested_metrics:
                        flat[target_key] = extract_action_value(v, action_type)
                continue
            flat[k] = parse_metric_value(v)
        out.append(flat)
    return out
