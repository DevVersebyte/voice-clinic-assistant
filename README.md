# City Care Clinic — Voice Appointment Assistant

A voice-first AI receptionist for booking, checking, rescheduling, and cancelling
doctor appointments, built with LiveKit Agents, Deepgram STT, an LLM for
understanding + tool-calling, and TTS for spoken responses. Backed by a real
Postgres (Neon) clinic schedule — the AI never invents availability.

## How it's built (architecture)

```
Patient's browser (React + LiveKit client)
        |  joins a LiveKit room (token from FastAPI backend)
        v
LiveKit Cloud (real-time audio transport)
        |
        v
LiveKit Agent (Python worker: agent/agent.py)
   mic audio -> VAD (Silero) -> STT (Deepgram) -> LLM (tool-calling) -> TTS -> speaker audio
   Turn detection + barge-in/interruption handled by the AgentSession.
   Noise cancellation applied to incoming mic audio (LiveKit BVC).
        |
        | LLM calls "tools" (agent/tools.py) instead of inventing data
        v
FastAPI backend (backend/app) -> Neon Postgres (doctors, slots, appointments)
```

Three separate processes run at once:
1. **backend** — FastAPI REST API + database (also mints LiveKit tokens)
2. **agent** — the LiveKit voice worker (this is what actually "answers the phone")
3. **frontend** — React page with the Start Call button

## 1. Set up the database

1. Create a free project at https://neon.com
2. Copy the connection string into `.env` as `DATABASE_URL`
3. Run `db/schema.sql` against it (Neon's SQL editor, or `psql "$DATABASE_URL" -f db/schema.sql`)
   — this also seeds 4 doctors and a week of open slots so you have real data to demo.

## 2. Set up accounts & fill in `.env`

Copy `.env.example` to `.env` in the project root and fill in:
- `LIVEKIT_URL`, `LIVEKIT_API_KEY`, `LIVEKIT_API_SECRET` — from cloud.livekit.io
- `DEEPGRAM_API_KEY` — from deepgram.com
- `CARTESIA_API_KEY` (or swap the TTS plugin in `agent/agent.py` for ElevenLabs/Sarvam)
- `OPENAI_API_KEY` — the LLM doing the understanding + tool-calling

Both `backend/` and `agent/` read from this same `.env` (via `python-dotenv`).
Copy it into both folders, or run everything from the repo root.

## 3. Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/health to confirm it's up, and http://localhost:8000/docs
for interactive API docs.

## 4. Run the voice agent

```bash
cd agent
pip install -r requirements.txt
python agent.py dev
```

This connects the worker to LiveKit and waits for a room to join.

## 5. Run the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, click **Start Call**, allow microphone access, and talk.

## Deployment

- **Frontend** → Vercel (`vercel deploy` inside `frontend/`, set `VITE_BACKEND_URL` env var)
- **Backend** → Render / Railway / Fly.io (needs to run persistently; set the same env vars)
- **Agent** → Render / Railway / Fly.io as a background worker (NOT serverless — it needs
  to stay running to accept jobs from LiveKit). `python agent.py start` for production mode.

## Language support

Currently: English, Hindi, Kannada. Deepgram's `nova-2` model with `language="multi"`
auto-detects across supported languages; the system prompt (`agent/prompts.py`)
instructs the LLM to reply in whichever language the patient used. Swap the TTS
voice per detected language for best results (see `agent/agent.py` TODO).

## Things still worth doing before submission

- [ ] Add a small "typing/thinking" or waveform indicator state in the frontend
- [ ] Pick and configure per-language TTS voices (one voice ID per language)
- [ ] Add basic logging/transcripts saved per call (nice for the Loom demo)
- [ ] Tighten CORS `allow_origins` to your deployed frontend URL
- [ ] Record the Loom: show VAD triggering, an interruption mid-sentence, a full
      booking, then a reschedule and a cancel, in at least two languages, and give
      a 60-second architecture walkthrough using the diagram above.
