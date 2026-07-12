import React from "react";
import StructuredForm from "./StructuredForm";
import ChatPanel from "./ChatPanel";

export default function LogInteractionScreen() {
  return (
    <>
      <div className="screen-header">
        <div className="screen-eyebrow">HCP Module</div>
        <h1 className="screen-title">Log HCP Interaction</h1>
        <p className="screen-sub">
          Capture a visit, call, or email &mdash; via structured form or natural conversation.
        </p>
      </div>
      <div className="screen-body">
        <StructuredForm />
        <ChatPanel />
      </div>
    </>
  );
}
