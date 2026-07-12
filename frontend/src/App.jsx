import React from "react";
import LogInteractionScreen from "./components/LogInteractionScreen";

export default function App() {
  return (
    <div className="app-shell">
      <div className="topbar">
        <div className="topbar-brand">
          <span className="mark">AI</span>
          CRM &middot; HCP Module
        </div>
        <div className="topbar-crumb">
          Field Rep &middot; <strong>Log HCP Interaction</strong>
        </div>
      </div>
      <LogInteractionScreen />
    </div>
  );
}
