from __future__ import annotations

import json
import time
import traceback
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from dataclasses import replace

from activity_agent import ActivityPlanningAgent
from activity_agent.config import ToolSettings
from activity_agent.domain import ConfirmationStatus, PayMode, Scene
from activity_agent.domain.models import (
    BookingReadiness,
    MerchantSupply,
    PlanOption,
    Theme,
    ThemeSlot,
    TimelineItem,
    TimelineType,
    UserRequest,
)
from activity_agent.llm.itinerary_curator import LLMItineraryCurator
from activity_agent.modules.itinerary_composer import ItineraryComposer
from activity_agent.modules.supply_matcher import SupplyMatcher
from activity_agent.providers import AmapMapDataProvider, AmapWebServiceClient, HybridLiveDataProvider
from activity_agent.storage.sqlite_repository import SQLiteRepository
from activity_agent.tools.mock_meituan import MockMeituanToolClient

from tests.acceptance_matrix.acceptance_validation_cases import AcceptanceCase


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"
REQUIRED_CARD_KEYS = {
    "designer",
    "title",
    "theme_line",
    "vibe_tags",
    "play_style",
    "flow",
    "signature_moments",
    "host_tips",
    "booking_note",
}


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    expected: Any
    actual: Any
    details: str = ""
    debug_hint: str = ""
    related_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceRecord:
    name: str
    value: Any
    details: str = ""


@dataclass(frozen=True)
class DialogueTurnRecord:
    turn_index: int
    user_input: str
    assistant_output: str
    state: str | None
    next_step: str | None
    options: list[str] = field(default_factory=list)
    request_snapshot: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0


@dataclass(frozen=True)
class ToolCallRecord:
    tool: str
    input_summary: dict[str, Any]
    output_summary: dict[str, Any]


@dataclass(frozen=True)
class ScenarioRun:
    validations: list[ValidationResult]
    evidence: list[EvidenceRecord] = field(default_factory=list)
    transcript: list[DialogueTurnRecord] = field(default_factory=list)
    tool_calls: list[ToolCallRecord] = field(default_factory=list)


@dataclass(frozen=True)
class AcceptanceCaseResult:
    case_id: str
    title: str
    category: str
    requirement: str
    description: str
    related_files: list[str]
    passed: bool
    validations: list[ValidationResult]
    evidence: list[EvidenceRecord]
    transcript: list[DialogueTurnRecord]
    tool_calls: list[ToolCallRecord]
    duration_ms: int
    exception_type: str | None = None
    exception_message: str | None = None
    traceback_text: str | None = None


@dataclass(frozen=True)
class AcceptanceMetrics:
    total_cases: int
    passed_cases: int
    failed_cases: int
    case_pass_rate: float
    total_validations: int
    failed_validations: int
    validation_pass_rate: float
    exception_cases: int


@dataclass(frozen=True)
class AcceptanceSuiteResult:
    generated_at: str
    metrics: AcceptanceMetrics
    case_results: list[AcceptanceCaseResult]
    markdown_report_path: str | None = None
    json_report_path: str | None = None


def _validation(
    name: str,
    expected: Any,
    actual: Any,
    passed: bool,
    details: str = "",
    debug_hint: str = "",
    related_files: list[str] | None = None,
) -> ValidationResult:
    return ValidationResult(
        name=name,
        expected=expected,
        actual=actual,
        passed=passed,
        details=details,
        debug_hint=debug_hint,
        related_files=related_files or [],
    )


def _evidence(name: str, value: Any, details: str = "") -> EvidenceRecord:
    return EvidenceRecord(name=name, value=value, details=details)


class AcceptanceValidationHarness:
    def __init__(self) -> None:
        self.runners: dict[str, Callable[[], ScenarioRun]] = {
            "AC-01": self._run_theme_confirmation,
            "AC-02": self._run_location_and_ip,
            "AC-03": self._run_distance_requirements,
            "AC-04": self._run_amap_poi_range,
            "AC-05": self._run_meituan_profiles_llm_selection,
            "AC-06": self._run_amap_route_planning,
            "AC-07": self._run_skill_cards,
            "AC-08": self._run_mock_booking_order,
        }

    def run_case(self, case: AcceptanceCase) -> AcceptanceCaseResult:
        started = time.perf_counter()
        try:
            run = self.runners[case.case_id]()
            exception_type = None
            exception_message = None
            traceback_text = None
        except Exception as exc:  # noqa: BLE001 - diagnostic report needs raw failures.
            run = ScenarioRun(
                validations=[
                    _validation(
                        "case_execution",
                        "no exception",
                        type(exc).__name__,
                        False,
                        debug_hint="先看 traceback 和本用例关联文件。",
                        related_files=case.related_files,
                    )
                ]
            )
            exception_type = type(exc).__name__
            exception_message = str(exc)
            traceback_text = traceback.format_exc()

        passed = exception_type is None and all(item.passed for item in run.validations)
        return AcceptanceCaseResult(
            case_id=case.case_id,
            title=case.title,
            category=case.category,
            requirement=case.requirement,
            description=case.description,
            related_files=case.related_files,
            passed=passed,
            validations=run.validations,
            evidence=run.evidence,
            transcript=run.transcript,
            tool_calls=run.tool_calls,
            duration_ms=round((time.perf_counter() - started) * 1000),
            exception_type=exception_type,
            exception_message=exception_message,
            traceback_text=traceback_text,
        )

    def run_cases(self, cases: list[AcceptanceCase], output_dir: Path | None = None) -> AcceptanceSuiteResult:
        results = [self.run_case(case) for case in cases]
        suite = AcceptanceSuiteResult(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            metrics=self._metrics(results),
            case_results=results,
        )
        if output_dir is None:
            return suite
        return self.write_reports(suite, output_dir)

    def write_reports(self, suite: AcceptanceSuiteResult, output_dir: Path = DEFAULT_REPORT_DIR) -> AcceptanceSuiteResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / "acceptance_matrix_report.md"
        json_path = output_dir / "acceptance_matrix_report.json"

        markdown_path.write_text(self._markdown_report(suite), encoding="utf-8")
        json_path.write_text(
            json.dumps(asdict(suite), ensure_ascii=False, indent=2, default=_json_default),
            encoding="utf-8",
        )

        return AcceptanceSuiteResult(
            generated_at=suite.generated_at,
            metrics=suite.metrics,
            case_results=suite.case_results,
            markdown_report_path=str(markdown_path),
            json_report_path=str(json_path),
        )

    def _metrics(self, results: list[AcceptanceCaseResult]) -> AcceptanceMetrics:
        total_cases = len(results)
        passed_cases = sum(1 for result in results if result.passed)
        total_validations = sum(len(result.validations) for result in results)
        failed_validations = sum(
            1
            for result in results
            for validation in result.validations
            if not validation.passed
        )
        exception_cases = sum(1 for result in results if result.exception_type)
        return AcceptanceMetrics(
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=total_cases - passed_cases,
            case_pass_rate=round((passed_cases / total_cases) if total_cases else 0.0, 4),
            total_validations=total_validations,
            failed_validations=failed_validations,
            validation_pass_rate=round(
                ((total_validations - failed_validations) / total_validations)
                if total_validations
                else 0.0,
                4,
            ),
            exception_cases=exception_cases,
        )

    def _run_theme_confirmation(self) -> ScenarioRun:
        agent = ActivityPlanningAgent()
        transcript: list[DialogueTurnRecord] = []
        try:
            session = agent.start_session()

            def turn(message: str, scene_hint: Scene | None = None):
                started = time.perf_counter()
                response = agent.chat_with_guidance(session.id, message, scene_hint=scene_hint)
                payload = agent.get_conversation_payload(session.id, has_options=bool(response.options))
                transcript.append(
                    DialogueTurnRecord(
                        turn_index=len(transcript) + 1,
                        user_input=message,
                        assistant_output=response.message,
                        state=str(payload.get("state")),
                        next_step=str(payload.get("next_step")),
                        options=[option.theme_name for option in response.options],
                        request_snapshot=_request_snapshot(response.request),
                        duration_ms=round((time.perf_counter() - started) * 1000),
                    )
                )
                return response, payload

            first, first_payload = turn("今晚想出去玩")
            turn("和朋友")
            turn("想放松回血")
            turn("人均200")
            prompt, _ = turn("今晚")
            ready, final_payload = turn("默认")

            validations = [
                _validation(
                    "ambiguous_opening_asks_scene",
                    "choose_scene",
                    first_payload.get("next_step"),
                    first_payload.get("next_step") == "choose_scene" and not first.options,
                    debug_hint="检查 DialogueManager INIT/IDENTIFYING_SCENE 分支。",
                    related_files=["activity_agent/modules/dialogue_manager.py"],
                ),
                _validation(
                    "distance_prompt_before_plan",
                    "提示默认集合点和距离",
                    prompt.message,
                    "集合点默认奥映世纪轩" in prompt.message and not prompt.options,
                    debug_hint="检查 DialogueManager._has_location_distance 和默认距离提示。",
                    related_files=["activity_agent/modules/dialogue_manager.py"],
                ),
                _validation(
                    "final_state",
                    "awaiting_selection",
                    final_payload.get("state"),
                    final_payload.get("state") == "awaiting_selection",
                    related_files=["activity_agent/modules/dialogue_manager.py"],
                ),
                _validation("options_count", ">=3", len(ready.options), len(ready.options) >= 3),
                _validation("budget", 200, ready.request.budget_per_person, ready.request.budget_per_person == 200),
                _validation("default_origin", "奥映世纪轩", ready.request.origin_name, ready.request.origin_name == "奥映世纪轩"),
                _validation("default_search_radius", 5.0, ready.request.search_radius_km, ready.request.search_radius_km == 5.0),
                _validation("route_plan_attached", "每个方案都有 route_plan", [bool(option.route_plan) for option in ready.options], all(option.route_plan for option in ready.options)),
            ]
            return ScenarioRun(validations=validations, transcript=transcript)
        finally:
            agent.close()

    def _run_location_and_ip(self) -> ScenarioRun:
        http = FakeHTTPClient()
        client = AmapWebServiceClient("fake-amap-key", http_client=http)
        payload = client.ip_location("101.68.1.1")
        result = ActivityPlanningAgent().plan("朋友局，想放松回血，人均180，今晚")
        request = result.request
        call = http.calls[0]
        validations = [
            _validation("ip_endpoint", "/ip", call["url"], str(call["url"]).endswith("/ip"), related_files=["activity_agent/providers/live_sources.py"]),
            _validation("ip_param", "101.68.1.1", call["params"].get("ip"), call["params"].get("ip") == "101.68.1.1"),
            _validation("ip_key_param", "fake-amap-key", call["params"].get("key"), call["params"].get("key") == "fake-amap-key"),
            _validation("default_origin_name", "奥映世纪轩", request.origin_name, request.origin_name == "奥映世纪轩", related_files=["activity_agent/domain/models.py", "activity_agent/modules/context_collector.py"]),
            _validation("default_origin_address", "民祥路与平澜路交汇处(地铁6号线丰北站C出口)", request.origin_address, request.origin_address == "民祥路与平澜路交汇处(地铁6号线丰北站C出口)"),
            _validation("default_amap_url", "https://surl.amap.com/4sRsg3c1oa7b", request.origin_amap_url, request.origin_amap_url == "https://surl.amap.com/4sRsg3c1oa7b"),
            _validation("default_coordinates", "120.2425,30.2426", f"{request.origin_longitude},{request.origin_latitude}", request.origin_longitude == 120.2425 and request.origin_latitude == 30.2426),
        ]
        return ScenarioRun(
            validations=validations,
            evidence=[
                _evidence("amap_ip_payload", payload),
                _evidence("default_request", _request_snapshot(request)),
            ],
            tool_calls=[ToolCallRecord("amap.ip_location", call["params"], payload)],
        )

    def _run_distance_requirements(self) -> ScenarioRun:
        agent = ActivityPlanningAgent()
        transcript: list[DialogueTurnRecord] = []
        try:
            session = agent.start_session()

            def turn(message: str, scene_hint: Scene | None = None):
                started = time.perf_counter()
                response = agent.chat_with_guidance(session.id, message, scene_hint=scene_hint)
                payload = agent.get_conversation_payload(session.id, has_options=bool(response.options))
                transcript.append(
                    DialogueTurnRecord(
                        turn_index=len(transcript) + 1,
                        user_input=message,
                        assistant_output=response.message,
                        state=str(payload.get("state")),
                        next_step=str(payload.get("next_step")),
                        options=[option.theme_name for option in response.options],
                        request_snapshot=_request_snapshot(response.request),
                        duration_ms=round((time.perf_counter() - started) * 1000),
                    )
                )
                return response

            turn("朋友局", Scene.FRIENDS)
            turn("想回血，轻松聊聊天")
            turn("人均180")
            prompt = turn("今晚")
            ready = turn("从西湖文化广场出发，周边3公里，路线控制在4公里，40分钟内")
            option = ready.options[0]
            validations = [
                _validation("distance_prompt", "提示默认 5km 与 6km/45min", prompt.message, "搜索范围默认周边 5km" in prompt.message and "整体路线目标 6km 或 45min 内" in prompt.message),
                _validation("origin_name", "西湖文化广场", ready.request.origin_name, ready.request.origin_name == "西湖文化广场"),
                _validation("search_radius_km", 3.0, ready.request.search_radius_km, ready.request.search_radius_km == 3.0),
                _validation("route_limit_km", 4.0, ready.request.route_limit_km, ready.request.route_limit_km == 4.0),
                _validation("route_limit_minutes", 40, ready.request.route_limit_minutes, ready.request.route_limit_minutes == 40),
                _validation("route_plan_limits", {"km": 4.0, "minutes": 40}, {"km": option.route_plan.get("route_limit_km"), "minutes": option.route_plan.get("route_limit_minutes")}, option.route_plan.get("route_limit_km") == 4.0 and option.route_plan.get("route_limit_minutes") == 40),
            ]
            return ScenarioRun(validations=validations, transcript=transcript, evidence=[_evidence("final_request", _request_snapshot(ready.request))])
        finally:
            agent.close()

    def _run_amap_poi_range(self) -> ScenarioRun:
        repository = SQLiteRepository(":memory:")
        try:
            amap_client = FakeAmapAroundClient()
            provider = HybridLiveDataProvider(
                repository,
                ToolSettings(data_mode="hybrid", amap_city="330100"),
                amap_client=amap_client,
            )
            result = provider.sync_theme_pois("hangzhou", ["烧烤", "桌游"], 120.2425, 30.2426, 3.0)
            supplies = [supply for supply in provider.list_supplies("hangzhou") if supply.source == "amap_poi"]
            names = {supply.name for supply in supplies}
            validations = [
                _validation("sync_status", "live_synced", result["status"], result["status"] == "live_synced"),
                _validation("around_call_count", 2, len(amap_client.around_calls), len(amap_client.around_calls) == 2),
                _validation("around_location", "120.2425,30.2426", [call["location"] for call in amap_client.around_calls], all(call["location"] == "120.2425,30.2426" for call in amap_client.around_calls)),
                _validation("radius_m", 3000, [call["radius_m"] for call in amap_client.around_calls], all(call["radius_m"] == 3000 for call in amap_client.around_calls)),
                _validation("food_and_fun_keywords", {"烧烤", "桌游"}, {call["keywords"] for call in amap_client.around_calls}, {call["keywords"] for call in amap_client.around_calls} == {"烧烤", "桌游"}),
                _validation("poi_supplies", {"范围测试烧烤店", "范围测试桌游馆"}, names, {"范围测试烧烤店", "范围测试桌游馆"} <= names),
            ]
            tool_calls = [
                ToolCallRecord("amap.search_pois_around", call, {"status": "1"})
                for call in amap_client.around_calls
            ]
            return ScenarioRun(validations=validations, evidence=[_evidence("sync_result", result), _evidence("live_supply_names", sorted(names))], tool_calls=tool_calls)
        finally:
            repository.close()

    def _run_meituan_profiles_llm_selection(self) -> ScenarioRun:
        catalog = [
            _supply("food_bbq", "热闹烧烤店", TimelineType.DINING, ["烧烤", "回血"], 98),
            _supply("activity_ktv", "下班K歌房", TimelineType.ACTIVITY, ["KTV", "解压"], 88),
            _supply("relax_tea", "收尾茶馆", TimelineType.RELAX, ["茶馆", "聊天"], 68),
        ]
        meituan = MockMeituanToolClient(catalog)
        profile_calls = []
        profiled_catalog = []
        for supply in catalog:
            profile_result = meituan.merchant_profile(supply.id, supply.name)
            profile_calls.append(ToolCallRecord("meituan.merchant_profile", {"merchant_id": supply.id, "merchant_name": supply.name}, dict(profile_result.data)))
            profiled_catalog.append(replace(supply, merchant_profile=dict(profile_result.data)))

        theme = Theme(
            id="acceptance_recovery",
            name="下班回血主题局",
            emotional_hook="先释放，再吃热的，最后收住聊天。",
            slots=[
                ThemeSlot(TimelineType.ACTIVITY, ["KTV", "解压"], "先释放压力"),
                ThemeSlot(TimelineType.DINING, ["烧烤", "回血"], "吃一口热的"),
                ThemeSlot(TimelineType.RELAX, ["茶馆", "聊天"], "低压力收尾"),
            ],
            add_ons=[],
        )
        request = UserRequest(
            scene=Scene.FRIENDS,
            time_window="today 18:30-23:30",
            location_anchor="奥映世纪轩",
            budget_per_person=260,
            party_size=4,
            mood_tags=["回血", "解压"],
        )
        llm = FakeCuratorLLM()
        preferred_ids = LLMItineraryCurator(llm).preferred_supply_ids(theme, request, profiled_catalog)
        option = ItineraryComposer(SupplyMatcher(profiled_catalog)).compose(
            [theme],
            replace(request, hard_constraints={"preferred_supply_ids": preferred_ids}),
        )[0]
        prompt = llm.messages[0][1]["content"]
        selected_ids = [item.merchant_id for item in option.timeline_items]
        validations = [
            _validation("profile_prompt_contains_reviews", "mock 用户评价摘要", "mock 用户评价摘要" in prompt, "mock 用户评价摘要" in prompt),
            _validation("profile_prompt_contains_intro", "mock 商户介绍", "mock 商户介绍" in prompt, "mock 商户介绍" in prompt),
            _validation("llm_filters_hallucinated_ids", "made_up_merchant 不进入结果", preferred_ids, "made_up_merchant" not in preferred_ids),
            _validation("preferred_ids", ["food_bbq", "activity_ktv", "relax_tea"], preferred_ids, preferred_ids == ["food_bbq", "activity_ktv", "relax_tea"]),
            _validation("theme_combination_types", {"activity", "dining", "relax"}, {item.type.value for item in option.timeline_items}, {item.type.value for item in option.timeline_items} == {"activity", "dining", "relax"}),
            _validation("selected_ids_match_llm", set(preferred_ids), set(selected_ids), set(selected_ids) == set(preferred_ids)),
        ]
        return ScenarioRun(
            validations=validations,
            evidence=[_evidence("preferred_ids", preferred_ids), _evidence("selected_ids", selected_ids), _evidence("llm_prompt_excerpt", prompt[:1200])],
            tool_calls=profile_calls + [ToolCallRecord("llm.preferred_supply_ids", {"candidate_count": len(profiled_catalog)}, {"merchant_ids": preferred_ids})],
        )

    def _run_amap_route_planning(self) -> ScenarioRun:
        agent = ActivityPlanningAgent()
        try:
            fake_client = FakeAmapRouteClient()
            agent.map_provider = AmapMapDataProvider(fake_client, agent.repository)
            request = UserRequest(
                scene=Scene.FRIENDS,
                time_window="today 18:30-23:30",
                location_anchor="奥映世纪轩",
                budget_per_person=220,
                party_size=4,
                route_limit_km=4.0,
                route_limit_minutes=40,
            )
            option = PlanOption(
                id="route-option",
                theme_name="路径规划验收局",
                emotional_hook="用真实路径把每一站串起来。",
                timeline_items=[
                    _item("第一站餐厅", 120.2500, 30.2450, 1),
                    _item("第二站游乐", 120.2600, 30.2500, 2),
                ],
                estimated_cost_per_person=176,
                total_distance=0,
                booking_readiness=BookingReadiness.NEEDS_CONFIRMATION,
                replaceable_slots=[],
                risk_notes=[],
                actions=[],
                add_ons=[],
            )
            route_plan = agent._route_plan_for_option(option, request)
            validations = [
                _validation("route_call_count", 2, len(fake_client.route_calls), len(fake_client.route_calls) == 2),
                _validation("route_provider", "amap_route", route_plan["provider"], route_plan["provider"] == "amap_route"),
                _validation("route_status", "live", route_plan["status"], route_plan["status"] == "live"),
                _validation("legs_count", 2, len(route_plan["legs"]), len(route_plan["legs"]) == 2),
                _validation("total_distance_km", 2.4, route_plan["total_distance_km"], route_plan["total_distance_km"] == 2.4),
                _validation("total_duration_minutes", 30, route_plan["total_duration_minutes"], route_plan["total_duration_minutes"] == 30),
                _validation("within_limits", True, route_plan["within_limits"], route_plan["within_limits"] is True),
            ]
            return ScenarioRun(
                validations=validations,
                evidence=[_evidence("route_plan", route_plan)],
                tool_calls=[ToolCallRecord("amap.walking_route", {"origin": origin, "destination": destination}, {"distance": "1200", "duration": "900"}) for origin, destination in fake_client.route_calls],
            )
        finally:
            agent.close()

    def _run_skill_cards(self) -> ScenarioRun:
        friends = ActivityPlanningAgent().plan("朋友局，今晚下班回血，4个人，人均220")
        couple = ActivityPlanningAgent().plan("想约TA出来，怕尴尬，周末下午，人均300")
        friend_card = friends.options[0].experience_card
        couple_card = couple.options[0].experience_card
        validations = [
            _validation("friend_designer", "themed-outing-designer", friend_card.get("designer"), friend_card.get("designer") == "themed-outing-designer"),
            _validation("couple_designer", "couple-date-designer", couple_card.get("designer"), couple_card.get("designer") == "couple-date-designer"),
            _validation("friend_required_keys", sorted(REQUIRED_CARD_KEYS), sorted(set(friend_card) & REQUIRED_CARD_KEYS), REQUIRED_CARD_KEYS <= set(friend_card)),
            _validation("couple_required_keys", sorted(REQUIRED_CARD_KEYS), sorted(set(couple_card) & REQUIRED_CARD_KEYS), REQUIRED_CARD_KEYS <= set(couple_card)),
            _validation("friend_flow_matches_timeline", len(friends.options[0].timeline_items), len(friend_card.get("flow", [])), len(friend_card.get("flow", [])) == len(friends.options[0].timeline_items)),
            _validation("couple_flow_matches_timeline", len(couple.options[0].timeline_items), len(couple_card.get("flow", [])), len(couple_card.get("flow", [])) == len(couple.options[0].timeline_items)),
            _validation("booking_note_safety", "确认前不会", [friend_card.get("booking_note"), couple_card.get("booking_note")], "确认前不会" in friend_card.get("booking_note", "") and "确认前不会" in couple_card.get("booking_note", "")),
        ]
        return ScenarioRun(
            validations=validations,
            evidence=[
                _evidence("friend_card", friend_card),
                _evidence("couple_card", couple_card),
            ],
        )

    def _run_mock_booking_order(self) -> ScenarioRun:
        meituan = RecordingMeituanClient()
        agent = ActivityPlanningAgent(tool_client=meituan)
        try:
            session = agent.start_session()
            response = agent.chat(session.id, "朋友局，今晚下班回血，4个人，人均220")
            option = response.options[0]
            draft = agent.create_booking_draft(session.id, option.id, PayMode.AA_PREPAY)
            cancelled = agent.confirm_booking(session.id, draft.id, confirm=False)
            confirmed = agent.confirm_booking(session.id, draft.id, confirm=True)
            validations = [
                _validation("draft_status", "pending_user_confirmation", draft.status, draft.status == "pending_user_confirmation"),
                _validation("confirmation_required", True, draft.confirmation_required, draft.confirmation_required is True),
                _validation("safety_notice", "不会未经授权支付", draft.safety_notice, "不会未经授权支付" in draft.safety_notice),
                _validation("aa_draft_created", True, bool(draft.aa_draft), bool(draft.aa_draft)),
                _validation("cancel_no_order", ConfirmationStatus.CANCELLED.value, cancelled.status.value, cancelled.status == ConfirmationStatus.CANCELLED and not cancelled.order_ids),
                _validation("confirm_creates_orders", "mock order ids", confirmed.order_ids, confirmed.status == ConfirmationStatus.CONFIRMED and bool(confirmed.order_ids)),
                _validation("availability_called_per_item", f">={len(option.timeline_items)}", meituan.calls.count("check_availability"), meituan.calls.count("check_availability") >= len(option.timeline_items)),
                _validation("hold_called", "create_booking_hold", meituan.calls, "create_booking_hold" in meituan.calls),
                _validation("aa_called", "create_aa_draft", meituan.calls, "create_aa_draft" in meituan.calls),
                _validation("confirm_called", "confirm_booking", meituan.calls, "confirm_booking" in meituan.calls),
            ]
            tool_calls = [ToolCallRecord(name, {}, {}) for name in meituan.calls]
            return ScenarioRun(
                validations=validations,
                evidence=[
                    _evidence("draft", {"id": draft.id, "status": draft.status, "items": len(draft.items), "aa_draft": draft.aa_draft}),
                    _evidence("cancelled", {"status": cancelled.status.value, "order_ids": cancelled.order_ids}),
                    _evidence("confirmed", {"status": confirmed.status.value, "order_ids": confirmed.order_ids}),
                ],
                tool_calls=tool_calls,
            )
        finally:
            agent.close()

    def _markdown_report(self, suite: AcceptanceSuiteResult) -> str:
        metrics = suite.metrics
        lines = [
            "# 8 项业务验收测试报告",
            "",
            f"- 生成时间: `{suite.generated_at}`",
            f"- 测试项总数: `{metrics.total_cases}`",
            f"- 通过测试项: `{metrics.passed_cases}`",
            f"- 失败测试项: `{metrics.failed_cases}`",
            f"- 测试项通过率: `{metrics.case_pass_rate:.2%}`",
            f"- 校验项总数: `{metrics.total_validations}`",
            f"- 失败校验项: `{metrics.failed_validations}`",
            f"- 校验项通过率: `{metrics.validation_pass_rate:.2%}`",
            f"- 异常测试项: `{metrics.exception_cases}`",
            "",
            "## 执行结果总览",
            "",
            "| ID | 分类 | 结果 | 失败校验 | 异常 | 主要关联文件 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for result in suite.case_results:
            failed = [item.name for item in result.validations if not item.passed]
            lines.append(
                "| {case_id} | {category} | {status} | {failed} | {error} | {files} |".format(
                    case_id=result.case_id,
                    category=result.category,
                    status="PASS" if result.passed else "FAIL",
                    failed=", ".join(failed) if failed else "-",
                    error=result.exception_type or "-",
                    files="<br>".join(result.related_files[:3]) if result.related_files else "-",
                )
            )

        lines.extend(["", "## 问题汇总", ""])
        issues = [result for result in suite.case_results if not result.passed or result.exception_type]
        if not issues:
            lines.append("- 未发现失败测试项。")
        else:
            for result in issues:
                lines.append(f"### {result.case_id} {result.title}")
                if result.exception_type:
                    lines.append(f"- 异常: `{result.exception_type}` {result.exception_message or ''}")
                for validation in result.validations:
                    if validation.passed:
                        continue
                    lines.append(
                        f"- `{validation.name}` 失败：预期 `{_short(validation.expected)}`，实际 `{_short(validation.actual)}`。"
                    )
                    if validation.debug_hint:
                        lines.append(f"  定位提示：{validation.debug_hint}")
                    files = validation.related_files or result.related_files
                    if files:
                        lines.append("  关联文件：" + "；".join(files))

        for result in suite.case_results:
            lines.extend(
                [
                    "",
                    f"## {result.case_id} {result.title}",
                    "",
                    f"- 分类: `{result.category}`",
                    f"- 结果: `{'PASS' if result.passed else 'FAIL'}`",
                    f"- 需求: {result.requirement}",
                    f"- 描述: {result.description}",
                    f"- 耗时: `{result.duration_ms}ms`",
                    "",
                    "### 关联文件",
                    "",
                ]
            )
            lines.extend([f"- `{file}`" for file in result.related_files] or ["- -"])
            lines.extend(
                [
                    "",
                    "### 校验明细",
                    "",
                    "| 校验项 | 结果 | 预期 | 实际 | 定位提示 |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for validation in result.validations:
                lines.append(
                    "| {name} | {status} | {expected} | {actual} | {hint} |".format(
                        name=validation.name,
                        status="PASS" if validation.passed else "FAIL",
                        expected=_md(_short(validation.expected)),
                        actual=_md(_short(validation.actual)),
                        hint=_md(validation.debug_hint or validation.details or "-"),
                    )
                )

            if result.evidence:
                lines.extend(["", "### 证据", "", "| 名称 | 值 | 说明 |", "| --- | --- | --- |"])
                for evidence in result.evidence:
                    lines.append(f"| {evidence.name} | {_md(_short(evidence.value, 600))} | {_md(evidence.details or '-')} |")

            if result.transcript:
                lines.extend(["", "### 对话转录", "", "| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 选项 | 请求快照 |", "| --- | --- | --- | --- | --- | --- | --- |"])
                for turn in result.transcript:
                    lines.append(
                        "| {idx} | {user} | {assistant} | {state} | {next_step} | {options} | {request} |".format(
                            idx=turn.turn_index,
                            user=_md(turn.user_input),
                            assistant=_md(turn.assistant_output),
                            state=turn.state or "-",
                            next_step=turn.next_step or "-",
                            options=_md(" / ".join(turn.options) if turn.options else "-"),
                            request=_md(_short(turn.request_snapshot, 420)),
                        )
                    )

            if result.tool_calls:
                lines.extend(["", "### 工具/外部接口调用记录", "", "| 工具 | 输入摘要 | 输出摘要 |", "| --- | --- | --- |"])
                for call in result.tool_calls:
                    lines.append(f"| {call.tool} | {_md(_short(call.input_summary, 360))} | {_md(_short(call.output_summary, 360))} |")

            if result.traceback_text:
                lines.extend(["", "### Traceback", "", "```text", result.traceback_text, "```"])

        return "\n".join(lines) + "\n"


class FakeHTTPClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def get_json(self, url: str, params: dict[str, Any] | None = None, headers: dict[str, str] | None = None):
        self.calls.append({"url": url, "params": params or {}, "headers": headers or {}})
        return {"status": "1", "province": "浙江省", "city": "杭州市", "adcode": "330100"}


class FakeAmapAroundClient:
    def __init__(self) -> None:
        self.around_calls: list[dict[str, Any]] = []

    def search_pois(self, city: str, keywords: str, types: str = "", offset: int = 20, page: int = 1):
        return {"status": "1", "pois": []}

    def search_pois_around(self, location: str, radius_m: int, keywords: str, city: str = "", types: str = "", offset: int = 20, page: int = 1):
        self.around_calls.append({"location": location, "radius_m": radius_m, "keywords": keywords, "city": city, "types": types, "offset": offset, "page": page})
        if keywords == "烧烤":
            pois = [{"id": "B0FFOOD001", "name": "范围测试烧烤店", "type": "餐饮服务;中餐厅;烧烤", "address": "奥映世纪轩周边", "adname": "萧山区", "location": "120.2430,30.2432", "biz_ext": {"cost": "98"}}]
        elif keywords == "桌游":
            pois = [{"id": "B0FFUN001", "name": "范围测试桌游馆", "type": "体育休闲服务;休闲场所;游戏厅", "address": "奥映世纪轩周边", "adname": "萧山区", "location": "120.2440,30.2435", "biz_ext": {"cost": "78"}}]
        else:
            pois = []
        return {"status": "1", "pois": pois}


class FakeCuratorLLM:
    def __init__(self) -> None:
        self.messages: list[list[dict[str, str]]] = []

    def complete(self, messages):
        self.messages.append(messages)
        return json.dumps({"merchant_ids": ["food_bbq", "activity_ktv", "relax_tea", "made_up_merchant"]}, ensure_ascii=False)


class FakeAmapRouteClient:
    def __init__(self) -> None:
        self.route_calls: list[tuple[str, str]] = []

    def walking_route(self, origin: str, destination: str):
        self.route_calls.append((origin, destination))
        return {"status": "1", "route": {"paths": [{"distance": "1200", "duration": "900"}]}}


class RecordingMeituanClient(MockMeituanToolClient):
    def __init__(self) -> None:
        super().__init__()
        self.calls: list[str] = []

    def check_availability(self, merchant_id: str, time_window: str, party_size: int):
        self.calls.append("check_availability")
        return super().check_availability(merchant_id, time_window, party_size)

    def create_booking_hold(self, items: list[dict[str, object]]):
        self.calls.append("create_booking_hold")
        return super().create_booking_hold(items)

    def create_aa_draft(self, total: int, party_size: int, mode: str):
        self.calls.append("create_aa_draft")
        return super().create_aa_draft(total, party_size, mode)

    def confirm_booking(self, hold_id: str, confirm_token: str, items: list[dict[str, object]]):
        self.calls.append("confirm_booking")
        return super().confirm_booking(hold_id, confirm_token, items)


def _request_snapshot(request: UserRequest | None) -> dict[str, Any]:
    if request is None:
        return {}
    return {
        "scene": request.scene.value,
        "origin_name": request.origin_name,
        "origin_address": request.origin_address,
        "origin_amap_url": request.origin_amap_url,
        "origin_longitude": request.origin_longitude,
        "origin_latitude": request.origin_latitude,
        "search_radius_km": request.search_radius_km,
        "route_limit_km": request.route_limit_km,
        "route_limit_minutes": request.route_limit_minutes,
        "budget_per_person": request.budget_per_person,
        "time_window": request.time_window,
        "mood_tags": request.mood_tags,
        "relationship_stage": request.relationship_stage,
    }


def _supply(merchant_id: str, name: str, item_type: TimelineType, tags: list[str], price: int) -> MerchantSupply:
    return MerchantSupply(
        id=merchant_id,
        name=name,
        type=item_type,
        price=price,
        duration_minutes=60,
        distance_km=1.0,
        district="萧山区",
        tags=tags,
        scene_fit=[Scene.FRIENDS],
        booking_modes=["reservation"],
        available=True,
        why=f"{name} 适合主题局。",
        address="奥映世纪轩周边",
        latitude=30.243,
        longitude=120.243,
        area_cluster="xianghu_lake",
        data_confidence="mock",
        matched_keywords=tags[:1],
    )


def _item(name: str, lng: float, lat: float, index: int) -> TimelineItem:
    return TimelineItem(
        type=TimelineType.DINING if index == 1 else TimelineType.ACTIVITY,
        merchant_id=f"merchant_{index}",
        merchant_name=name,
        start_time="18:30",
        end_time="19:30",
        booking_required=True,
        price_estimate=88,
        why_this_fits=f"{name} 适合当前主题。",
        booking_modes=["reservation"],
        address=f"{name}地址",
        longitude=lng,
        latitude=lat,
    )


def _short(value: Any, limit: int = 220) -> str:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, ensure_ascii=False, default=str)
    text = text.replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _md(value: Any) -> str:
    return str(value).replace("\n", "<br>").replace("|", "\\|")


def _json_default(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    if hasattr(value, "value"):
        return value.value
    return str(value)
