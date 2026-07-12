import React from "react";
import { useSelector } from "react-redux";

export default function SuggestedFollowUps() {
  const suggestions = useSelector((s) => s.interaction.suggestedFollowUps);
  if (!suggestions.length) return null;

  return (
    <div className="suggested-box">
      <div className="label">&#10022; AI Suggested Follow-Ups</div>
      <ul>
        {suggestions.map((s, i) => (
          <li key={i}>{s}</li>
        ))}
      </ul>
    </div>
  );
}
