import React, { useState, useRef, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { pushUserMessage, sendChatMessage } from "../store/interactionSlice";

export default function ChatPanel() {
  const dispatch = useDispatch();
  const { messages, pending, connectionError } = useSelector((s) => s.interaction.chat);
  const [draft, setDraft] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  const send = () => {
    if (!draft.trim() || pending) return;
    dispatch(pushUserMessage(draft));
    dispatch(sendChatMessage(draft));
    setDraft("");
  };

  return (
    <div className="card assistant-panel">
      <div className="assistant-header">
        <div className="avatar">
          <span className="pulse" />
          AI
        </div>
        <div className="assistant-header-text">
          <div className="title">AI Assistant</div>
          <div className="sub">Log interaction via chat &middot; LangGraph agent</div>
        </div>
      </div>

      <div className="assistant-messages">
        {messages.map((m, i) => (
          <React.Fragment key={i}>
            {m.toolCalls && m.toolCalls.length > 0 && (
              <div className="msg-bubble tool">
                <span className="tool-icon">&#9881;</span>
                {m.toolCalls.join(" \u00b7 ")}
              </div>
            )}
            <div className={`msg-bubble ${m.role} ${m.isError ? "is-error" : ""}`}>
              {m.content}
            </div>
          </React.Fragment>
        ))}
        {pending && (
          <div className="msg-bubble assistant">
            <span className="typing-dots">
              <span /> <span /> <span />
            </span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {connectionError && (
        <div className="connection-banner">
          <strong>Connection issue:</strong> {connectionError}
        </div>
      )}

      <div className="assistant-composer">
        <input
          placeholder="Describe interaction..."
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={pending}
        />
        <button className="btn btn-primary" onClick={send} disabled={pending || !draft.trim()}>
          {pending ? "..." : "Log"}
        </button>
      </div>
    </div>
  );
}
