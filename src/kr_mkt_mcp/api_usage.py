"""Meta Graph API usage 모니터링 — rate limit 헤더 파싱 + 시각화.

Meta는 API 응답에 다음 헤더로 사용량을 알려줌:
- X-App-Usage: 앱 단위 사용량 (call_count, total_cputime, total_time, 각 0-100%)
- X-Ad-Account-Usage: 광고 계정 단위 (acc_id_util_pct, ads_api_access_tier 등)
- X-Business-Use-Case-Usage: business use case 단위 (id별 list[record])

Meta API 100%에 도달하면 일정 시간 호출 차단됨. 본 모듈은 도달 전에 사용자에게
gauge bar + warning level로 안내.
"""
from __future__ import annotations

import json
from typing import Any


def _get_header(headers: Any, name: str) -> str | None:
    """case-insensitive header 값 추출. httpx.Headers 또는 dict 모두 지원."""
    if not headers:
        return None
    # 1차 — httpx.Headers는 자체 case-insensitive get 지원
    try:
        v = headers.get(name)
        if v is not None:
            return v
    except (AttributeError, TypeError):
        pass
    # 2차 — 일반 dict의 경우 lower() 비교로 case-insensitive 검색
    target = name.lower()
    try:
        for k, v in headers.items():
            if k.lower() == target:
                return v
    except (AttributeError, TypeError):
        pass
    return None


def parse_usage_headers(headers: Any) -> dict:
    """응답 헤더에서 usage JSON 3종 파싱. 누락된 항목은 None."""
    out: dict[str, Any] = {"app": None, "ad_account": None, "business_use_case": None}
    for header_name, key in (
        ("X-App-Usage", "app"),
        ("X-Ad-Account-Usage", "ad_account"),
        ("X-Business-Use-Case-Usage", "business_use_case"),
    ):
        raw = _get_header(headers, header_name)
        if not raw:
            continue
        try:
            out[key] = json.loads(raw)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return out


def format_gauge(pct: float, *, width: int = 20) -> str:
    """0~100 percent → text gauge bar.

    예: 28 → "██████░░░░░░░░░░░░░░ 28.0%"
    """
    pct = max(0.0, min(100.0, float(pct)))
    filled = int(round((pct / 100.0) * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"{bar} {pct:.1f}%"


# (threshold, level, message) — 내림차순. 첫 매칭이 결과.
_THRESHOLDS = (
    (90.0, "critical", "🔴 위험: API 한도 90% 초과 — 호출 즉시 중단 권장"),
    (75.0, "high", "🟠 주의: API 한도 75% 초과 — 호출 빈도 줄이기"),
    (50.0, "medium", "🟡 알림: API 한도 50% 초과 — 모니터링 필요"),
)


def compute_warning(max_pct: float) -> tuple[str, str]:
    """가장 높은 percent → (level, message). 50% 미만은 ok."""
    for threshold, level, msg in _THRESHOLDS:
        if max_pct >= threshold:
            return level, msg
    return "ok", "🟢 정상"


def _flatten_business_use_case(buc: dict | None) -> list[float]:
    """X-Business-Use-Case-Usage 안의 percent 값들 추출."""
    if not buc:
        return []
    out: list[float] = []
    for records in buc.values():
        if not isinstance(records, list):
            continue
        for rec in records:
            if not isinstance(rec, dict):
                continue
            for key in ("call_count", "total_cputime", "total_time"):
                v = rec.get(key)
                if isinstance(v, (int, float)):
                    out.append(float(v))
    return out


def summarize_usage(headers: Any) -> dict | None:
    """헤더 → 사용량 요약 dict. 헤더에 사용량 정보 없으면 None.

    반환 dict:
        app, ad_account, business_use_case (raw)
        max_pct (가장 높은 % 값)
        warning_level: ok | medium | high | critical
        warning_message: 🟢/🟡/🟠/🔴 + 한국어 메시지
        gauge: max_pct 기준 텍스트 게이지 바
    """
    parsed = parse_usage_headers(headers)
    if not any(parsed.values()):
        return None

    pcts: list[float] = []

    app = parsed.get("app") or {}
    for key in ("call_count", "total_cputime", "total_time"):
        v = app.get(key)
        if isinstance(v, (int, float)):
            pcts.append(float(v))

    acc = parsed.get("ad_account") or {}
    if isinstance(acc.get("acc_id_util_pct"), (int, float)):
        pcts.append(float(acc["acc_id_util_pct"]))

    pcts.extend(_flatten_business_use_case(parsed.get("business_use_case")))

    if not pcts:
        return None

    max_pct = max(pcts)
    level, message = compute_warning(max_pct)

    return {
        "app": parsed.get("app"),
        "ad_account": parsed.get("ad_account"),
        "business_use_case": parsed.get("business_use_case"),
        "max_pct": round(max_pct, 1),
        "warning_level": level,
        "warning_message": message,
        "gauge": format_gauge(max_pct),
    }
