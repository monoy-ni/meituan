from __future__ import annotations

import json

from activity_agent.domain.models import MerchantSupply, Theme, UserRequest
from activity_agent.llm.client import LLMClient


class LLMItineraryCurator:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def preferred_supply_ids(
        self,
        theme: Theme,
        request: UserRequest,
        candidates: list[MerchantSupply],
    ) -> list[str]:
        if not self.llm_client or not candidates:
            return []
        allowed_ids = {candidate.id for candidate in candidates}
        payload = {
            "theme": {"id": theme.id, "name": theme.name, "slots": [slot.type.value for slot in theme.slots]},
            "request": {
                "budget_per_person": request.budget_per_person,
                "party_size": request.party_size,
                "mood_tags": request.mood_tags,
                "experience_tags": request.experience_tags,
                "route_limit_km": request.route_limit_km,
                "route_limit_minutes": request.route_limit_minutes,
            },
            "candidates": [_candidate_payload(candidate) for candidate in candidates[:30]],
            "output_schema": {"merchant_ids": ["amap_xxx", "amap_yyy", "amap_zzz"]},
            "rules": [
                "merchant_ids 只能从 candidates.id 中选择",
                "优先满足主题 slots 的餐饮、活动、休闲/打卡组合",
                "不要编造商户，不要确认预约或支付",
            ],
        }
        try:
            raw = self.llm_client.complete(
                [
                    {"role": "system", "content": "你是主题局商户组合器。只输出 JSON，不要输出 markdown，不要编造候选。"},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ]
            )
            data = json.loads(raw)
        except Exception:
            return []
        merchant_ids = data.get("merchant_ids") if isinstance(data, dict) else None
        if not isinstance(merchant_ids, list):
            return []
        valid = [str(item) for item in merchant_ids if str(item) in allowed_ids]
        return list(dict.fromkeys(valid))[:6]


def _candidate_payload(candidate: MerchantSupply) -> dict[str, object]:
    profile = candidate.merchant_profile or {}
    return {
        "id": candidate.id,
        "name": candidate.name,
        "type": candidate.type.value,
        "price": candidate.price,
        "distance_km": candidate.distance_km,
        "tags": candidate.tags[:6],
        "matched_keywords": candidate.matched_keywords,
        "rating": profile.get("rating"),
        "review_summary": profile.get("review_summary"),
        "intro": profile.get("intro"),
    }
