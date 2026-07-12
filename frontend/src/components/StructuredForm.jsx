import React from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  updateField,
  fetchHcpSuggestions,
  selectHcp,
  fetchMaterialSuggestions,
  addMaterial,
  removeMaterial,
  addSample,
  removeSample,
  saveInteraction,
} from "../store/interactionSlice";
import SentimentSelector from "./SentimentSelector";
import SuggestedFollowUps from "./SuggestedFollowUps";

export default function StructuredForm() {
  const dispatch = useDispatch();
  const { form, hcpSuggestions, materialSuggestions, saveStatus } = useSelector(
    (s) => s.interaction
  );

  const set = (field) => (e) =>
    dispatch(updateField({ field, value: e.target.value }));

  const onHcpInput = (e) => {
    dispatch(updateField({ field: "hcpName", value: e.target.value }));
    if (e.target.value.length > 1) dispatch(fetchHcpSuggestions(e.target.value));
  };

  const onMaterialInput = (e) => {
    if (e.target.value.length > 1) dispatch(fetchMaterialSuggestions(e.target.value));
  };

  return (
    <div className="card">
      <div className="card-header">
        <span className="dot" /> Interaction Details
      </div>
      <div className="card-body">
        <div className="field-row">
          <div className="field">
            <label>HCP Name</label>
            <input
              placeholder="Search or select HCP..."
              value={form.hcpName}
              onChange={onHcpInput}
            />
            {hcpSuggestions.length > 0 && (
              <div className="autocomplete-list">
                {hcpSuggestions.map((h) => (
                  <div
                    key={h.id}
                    className="autocomplete-item"
                    onClick={() => dispatch(selectHcp(h))}
                  >
                    {h.name}
                    <div className="meta">{h.specialty} &middot; {h.hospital}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="field">
            <label>Interaction Type</label>
            <select value={form.interactionType} onChange={set("interactionType")}>
              <option>Meeting</option>
              <option>Call</option>
              <option>Email</option>
              <option>Conference</option>
            </select>
          </div>
        </div>

        <div className="field-row">
          <div className="field">
            <label>Date</label>
            <input type="date" value={form.date} onChange={set("date")} />
          </div>
          <div className="field">
            <label>Time</label>
            <input type="time" value={form.time} onChange={set("time")} />
          </div>
        </div>

        <div className="field">
          <label>Attendees</label>
          <input
            placeholder="Enter names or search..."
            value={form.attendees}
            onChange={set("attendees")}
          />
        </div>

        <div className="field">
          <label>Topics Discussed</label>
          <textarea
            placeholder="Enter key discussion points..."
            value={form.topicsDiscussed}
            onChange={set("topicsDiscussed")}
          />
          <button className="hint-btn" type="button">
            &#127908; Summarize from Voice Note (Requires Consent)
          </button>
        </div>

        <div className="field">
          <label>Materials Shared</label>
          <div style={{ position: "relative" }}>
            <input
              placeholder="No materials added &mdash; search to add..."
              onChange={onMaterialInput}
            />
            {materialSuggestions.length > 0 && (
              <div className="autocomplete-list">
                {materialSuggestions.filter((m) => !m.is_sample).map((m) => (
                  <div
                    key={m.id}
                    className="autocomplete-item"
                    onClick={() => dispatch(addMaterial(m.name))}
                  >
                    {m.name}
                    <div className="meta">{m.type}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {form.materials.length > 0 && (
            <div className="chip-row">
              {form.materials.map((m) => (
                <span className="chip-tag" key={m}>
                  {m}
                  <button onClick={() => dispatch(removeMaterial(m))}>&times;</button>
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="field">
          <label>Samples Distributed</label>
          <div style={{ position: "relative" }}>
            <input
              placeholder="No samples added &mdash; search to add..."
              onChange={onMaterialInput}
            />
            {materialSuggestions.length > 0 && (
              <div className="autocomplete-list">
                {materialSuggestions.filter((m) => m.is_sample).map((m) => (
                  <div
                    key={m.id}
                    className="autocomplete-item"
                    onClick={() => dispatch(addSample(m.name))}
                  >
                    {m.name}
                    <div className="meta">Sample</div>
                  </div>
                ))}
              </div>
            )}
          </div>
          {form.samples.length > 0 && (
            <div className="chip-row">
              {form.samples.map((s) => (
                <span className="chip-tag" key={s}>
                  {s}
                  <button onClick={() => dispatch(removeSample(s))}>&times;</button>
                </span>
              ))}
            </div>
          )}
        </div>

        <SentimentSelector value={form.sentiment} />

        <div className="field">
          <label>Outcomes</label>
          <textarea
            placeholder="Key outcomes or agreements..."
            value={form.outcomes}
            onChange={set("outcomes")}
          />
        </div>

        <div className="field">
          <label>Follow-up Actions</label>
          <textarea
            placeholder="Enter next steps or tasks..."
            value={form.followUpActions}
            onChange={set("followUpActions")}
          />
        </div>

        <SuggestedFollowUps />

        <div className="submit-bar">
          <button className="btn btn-ghost" type="button">
            Save Draft
          </button>
          <button
            className="btn btn-primary"
            type="button"
            disabled={saveStatus === "saving" || !form.hcpName}
            onClick={() => dispatch(saveInteraction())}
          >
            {saveStatus === "saving"
              ? "Logging..."
              : saveStatus === "saved"
              ? "Logged \u2713"
              : "Log Interaction"}
          </button>
        </div>
      </div>
    </div>
  );
}
