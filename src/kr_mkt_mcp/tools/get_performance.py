"""광고 성과 메트릭 조회 — V1의 묶음 도구.

지원:
- level: account / campaign / adset / ad
- tier: tier1(디폴트, 10개 메트릭) / all(어트리뷰션 윈도우 분해 + 동영상 + 소재 품질)
- metrics: 명시 시 그 메트릭만 반환 (tier 무시)
- date_preset (디폴트 last_7d) + since/until override
- breakdown + top_n + sort_by (Task 10에서 추가)
"""
from __future__ import annotations

import json as _json
from datetime import date as _date

from kr_mkt_mcp.config import (
    ATTRIBUTION_WINDOWS_DEFAULT,
    DATE_PRESET_DEFAULT,
    TIER1_METRICS,
    TIER_ALL_EXTRA_METRICS,
)
from kr_mkt_mcp.dates import resolve_date_range
from kr_mkt_mcp.meta_client import MetaClient
from kr_mkt_mcp.normalize import flatten_insights

# level별 추가 식별 필드 (응답에 같이 받아오는 게 AI 분석에 유리)
_LEVEL_ID_FIELDS = {
    "account": ("account_id",),
    "campaign": ("campaign_id", "campaign_name"),
    "adset": ("campaign_id", "campaign_name", "adset_id", "adset_name"),
    "ad": ("campaign_id", "campaign_name", "adset_id", "adset_name", "ad_id", "ad_name", "creative_id"),
}


def _resolve_metrics(*, tier: str, metrics: list[str] | None) -> list[str]:
    if metrics:
        return list(metrics)
    if tier == "tier1":
        return list(TIER1_METRICS)
    if tier == "all":
        return list(TIER1_METRICS) + list(TIER_ALL_EXTRA_METRICS)
    raise ValueError(f"알 수 없는 tier: {tier}")


def _build_insights_params(
    *,
    level: str,
    metric_fields: list[str],
    id_fields: tuple[str, ...],
    date_range: dict[str, str],
) -> dict[str, str]:
    fields = ",".join(list(id_fields) + metric_fields)
    return {
        "level": level,
        "fields": fields,
        "time_range": _json.dumps(date_range),
        "action_attribution_windows": _json.dumps(list(ATTRIBUTION_WINDOWS_DEFAULT)),
    }


async def get_performance(
    client: MetaClient,
    *,
    account_id: str,
    level: str = "campaign",
    tier: str = "tier1",
    metrics: list[str] | None = None,
    breakdown: str | None = None,
    sort_by: str | None = None,
    top_n: int | None = None,  # Task 10에서 사용
    date_preset: str | None = None,
    since: str | None = None,
    until: str | None = None,
    today: _date | None = None,
) -> dict:
    """광고 성과 조회. 응답 = {"data": list[dict], "meta": {...}}."""
    if level not in {"account", "campaign", "adset", "ad"}:
        raise ValueError(f"level은 account/campaign/adset/ad 중 하나: {level}")
    if tier not in {"tier1", "all"}:
        raise ValueError(f"tier는 tier1/all 중 하나: {tier}")

    acc = account_id if account_id.startswith("act_") else f"act_{account_id}"
    metric_fields = _resolve_metrics(tier=tier, metrics=metrics)
    id_fields = _LEVEL_ID_FIELDS[level]
    date_range = resolve_date_range(
        date_preset=date_preset or DATE_PRESET_DEFAULT,
        since=since,
        until=until,
        today=today,
    )

    # sort_by가 metrics에 없으면 자동 포함 — 정렬 기준이 응답에 있어야 하므로
    if sort_by and sort_by not in metric_fields:
        metric_fields = metric_fields + [sort_by]

    params = _build_insights_params(
        level=level,
        metric_fields=metric_fields,
        id_fields=id_fields,
        date_range=date_range,
    )
    if breakdown:
        params["breakdowns"] = breakdown

    rows, page_meta = await client.get_paginated(f"/{acc}/insights", params=params)
    flat = flatten_insights(rows, requested_metrics=metric_fields)

    flat = _apply_top_n(
        rows=flat,
        breakdown=breakdown,
        top_n=top_n,
        sort_by=sort_by or "spend",
        level=level,
    )

    meta = {
        **page_meta,
        "level": level,
        "tier": tier,
        "metrics_used": metric_fields,
        "date_range": date_range,
        "breakdown": breakdown,
    }
    return {"data": flat, "meta": meta}


def _sort_key(row: dict, key: str) -> float:
    v = row.get(key)
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _apply_top_n(
    *,
    rows: list[dict],
    breakdown: str | None,
    top_n: int | None,
    sort_by: str,
    level: str,
) -> list[dict]:
    """top_n 적용.

    - breakdown 없음: 단순 sort + slice
    - breakdown 있음: level별 entity(예: campaign_id)로 그룹화 → 그룹 합계 sort_by 기준 상위 top_n entity 선택 → 그 entity의 모든 breakdown 행 반환
    """
    if not top_n:
        return rows

    if not breakdown:
        return sorted(rows, key=lambda r: _sort_key(r, sort_by), reverse=True)[:top_n]

    # breakdown 있음: entity 기준 그룹화
    entity_field = _LEVEL_ID_FIELDS[level][0]  # campaign_id, adset_id, ad_id 등
    by_entity: dict[str, list[dict]] = {}
    totals: dict[str, float] = {}
    for r in rows:
        eid = r.get(entity_field)
        if eid is None:
            continue
        by_entity.setdefault(eid, []).append(r)
        totals[eid] = totals.get(eid, 0) + (_sort_key(r, sort_by) or 0)

    top_entities = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    top_ids = {eid for eid, _ in top_entities}
    return [r for r in rows if r.get(entity_field) in top_ids]
