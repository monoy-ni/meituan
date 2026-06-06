from activity_agent import ActivityPlanningAgent
from activity_agent.domain import FeedbackStatus, InviteFeedback


def print_section(title: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_message(role: str, text: str) -> None:
    prefix = "👤 用户:" if role == "user" else "🤖 Agent:"
    print(f"\n{prefix}")
    print(text)


def demo_friends_scenario():
    print_section("场景一：朋友聚会 - 完整对话流程")

    agent = ActivityPlanningAgent()
    session = agent.start_session(user_id="demo_friends")

    # 第一轮：识别场景
    print_message("user", "今晚有点无聊")
    response = agent.chat_with_guidance(session.id, "今晚有点无聊")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第二轮：确定是朋友局
    print_message("user", "想叫朋友出来聚聚")
    response = agent.chat_with_guidance(session.id, "想叫朋友出来聚聚")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第三轮：确定氛围
    print_message("user", "轻松点聊聊天吧，最近太累了")
    response = agent.chat_with_guidance(session.id, "轻松点聊聊天吧，最近太累了")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第四轮：确定预算
    print_message("user", "人均200左右吧")
    response = agent.chat_with_guidance(session.id, "人均200左右吧")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第五轮：确定时间
    print_message("user", "就今晚吧")
    response = agent.chat_with_guidance(session.id, "就今晚吧")
    print_message("assistant", response.message)

    if response.options:
        print("\n📋 推荐方案：")
        for i, card in enumerate(response.share_cards, 1):
            print(f"\n--- 方案 {i} ---")
            print(card)

        # 选择方案并预约
        print_section("选择方案并自动预约")
        selected_option_id = response.options[0].id
        print(f"选择方案: {response.options[0].theme_name}")

        draft, confirmation = agent.select_and_book(session.id, selected_option_id)

        print("\n✅ 预约完成！")
        print(f"订单号: {', '.join(confirmation.order_ids)}")
        if confirmation.reservation_ids:
            print(f"订座号: {', '.join(confirmation.reservation_ids)}")


def demo_couple_scenario():
    print_section("场景二：情侣约会 - 智能识别关系阶段（不直接问）")

    agent = ActivityPlanningAgent()
    session = agent.start_session(user_id="demo_couple")

    # 第一轮：识别情侣场景
    print_message("user", "周末想约她出来")
    response = agent.chat_with_guidance(session.id, "周末想约她出来")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第二轮：暗示关系阶段（怕尴尬 → 暧昧/追求中）
    print_message("user", "有点怕尴尬，想安排轻松点")
    response = agent.chat_with_guidance(session.id, "有点怕尴尬，想安排轻松点")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第三轮：确定预算
    print_message("user", "人均300左右可以接受")
    response = agent.chat_with_guidance(session.id, "人均300左右可以接受")
    print_message("assistant", response.message)
    print(f"[当前状态: {agent.get_conversation_state(session.id)}]")

    # 第四轮：确定时间
    print_message("user", "周六下午吧")
    response = agent.chat_with_guidance(session.id, "周六下午吧")
    print_message("assistant", response.message)

    if response.options:
        print("\n💝 约会方案：")
        for i, card in enumerate(response.share_cards, 1):
            print(f"\n--- 方案 {i} ---")
            print(card)

        print("\n💡 智能推断：")
        print("Agent 通过对话推断出这是「暧昧/追求中」阶段")
        print("因此推荐了「轻升温不尴尬约会」方案")
        print("没有安排酒店等高压选项")


def demo_anniversary_scenario():
    print_section("场景三：纪念日 - 自动识别并推荐浪漫方案")

    agent = ActivityPlanningAgent()
    session = agent.start_session(user_id="demo_anniversary")

    # 一句话触发纪念日模式
    print_message("user", "下周三是纪念日，想安排一下，人均500左右")
    response = agent.chat_with_guidance(session.id, "下周三是纪念日，想安排一下，人均500左右")
    print_message("assistant", response.message)

    if response.options:
        print("\n💐 纪念日方案：")
        for i, card in enumerate(response.share_cards, 1):
            print(f"\n--- 方案 {i} ---")
            print(card)


def main():
    print("=" * 60)
    print("  🎉 智能活动规划 Agent - 对话式体验演示")
    print("=" * 60)
    print("\n本演示展示：")
    print(" 1. 智能识别用户群体（朋友/情侣）")
    print(" 2. 多轮对话引导，逐步确定需求")
    print(" 3. 情侣关系阶段智能推断（不直接问）")
    print(" 4. 生成多个方案供选择")
    print(" 5. 一键选择并自动预约")

    input("\n按 Enter 开始演示...")

    demo_friends_scenario()

    input("\n\n按 Enter 看情侣约会演示...")

    demo_couple_scenario()

    input("\n\n按 Enter 看纪念日快速演示...")

    demo_anniversary_scenario()

    print_section("🎉 演示完成！")
    print("\n总结：")
    print(" - Agent 可以自然地引导用户完成需求收集")
    print(" - 通过对话内容智能推断关系阶段，不直接问")
    print(" - 朋友局和约会场景有不同的引导策略")
    print(" - 收集完需求后自动生成多个方案")
    print(" - 选择方案后可一键完成预约")


if __name__ == "__main__":
    main()
