"""Meta Graph API GET-only 클라이언트.

read-only 강제: POST/PUT/DELETE/PATCH 메서드 자체가 없다.
페이지네이션은 자동 fetch + PAGINATION_HARD_CAP 상한.
"""
from __future__ import annotations

import re
from typing import Any

import httpx

from kr_mkt_mcp import config as _config
from kr_mkt_mcp.config import Config

# Meta API 버전 prefix 정규식 — endpoint 시작이 /v숫자.숫자/ 면 사용자 override
_VERSION_PREFIX_RE = re.compile(r"^/v\d+\.\d+/")


class ReadOnlyViolation(Exception):
    """raw passthrough에서 GET 외 method 또는 write-shape 호출이 감지될 때."""


class MetaClient:
    """Meta Graph API GET wrapper.

    - GET only — POST/PUT/DELETE/PATCH 메서드 없음
    - 토큰은 Bearer header로 자동 주입
    - 페이지네이션 자동, hard_cap 도달 시 truncated=True 반환
    """

    def __init__(self, cfg: Config, *, http_client: httpx.AsyncClient | None = None):
        self._cfg = cfg
        self._http = http_client or httpx.AsyncClient(timeout=30.0)

    def _build_url(self, endpoint: str) -> str:
        if _VERSION_PREFIX_RE.match(endpoint):
            # 사용자 override: endpoint에 /v22.0/ 같은 prefix 있음 → base_url + endpoint
            return f"{self._cfg.base_url}{endpoint}"
        # 디폴트 버전 prefix 추가
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
        return f"{self._cfg.graph_url}{endpoint}"

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._cfg.access_token}"}

    async def call_endpoint(
        self,
        endpoint: str,
        params: dict[str, Any] | None,
    ) -> dict:
        """raw GET — `call_meta_api` 도구에서 사용. 응답 본문 그대로 반환."""
        url = self._build_url(endpoint)
        resp = await self._http.get(url, params=params if params else None, headers=self._headers())
        resp.raise_for_status()
        return resp.json()

    async def get_paginated(
        self,
        endpoint: str,
        params: dict[str, Any] | None,
    ) -> tuple[list[dict], dict]:
        """자동 페이지네이션. hard_cap 도달 시 truncated 플래그 반환.

        반환:
            rows: list[dict] — 모든 페이지의 data를 합친 평탄 list
            meta: {"truncated": bool, "hard_cap": int, "pages_fetched": int}
        """
        url = self._build_url(endpoint)
        rows: list[dict] = []
        pages = 0
        truncated = False

        while url:
            resp = await self._http.get(url, params=params if params else None, headers=self._headers())
            resp.raise_for_status()
            body = resp.json()
            pages += 1
            rows.extend(body.get("data", []))

            cap = _config.PAGINATION_HARD_CAP
            if len(rows) >= cap:
                rows = rows[:cap]
                truncated = bool(body.get("paging", {}).get("next")) or len(rows) >= cap
                break

            next_url = body.get("paging", {}).get("next")
            if not next_url:
                break
            url = next_url
            params = None  # next URL에 쿼리 다 포함됨

        return rows, {
            "truncated": truncated,
            "hard_cap": _config.PAGINATION_HARD_CAP,
            "pages_fetched": pages,
        }

    async def aclose(self) -> None:
        await self._http.aclose()
