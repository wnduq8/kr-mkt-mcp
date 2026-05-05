"""raw GET passthrough — V1 비커버 케이스 escape hatch.

안전장치:
- HTTP method GET만 (MetaClient에 POST 등이 없음)
- endpoint가 / 로 시작하는 graph 경로만 허용 (외부 URL 차단)
- // 시작 차단 (경로 traversal 시도)
- endpoint에 ? 포함 차단 (query string은 params로만 전달)
- params에 method 키 거부 (POST-as-GET 우회 시도)
"""
from __future__ import annotations

from typing import Any

from kr_mkt_mcp.meta_client import MetaClient

_FORBIDDEN_PARAM_KEYS = {"method", "_method", "http_method"}


def _validate_endpoint(endpoint: str) -> None:
    if not endpoint.startswith("/"):
        raise ValueError(
            f"endpoint는 '/'로 시작해야 합니다. 외부 URL 호출 차단. 받은 값: {endpoint!r}"
        )
    if endpoint.startswith("//"):
        raise ValueError(f"잘못된 endpoint 형식 ('//'로 시작): {endpoint!r}")
    if "?" in endpoint or "&" in endpoint:
        raise ValueError(
            f"endpoint에 query string을 포함할 수 없습니다. params 인자로 전달하세요. 받은 값: {endpoint!r}"
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
    """raw GET. Meta Graph API 응답 본문을 그대로 반환."""
    _validate_endpoint(endpoint)
    _validate_params(params)
    return await client.call_endpoint(endpoint, params=params)
