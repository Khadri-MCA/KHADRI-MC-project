# AI-First CRM — HCP Module — Log Interaction Screen

A full-stack reference implementation matching the technical spec:
**React + Redux** frontend · **Python/FastAPI** backend · **LangGraph** agent
on **Groq** (`gemma2-9b-it` + `llama-3.3-70b-versatile` for context) ·
**PostgreSQL/MySQL** persistence (SQLite fallback for local/no-DB dev) ·
**Google Inter** throughout.

The Log Interaction screen offers both required entry paths side by side:
a **structured form** (left) and a **conversational AI Assistant** (right).
Either one can log or edit the same interaction record.

> ### Update — reliability fixes + redesign
> Fixed the "AI assistant not responding" issue, caused by a few
> compounding bugs:
> - The `/api/chat` endpoint always returned `interaction: null`, so even a
>   successful log never showed up anywhere in the UI.
> - Groq's models sometimes wrap JSON replies in ` ```json ` code fences,
>   which broke `json.loads()` and silently degraded to placeholder data.
>   Parsing is now fence-tolerant.
> - Neither the frontend nor backend had a request timeout, so a slow/hung
>   call to Groq just spun forever with no error. Both now fail fast (25s
>   backend, 35s frontend) with a clear message.
> - A failed agent call raised a raw, unhandled 500. It's now caught and
>   returned as a 502 with the actual cause (bad/missing `GROQ_API_KEY`, no
>   network route to `api.groq.com`, etc.) so you can actually diagnose it.
> - An interaction logged via chat now also populates the structured form
>   (HCP, sentiment, topics, outcomes, follow-ups), so both panels always
>   reflect the same record.
>
> **If the assistant still doesn't respond after these fixes**, it's almost
> always one of: (1) `GROQ_API_KEY` in `backend/.env` is missing/expired —
> get a fresh one at console.groq.com/keys, or (2) your network blocks
> `api.groq.com`. The error banner in the chat panel and the backend logs
> will now tell you which.

See **`PROJECT_ANALYSIS.md`** for the full architecture write-up, agent
design, and tool descriptions.

```
ai-crm-hcp-log-interaction/
├── PROJECT_ANALYSIS.md      ← full design + architecture doc
├── backend/                 ← FastAPI + LangGraph agent
│   ├── app/
│   │   ├── agent/           ← graph.py, tools.py, llm.py, state.py
│   │   ├── routers/         ← REST endpoints
│   │   ├── main.py
│   │   ├── models.py / schemas.py / database.py / config.py
│   ├── sql/schema.sql
│   ├── requirements.txt
│   └── .env.example
└── frontend/                 ← React + Redux Log Interaction screen
    ├── src/components/       ← StructuredForm, ChatPanel, etc.
    ├── src/store/             ← Redux Toolkit slice
    └── package.json
```

## 1. Backend setup

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env:
#   GROQ_API_KEY=<your key from https://console.groq.com/keys>
#   DATABASE_URL=<your Postgres or MySQL connection string>

# create the database first, e.g.:
#   createdb crm_hcp        (Postgres)
# then load the schema:
psql "$DATABASE_URL" -f sql/schema.sql       # or: mysql -u ... crm_hcp < sql/schema.sql

uvicorn app.main:app --reload --port 8000
```

API docs will be live at `http://localhost:8000/docs`.

> Tables are also auto-created via SQLAlchemy on startup if you skip the
> manual `schema.sql` load — but running it directly also seeds sample HCPs
> and materials, which is recommended for a working demo.

## 2. Frontend setup

```bash
cd frontend
npm install
npm start
```

Runs at `http://localhost:3000`. Set `REACT_APP_API_BASE` in a `.env` file
if your backend isn't on `localhost:8000`.

## 3. Try it

- **Structured form (left panel):** fill in HCP, type, topics, sentiment,
  materials — click **Log Interaction**.
- **AI Assistant (right panel):** type something like *"Met Dr. Sharma,
  discussed CardioPlus efficacy, she seemed positive, shared the brochure"*
  and watch the LangGraph agent call `log_interaction`, `search_materials`,
  and `suggest_follow_ups` on your behalf — the result also fills in the
  structured form on the left, since both panels write to the same record.
  Say *"change the sentiment to positive"* to see `edit_interaction` update
  it in place.

## Notes on the Groq models

- `gemma2-9b-it` — bound to all 5 tools, drives the main agent loop (fast,
  cheap, good tool-calling).
- `llama-3.3-70b-versatile` — used inside `log_interaction`,
  `edit_interaction`, and `suggest_follow_ups` for the heavier
  entity-extraction / reasoning pass on longer text.

Get a free API key at https://console.groq.com/keys.
