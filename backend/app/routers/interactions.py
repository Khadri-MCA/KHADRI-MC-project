from typing import List
import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from app.database import get_db, SessionLocal
from app import models, schemas
from app.agent.graph import hcp_agent

router = APIRouter()
logger = logging.getLogger("hcp_crm.chat")

# In-memory chat session store (swap for Redis in production)
_SESSIONS: dict[str, list] = {}


def _with_hcp_name(interaction: models.Interaction) -> models.Interaction:
    """Attach the HCP's display name onto the ORM object so InteractionOut
    (which has no hcp_name column of its own) can serialize it."""
    if interaction is not None:
        interaction.hcp_name = interaction.hcp.name if interaction.hcp else None
    return interaction


@router.get("/hcps", response_model=List[schemas.HCPOut])
def list_hcps(q: str = "", db: Session = Depends(get_db)):
    query = db.query(models.HCP)
    if q:
        query = query.filter(models.HCP.name.ilike(f"%{q}%"))
    return query.limit(20).all()


@router.get("/materials", response_model=List[schemas.MaterialOut])
def list_materials(q: str = "", db: Session = Depends(get_db)):
    query = db.query(models.Material)
    if q:
        query = query.filter(models.Material.name.ilike(f"%{q}%"))
    return query.limit(20).all()


@router.post("/interactions", response_model=schemas.InteractionOut)
def create_interaction_form(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """Structured-form submission path (non-chat)."""
    hcp = None
    if payload.hcp_id:
        hcp = db.query(models.HCP).get(payload.hcp_id)
    elif payload.hcp_name:
        hcp = db.query(models.HCP).filter(models.HCP.name.ilike(f"%{payload.hcp_name}%")).first()
        if not hcp:
            hcp = models.HCP(name=payload.hcp_name)
            db.add(hcp)
            db.commit()
            db.refresh(hcp)
    if not hcp:
        raise HTTPException(400, "hcp_id or hcp_name is required")

    interaction = models.Interaction(
        hcp_id=hcp.id,
        rep_id=1,
        interaction_type=payload.interaction_type,
        interaction_date=payload.interaction_date,
        interaction_time=payload.interaction_time,
        attendees=payload.attendees,
        topics_discussed=payload.topics_discussed,
        sentiment=payload.sentiment,
        outcomes=payload.outcomes,
        follow_up_actions=payload.follow_up_actions,
        raw_source=payload.raw_source,
        raw_transcript=payload.raw_transcript,
        status="logged",
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    db.add(models.InteractionAuditLog(
        interaction_id=interaction.id, action="created", tool_used="structured_form",
    ))
    db.commit()
    return _with_hcp_name(interaction)


@router.get("/interactions/{interaction_id}", response_model=schemas.InteractionOut)
def get_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).get(interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    return _with_hcp_name(interaction)


@router.patch("/interactions/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction_form(interaction_id: int, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    """Structured-form edit path (non-chat)."""
    interaction = db.query(models.Interaction).get(interaction_id)
    if not interaction:
        raise HTTPException(404, "Interaction not found")

    for field, value in payload.model_dump(exclude_unset=True, exclude={"edit_instruction"}).items():
        setattr(interaction, field, value)
    interaction.status = "edited"
    db.commit()
    db.refresh(interaction)

    db.add(models.InteractionAuditLog(
        interaction_id=interaction.id, action="edited", tool_used="structured_form",
    ))
    db.commit()
    return _with_hcp_name(interaction)


@router.post("/chat", response_model=schemas.ChatResponse)
def chat_with_agent(payload: schemas.ChatMessage):
    """Conversational logging path — routes through the LangGraph agent.

    This is the ONLY way interactions get created/edited in the AI-only
    flow: every field the rep would otherwise have typed by hand is
    extracted by the agent's tools and written straight to the database,
    then echoed back here so the UI can render a live, read-only record.
    """
    history = _SESSIONS.setdefault(payload.session_id, [])
    history.append(HumanMessage(content=payload.message))

    try:
        result = hcp_agent.invoke({
            "messages": history,
            "interaction_id": payload.interaction_id,
            "hcp_id": None,
            "session_id": payload.session_id,
            "tool_calls_made": [],
        })


        from langchain_core.messages import ToolMessage

        print("=" * 80)

        for m in result["messages"]:
            print(type(m).__name__)

        print("=" * 80)

        for m in result["messages"]:
            if isinstance(m, ToolMessage):
                print("TOOL:", m.name)
                print(m.content)

        print("=" * 80)
    except Exception as e:
        import traceback

        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"{type(e).__name__}: {e}",
        )

    _SESSIONS[payload.session_id] = result["messages"]

    tool_calls: List[str] = [
        m.name for m in result["messages"] if isinstance(m, ToolMessage)
    ]

    # Pull the interaction id and any follow-up suggestions straight out of
    # the tool results so the UI can render the AI-filled record without the
    # rep ever typing into a form.
    interaction_id = payload.interaction_id
    suggested_follow_ups: List[str] = []
    for m in result["messages"]:
        if not isinstance(m, ToolMessage):
            continue
        try:
            data = json.loads(m.content)
        except (TypeError, ValueError):
            continue
        if m.name in ("log_interaction", "edit_interaction") and isinstance(data, dict):
            if data.get("status") == "ok" and data.get("interaction_id"):
                interaction_id = data["interaction_id"]
        if m.name == "suggest_follow_ups" and isinstance(data, dict):
            suggested_follow_ups = data.get("suggestions", [])

    interaction_out = None
    if interaction_id:
        db = SessionLocal()
        try:
            interaction_out = db.query(models.Interaction).get(interaction_id)
            if interaction_out:
                _with_hcp_name(interaction_out)
                db.expunge(interaction_out)
        finally:
            db.close()

    final_ai_message = next(
        (m for m in reversed(result["messages"]) if isinstance(m, AIMessage) and m.content), None
    )

    return schemas.ChatResponse(
        reply=final_ai_message.content if final_ai_message else "Got it.",
        tool_calls=tool_calls,
        interaction=interaction_out,
        suggested_follow_ups=suggested_follow_ups,
    )
