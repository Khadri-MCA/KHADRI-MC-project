-- ============================================================
-- AI-First CRM :: HCP Module Database Schema
-- Compatible with PostgreSQL and MySQL (minor type notes inline)
-- ============================================================

CREATE TABLE hcps (
    id              SERIAL PRIMARY KEY,               -- MySQL: INT AUTO_INCREMENT PRIMARY KEY
    name            VARCHAR(150) NOT NULL,
    specialty       VARCHAR(120),
    hospital        VARCHAR(180),
    email           VARCHAR(150),
    phone           VARCHAR(30),
    tier            VARCHAR(20) DEFAULT 'B',           -- A / B / C engagement tier
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE materials (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(180) NOT NULL,
    type            VARCHAR(40) NOT NULL,               -- brochure / leaflet / study / sample
    sku             VARCHAR(60),
    is_sample       BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interactions (
    id                  SERIAL PRIMARY KEY,
    hcp_id              INTEGER NOT NULL REFERENCES hcps(id),
    rep_id              INTEGER NOT NULL,               -- FK to a users/reps table (out of scope for this module)
    interaction_type    VARCHAR(30) NOT NULL,           -- Meeting / Call / Email / Conference
    interaction_date    DATE NOT NULL,
    interaction_time    TIME,
    attendees           TEXT,
    topics_discussed    TEXT,
    sentiment           VARCHAR(20),                    -- Positive / Neutral / Negative
    outcomes            TEXT,
    follow_up_actions   TEXT,
    ai_summary          TEXT,                           -- LLM-generated structured summary
    raw_source          VARCHAR(20) DEFAULT 'form',      -- form / chat / voice_note
    raw_transcript      TEXT,                            -- original free-text / voice note transcript
    status              VARCHAR(20) DEFAULT 'draft',      -- draft / logged / edited
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interaction_materials (
    id              SERIAL PRIMARY KEY,
    interaction_id  INTEGER NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    material_id     INTEGER NOT NULL REFERENCES materials(id),
    quantity        INTEGER DEFAULT 1
);

CREATE TABLE interaction_audit_log (
    id              SERIAL PRIMARY KEY,
    interaction_id  INTEGER NOT NULL REFERENCES interactions(id) ON DELETE CASCADE,
    action          VARCHAR(30) NOT NULL,               -- created / edited / follow_up_suggested
    tool_used       VARCHAR(60),                        -- LangGraph tool name that performed the action
    diff            TEXT,                                -- JSON diff of what changed
    performed_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_interactions_hcp ON interactions(hcp_id);
CREATE INDEX idx_interactions_date ON interactions(interaction_date);
CREATE INDEX idx_audit_interaction ON interaction_audit_log(interaction_id);

-- Seed sample reference data
INSERT INTO hcps (name, specialty, hospital, email, phone, tier) VALUES
('Dr. Aditi Sharma', 'Cardiology', 'Manipal Hospital, Bengaluru', 'aditi.sharma@example.com', '+91-9876500001', 'A'),
('Dr. Rohan Mehta', 'Endocrinology', 'Apollo Hospitals, Chennai', 'rohan.mehta@example.com', '+91-9876500002', 'B'),
('Dr. Neha Kapoor', 'Oncology', 'Fortis Hospital, Delhi', 'neha.kapoor@example.com', '+91-9876500003', 'A');

INSERT INTO materials (name, type, sku, is_sample) VALUES
('CardioPlus Efficacy Brochure', 'brochure', 'MAT-1001', FALSE),
('CardioPlus 10mg Sample Pack', 'sample', 'SMP-2001', TRUE),
('GlycoBalance Clinical Study Reprint', 'study', 'MAT-1002', FALSE),
('OncoRelief Patient Leaflet', 'leaflet', 'MAT-1003', FALSE);
