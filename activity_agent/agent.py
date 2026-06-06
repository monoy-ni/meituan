from __future__ import annotations

from dataclasses import replace
from typing import Any

from activity_agent.config import AgentSettings, LLMSettings, StorageSettings, ToolSettings
from activity_agent.domain.models import (
    AgentResponse,
    AfterActionReview,
    BookingConfirmation,
    BookingDraft,
    FeedbackStatus,
    Intent,
    InviteFeedback,
    PayMode,
    PlanningResult,
    PlanOption,
    RouteResult,
    Scene,
    Session,
    UserRequest,
)
from activity_agent.llm import LLMClient, LLMOrchestrator, MockLLMClient, OpenAICompatibleLLMClient
from activity_agent.modules.booking_orchestrator import BookingOrchestrator
from activity_agent.modules.context_collector import ContextCollector
from activity_agent.modules.dialogue_manager import DialogueManager, DialogueState
from activity_agent.modules.feedback_resolver import FeedbackResolver
from activity_agent.modules.intent_router import IntentRouter
from activity_agent.modules.itinerary_composer import ItineraryComposer
from activity_agent.modules.review_memory import ReviewMemory
from activity_agent.modules.share_card_generator import ShareCardGenerator
from activity_agent.modules.theme_planner import ThemePlanner
from activity_agent.storage import SQLiteRepository
from activity_agent.tools import MockMeituanToolClient


class ActivityPlanningAgent:
    """Python SDK facade for the local activity planning Agent MVP."""

    def __init__(
        self,
        settings: AgentSettings | None = None,
        llm_client: LLMClient | None = None,
        repository: SQLiteRepository | None = None,
        tool_client: MockMeituanToolClient | None = None,
    ) -> None:
        self.settings = settings or AgentSettings(
            llm=LLMSettings(),
            storage=StorageSettings(path=":memory:"),
            tools=ToolSettings(),
        )
        self.repository = repository or SQLiteRepository(self.settings.storage.path)
        self.tool_client = tool_client or MockMeituanToolClient()
        self.llm_client = llm_client or (
            OpenAICompatibleLLMClient(self.settings.llm) if self.settings.llm.api_key else MockLLMClient()
        )
        self.llm_orchestrator = LLMOrchestrator(self.llm_client)

        self.intent_router = IntentRouter()
        self.context_collector = ContextCollector()
        self.theme_planner = ThemePlanner()
        self.itinerary_composer = ItineraryComposer()
        self.share_card_generator = ShareCardGenerator()
        self.feedback_resolver = FeedbackResolver(self.theme_planner, self.itinerary_composer)
        self.booking_orchestrator = BookingOrchestrator(self.tool_client)
        self.review_memory = ReviewMemory()
        self.dialogue_manager = DialogueManager(self.llm_client)

    @classmethod
    def from_env(cls) -> "ActivityPlanningAgent":
        settings = AgentSettings.from_env()
        return cls(settings=settings)

    def start_session(self, user_id: str | None = None) -> Session:
        return self.repository.create_session(user_id)

    def close(self) -> None:
        self.repository.close()

    def chat(self, session_id: str, text: str) -> AgentResponse:
        self._ensure_session(session_id)
        history = self.repository.list_messages(session_id)
        understanding = self.llm_orchestrator.understand(text, history)
        self.repository.add_message(session_id, "user", text)

        latest = self.repository.get_latest_planning(session_id)
        partial_request = latest["request"] if latest else None
        result = self.plan(text, partial_request=partial_request, llm_data=understanding.data)
        share_cards = [self.render_share_card(option, result.request) for option in result.options]
        self.repository.save_planning_result(session_id, result, share_cards)

        message = self._planning_message(result)
        self.repository.add_message(session_id, "assistant", message)
        return AgentResponse(
            session_id=session_id,
            intent=result.route.intent,
            scene=result.request.scene,
            message=message,
            request=result.request,
            options=result.options,
            share_cards=share_cards,
            missing_questions=result.missing_questions,
            assumptions=result.assumptions,
            tool_events=[understanding.event],
            degraded=understanding.degraded,
        )

    def select_option(self, session_id: str, option_id: str) -> AgentResponse:
        latest = self._latest_planning_or_raise(session_id)
        option = self._find_option(latest["options"], option_id)
        request = latest["request"]
        self.repository.save_selected_option(session_id, option, request)
        card = self.render_share_card(option, request)
        message = f"已选择“{option.theme_name}”。下一步可以提交朋友反馈，或创建预约草稿。"
        self.repository.add_message(session_id, "assistant", message)
        return AgentResponse(
            session_id=session_id,
            intent=Intent.PLAN,
            scene=request.scene,
            message=message,
            request=request,
            options=[option],
            share_cards=[card],
        )

    def submit_feedback(self, session_id: str, feedback: list[InviteFeedback]) -> AgentResponse:
        latest = self._latest_planning_or_raise(session_id)
        selected = self.repository.get_selected_option(session_id)
        preferred_option, request = selected if selected else (latest["options"][0], latest["request"])
        self.repository.save_feedback(session_id, feedback)
        revised_request, revised_option, notes = self.resolve_feedback(request, feedback, preferred_option.theme_name)
        route = RouteResult(intent=Intent.FEEDBACK, scene=revised_request.scene, confidence=0.9, signals=["invite_feedback"])
        result = PlanningResult(
            route=route,
            request=revised_request,
            missing_questions=[],
            assumptions=notes,
            options=[revised_option],
        )
        share_cards = [self.render_share_card(revised_option, revised_request)]
        self.repository.save_planning_result(session_id, result, share_cards)
        self.repository.save_selected_option(session_id, revised_option, revised_request)
        message = "已根据反馈收敛方案：" + "；".join(notes)
        self.repository.add_message(session_id, "assistant", message)
        return AgentResponse(
            session_id=session_id,
            intent=Intent.FEEDBACK,
            scene=revised_request.scene,
            message=message,
            request=revised_request,
            options=[revised_option],
            share_cards=share_cards,
            assumptions=notes,
        )

    def plan(
        self,
        text: str,
        partial_request: UserRequest | None = None,
        scene_hint: Scene | None = None,
        llm_data: dict[str, Any] | None = None,
    ) -> PlanningResult:
        scene_from_llm = self._scene_from_llm(llm_data)
        route = self.intent_router.route(text, scene_hint=scene_hint or scene_from_llm or (partial_request.scene if partial_request else None))
        request, missing_questions, assumptions = self.context_collector.collect(route, text, partial_request)
        request = self._merge_llm_data(request, llm_data or {})
        request = self._apply_adjustments(text, request)
        themes = self.theme_planner.plan(request)
        options = self.itinerary_composer.compose(themes, request)
        return PlanningResult(
            route=route,
            request=request,
            missing_questions=missing_questions,
            assumptions=assumptions,
            options=options,
        )

    def render_share_card(self, option: PlanOption, request: UserRequest) -> str:
        return self.share_card_generator.render(option, request)

    def resolve_feedback(
        self,
        request: UserRequest,
        feedback: list[InviteFeedback],
        preferred_theme_name: str | None = None,
    ) -> tuple[UserRequest, PlanOption, list[str]]:
        return self.feedback_resolver.resolve(request, feedback, preferred_theme_name)

    def create_booking_draft(
        self,
        session_or_option: str | PlanOption,
        option_id_or_request: str | UserRequest | None = None,
        pay_mode: PayMode | None = None,
    ) -> BookingDraft:
        if isinstance(session_or_option, PlanOption):
            if not isinstance(option_id_or_request, UserRequest):
                raise ValueError("The legacy create_booking_draft(option, request) form requires a UserRequest.")
            return self.booking_orchestrator.create_draft(session_or_option, option_id_or_request, pay_mode)

        session_id = session_or_option
        latest = self._latest_planning_or_raise(session_id)
        request = latest["request"]
        option_id = option_id_or_request if isinstance(option_id_or_request, str) else None
        if option_id:
            option = self._find_option(latest["options"], option_id)
        else:
            selected = self.repository.get_selected_option(session_id)
            option = selected[0] if selected else latest["options"][0]

        draft = self.booking_orchestrator.create_draft(option, request, pay_mode)
        self.repository.save_booking_draft(session_id, draft)
        return draft

    def confirm_booking(self, session_id: str, draft_id: str, confirm: bool) -> BookingConfirmation:
        self._ensure_session(session_id)
        draft = self.repository.get_booking_draft(session_id, draft_id)
        if not draft:
            raise ValueError(f"Booking draft not found: {draft_id}")
        confirmation = self.booking_orchestrator.confirm_draft(draft, confirm)
        self.repository.save_booking_confirmation(session_id, confirmation)
        return confirmation

    def create_review(
        self,
        session_or_option: str | PlanOption,
        actual_cost_per_person: int,
        attendance: int,
        ratings: dict[str, float],
        complaints: list[str] | None = None,
    ) -> AfterActionReview:
        if isinstance(session_or_option, PlanOption):
            return self.review_memory.create_review(session_or_option, actual_cost_per_person, attendance, ratings, complaints)

        session_id = session_or_option
        selected = self.repository.get_selected_option(session_id)
        latest = self._latest_planning_or_raise(session_id)
        option = selected[0] if selected else latest["options"][0]
        review = self.review_memory.create_review(option, actual_cost_per_person, attendance, ratings, complaints)
        self.repository.save_review(session_id, review)
        return review

    def _ensure_session(self, session_id: str) -> None:
        if not self.repository.get_session(session_id):
            raise ValueError(f"Session not found: {session_id}")

    def _latest_planning_or_raise(self, session_id: str) -> dict[str, Any]:
        self._ensure_session(session_id)
        latest = self.repository.get_latest_planning(session_id)
        if not latest:
            raise ValueError(f"No planning result found for session: {session_id}")
        return latest

    def _find_option(self, options: list[PlanOption], option_id: str) -> PlanOption:
        try:
            return next(option for option in options if option.id == option_id)
        except StopIteration as exc:
            raise ValueError(f"Plan option not found: {option_id}") from exc

    def _planning_message(self, result: PlanningResult) -> str:
        label = "约会方案" if result.request.scene == Scene.COUPLE else "组局方案"
        names = " / ".join(option.theme_name for option in result.options)
        return f"我给你配了 {len(result.options)} 个{label}：{names}。"

    def _scene_from_llm(self, llm_data: dict[str, Any] | None) -> Scene | None:
        if not llm_data or not llm_data.get("scene"):
            return None
        try:
            return Scene(str(llm_data["scene"]))
        except ValueError:
            return None

    def _merge_llm_data(self, request: UserRequest, data: dict[str, Any]) -> UserRequest:
        if not data:
            return request

        hard_constraints = dict(request.hard_constraints)
        hard_constraints.update({key: bool(value) for key, value in dict(data.get("hard_constraints") or {}).items()})

        mood_tags = list(dict.fromkeys([*request.mood_tags, *list(data.get("mood_tags") or [])]))
        budget = self._safe_int(data.get("budget_per_person"), request.budget_per_person)
        party_size = self._safe_int(data.get("party_size"), request.party_size)

        return replace(
            request,
            time_window=str(data.get("time_window") or request.time_window),
            location_anchor=str(data.get("location_anchor") or request.location_anchor),
            budget_per_person=budget,
            party_size=party_size,
            mood_tags=mood_tags,
            relationship_stage=data.get("relationship_stage") or request.relationship_stage,
            relationship_goal=data.get("relationship_goal") or request.relationship_goal,
            hard_constraints=hard_constraints,
        )

    def _safe_int(self, value: object, fallback: int) -> int:
        try:
            return int(value) if value is not None else fallback
        except (TypeError, ValueError):
            return fallback

    def _apply_adjustments(self, text: str, request: UserRequest) -> UserRequest:
        normalized = str(text or "")
        constraints = dict(request.hard_constraints)
        budget = request.budget_per_person
        mood_tags = list(request.mood_tags)

        if "便宜点" in normalized or "预算太高" in normalized:
            constraints["cheaper"] = True
            budget = max(80, int(budget * 0.75))
            mood_tags.append("省钱")
        if "不喝酒" in normalized:
            constraints["no_alcohol"] = True
        if "室内" in normalized:
            constraints["indoor_only"] = True
        if "出片" in normalized or "拍照" in normalized:
            constraints["photo_friendly"] = True
            mood_tags.append("出片")
        if "酒店" in normalized or "过夜" in normalized:
            constraints["hotel_wanted"] = True
        if "礼物" in normalized or "花" in normalized or "蛋糕" in normalized:
            constraints["gift_wanted"] = True

        return replace(
            request,
            budget_per_person=budget,
            mood_tags=list(dict.fromkeys(mood_tags)),
            hard_constraints=constraints,
        )

    def chat_with_guidance(self, session_id: str, text: str) -> AgentResponse:
        """
        带对话引导的聊天接口 - 实现多轮对话流程
        
        1. 先识别用户群体（朋友/情侣）
        2. 多轮交流确定需求
        3. 提供多个方案
        4. 用户选择后自动预约
        """
        self._ensure_session(session_id)

        latest = self.repository.get_latest_planning(session_id)
        partial_request = latest["request"] if latest else None

        ctx, reply_msg, should_continue = self.dialogue_manager.process_input(
            session_id, text, partial_request
        )

        self.repository.add_message(session_id, "user", text)

        if not should_continue and ctx.state == DialogueState.READY_TO_PLAN:
            response = self.chat(session_id, text)
            self.dialogue_manager.mark_options_presented(session_id)
            return replace(
                response,
                message=reply_msg + "\n\n" + response.message,
            )

        self.repository.add_message(session_id, "assistant", reply_msg)

        return AgentResponse(
            session_id=session_id,
            intent=Intent.PLAN,
            scene=ctx.scene or Scene.FRIENDS,
            message=reply_msg,
            request=partial_request,
            options=[],
            share_cards=[],
            missing_questions=[],
            assumptions=[],
            tool_events=[],
            degraded=False,
        )

    def select_and_book(self, session_id: str, option_id: str) -> tuple[BookingDraft, BookingConfirmation]:
        """
        选择方案并自动完成预约
        
        Returns:
            (booking_draft, booking_confirmation)
        """
        select_response = self.select_option(session_id, option_id)

        draft = self.create_booking_draft(session_id, option_id)
        confirmation = self.confirm_booking(session_id, draft.id, confirm=True)

        self.dialogue_manager.mark_booking(session_id)
        self.dialogue_manager.mark_completed(session_id)

        return draft, confirmation

    def get_conversation_state(self, session_id: str) -> str:
        """获取当前对话状态"""
        ctx = self.dialogue_manager.get_or_create_context(session_id)
        return ctx.state.value
