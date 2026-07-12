from datetime import date, time, datetime
from typing import Optional, List

from pydantic import BaseModel


class HCPOut(BaseModel):
    id: int
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None
    tier: Optional[str] = None

    class Config:
        from_attributes = True


class MaterialOut(BaseModel):
    id: int
    name: str
    type: str
    is_sample: bool

    class Config:
        from_attributes = True


class InteractionCreate(BaseModel):
    hcp_id: Optional[int] = None
    hcp_name: Optional[str] = None            # allows free-text HCP entry; agent resolves/creates
    interaction_type: str
    interaction_date: date
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    materials: Optional[List[str]] = None
    samples: Optional[List[str]] = None
    raw_source: str = "form"
    raw_transcript: Optional[str] = None


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    interaction_date: Optional[date] = None
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    edit_instruction: Optional[str] = None    # natural-language edit, e.g. "change sentiment to positive"


class InteractionOut(BaseModel):
    id: int
    hcp_id: int
    hcp_name: Optional[str] = None
    interaction_type: str
    interaction_date: date
    interaction_time: Optional[time] = None
    attendees: Optional[str] = None
    topics_discussed: Optional[str] = None
    sentiment: Optional[str] = None
    outcomes: Optional[str] = None
    follow_up_actions: Optional[str] = None
    ai_summary: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    session_id: str
    message: str
    interaction_id: Optional[int] = None      # set when continuing/editing an existing log


class ChatResponse(BaseModel):
    reply: str
    tool_calls: List[str] = []
    interaction: Optional[InteractionOut] = None
    suggested_follow_ups: List[str] = []
