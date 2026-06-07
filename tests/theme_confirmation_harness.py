from __future__ import annotations

import importlib.util
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import AgentResponse, Scene
from activity_agent.modules.theme_planner import COUPLE_THEMES, FRIENDS_THEMES, HANGZHOU_CITY_THEMES


def _load_dotenv():
    """手动加载 .env 文件（不依赖 python-dotenv）"""
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            os.environ[key] = value


_load_dotenv()


PROJECT_ROOT = Path(__file__).resolve().parents[1]
THEME_KEYWORD_SEEDS_PATH = PROJECT_ROOT / "activity_agent" / "data" / "theme_keyword_seeds.py"
DEFAULT_REPORT_DIR = PROJECT_ROOT / "reports"


class DialogueTurnTimeoutError(RuntimeError):
    """Raised when one turn exceeds the configured timeout."""


class ResponseFormatError(RuntimeError):
    """Raised when the response shape is not compatible with the harness."""


@dataclass(frozen=True)
class ThemeConfirmationTurn:
    message: str
    scene_hint: Scene | str | None = None


@dataclass(frozen=True)
class ThemeConfirmationCase:
    case_id: str
    title: str
    category: str
    description: str
    turns: list[ThemeConfirmationTurn]
    expected_scene: Scene | None = None
    expected_relationship_stage: str | None = None
    expected_top_theme_key: str | None = None
    expected_final_state: str = "awaiting_selection"
    min_options: int = 3
    require_options: bool = True
    notes: str = ""


@dataclass(frozen=True)
class ValidationResult:
    name: str
    passed: bool
    expected: Any
    actual: Any
    details: str = ""


@dataclass(frozen=True)
class DialogueTurnRecord:
    turn_index: int
    user_input: str
    scene_hint: str | None
    assistant_output: str | None
    conversation_state: str | None
    conversation_next_step: str | None
    options_theme_names: list[str] = field(default_factory=list)
    request_scene: str | None = None
    request_relationship_stage: str | None = None
    duration_ms: int = 0


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    title: str
    category: str
    passed: bool
    seed_basis: str
    transcript: list[DialogueTurnRecord]
    validations: list[ValidationResult]
    final_scene: str | None
    final_relationship_stage: str | None
    final_top_theme_name: str | None
    final_state: str | None
    final_next_step: str | None
    options_count: int
    exception_type: str | None = None
    exception_message: str | None = None


@dataclass(frozen=True)
class SuiteMetrics:
    total_cases: int
    passed_cases: int
    failed_cases: int
    case_pass_rate: float
    theme_accuracy: float
    relationship_stage_accuracy: float
    exception_case_count: int
    avg_turns_per_case: float


@dataclass(frozen=True)
class SuiteResult:
    generated_at: str
    seed_file_path: str
    metrics: SuiteMetrics
    case_results: list[CaseResult]
    theme_catalog: dict[str, str]
    seed_keywords: dict[str, list[str]]
    markdown_report_path: str | None = None
    json_report_path: str | None = None


@dataclass(frozen=True)
class ThemeSeedReference:
    file_path: str
    keywords_by_key: dict[str, list[str]]
    alias_groups_by_key: dict[str, list[str]]

    def basis_text(self, theme_key: str | None) -> str:
        if not theme_key:
            return "未指定主题校验。"
        aliases = self.alias_groups_by_key.get(theme_key, [theme_key])
        keywords = self.keywords_by_key.get(theme_key, [])
        return f"{theme_key} -> aliases={aliases}, keywords={keywords}"


def _load_theme_seed_reference(file_path: Path) -> ThemeSeedReference:
    spec = importlib.util.spec_from_file_location("theme_keyword_seeds_reference", file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load theme seed module from {file_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    keywords_by_key: dict[str, list[str]] = {
        **dict(getattr(module, "FRIENDS_THEME_KEYWORD_SEEDS")),
        **dict(getattr(module, "HANGZHOU_THEME_KEYWORD_SEEDS")),
        **dict(getattr(module, "COUPLE_THEME_KEYWORD_SEEDS")),
    }

    grouped: dict[tuple[str, ...], list[str]] = {}
    for key, keywords in keywords_by_key.items():
        grouped.setdefault(tuple(keywords), []).append(key)

    alias_groups_by_key = {
        key: sorted(grouped[tuple(keywords)])
        for key, keywords in keywords_by_key.items()
    }
    return ThemeSeedReference(str(file_path), keywords_by_key, alias_groups_by_key)


def _theme_catalog() -> dict[str, str]:
    themes = [*FRIENDS_THEMES, *HANGZHOU_CITY_THEMES, *COUPLE_THEMES]
    return {theme.id: theme.name for theme in themes}


def _coerce_scene_value(value: Scene | str | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, Scene):
        return value.value
    try:
        return Scene(str(value)).value
    except ValueError:
        return str(value)


def _validation(name: str, expected: Any, actual: Any, passed: bool, details: str = "") -> ValidationResult:
    return ValidationResult(name=name, expected=expected, actual=actual, passed=passed, details=details)


class ThemeConfirmationHarness:
    """Reusable end-to-end validator for the guided theme-confirmation dialogue."""

    def __init__(
        self,
        agent_factory: Callable[[], ActivityPlanningAgent] = ActivityPlanningAgent.from_env,
        timeout_seconds: float = 20.0,
        theme_seed_path: Path = THEME_KEYWORD_SEEDS_PATH,
        turn_executor: Callable[[ActivityPlanningAgent, str, ThemeConfirmationTurn], AgentResponse] | None = None,
    ) -> None:
        self.agent_factory = agent_factory
        self.timeout_seconds = timeout_seconds
        self.seed_reference = _load_theme_seed_reference(theme_seed_path)
        self.catalog = _theme_catalog()
        self.turn_executor = turn_executor or self._default_turn_executor

    def _default_turn_executor(
        self,
        agent: ActivityPlanningAgent,
        session_id: str,
        turn: ThemeConfirmationTurn,
    ) -> AgentResponse:
        return agent.chat_with_guidance(session_id, turn.message, scene_hint=turn.scene_hint)

    def run_case(self, case: ThemeConfirmationCase) -> CaseResult:
        agent = self.agent_factory()
        # 调试输出：确认是否使用了真实LLM
        from activity_agent.llm import MockLLMClient
        is_mock = isinstance(agent.llm_client, MockLLMClient)
        if not hasattr(self, '_debug_printed'):
            print(f"[DEBUG] Using LLM client: {'MockLLMClient' if is_mock else f'{type(agent.llm_client).__name__}'}")
            print(f"[DEBUG] API key configured: {agent.settings.llm.api_key is not None}")
            self._debug_printed = True
            
        transcript: list[DialogueTurnRecord] = []
        response: AgentResponse | None = None
        conversation: dict[str, object] | None = None
        error: Exception | None = None

        try:
            session = agent.start_session()
            for index, turn in enumerate(case.turns, start=1):
                turn_started_at = time.perf_counter()
                response = self._execute_turn(agent, session.id, turn)
                self._validate_response_format(response)
                conversation = agent.get_conversation_payload(session.id, has_options=bool(response.options))
                
                # 提取选项主题名，防止response.options为None
                options_theme_names = []
                if response.options:
                    try:
                        options_theme_names = [option.theme_name for option in response.options if option and hasattr(option, "theme_name")]
                    except Exception:
                        pass
                
                # 提取request_scene，防止相关属性为None
                request_scene = None
                try:
                    if response.request and hasattr(response.request, "scene") and response.request.scene:
                        request_scene = response.request.scene.value
                    elif hasattr(response, "scene") and response.scene:
                        request_scene = response.scene.value
                except Exception:
                    pass
                
                # 提取relationship_stage
                request_relationship_stage = None
                try:
                    if response.request and hasattr(response.request, "relationship_stage"):
                        request_relationship_stage = response.request.relationship_stage
                except Exception:
                    pass
                
                transcript.append(
                    DialogueTurnRecord(
                        turn_index=index,
                        user_input=turn.message,
                        scene_hint=_coerce_scene_value(turn.scene_hint),
                        assistant_output=response.message if response and hasattr(response, "message") else None,
                        conversation_state=str(conversation.get("state")) if conversation else None,
                        conversation_next_step=str(conversation.get("next_step")) if conversation else None,
                        options_theme_names=options_theme_names,
                        request_scene=request_scene,
                        request_relationship_stage=request_relationship_stage,
                        duration_ms=round((time.perf_counter() - turn_started_at) * 1000),
                    )
                )
        except Exception as exc:  # noqa: BLE001 - report generation needs the raw failure.
            error = exc
        finally:
            agent.close()

        if response is None and conversation is None:
            conversation = {}

        validations = self._build_validations(case, response, conversation)
        passed = error is None and all(item.passed for item in validations)
        final_scene = None
        final_relationship_stage = None
        final_top_theme_name = None
        final_state = str(conversation.get("state")) if conversation else None
        final_next_step = str(conversation.get("next_step")) if conversation else None
        options_count = 0

        if response is not None:
            final_scene = response.request.scene.value if response.request else response.scene.value
            final_relationship_stage = response.request.relationship_stage if response.request else None
            final_top_theme_name = response.options[0].theme_name if response.options else None
            options_count = len(response.options)

        return CaseResult(
            case_id=case.case_id,
            title=case.title,
            category=case.category,
            passed=passed,
            seed_basis=self.seed_reference.basis_text(case.expected_top_theme_key),
            transcript=transcript,
            validations=validations,
            final_scene=final_scene,
            final_relationship_stage=final_relationship_stage,
            final_top_theme_name=final_top_theme_name,
            final_state=final_state,
            final_next_step=final_next_step,
            options_count=options_count,
            exception_type=type(error).__name__ if error else None,
            exception_message=str(error) if error else None,
        )

    def run_cases(self, cases: list[ThemeConfirmationCase], output_dir: Path | None = None) -> SuiteResult:
        case_results = [self.run_case(case) for case in cases]
        metrics = self._build_metrics(case_results)
        suite = SuiteResult(
            generated_at=datetime.now().isoformat(timespec="seconds"),
            seed_file_path=self.seed_reference.file_path,
            metrics=metrics,
            case_results=case_results,
            theme_catalog=self.catalog,
            seed_keywords=self.seed_reference.keywords_by_key,
        )
        if output_dir is None:
            return suite
        return self.write_reports(suite, output_dir)

    def write_reports(self, suite: SuiteResult, output_dir: Path = DEFAULT_REPORT_DIR) -> SuiteResult:
        output_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = output_dir / "theme_confirmation_report.md"
        json_path = output_dir / "theme_confirmation_report.json"

        markdown_path.write_text(self._markdown_report(suite), encoding="utf-8")
        json_path.write_text(
            json.dumps(self._suite_to_dict(suite), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return SuiteResult(
            generated_at=suite.generated_at,
            seed_file_path=suite.seed_file_path,
            metrics=suite.metrics,
            case_results=suite.case_results,
            theme_catalog=suite.theme_catalog,
            seed_keywords=suite.seed_keywords,
            markdown_report_path=str(markdown_path),
            json_report_path=str(json_path),
        )

    def _execute_turn(
        self,
        agent: ActivityPlanningAgent,
        session_id: str,
        turn: ThemeConfirmationTurn,
    ) -> AgentResponse:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.turn_executor, agent, session_id, turn)
            try:
                return future.result(timeout=self.timeout_seconds)
            except FuturesTimeoutError as exc:
                future.cancel()
                raise DialogueTurnTimeoutError(
                    f"Turn timed out after {self.timeout_seconds:.2f}s: {turn.message}"
                ) from exc

    def _validate_response_format(self, response: AgentResponse) -> None:
        if not isinstance(response, AgentResponse):
            raise ResponseFormatError(f"Unexpected response object type: {type(response)!r}")
        if not isinstance(response.message, str) or not response.message.strip():
            raise ResponseFormatError("Response message is empty or not a string.")
        if not isinstance(response.options, list):
            raise ResponseFormatError("Response options is not a list.")
        if response.options and response.request is None:
            raise ResponseFormatError("Response contains options but request is missing.")

    def _build_validations(
        self,
        case: ThemeConfirmationCase,
        response: AgentResponse | None,
        conversation: dict[str, object] | None,
    ) -> list[ValidationResult]:
        validations: list[ValidationResult] = []
        final_state = str(conversation.get("state")) if conversation else None
        final_scene = None
        final_stage = None
        final_theme_name = None
        options_count = 0

        if response is not None:
            final_scene = response.request.scene.value if response.request else response.scene.value
            final_stage = response.request.relationship_stage if response.request else None
            final_theme_name = response.options[0].theme_name if response.options else None
            options_count = len(response.options)

        if case.expected_scene is not None:
            validations.append(
                _validation(
                    "scene",
                    case.expected_scene.value,
                    final_scene,
                    final_scene == case.expected_scene.value,
                )
            )

        if case.expected_relationship_stage is not None:
            validations.append(
                _validation(
                    "relationship_stage",
                    case.expected_relationship_stage,
                    final_stage,
                    final_stage == case.expected_relationship_stage,
                )
            )

        if case.expected_top_theme_key is not None:
            expected_theme_name = self.catalog.get(case.expected_top_theme_key)
            validations.append(
                _validation(
                    "top_theme",
                    expected_theme_name,
                    final_theme_name,
                    final_theme_name == expected_theme_name,
                    details=self.seed_reference.basis_text(case.expected_top_theme_key),
                )
            )

        validations.append(
            _validation(
                "final_state",
                case.expected_final_state,
                final_state,
                final_state == case.expected_final_state,
            )
        )

        if case.require_options:
            validations.append(
                _validation(
                    "options_count",
                    f">={case.min_options}",
                    options_count,
                    options_count >= case.min_options,
                )
            )

        return validations

    def _build_metrics(self, case_results: list[CaseResult]) -> SuiteMetrics:
        total_cases = len(case_results)
        passed_cases = sum(1 for result in case_results if result.passed)
        failed_cases = total_cases - passed_cases
        exception_case_count = sum(1 for result in case_results if result.exception_type)
        total_turns = sum(len(result.transcript) for result in case_results)

        theme_validations = [
            validation
            for result in case_results
            for validation in result.validations
            if validation.name == "top_theme"
        ]
        stage_validations = [
            validation
            for result in case_results
            for validation in result.validations
            if validation.name == "relationship_stage"
        ]

        return SuiteMetrics(
            total_cases=total_cases,
            passed_cases=passed_cases,
            failed_cases=failed_cases,
            case_pass_rate=round((passed_cases / total_cases) if total_cases else 0.0, 4),
            theme_accuracy=round(
                (sum(1 for item in theme_validations if item.passed) / len(theme_validations))
                if theme_validations
                else 0.0,
                4,
            ),
            relationship_stage_accuracy=round(
                (sum(1 for item in stage_validations if item.passed) / len(stage_validations))
                if stage_validations
                else 0.0,
                4,
            ),
            exception_case_count=exception_case_count,
            avg_turns_per_case=round((total_turns / total_cases) if total_cases else 0.0, 2),
        )

    def _suite_to_dict(self, suite: SuiteResult) -> dict[str, Any]:
        payload = asdict(suite)
        payload["case_results"] = [self._case_result_to_dict(item) for item in suite.case_results]
        return payload

    def _case_result_to_dict(self, case_result: CaseResult) -> dict[str, Any]:
        return {
            "case_id": case_result.case_id,
            "title": case_result.title,
            "category": case_result.category,
            "passed": case_result.passed,
            "seed_basis": case_result.seed_basis,
            "transcript": [asdict(turn) for turn in case_result.transcript],
            "validations": [asdict(validation) for validation in case_result.validations],
            "final_scene": case_result.final_scene,
            "final_relationship_stage": case_result.final_relationship_stage,
            "final_top_theme_name": case_result.final_top_theme_name,
            "final_state": case_result.final_state,
            "final_next_step": case_result.final_next_step,
            "options_count": case_result.options_count,
            "exception_type": case_result.exception_type,
            "exception_message": case_result.exception_message,
        }

    def _markdown_report(self, suite: SuiteResult) -> str:
        metrics = suite.metrics
        lines = [
            "# 主题确认功能验证测试报告",
            "",
            f"- 生成时间: `{suite.generated_at}`",
            f"- 主题参考定义文件: `{suite.seed_file_path}`",
            f"- 测试用例总数: `{metrics.total_cases}`",
            f"- 通过用例数: `{metrics.passed_cases}`",
            f"- 失败用例数: `{metrics.failed_cases}`",
            f"- 用例通过率: `{metrics.case_pass_rate:.2%}`",
            f"- 主题定位准确率: `{metrics.theme_accuracy:.2%}`",
            f"- 关系阶段定位准确率: `{metrics.relationship_stage_accuracy:.2%}`",
            f"- 异常用例数: `{metrics.exception_case_count}`",
            f"- 平均对话轮数: `{metrics.avg_turns_per_case}`",
            "",
            "## 执行结果总览",
            "",
            "| 用例ID | 分类 | 结果 | 最终主题 | 关系阶段 | 状态 | 异常 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]

        for result in suite.case_results:
            lines.append(
                "| {case_id} | {category} | {status} | {theme} | {stage} | {state} | {error} |".format(
                    case_id=result.case_id,
                    category=result.category,
                    status="PASS" if result.passed else "FAIL",
                    theme=result.final_top_theme_name or "-",
                    stage=result.final_relationship_stage or "-",
                    state=result.final_state or "-",
                    error=result.exception_type or "-",
                )
            )

        lines.extend(["", "## 问题汇总", ""])
        issues = [
            result
            for result in suite.case_results
            if (not result.passed) or result.exception_type
        ]
        if not issues:
            lines.append("- 未发现未通过用例或执行异常。")
        else:
            for result in issues:
                lines.append(
                    f"- `{result.case_id}` {result.title}: "
                    f"{result.exception_type or '校验未通过'}"
                    f"{' - ' + result.exception_message if result.exception_message else ''}"
                )

        for result in suite.case_results:
            lines.extend(
                [
                    "",
                    f"## {result.case_id} {result.title}",
                    "",
                    f"- 分类: `{result.category}`",
                    f"- 结果: `{'PASS' if result.passed else 'FAIL'}`",
                    f"- 主题参考依据: `{result.seed_basis}`",
                    f"- 最终定位: `scene={result.final_scene}` / "
                    f"`relationship_stage={result.final_relationship_stage}` / "
                    f"`top_theme={result.final_top_theme_name}`",
                    "",
                    "### 校验明细",
                    "",
                    "| 校验项 | 结果 | 预期 | 实际 | 说明 |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for validation in result.validations:
                lines.append(
                    "| {name} | {status} | {expected} | {actual} | {details} |".format(
                        name=validation.name,
                        status="PASS" if validation.passed else "FAIL",
                        expected=validation.expected,
                        actual=validation.actual,
                        details=validation.details or "-",
                    )
                )

            lines.extend(["", "### 对话转录", "", "| 轮次 | 用户输入 | 系统输出 | 状态 | next_step | 候选主题 |", "| --- | --- | --- | --- | --- | --- |"])
            for turn in result.transcript:
                lines.append(
                    "| {turn_index} | {user_input} | {assistant_output} | {state} | {next_step} | {themes} |".format(
                        turn_index=turn.turn_index,
                        user_input=turn.user_input.replace("\n", "<br>"),
                        assistant_output=(turn.assistant_output or "-").replace("\n", "<br>"),
                        state=turn.conversation_state or "-",
                        next_step=turn.conversation_next_step or "-",
                        themes=" / ".join(turn.options_theme_names) if turn.options_theme_names else "-",
                    )
                )

            if result.exception_type:
                lines.extend(
                    [
                        "",
                        "### 异常信息",
                        "",
                        f"- 类型: `{result.exception_type}`",
                        f"- 信息: `{result.exception_message}`",
                    ]
                )

        return "\n".join(lines) + "\n"
