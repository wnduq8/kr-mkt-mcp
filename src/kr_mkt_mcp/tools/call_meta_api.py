"""raw GET passthrough — V1 비커버 케이스 escape hatch.

안전장치:
- HTTP method GET만 (MetaClient에 POST 등이 없음)
- endpoint가 / 로 시작하는 graph 경로만 허용 (외부 URL 차단)
- // 시작 차단 (경로 traversal 시도)
- endpoint에 ? 또는 URL 인코딩(%3F) 포함 차단 (query string은 params로만)
- params에 method/access_token 등 키 거부 (write 우회 + 토큰 leak 차단)
"""
from __future__ import annotations

import urllib.parse
from typing import Any

from kr_mkt_mcp.meta_client import MetaClient

# write 우회 시도 + 토큰 노출 차단
_FORBIDDEN_PARAM_KEYS = {
    "method",
    "_method",
    "http_method",
    "access_token",  # Bearer 헤더로 자동 주입되므로 params로 받으면 안 됨 (URL leak 위험)
    "appsecret_proof",
}


def _validate_endpoint(endpoint: str) -> None:
    if not endpoint.startswith("/"):
        raise ValueError(
            f"endpoint는 '/'로 시작해야 합니다. 외부 URL 호출 차단. 받은 값: {endpoint!r}"
        )
    if endpoint.startswith("//"):
        raise ValueError(f"잘못된 endpoint 형식 ('//'로 시작): {endpoint!r}")
    # URL 인코딩(%3F=?, %26=&) 우회 차단 — decode 후 재검사
    decoded = urllib.parse.unquote(endpoint)
    if "?" in decoded or "&" in decoded:
        raise ValueError(
            f"endpoint에 query string(?/&)을 포함할 수 없습니다. "
            f"params 인자로 전달하세요. 받은 값: {endpoint!r}"
        )


def _validate_params(params: dict[str, Any] | None) -> None:
    if not params:
        return
    bad = _FORBIDDEN_PARAM_KEYS.intersection(params.keys())
    if bad:
        raise ValueError(
            f"params에 금지된 키가 포함됨 (write 우회 시도 차단): {sorted(bad)}"
        )


async def call_meta_api(
    client: MetaClient,
    *,
    endpoint: str,
    params: dict[str, Any] | None,
) -> dict:
    """raw GET. 반환: {"data": <Meta 원본 응답>, "meta": {"api_usage": ...}}.

    api_usage가 있으면 meta에 포함, 없으면 None. data는 Meta 응답 그대로.
    """
    _validate_endpoint(endpoint)
    _validate_params(params)
    raw = await client.call_endpoint(endpoint, params=params)
    return {"data": raw, "meta": {"api_usage": client.last_usage}}
