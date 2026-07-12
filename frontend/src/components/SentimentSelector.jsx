import React from "react";
import { useDispatch } from "react-redux";
import { updateField } from "../store/interactionSlice";

const OPTIONS = ["Positive", "Neutral", "Negative"];

export default function SentimentSelector({ value }) {
  const dispatch = useDispatch();
  return (
    <div className="field">
      <label>Observed / Inferred HCP Sentiment</label>
      <div className="sentiment-scale">
        {OPTIONS.map((opt) => (
          <div
            key={opt}
            className={`sentiment-pill ${opt.toLowerCase()} ${value === opt ? "active" : ""}`}
            onClick={() => dispatch(updateField({ field: "sentiment", value: opt }))}
          >
            <span className="dot" />
            {opt}
          </div>
        ))}
      </div>
    </div>
  );
}
