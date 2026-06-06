from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional
from datetime import datetime, timedelta

from activity_agent.domain.models import Intent, Scene, UserRequest
from activity_agent.llm import LLMClient, MockLLMClient


class DialogueState(StrEnum):
    INIT = "init"
    IDENTIFYING_SCENE = "identifying_scene"
    COLLECTING_FRIENDS_CONTEXT = "collecting_friends_context"
    COLLECTING_COUPLE_CONTEXT = "collecting_couple_context"
    REFINING_DETAILS = "refining_details"
    READY_TO_PLAN = "ready_to_plan"
    PRESENTING_OPTIONS = "presenting_options"
    AWAITING_SELECTION = "awaiting_selection"
    AWAITING_FEEDBACK = "awaiting_feedback"
    READY_TO_BOOK = "ready_to_book"
    BOOKING = "booking"
    COMPLETED = "completed"


@dataclass
class UserUnderstanding:
    """LLM 理解的用户需求结构化结果 - 统一的理解层"""
    scene: Optional[Scene] = None
    relationship_stage: Optional[str] = None
    relationship_goal: Optional[str] = None
    mood_tags: list[str] = field(default_factory=list)
    budget: Optional[int] = None
    time_window: Optional[str] = None
    location: Optional[str] = None
    constraints: dict[str, bool] = field(default_factory=dict)
    confidence: float = 0.6  # 规则解析的默认置信度


@dataclass
class DialogueContext:
    state: DialogueState = DialogueState.INIT
    scene: Scene | None = None
    request: UserRequest | None = None
    collected_info: dict[str, Any] = field(default_factory=dict)
    messages: list[dict[str, str]] = field(default_factory=list)
    last_response: str = ""
    understanding: UserUnderstanding | None = None
    created_at: datetime = field(default_factory=datetime.now)
    turn_count: int = 0
    max_turns: int = 8  # 最大对话轮数
    session_timeout_minutes: int = 5  # 会话超时分钟数


class DialogueManager:
    """
    智能对话管理器 - 统一的 LLM + 规则混合理解层
    
    不再有 L1/L2 分层，所有理解逻辑集中在这里
    """

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        self.contexts: dict[str, DialogueContext] = {}
        self.llm_client = llm_client or MockLLMClient()
        self._use_llm = not isinstance(llm_client, MockLLMClient)

    def get_or_create_context(self, session_id: str) -> DialogueContext:
        if session_id not in self.contexts:
            self.contexts[session_id] = DialogueContext()
        return self.contexts[session_id]

    def _understand(
        self,
        text: str,
        history: list[dict[str, str]] | None = None,
        scene_hint: Scene | None = None,
    ) -> UserUnderstanding:
        """
        统一理解入口：尝试 LLM -> 失败则回退规则
        
        不再有 L1/L2 分层，所有理解在这里完成
        """
        understanding = UserUnderstanding()
        
        if self._use_llm:
            try:
                understanding = self._understand_with_llm(text, history)
                if understanding.confidence >= 0.3:
                    return self._apply_scene_context(understanding, text, scene_hint)
            except Exception:
                pass
        
        return self._apply_scene_context(self._understand_with_rules(text, scene_hint), text, scene_hint)

    def _understand_with_llm(self, text: str, history: list[dict[str, str]] | None = None) -> UserUnderstanding:
        """使用 LLM 深度理解（统一的 LLM 调用层）"""
        understanding = UserUnderstanding(confidence=0.5)
        
        system_prompt = """你是一个活动规划助手，负责理解用户的需求。请仔细分析用户的话，提取以下信息，以JSON格式返回：

{
  "scene": "friends" 或 "couple"，根据用户说的话判断是朋友聚会还是情侣约会，拿不准就null,
  "relationship_stage": "暧昧/追求中"|"刚在一起"|"稳定情侣"|"纪念日"|"想修复关系"，仅当scene是couple时推断,
  "relationship_goal": "降低邀约门槛"|"降低尴尬"|"自然升温"|"创造共同体验"|"制造仪式感"|"缓和关系"等，仅当scene是couple时,
  "mood_tags": ["回血", "放松", "热闹", "疯玩", "拍照", "省钱", "安静", "浪漫"],
  "budget": 整数，人均预算，没有提到就是null,
  "time": "今晚"|"明晚"|"周末"|"周末下午"|"周六"等,
  "constraints": {
    "no_alcohol": true/false,
    "indoor_only": true/false,
    "cheaper": true/false,
    "hotel_wanted": true/false,
    "gift_wanted": true/false
  },
  "confidence": 0-1之间的数字，表示对你的把握程度
}

注意：
- 如果用户提到"怕尴尬"、"约她"、"约他"、"第一次"，relationship_stage很可能是"暧昧/追求中"
- 如果用户提到"纪念日"、"惊喜"、"浪漫"，scene很可能是"couple"
- 如果用户提到"朋友"、"聚聚"、"哥们"、"姐妹"、"大家"，scene很可能是"friends"
- 只返回JSON，不要其他文字
"""

        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-3:])
        messages.append({"role": "user", "content": text})

        try:
            response = self.llm_client.complete(messages)
            import json
            result = json.loads(response)

            if result:
                if result.get("scene") in ["friends", "couple"]:
                    understanding.scene = Scene(result["scene"])
                understanding.relationship_stage = result.get("relationship_stage")
                understanding.relationship_goal = result.get("relationship_goal")
                understanding.mood_tags = result.get("mood_tags", [])
                understanding.budget = result.get("budget")
                understanding.time_window = result.get("time")
                understanding.constraints = result.get("constraints", {})
                understanding.confidence = result.get("confidence", 0.5)
        except Exception:
            pass

        return understanding

    def _understand_with_rules(self, text: str, scene_hint: Scene | None = None) -> UserUnderstanding:
        """降级方案：规则解析（当 LLM 不可用时）"""
        understanding = UserUnderstanding(confidence=0.6)

        text_lower = text.lower()

        friends_keywords = ["朋友", "朋友局", "聚聚", "局", "哥们", "姐妹", "同事", "大家", "几个人"]
        couple_keywords = [
            "情侣",
            "情侣约会",
            "约会",
            "对象",
            "女朋友",
            "男朋友",
            "老婆",
            "老公",
            "另一半",
            "ta",
            "两个人",
            "纪念日",
            "惊喜",
            "浪漫",
            "暧昧",
            "约她",
            "约他",
            "升温",
            "老夫老妻",
        ]

        has_friends = any(k in text for k in friends_keywords)
        has_couple = any(k in text_lower for k in couple_keywords)

        if scene_hint is not None:
            understanding.scene = scene_hint
        elif has_couple and not has_friends:
            understanding.scene = Scene.COUPLE
        elif has_friends:
            understanding.scene = Scene.FRIENDS

        mood_mapping = [
            (["累", "回血", "放松", "解压"], ["回血", "放松"]),
            (["疯", "热闹", "嗨"], ["发疯", "热闹"]),
            (["拍照", "出片", "好看"], ["出片"]),
            (["省钱", "便宜", "预算"], ["省钱"]),
            (["安静", "不吵"], ["安静"]),
            (["浪漫", "惊喜"], ["浪漫"]),
        ]

        for keywords, tags in mood_mapping:
            if any(k in text for k in keywords):
                understanding.mood_tags.extend(tags)

        import re
        budget_match = re.search(r'(?:人均|预算|每人)\D*(\d{2,4})', text)
        if budget_match:
            understanding.budget = int(budget_match.group(1))

        understanding.time_window = self._parse_time_window_with_local_time(text)

        understanding.constraints = {
            "no_alcohol": "不喝酒" in text or "不要酒" in text,
            "indoor_only": "室内" in text,
            "cheaper": "便宜" in text or "省钱" in text,
            "hotel_wanted": "酒店" in text or "过夜" in text,
            "gift_wanted": "礼物" in text or "花" in text or "蛋糕" in text,
        }

        return understanding

    def _apply_scene_context(
        self,
        understanding: UserUnderstanding,
        text: str,
        scene_hint: Scene | None = None,
    ) -> UserUnderstanding:
        if scene_hint is not None and understanding.scene is None:
            understanding.scene = scene_hint

        if understanding.scene != Scene.COUPLE:
            return understanding

        stage, goal = self._infer_couple_relationship(text)
        if stage and not understanding.relationship_stage:
            understanding.relationship_stage = stage
        if goal and not understanding.relationship_goal:
            understanding.relationship_goal = goal

        if not understanding.relationship_stage:
            understanding.relationship_stage = "稳定情侣"
        if not understanding.relationship_goal:
            understanding.relationship_goal = "创造共同体验"

        return understanding

    def _infer_couple_relationship(self, text: str) -> tuple[str | None, str | None]:
        if any(word in text for word in ["怕尴尬", "第一次", "约她", "约他", "暧昧", "追求"]):
            return "暧昧/追求中", "降低尴尬"
        if any(word in text for word in ["升温", "自然一点", "轻松自然"]):
            return "暧昧/追求中", "自然升温"
        if "纪念日" in text:
            return "纪念日", "制造仪式感"
        if "修复" in text or "吵架" in text or "道歉" in text:
            return "想修复关系", "缓和关系"
        if any(word in text for word in ["老夫老妻", "日常", "稳定", "对象", "女朋友", "男朋友", "老婆", "老公"]):
            return "稳定情侣", "创造共同体验"
        return None, None

    def _parse_time_window_with_local_time(self, text: str) -> Optional[str]:
        """
        时间窗口解析 - 使用本地真实时间
        
        根据当前时间和用户输入智能推断合适的时间窗口
        """
        now = datetime.now()
        current_hour = now.hour

        if "今晚" in text or "今天晚上" in text:
            if current_hour < 17:
                return f"today 18:30-23:30"
            elif current_hour < 20:
                return f"today {current_hour+1}:00-23:30"
            else:
                return f"today 20:00-23:00"
        elif "明晚" in text or "明天晚上" in text:
            return f"tomorrow 18:30-23:30"
        elif "周五" in text:
            return f"friday 18:30-23:30"
        elif "周末" in text:
            return f"weekend 15:00-23:30"
        elif "下午" in text:
            return f"selected_day 15:00-20:30"
        elif "晚上" in text:
            return f"selected_day 18:30-23:30"
        return None

    def _check_termination_conditions(self, ctx: DialogueContext) -> Optional[str]:
        """检查对话是否应该终止"""
        # 1. 检查会话超时
        if datetime.now() - ctx.created_at > timedelta(minutes=ctx.session_timeout_minutes):
            return f"会话已超时（{ctx.session_timeout_minutes}分钟）。如果需要继续规划，请开始新会话。"
        
        # 2. 检查最大轮次
        if ctx.turn_count >= ctx.max_turns:
            return f"已达到最大对话轮次（{ctx.max_turns}）。我们已经提供了方案，你可以直接选择或重新开始。"
        
        # 3. 检查是否已经完成预订
        if ctx.state == DialogueState.COMPLETED:
            return "预订已完成！如果你需要新的规划，可以开始新会话。"
        
        return None
    
    def _generate_response(self, ctx: DialogueContext, understanding: UserUnderstanding) -> tuple[str, bool]:
        """根据理解结果生成回复，并决定是否继续对话"""
        
        # 先检查终止条件
        termination_msg = self._check_termination_conditions(ctx)
        if termination_msg:
            return termination_msg, False
        
        info = ctx.collected_info
        ctx.turn_count += 1
        last_user_msg = ctx.messages[-1]["content"] if ctx.messages else ""
        
        if ctx.state == DialogueState.INIT:
            if understanding.scene:
                ctx.scene = understanding.scene
                if understanding.scene == Scene.FRIENDS:
                    ctx.state = DialogueState.COLLECTING_FRIENDS_CONTEXT
                    return self._friends_opening(understanding), True
                else:
                    ctx.state = DialogueState.COLLECTING_COUPLE_CONTEXT
                    return self._couple_opening(understanding), True
            else:
                ctx.state = DialogueState.IDENTIFYING_SCENE
                return "好的！是想和朋友聚聚，还是想安排约会呢？", True

        if ctx.state == DialogueState.IDENTIFYING_SCENE:
            if understanding.scene == Scene.FRIENDS:
                ctx.scene = Scene.FRIENDS
                ctx.state = DialogueState.COLLECTING_FRIENDS_CONTEXT
                return "好的，朋友局！我来帮你安排。" + self._friends_opening(understanding), True
            elif understanding.scene == Scene.COUPLE:
                ctx.scene = Scene.COUPLE
                ctx.state = DialogueState.COLLECTING_COUPLE_CONTEXT
                return "好的，约会安排！" + self._couple_opening(understanding), True
            else:
                return "我还在确认... 是朋友聚会还是约会呢？", True

        if ctx.state == DialogueState.COLLECTING_FRIENDS_CONTEXT:
            if understanding.mood_tags and "mood" not in info:
                info["mood"] = understanding.mood_tags
            if understanding.budget and "budget" not in info:
                info["budget"] = understanding.budget
            if understanding.time_window and "time" not in info:
                info["time"] = understanding.time_window

            if "mood" not in info:
                return "今晚想要什么样的局呢？是想放松回血、热闹一下、拍照出片，还是简单聚聚聊聊天？", True
            if "budget" not in info:
                return "人均预算大概多少呢？100-200、200-300，还是更高一些？", True
            if "time" not in info:
                return "安排在什么时候呢？今晚、明晚，还是周末？", True

            ctx.state = DialogueState.READY_TO_PLAN
            return "好的！我已经了解得差不多了，这就为你生成几个方案。", False

        if ctx.state == DialogueState.COLLECTING_COUPLE_CONTEXT:
            if understanding.relationship_stage and "relationship_stage" not in info:
                info["relationship_stage"] = understanding.relationship_stage
                info["relationship_goal"] = understanding.relationship_goal
            if understanding.budget and "budget" not in info:
                info["budget"] = understanding.budget
            if understanding.time_window and "time" not in info:
                info["time"] = understanding.time_window

            if "relationship_stage" not in info:
                return "这次约会想安排成什么样的感觉呢？是轻松自然一些，还是想制造些浪漫？", True
            if "budget" not in info:
                return "人均预算大概多少呢？我可以根据预算调整推荐。", True
            if "time" not in info:
                return "安排在什么时候比较好呢？周末下午，还是晚上？", True

            ctx.state = DialogueState.READY_TO_PLAN
            return "好的，我懂了！这就为你准备几个合适的方案。", False

        if ctx.state == DialogueState.REFINING_DETAILS:
            ctx.state = DialogueState.READY_TO_PLAN
            return "好的，我调整一下方案。", False

        if ctx.state == DialogueState.AWAITING_SELECTION:
            if self._is_adjustment_request(last_user_msg):
                ctx.state = DialogueState.REFINING_DETAILS
                return "明白了，我按你的反馈重新收一版方案。", False
            if self._is_booking_request(last_user_msg):
                ctx.state = DialogueState.READY_TO_BOOK
                return "好的，我先帮你整理预约草稿，确认前不会支付或下不可逆订单。", False
            info["selected"] = True
            ctx.state = DialogueState.AWAITING_FEEDBACK
            return "选好了！需要调整什么吗，还是直接帮你预约？", True

        if ctx.state == DialogueState.AWAITING_FEEDBACK:
            # 修复：使用 understanding 或最后一条消息
            if self._is_booking_request(last_user_msg):
                ctx.state = DialogueState.READY_TO_BOOK
                return "好的，这就帮你安排预约！", False
            else:
                ctx.state = DialogueState.REFINING_DETAILS
                return "明白了，我调整一下方案。", False

        if ctx.state in [DialogueState.READY_TO_BOOK, DialogueState.BOOKING]:
            return "正在处理预订...", False

        return "我理解了，让我继续为你规划。", False

    def _is_adjustment_request(self, text: str) -> bool:
        return any(word in text for word in ["更近", "便宜", "少走路", "改室内", "室内", "加拍照", "拍照", "换", "不要", "太贵", "太累"])

    def _is_booking_request(self, text: str) -> bool:
        return any(word in text for word in ["预约", "预定", "订", "下单", "确定", "就这个", "帮我订", "帮我定"])

    def _friends_opening(self, understanding: UserUnderstanding) -> str:
        base = "帮你安排朋友局没问题！"
        if "回血" in understanding.mood_tags or "放松" in understanding.mood_tags:
            return base + " 刚下班辛苦了，给你安排点放松的？"
        return base + " 跟我说说大概想怎么玩？"

    def _couple_opening(self, understanding: UserUnderstanding) -> str:
        base = "约会安排包在我身上！"
        if understanding.relationship_stage == "纪念日":
            return base + " 纪念日要好好安排一下，给你准备点有仪式感的！"
        if understanding.relationship_stage == "暧昧/追求中":
            return base + " 懂，给你安排点轻松不尴尬的！"
        return base

    def process_input(
        self,
        session_id: str,
        text: str,
        current_request: UserRequest | None = None,
        scene_hint: Scene | None = None,
    ) -> tuple[DialogueContext, str, bool]:
        """
        处理用户输入，返回更新后的上下文、回复消息、是否需要继续对话
        
        统一的处理入口
        """
        ctx = self.get_or_create_context(session_id)
        ctx.messages.append({"role": "user", "content": text})

        effective_scene = scene_hint or ctx.scene or (current_request.scene if current_request else None)
        understanding = self._understand(text, ctx.messages, effective_scene)
        ctx.understanding = understanding

        response, should_continue = self._generate_response(ctx, understanding)

        ctx.last_response = response
        return ctx, response, should_continue

    def conversation_payload(self, session_id: str, has_options: bool = False) -> dict[str, object]:
        ctx = self.get_or_create_context(session_id)
        return {
            "state": ctx.state.value,
            "scene": ctx.scene.value if ctx.scene else None,
            "turn_count": ctx.turn_count,
            "should_show_options": has_options or ctx.state in {DialogueState.AWAITING_SELECTION, DialogueState.AWAITING_FEEDBACK, DialogueState.READY_TO_BOOK},
            "next_step": self._next_step(ctx),
        }

    def _next_step(self, ctx: DialogueContext) -> str:
        info = ctx.collected_info
        if ctx.state == DialogueState.INIT:
            return "choose_scene"
        if ctx.state == DialogueState.IDENTIFYING_SCENE:
            return "choose_scene"
        if ctx.state == DialogueState.COLLECTING_FRIENDS_CONTEXT:
            if "mood" not in info:
                return "ask_mood"
            if "budget" not in info:
                return "ask_budget"
            if "time" not in info:
                return "ask_time"
            return "generate_options"
        if ctx.state == DialogueState.COLLECTING_COUPLE_CONTEXT:
            if "relationship_stage" not in info:
                return "ask_couple_feeling"
            if "budget" not in info:
                return "ask_budget"
            if "time" not in info:
                return "ask_time"
            return "generate_options"
        if ctx.state == DialogueState.REFINING_DETAILS:
            return "regenerate_options"
        if ctx.state == DialogueState.AWAITING_SELECTION:
            return "select_option"
        if ctx.state == DialogueState.AWAITING_FEEDBACK:
            return "adjust_or_book"
        if ctx.state == DialogueState.READY_TO_BOOK:
            return "create_booking_draft"
        if ctx.state == DialogueState.BOOKING:
            return "booking"
        if ctx.state == DialogueState.COMPLETED:
            return "completed"
        return "continue"

    def mark_options_presented(self, session_id: str) -> None:
        ctx = self.get_or_create_context(session_id)
        ctx.state = DialogueState.AWAITING_SELECTION

    def mark_booking(self, session_id: str) -> None:
        ctx = self.get_or_create_context(session_id)
        ctx.state = DialogueState.BOOKING

    def mark_completed(self, session_id: str) -> None:
        ctx = self.get_or_create_context(session_id)
        ctx.state = DialogueState.COMPLETED
