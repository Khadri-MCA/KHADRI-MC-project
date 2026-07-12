from typing import Annotated, Optional, List, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Shared state that flows through every node of the LangGraph."""
    messages: Annotated[list, add_messages]     # full chat history (HumanMessage/AIMessage/ToolMessage)
    interaction_id: Optional[int]                # set once an interaction has been logged/loaded
    hcp_id: Optional[int]
    session_id: str
    tool_calls_made: List[str]                   # audit trail of which tools fired this turn
