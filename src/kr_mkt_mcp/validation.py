"""입력 검증 헬퍼 — path traversal, field injection, 범위 초과 차단.

도구 진입점에서 사용자/LLM 제공 인자를 신뢰하지 않고 검증.
"""
from __future__ import annotations

import re

# 영문 소문자로 시작 + 알파벳/숫자/언더스코어만. Meta API 필드명 표준.
_FIELD_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")

# Path traversal/injection을 차단할 문자 (ID 파라미터용)
_FORBIDDEN_ID_PARTS = ("..", "/", "\\", "?", "&", "#", "%", "\n", "\r", "\t", " ")


def validate_id(value: str, name: str) -> None:
    """account_id/campaign_id/ad_id 등 ID 파라미터 검증.

    Meta ID는 숫자 또는 act_숫자 형태. path traversal/query injection 시도 차단.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name}는 빈 문자열이 될 수 없습니다.")
    for part in _FORBIDDEN_ID_PARTS:
        if part in value:
            raise ValueError(
                f"{name}에 허용되지 않는 문자가 포함되어 있습니다: {part!r}"
            )


def validate_field_name(value: str, name: str = "field") -> None:
    """metric/sort_by 같은 Meta API 필드명 검증.

    `^[a-z][a-z0-9_]*$` 패턴만 허용 — 컴마/공백 통한 의도치 않은 필드 추가 차단.
    """
    if not isinstance(value, str) or not _FIELD_NAME_RE.match(value):
        raise ValueError(
            f"{name}는 영문 소문자 + 숫자/언더스코어만 허용됩니다: {value!r}"
        )


def validate_in_set(value: str, allowed: tuple[str, ...] | set[str], name: str) -> None:
    """enum 값 검증. allowed 외 값은 거부."""
    if value not in allowed:
        raise ValueError(
            f"{name} 허용 값이 아닙니다: {value!r}. 허용: {sorted(allowed)}"
        )


def validate_int_range(value: int, *, lo: int, hi: int, name: str) -> None:
    """정수 범위 검증."""
    if not isinstance(value, int) or value < lo or value > hi:
        raise ValueError(f"{name}은 {lo}~{hi} 사이 정수여야 합니다: {value!r}")
