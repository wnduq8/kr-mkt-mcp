"""ad의 creative 본문 조회. type-conditional 응답 (IMAGE/VIDEO/CAROUSEL)."""
from __future__ import annotations

from kr_mkt_mcp.meta_client import MetaClient

_AD_FIELDS = "id,name,creative"
_CREATIVE_FIELDS = (
    "id,name,object_type,thumbnail_url,image_url,video_id,title,body,"
    "call_to_action_type,object_url,link_url,object_story_spec,effective_object_story_id"
)


def _detect_type(creative: dict) -> str:
    if creative.get("video_id"):
        return "VIDEO"
    spec = creative.get("object_story_spec") or {}
    link = spec.get("link_data") or {}
    if link.get("child_attachments"):
        return "CAROUSEL"
    return "IMAGE"


def _build_carousel_cards(creative: dict) -> list[dict]:
    spec = creative.get("object_story_spec") or {}
    link = spec.get("link_data") or {}
    cards = []
    for child in link.get("child_attachments") or []:
        cta = (child.get("call_to_action") or {}).get("type")
        cards.append(
            {
                "image_url": child.get("image_url"),
                "headline": child.get("name"),
                "body": child.get("description"),
                "link": child.get("link"),
                "cta": cta,
            }
        )
    return cards


async def get_creative_preview(client: MetaClient, *, ad_id: str) -> dict:
    """ad → creative 두 단계 GET. 응답은 creative_type별 조건부 필드."""
    ad = await client.call_endpoint(f"/{ad_id}", params={"fields": _AD_FIELDS})
    creative_id = (ad.get("creative") or {}).get("id")
    if not creative_id:
        return {"ad_id": ad_id, "creative_type": "UNKNOWN", "error": "ad에 creative가 연결되지 않음"}

    creative = await client.call_endpoint(f"/{creative_id}", params={"fields": _CREATIVE_FIELDS})
    ctype = _detect_type(creative)

    base = {
        "ad_id": ad_id,
        "ad_name": ad.get("name"),
        "creative_id": creative_id,
        "creative_type": ctype,
        "thumbnail_url": creative.get("thumbnail_url"),
    }

    if ctype == "CAROUSEL":
        return {**base, "cards": _build_carousel_cards(creative)}

    if ctype == "VIDEO":
        return {
            **base,
            "video_id": creative.get("video_id"),
            "headline": creative.get("title"),
            "body": creative.get("body"),
            "cta": creative.get("call_to_action_type"),
            "link_url": creative.get("link_url") or creative.get("object_url"),
        }

    # IMAGE
    return {
        **base,
        "image_url": creative.get("image_url"),
        "headline": creative.get("title"),
        "body": creative.get("body"),
        "cta": creative.get("call_to_action_type"),
        "link_url": creative.get("link_url") or creative.get("object_url"),
    }
