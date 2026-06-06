
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from activity_agent import ActivityPlanningAgent
from activity_agent.domain import UserRequest, PlanOption, BookingDraft, BookingConfirmation

app = FastAPI(title="活动规划 Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = ActivityPlanningAgent()
sessions: Dict[str, Any] = {}


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class SelectOptionRequest(BaseModel):
    session_id: str
    option_id: str


class BookingConfirmRequest(BaseModel):
    session_id: str
    draft_id: str
    confirm: bool = True


@app.post("/api/sessions")
def create_session():
    session = agent.start_session()
    sessions[session.id] = session
    return {"session_id": session.id}


@app.post("/api/chat")
def chat(request: ChatRequest):
    if not request.session_id:
        session = agent.start_session()
        request.session_id = session.id
        sessions[session.id] = session
    
    response = agent.chat_with_guidance(request.session_id, request.message)
    
    result = {
        "session_id": response.session_id,
        "message": response.message,
        "intent": response.intent.value if response.intent else None,
        "scene": response.scene.value if response.scene else None,
        "missing_questions": response.missing_questions,
        "assumptions": response.assumptions,
        "options": [],
        "share_cards": []
    }
    
    if response.options:
        for option in response.options:
            result["options"].append({
                "id": option.id,
                "theme_name": option.theme_name,
                "emotional_hook": option.emotional_hook,
                "estimated_cost_per_person": option.estimated_cost_per_person,
                "total_distance": option.total_distance,
                "timeline_items": [
                    {
                        "type": item.type.value,
                        "merchant_name": item.merchant_name,
                        "start_time": item.start_time,
                        "end_time": item.end_time,
                        "price_estimate": item.price_estimate,
                        "why_this_fits": item.why_this_fits
                    } for item in option.timeline_items
                ],
                "risk_notes": option.risk_notes,
                "dating_tips": option.dating_tips
            })
    
    if response.share_cards:
        result["share_cards"] = response.share_cards
    
    return result


@app.post("/api/select-option")
def select_option(request: SelectOptionRequest):
    response = agent.select_option(request.session_id, request.option_id)
    
    result = {
        "session_id": response.session_id,
        "message": response.message,
        "options": [],
        "share_cards": []
    }
    
    if response.options:
        for option in response.options:
            result["options"].append({
                "id": option.id,
                "theme_name": option.theme_name,
                "emotional_hook": option.emotional_hook,
                "estimated_cost_per_person": option.estimated_cost_per_person
            })
    
    return result


@app.post("/api/create-booking-draft")
def create_booking_draft(request: SelectOptionRequest):
    draft = agent.create_booking_draft(request.session_id, request.option_id)
    
    return {
        "draft_id": draft.id,
        "hold_id": draft.hold_id,
        "status": draft.status,
        "pay_mode": draft.pay_mode.value,
        "safety_notice": draft.safety_notice,
        "items": [
            {
                "merchant_id": item.merchant_id,
                "merchant_name": item.merchant_name,
                "type": item.type.value,
                "estimated_price_per_person": item.estimated_price_per_person,
                "action": item.action,
                "status": item.status
            } for item in draft.items
        ]
    }


@app.post("/api/confirm-booking")
def confirm_booking(request: BookingConfirmRequest):
    confirmation = agent.confirm_booking(request.session_id, request.draft_id, request.confirm)
    
    return {
        "status": confirmation.status.value,
        "message": confirmation.message,
        "order_ids": confirmation.order_ids,
        "reservation_ids": confirmation.reservation_ids
    }


@app.get("/api/conversation-state/{session_id}")
def get_conversation_state(session_id: str):
    state = agent.get_conversation_state(session_id)
    return {"session_id": session_id, "state": state}


if __name__ == "__main__":
    import uvicorn
    print("🚀 启动活动规划 Agent API 服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000)

