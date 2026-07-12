"""
LangGraph Tools for the HCP "Log Interaction" agent.

Required by the task spec: a minimum of 5 sales-related tools, with
`log_interaction` and `edit_interaction` mandatory. Each tool is a plain
LangChain @tool so the agent's LLM (Groq gemma2-9b-it) can call it directly
via native tool-calling inside the LangGraph loop.
"""
import json
import re
from datetime import datetime

from langchain_core.tools import tool
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import HCP, Material, Interaction, InteractionMaterial, InteractionAuditLog
from app.agent.llm import get_context_llm


def _db() -> Session:
    return SessionLocal()


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def _extract_json(raw: str):
    """Open-weight Groq models frequently wrap JSON in ```json fences or add a
    stray sentence before/after it. Strip fences, then fall back to grabbing
    the first {...} or [...] block so a single formatting quirk doesn't kill
    the whole extraction (this was a real cause of the AI assistant appearing
    to 'not respond' / silently falling back to empty fields)."""
    if not isinstance(raw, str):
        raise ValueError("empty response")
    text = _FENCE_RE.sub("", raw).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))
    raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]!r}")


# ---------------------------------------------------------------------------
# Tool 1 (mandatory) — log_interaction
# ---------------------------------------------------------------------------
@tool
def log_interaction(
    hcp_name: str,
    interaction_type: str,
    raw_notes: str,
    interaction_date: str = "",
) -> str:
    """Create a new HCP interaction log entry.

    Use this when the rep describes a visit/call/email either as free text or
    a voice-note transcript (e.g. "Met Dr. Sharma, discussed CardioPlus
    efficacy, positive sentiment, shared brochure"). This tool sends the raw
    text to the LLM for entity extraction (topics, sentiment, outcomes) and
    then persists a structured interaction record.

    Args:
        hcp_name: Name of the healthcare professional visited/contacted.
        interaction_type: One of Meeting, Call, Email, Conference.
        raw_notes: The rep's free-text description or voice-note transcript.
        interaction_date: ISO date (YYYY-MM-DD). Defaults to today if blank.
    """
    db = _db()
    try:
        hcp = db.query(HCP).filter(HCP.name.ilike(f"%{hcp_name}%")).first()
        if not hcp:
            hcp = HCP(name=hcp_name, tier="B")
            db.add(hcp)
            db.commit()
            db.refresh(hcp)

        # LLM entity extraction / summarization from raw notes
        extractor = get_context_llm(temperature=0.1)
        prompt = (
            "Extract structured fields from this HCP interaction note as strict JSON "
            'with keys: topics_discussed, sentiment (Positive/Neutral/Negative), '
            'outcomes, follow_up_actions, summary. '
            "Respond with raw JSON only \u2014 no markdown fences, no commentary. "
            f"Note: {raw_notes}"
        )
        extracted = {}
        try:
            resp = extractor.invoke(prompt)
            extracted = _extract_json(resp.content)
        except Exception:
            extracted = {
                "topics_discussed": raw_notes,
                "sentiment": "Neutral",
                "outcomes": "",
                "follow_up_actions": "",
                "summary": raw_notes[:280],
            }

        def ensure_json_list(value):
            if value is None:
                return ""
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            if isinstance(value, str):
                return value
            return str(value)

        interaction = Interaction(
            hcp_id=hcp.id,
            rep_id=1,
            interaction_type=interaction_type,
            interaction_date=(
                datetime.fromisoformat(interaction_date).date()
                if interaction_date
                else datetime.utcnow().date()
            ),
            topics_discussed=ensure_json_list(extracted.get("topics_discussed")),
            sentiment=extracted.get("sentiment", "Neutral"),
            outcomes=ensure_json_list(extracted.get("outcomes")),
            follow_up_actions=ensure_json_list(extracted.get("follow_up_actions")),
            ai_summary=extracted.get("summary"),
            raw_source="chat",
            raw_transcript=raw_notes,
            status="logged",
        )



        db.add(interaction)
        db.commit()
        db.refresh(interaction)

        db.add(InteractionAuditLog(
            interaction_id=interaction.id,
            action="created",
            tool_used="log_interaction",
            diff=json.dumps(extracted),
        ))
        db.commit()

        return json.dumps({
            "status": "ok",
            "interaction_id": interaction.id,
            "hcp_id": hcp.id,
            "summary": interaction.ai_summary,
            "sentiment": interaction.sentiment,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 2 (mandatory) — edit_interaction
# ---------------------------------------------------------------------------
@tool
def edit_interaction(interaction_id: int, edit_instruction: str) -> str:
    """Modify a previously logged interaction using a natural-language instruction.

    Use this when the rep wants to correct or update an existing log, e.g.
    "change the sentiment to positive" or "add that Dr. Mehta also asked for
    a dosage chart". The LLM interprets the instruction and produces a JSON
    patch of only the fields that should change; every edit is written to the
    audit log so nothing is silently overwritten.

    Args:
        interaction_id: The ID of the interaction to edit.
        edit_instruction: Natural-language description of the desired change.
    """
    db = _db()
    try:
        interaction = db.query(Interaction).get(interaction_id)
        if not interaction:
            return json.dumps({"status": "error", "message": "Interaction not found"})

        editor = get_context_llm(temperature=0.1)
        current_state = {
            "topics_discussed": interaction.topics_discussed,
            "sentiment": interaction.sentiment,
            "outcomes": interaction.outcomes,
            "follow_up_actions": interaction.follow_up_actions,
        }
        prompt = (
            "You are editing a CRM interaction record. Given the current JSON "
            "state and an edit instruction, return ONLY a JSON object containing "
            "the fields that need to change (a partial patch), same keys as input.\n"
            f"Current state: {json.dumps(current_state)}\n"
            f"Edit instruction: {edit_instruction}\n"
            "Respond with raw JSON only \u2014 no markdown fences, no commentary."
        )
        patch = {}
        try:
            resp = editor.invoke(prompt)
            patch = _extract_json(resp.content)
        except Exception:
            return json.dumps({"status": "error", "message": "Could not parse edit"})

        before = dict(current_state)
        for key, value in patch.items():
            if hasattr(interaction, key) and value is not None:
                setattr(interaction, key, value)
        interaction.status = "edited"
        interaction.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(interaction)

        db.add(InteractionAuditLog(
            interaction_id=interaction.id,
            action="edited",
            tool_used="edit_interaction",
            diff=json.dumps({"before": before, "after": patch}),
        ))
        db.commit()

        return json.dumps({"status": "ok", "interaction_id": interaction.id, "changed_fields": list(patch.keys())})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 3 — search_hcp
# ---------------------------------------------------------------------------
@tool
def search_hcp(query: str) -> str:
    """Search the HCP directory by name, specialty, or hospital.

    Use this to resolve which doctor the rep means, or to autocomplete the
    "HCP Name" field in the structured form.

    Args:
        query: Partial name, specialty, or hospital to search for.
    """
    db = _db()
    try:
        results = db.query(HCP).filter(
            (HCP.name.ilike(f"%{query}%")) |
            (HCP.specialty.ilike(f"%{query}%")) |
            (HCP.hospital.ilike(f"%{query}%"))
        ).limit(5).all()
        return json.dumps([
            {"id": h.id, "name": h.name, "specialty": h.specialty, "hospital": h.hospital, "tier": h.tier}
            for h in results
        ])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 4 — search_materials
# ---------------------------------------------------------------------------
@tool
def search_materials(query: str, interaction_id: int = 0) -> str:
    """Search marketing materials / samples and optionally attach them to an interaction.

    Use this when the rep says which brochures, leaflets, studies, or drug
    samples were shared/distributed during the visit.

    Args:
        query: Material or sample name/keyword to search for.
        interaction_id: If > 0, the matched materials are attached to this interaction.
    """
    db = _db()
    try:
        results = db.query(Material).filter(Material.name.ilike(f"%{query}%")).limit(5).all()
        if interaction_id:
            for m in results:
                db.add(InteractionMaterial(interaction_id=interaction_id, material_id=m.id, quantity=1))
            db.commit()
        return json.dumps([
            {"id": m.id, "name": m.name, "type": m.type, "is_sample": m.is_sample}
            for m in results
        ])
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Tool 5 — suggest_follow_ups
# ---------------------------------------------------------------------------
@tool
def suggest_follow_ups(interaction_id: int) -> str:
    """Generate AI-suggested next-best-actions for a logged interaction.

    Uses the LLM to read the topics, sentiment, and outcomes of an interaction
    and propose 2-4 concrete follow-up actions (e.g. "Schedule follow-up
    meeting in 2 weeks", "Send dosage chart PDF").

    Args:
        interaction_id: The ID of the interaction to generate follow-ups for.
    """
    db = _db()
    try:
        interaction = db.query(Interaction).get(interaction_id)
        if not interaction:
            return json.dumps({"status": "error", "message": "Interaction not found"})

        llm = get_context_llm(temperature=0.4)
        prompt = (
            "Based on this HCP interaction, suggest 2-4 short, concrete "
            "follow-up actions for the sales rep. Return ONLY a JSON array of strings.\n"
            f"Topics: {interaction.topics_discussed}\n"
            f"Sentiment: {interaction.sentiment}\n"
            f"Outcomes: {interaction.outcomes}\n"
            "Respond with a raw JSON array only \u2014 no markdown fences, no commentary."
        )
        try:
            resp = llm.invoke(prompt)
            suggestions = _extract_json(resp.content)
        except Exception:
            suggestions = ["Schedule a follow-up meeting in 2 weeks", "Send requested materials"]

        interaction.follow_up_actions = "; ".join(suggestions)
        db.commit()

        db.add(InteractionAuditLog(
            interaction_id=interaction.id,
            action="follow_up_suggested",
            tool_used="suggest_follow_ups",
            diff=json.dumps(suggestions),
        ))
        db.commit()

        return json.dumps({"status": "ok", "suggestions": suggestions})
    finally:
        db.close()


ALL_TOOLS = [log_interaction, edit_interaction, search_hcp, search_materials, suggest_follow_ups]
