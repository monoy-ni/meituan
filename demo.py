from activity_agent import ActivityPlanningAgent
from activity_agent.domain import FeedbackStatus, InviteFeedback


def print_section(title: str) -> None:
    print("\n" + "=" * 18 + f" {title} " + "=" * 18)


def main() -> None:
    agent = ActivityPlanningAgent()
    session = agent.start_session(user_id="demo_user")

    print_section("SDK Chat 生成朋友组局")
    response = agent.chat(session.id, "今晚有点无聊，想叫朋友出来，预算人均200，别太远")
    print(response.message)
    print(response.share_cards[0])

    selected = agent.select_option(session.id, response.options[0].id)
    print("\n已选：", selected.options[0].theme_name)

    print_section("提交朋友反馈并收敛")
    feedback = [
        InviteFeedback("小王", FeedbackStatus.JOIN, budget_feedback=180, preference_tags=["聊天"]),
        InviteFeedback("小李", FeedbackStatus.LATE, time_feedback="20:30后到"),
        InviteFeedback("小陈", FeedbackStatus.JOIN, dietary_or_boundary_constraints=["不喝酒"]),
        InviteFeedback("小周", FeedbackStatus.PARTIAL, preference_tags=["省钱"]),
    ]
    revised = agent.submit_feedback(session.id, feedback)
    print(revised.message)
    print(revised.share_cards[0])

    print_section("创建并确认 mock 美团预约草稿")
    draft = agent.create_booking_draft(session.id, revised.options[0].id)
    print(draft.safety_notice)
    print("draft_id:", draft.id)
    print("hold_id:", draft.hold_id)
    for item in draft.items:
        print(f"- {item.merchant_name}: {item.action} ({item.status})")

    blocked = agent.confirm_booking(session.id, draft.id, confirm=False)
    print("未确认结果：", blocked.status, blocked.message)

    confirmed = agent.confirm_booking(session.id, draft.id, confirm=True)
    print("确认结果：", confirmed.status, confirmed.message)
    print("mock order ids:", ", ".join(confirmed.order_ids))

    print_section("局后复盘")
    review = agent.create_review(
        session.id,
        actual_cost_per_person=166,
        attendance=4,
        ratings={revised.options[0].timeline_items[1].merchant_name: 4.8},
    )
    print(review.share_copy)
    print("下次推荐：", " / ".join(review.next_recommendations))

    print_section("情侣约会")
    couple_session = agent.start_session(user_id="demo_user")
    couple = agent.chat(couple_session.id, "想约TA出来，怕尴尬，周末下午，人均300")
    print(couple.share_cards[0])


if __name__ == "__main__":
    main()

