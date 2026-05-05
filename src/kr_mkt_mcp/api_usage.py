"""Meta Graph API usage 모니터링 — rate limit 헤더 파싱 + 친화적 한국어 요약 + gauge.

Meta API v25에서 응답에 포함되는 사용량 헤더 4종:
- X-App-Usage: 앱 단위 사용량 (call_count/total_cputime/total_time, 0~100%)
  → 일부 토큰/scope에서만 제공
- X-Ad-Account-Usage: 광고 계정 단위 (acc_id_util_pct, ads_api_access_tier 등)
  → 일부 토큰/scope에서만 제공
- X-Business-Use-Case-Usage: business use case별 (ads_management / ads_insights 등)
  → 거의 모든 응답에 포함 (가장 신뢰 가능)
- X-FB-Ads-Insights-Throttle: insights 호출 전용 (app_id_util_pct, acc_id_util_pct,
  ads_api_access_tier) → /act_*/insights 호출 시 자동 포함

Meta API 100% 도달 시 일정 시간 호출 차단되므로 도달 전에 사용자에게 gauge bar +
한국어 warning 메시지로 안내.
"""
from __future__ import annotations

import json
from typing import Any


# 헤더 raw key → 우리 dict의 친화적 슬러그
_HEADER_TO_KEY = {
    "X-App-Usage": "app_usage",
    "X-Ad-Account-Usage": "ad_account_usage",
    "X-Business-Use-Case-Usage": "business_use_case_usage",
    "X-FB-Ads-Insights-Throttle": "insights_throttle",
}


# Meta가 사용하는 코드 → 한국어
_TIER_KO = {
    "development_access": "개발자 등급 (시간당 한도 낮음 — Standard Access 신청 권장)",
    "standard_access": "스탠다드 등급",
    "basic_access": "베이직 등급",
}

_USE_CASE_TYPE_KO = {
    "ads_management": "광고 관리",
    "ads_insights": "광고 분석",
    "instagram_basic": "Instagram 기본",
    "pages_messaging": "페이지 메시징",
}

_LEVEL_TO_BADGE = {
    "ok": "🟢 정상",
    "medium": "🟡 알림",
    "high": "🟠 주의",
    "critical": "🔴 위험",
}


def _get_header(headers: Any, name: str) -> str | None:
    """case-insensitive header 값 추출. httpx.Headers 또는 dict 모두 지원."""
    if not headers:
        return None
    try:
        v = headers.get(name)
        if v is not None:
            return v
    except (AttributeError, TypeError):
        pass
    target = name.lower()
    try:
        for k, v in headers.items():
            if k.lower() == target:
                return v
    except (AttributeError, TypeError):
        pass
    return None


def parse_usage_headers(headers: Any) -> dict:
    """응답 헤더에서 usage JSON 4종 파싱. 누락된 항목은 None.

    반환 키: app_usage, ad_account_usage, business_use_case_usage, insights_throttle.
    """
    out: dict[str, Any] = {key: None for key in _HEADER_TO_KEY.values()}
    for header_name, key in _HEADER_TO_KEY.items():
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


def _detect_access_tier(parsed: dict) -> str | None:
    """여러 헤더에서 ads_api_access_tier 값 찾기."""
    for source_key in ("ad_account_usage", "insights_throttle"):
        src = parsed.get(source_key) or {}
        tier = src.get("ads_api_access_tier")
        if tier:
            return tier
    buc = parsed.get("business_use_case_usage") or {}
    for records in buc.values():
        for rec in records or []:
            if isinstance(rec, dict) and rec.get("ads_api_access_tier"):
                return rec["ads_api_access_tier"]
    return None


def _build_friendly_summary(parsed: dict, max_pct: float, level: str) -> list[str]:
    """사용자에게 그대로 노출 가능한 한국어 요약 lines.

    AI는 이 list를 응답에 그대로 박아넣어도 됨.
    """
    lines: list[str] = []
    badge = _LEVEL_TO_BADGE.get(level, "🟢")
    lines.append(f"{badge} 최대 사용률 {max_pct:.1f}%")

    # X-FB-Ads-Insights-Throttle (insights 호출 시 가장 정확)
    throttle = parsed.get("insights_throttle") or {}
    if isinstance(throttle.get("acc_id_util_pct"), (int, float)):
        lines.append(f"광고 계정 부하율: {throttle['acc_id_util_pct']}%")
    if isinstance(throttle.get("app_id_util_pct"), (int, float)):
        lines.append(f"앱 부하율: {throttle['app_id_util_pct']}%")

    # X-Ad-Account-Usage (가용 시)
    acc = parsed.get("ad_account_usage") or {}
    if isinstance(acc.get("acc_id_util_pct"), (int, float)) and "acc_id_util_pct" not in throttle:
        lines.append(f"광고 계정 부하율: {acc['acc_id_util_pct']}%")
    if isinstance(acc.get("reset_time_duration"), (int, float)):
        lines.append(f"한도 리셋까지: {acc['reset_time_duration']}초")

    # X-App-Usage (앱 단위 — 가용 시)
    app = parsed.get("app_usage") or {}
    if app:
        cc = app.get("call_count", 0)
        cpu = app.get("total_cputime", 0)
        tt = app.get("total_time", 0)
        lines.append(f"앱 사용률: 호출수 {cc}% / CPU {cpu}% / 전체 {tt}%")

    # X-Business-Use-Case-Usage (호출 유형별)
    buc = parsed.get("business_use_case_usage") or {}
    for biz_id, records in buc.items():
        for rec in records or []:
            if not isinstance(rec, dict):
                continue
            type_ko = _USE_CASE_TYPE_KO.get(rec.get("type"), rec.get("type") or "기타")
            cc = rec.get("call_count", 0)
            cpu = rec.get("total_cputime", 0)
            tt = rec.get("total_time", 0)
            lines.append(
                f"{type_ko} 호출 (계정 {biz_id}): 호출수 {cc}% / CPU {cpu}% / 전체 {tt}%"
            )
            etr = rec.get("estimated_time_to_regain_access", 0)
            if isinstance(etr, (int, float)) and etr > 0:
                lines.append(f"⚠️ 차단 해제까지 {etr}초 대기 필요")

    # API 접근 등급
    tier = _detect_access_tier(parsed)
    if tier:
        lines.append(f"API 접근 등급: {_TIER_KO.get(tier, tier)}")

    # 권장 조치
    lines.append(f"권장: {_recommend_action(level, tier)}")

    return lines


def _recommend_action(level: str, tier: str | None) -> str:
    base_map = {
        "ok": "현재 정상 — 추가 조치 불필요",
        "medium": "호출 빈도 모니터링 권장",
        "high": "호출 빈도 줄이기 — 잠시 대기 후 재시도",
        "critical": "즉시 호출 중단 — Meta API rate limit 도달 임박",
    }
    base = base_map.get(level, base_map["ok"])
    if tier == "development_access":
        base += ". 현재 Development Access 등급이라 시간당 한도가 매우 낮음 — Standard Access 신청 시 한도 대폭 상향"
    return base


def summarize_usage(headers: Any) -> dict | None:
    """헤더 → 사용량 요약 dict. 헤더에 사용량 정보 없으면 None.

    반환 dict 키:
        app_usage / ad_account_usage / business_use_case_usage / insights_throttle (raw)
        max_pct (가장 높은 percent)
        warning_level: ok | medium | high | critical
        warning_message: 🟢/🟡/🟠/🔴 + 한국어 메시지
        gauge: max_pct 기준 텍스트 게이지 바
        access_tier: development_access | standard_access | basic_access | None
        access_tier_ko: 한국어 해석
        summary_ko: list[str] — 사용자에게 그대로 노출 가능한 한국어 요약 라인들
    """
    parsed = parse_usage_headers(headers)
    if not any(parsed.values()):
        return None

    pcts: list[float] = []

    app = parsed.get("app_usage") or {}
    for key in ("call_count", "total_cputime", "total_time"):
        v = app.get(key)
        if isinstance(v, (int, float)):
            pcts.append(float(v))

    acc = parsed.get("ad_account_usage") or {}
    if isinstance(acc.get("acc_id_util_pct"), (int, float)):
        pcts.append(float(acc["acc_id_util_pct"]))

    throttle = parsed.get("insights_throttle") or {}
    for key in ("app_id_util_pct", "acc_id_util_pct"):
        v = throttle.get(key)
        if isinstance(v, (int, float)):
            pcts.append(float(v))

    pcts.extend(_flatten_business_use_case(parsed.get("business_use_case_usage")))

    if not pcts:
        return None

    max_pct = max(pcts)
    level, message = compute_warning(max_pct)
    tier = _detect_access_tier(parsed)

    return {
        # raw
        "app_usage": parsed.get("app_usage"),
        "ad_account_usage": parsed.get("ad_account_usage"),
        "business_use_case_usage": parsed.get("business_use_case_usage"),
        "insights_throttle": parsed.get("insights_throttle"),
        # 핵심 메트릭
        "max_pct": round(max_pct, 1),
        "warning_level": level,
        "warning_message": message,
        "gauge": format_gauge(max_pct),
        # API 접근 등급
        "access_tier": tier,
        "access_tier_ko": _TIER_KO.get(tier, tier) if tier else None,
        # 사용자 노출용 한국어 요약
        "summary_ko": _build_friendly_summary(parsed, max_pct, level),
    }
