
from activity_agent import ActivityPlanningAgent
from activity_agent.modules.dialogue_manager import DialogueManager, UserUnderstanding
from activity_agent.llm import MockLLMClient


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def demo_understanding_cases():
    """
    演示 LLM 如何理解不同的自然语言表达（而不只是关键字）
    """
    print_section("LLM 智能理解能力演示")

    manager = DialogueManager(MockLLMClient())

    test_cases = [
        {
            "description": "场景：朋友聚会",
            "inputs": [
                "今晚想找几个朋友出来聚聚",
                "大家好久没见了，约一下",
                "下班了想放松放松"
            ]
        },
        {
            "description": "场景：情侣约会",
            "inputs": [
                "周末想约她出来",
                "想给她一个惊喜",
                "纪念日要好好安排"
            ]
        },
        {
            "description": "关系阶段：暧昧/追求中",
            "inputs": [
                "有点怕尴尬，想安排轻松点",
                "第一次约她，不想太有压力",
                "想自然一点，不要太刻意"
            ]
        },
        {
            "description": "氛围需求",
            "inputs": [
                "想找个地方聊聊天",
                "需要发泄一下",
                "想拍点好看的照片"
            ]
        }
    ]

    for case in test_cases:
        print(f"\n {case['description']}")
        for user_input in case["inputs"]:
            print(f"\n  用户: \"{user_input}\"")

            understanding = manager._understand(user_input)
            print(f"  理解:")

            if understanding.scene:
                print(f"    - 场景: {understanding.scene.value}")

            if understanding.relationship_stage:
                print(f"    - 关系: {understanding.relationship_stage}")
                if understanding.relationship_goal:
                    print(f"    - 目标: {understanding.relationship_goal}")

            if understanding.mood_tags:
                print(f"    - 氛围: {', '.join(understanding.mood_tags)}")

            if understanding.budget:
                print(f"    - 预算: 人均 {understanding.budget}")

            if understanding.time_window:
                print(f"    - 时间: {understanding.time_window}")

            if any(understanding.constraints.values()):
                constraints = [k for k, v in understanding.constraints.items() if v]
                print(f"    - 约束: {', '.join(constraints)}")

            print(f"    - 置信度: {understanding.confidence:.2f}")


def demo_conversation_flow():
    """
    演示完整的对话流程
    """
    print_section("完整对话流程演示")

    agent = ActivityPlanningAgent()
    session = agent.start_session(user_id="demo")

    conversation = [
        "好无聊啊",
        "想叫几个朋友出来",
        "累了一周了，想放松一下",
        "人均200左右吧",
        "就今晚"
    ]

    for i, user_msg in enumerate(conversation, 1):
        print(f"\n--- 轮次 {i} ---")
        print(f"用户: {user_msg}")
        response = agent.chat_with_guidance(session.id, user_msg)
        print(f"Agent: {response.message}")
        print(f"状态: {agent.get_conversation_state(session.id)}")


def main():
    print("\n" + "*" * 60)
    print("  智能理解 vs 关键字匹配")
    print("*" * 60)

    print("\n升级亮点:")
    print("  1. LLM 优先理解用户真实意图")
    print("  2. 自然语言推断，不依赖硬编码")
    print("  3. 智能降级机制，无 LLM 时回退规则")
    print("  4. 置信度评估，把握不大时会确认")

    demo_understanding_cases()

    print("\n" + "-" * 60)
    print("  注：当前使用的是 MockLLMClient（演示规则模式）")
    print("  设置 OpenAI API Key 后可体验真实 LLM 理解能力")
    print("-" * 60)


if __name__ == "__main__":
    main()

