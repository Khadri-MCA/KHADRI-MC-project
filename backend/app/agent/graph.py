"""
LangGraph agent for the "Log HCP Interaction" screen.

Graph shape:

    START -> agent -> (conditional) -> tools -> agent -> ... -> END
                    -> (no tool call) -> END

The `agent` node is the Groq gemma2-9b-it model bound to the 5 tools. On each
turn it either replies directly (conversational chat interface requirement)
or emits one/more tool calls, which the `tools` node executes against the
Postgres/MySQL-backed CRM before looping back so the agent can compose a
natural-language reply grounded in the tool results.
"""
from urllib import response

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage, AIMessage

from app.agent.state import AgentState
from app.agent.tools import ALL_TOOLS
from app.agent.llm import get_primary_llm

SYSTEM_PROMPT = """You are the AI Assistant embedded in the "Log HCP Interaction" \
screen of a pharma CRM used by field sales reps. Your job is to help the rep \
log, edit, and enrich records of their interactions with Healthcare \
Professionals (HCPs) through natural conversation, as an alternative to the \
structured form.

Rules:
- When the rep describes a visit/call (free text or voice-note transcript), call log_interaction.
- When the rep wants to change something already logged, call edit_interaction.
- Use search_hcp to resolve ambiguous doctor names before logging.
- Use search_materials when brochures/samples are mentioned.
- After logging, proactively call suggest_follow_ups and present the suggestions.
- Always confirm briefly what was captured, in plain language a busy field rep can skim in 2 seconds.
- Never invent data you were not given; ask a brief clarifying question if the request is ambiguous.
"""


def build_agent_graph():
    llm = get_primary_llm().bind_tools(ALL_TOOLS)
    print(llm)

    def agent_node(state: AgentState):
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        response = llm.invoke(messages)
        print(response)
        return {"messages": [response]}

    def route(state: AgentState):
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            return "tools"
        return END

    tool_node = ToolNode(ALL_TOOLS)

    graph = StateGraph(AgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", tool_node)
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    return graph.compile()


# Compiled once at import time and reused across requests.
hcp_agent = build_agent_graph()
