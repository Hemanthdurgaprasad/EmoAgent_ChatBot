# EmoAgent — AI Empathetic Mental Health Chatbot

Full-stack mental wellness chatbot using FastAPI + React + MongoDB.
Currently powered by Claude API. Swap to your fine-tuned Mistral 7B with one config change.

---

## Project Structure

```
emoagent/
├── backend/
│   ├── main.py                  # FastAPI app + MongoDB lifespan
│   ├── requirements.txt
│   ├── .env.example
│   ├── core/
│   │   ├── config.py            # All env vars + AI_PROVIDER switch
│   │   ├── security.py          # JWT + get_current_user dependency
│   │   └── ai_provider.py       # Claude now, Mistral later (one line swap)
│   ├── models/
│   │   ├── user.py              # Beanie User document
│   │   └── session.py           # Beanie ChatSession + Message documents
│   ├── routers/
│   │   ├── auth.py              # POST /register, POST /login
│   │   ├── chat.py              # POST /chat/stream (SSE)
│   │   └── history.py           # GET/DELETE /history/sessions
│   └── middleware/
│       └── safety.py            # Crisis detection + hotline injection
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx              # Auth guard routing
        ├── index.css            # DM Serif Display + warm sage palette
        ├── api/
        │   └── client.js        # All API calls + SSE stream consumer
        ├── hooks/
        │   └── useAuth.jsx      # Auth context + login/register/logout
        └── pages/
            ├── AuthPage.jsx     # Login + register UI
            └── ChatPage.jsx     # Sidebar + chat UI + streaming bubbles
```

---

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- MongoDB running locally (`mongod`)

### 1. Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
& .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at: http://localhost:5173

---

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | /api/auth/register | No | Create account |
| POST | /api/auth/login | No | Get JWT token |
| POST | /api/chat/stream | JWT | SSE streaming chat |
| GET | /api/history/sessions | JWT | List all sessions |
| GET | /api/history/sessions/:id | JWT | Get full session messages |
| DELETE | /api/history/sessions/:id | JWT | Delete a session |

---

## Swapping Claude → Mistral 7B (after fine-tuning)

**Step 1** — Export your LoRA adapter from Kaggle/Colab:
```python
model.save_pretrained("./adapter")
tokenizer.save_pretrained("./adapter")
```

**Step 2** — Copy the adapter folder into `backend/`:
```
backend/
└── adapter/
    ├── adapter_config.json
    ├── adapter_model.safetensors
    └── tokenizer files...
```

**Step 3** — Update `.env` (literally one line):
```env
AI_PROVIDER=mistral
# AI_PROVIDER=claude   ← comment this out
```

**Step 4** — Uncomment the Mistral packages in `requirements.txt` and reinstall:
```bash
pip install transformers peft bitsandbytes accelerate torch
```

**Step 5** — Restart the server. That's it.

The `core/ai_provider.py` file handles everything else. No other code changes needed.

---

## Safety Features

- **Crisis keyword detection** in `middleware/safety.py`
- Scans every user message before sending to AI
- If crisis language detected, prepends Indian helpline numbers:
  - iCall: 9152987821 (Mon–Sat 8am–10pm)
  - Vandrevala Foundation: 1860-2662-345 (24/7)
  - AASRA: 9820466627 (24/7)
- AI response still follows, with safety message first

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| MONGO_URI | mongodb://localhost:27017 | MongoDB connection string |
| DB_NAME | emoagent | Database name |
| SECRET_KEY | — | JWT signing secret (change this!) |
| AI_PROVIDER | claude | "claude" or "mistral" |
| ANTHROPIC_API_KEY | — | Your Claude API key |
| CLAUDE_MODEL | claude-sonnet-4-20250514 | Claude model version |
| MODEL_PATH | ./adapter | Path to LoRA adapter (Mistral only) |
