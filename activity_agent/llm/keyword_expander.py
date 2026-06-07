from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from activity_agent.domain.models import UserRequest
from activity_agent.llm.client import LLMClient


RELATED_KEYWORDS: dict[str, list[str]] = {
    "KTV": ["KTV", "ktv", "量贩KTV", "K歌", "唱歌"],
    "烧烤": ["烧烤", "烤肉", "夜宵"],
    "酒吧": ["酒吧", "精酿", "小酒馆", "清吧"],
    "拳击": ["拳击", "运动", "解压"],
    "小吃": ["小吃", "夜宵", "美食"],
    "桌游": ["桌游", "棋牌", "游戏"],
    "密室": ["密室", "剧本杀", "沉浸"],
    "手作": ["手作", "陶艺", "银饰", "香薰", "DIY"],
    "轻手作": ["轻手作", "手作", "陶艺", "银饰", "香薰", "DIY"],
    "陶艺": ["陶艺", "手作", "DIY"],
    "茶馆": ["茶馆", "茶室", "茶点"],
    "咖啡": ["咖啡", "咖啡馆"],
    "甜品": ["甜品", "蛋糕"],
    "西餐": ["西餐", "西餐厅", "牛排", "法餐", "意面", "餐厅"],
    "安静餐厅": ["安静餐厅", "餐厅", "私房菜", "西餐"],
    "花店": ["花店", "鲜花", "花束"],
    "蛋糕": ["蛋糕", "甜品", "烘焙"],
    "酒店": ["酒店", "民宿", "泡汤", "度假酒店"],
    "展览": ["展览", "美术馆", "博物馆", "展馆"],
    "博物馆": ["博物馆", "展览", "展馆"],
    "夜景": ["夜景", "观景", "散步"],
    "散步": ["散步", "夜景", "公园", "湖滨"],
    "商场": ["商场", "购物中心", "市集"],
    "杭帮菜": ["杭帮菜", "餐厅", "本帮菜"],
    "农家菜": ["农家菜", "土菜", "餐厅"],
    "茶山": ["茶山", "龙井", "茶园"],
    "西湖景点": ["西湖景点", "西湖", "湖滨", "景点"],
}


@dataclass(frozen=True)
class ExpandedKeyword:
    keyword: str
    intent_type: str
    reason: str
    source: str = "llm"

    def as_dict(self) -> dict[str, str]:
        return {
            "keyword": self.keyword,
            "intent_type": self.intent_type,
            "reason": self.reason,
            "source": self.source,
        }


class LLMKeywordExpander:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client

    def expand(
        self,
        theme_name: str,
        seed_keywords: list[str],
        request: UserRequest,
    ) -> list[ExpandedKeyword]:
        seeds = _unique(seed_keywords)
        if not self.llm_client or not seeds:
            return _fallback_keywords(seeds)

        prompt = _prompt(theme_name, seeds, request)
        try:
            raw = self.llm_client.complete(
                [
                    {
                        "role": "system",
                        "content": "你是本地主题局 POI 搜索关键词扩展器。只输出 JSON，不要输出 markdown。关键词必须围绕给定种子，不要编造商户。",
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            data = json.loads(raw)
        except Exception:
            return _fallback_keywords(seeds)

        keywords = data.get("keywords") if isinstance(data, dict) else None
        if not isinstance(keywords, list):
            return _fallback_keywords(seeds)

        expanded: list[ExpandedKeyword] = []
        for item in keywords:
            if not isinstance(item, dict):
                continue
            keyword = str(item.get("keyword") or "").strip()
            if not keyword or not _is_related(keyword, seeds):
                continue
            expanded.append(
                ExpandedKeyword(
                    keyword=keyword,
                    intent_type=str(item.get("intent_type") or "poi"),
                    reason=str(item.get("reason") or "来自主题种子扩展"),
                )
            )

        if len(expanded) < 3:
            return _fallback_keywords(seeds)
        return _dedupe_expanded(expanded)[:8]


def _prompt(theme_name: str, seeds: list[str], request: UserRequest) -> str:
    return json.dumps(
        {
            "theme_name": theme_name,
            "seed_keywords": seeds,
            "constraints": {
                "budget_per_person": request.budget_per_person,
                "party_size": request.party_size,
                "time_window": request.time_window,
                "search_radius_km": request.search_radius_km,
                "route_limit_km": request.route_limit_km,
                "route_limit_minutes": request.route_limit_minutes,
                "mood_tags": request.mood_tags,
                "experience_tags": request.experience_tags,
            },
            "output_schema": {
                "keywords": [
                    {
                        "keyword": "量贩KTV",
                        "intent_type": "activity|dining|nightlife|relax|checkin",
                        "reason": "为什么这个关键词贴合主题",
                    }
                ]
            },
            "rules": [
                "输出 3 到 8 个关键词",
                "关键词必须围绕 seed_keywords 的语义",
                "不要输出具体商户名",
                "不要输出与主题无关的泛词",
            ],
        },
        ensure_ascii=False,
    )


def _fallback_keywords(seeds: list[str]) -> list[ExpandedKeyword]:
    return [
        ExpandedKeyword(keyword=keyword, intent_type="poi", reason="来自主题关键词种子", source="seed")
        for keyword in _unique(seeds)[:8]
    ]


def _is_related(keyword: str, seeds: list[str]) -> bool:
    normalized = keyword.lower()
    for seed in seeds:
        seed_normalized = seed.lower()
        if seed_normalized in normalized or normalized in seed_normalized:
            return True
        for related in RELATED_KEYWORDS.get(seed, []):
            related_normalized = related.lower()
            if related_normalized in normalized or normalized in related_normalized:
                return True
    return False


def _dedupe_expanded(values: list[ExpandedKeyword]) -> list[ExpandedKeyword]:
    seen: set[str] = set()
    deduped: list[ExpandedKeyword] = []
    for value in values:
        key = value.keyword.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(value)
    return deduped


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
