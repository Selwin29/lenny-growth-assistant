# Lenny Growth Assistant

An AI-powered conversational growth and product management assistant strictly grounded in **Lenny's Podcast** transcripts. Ask product management, growth, and startup execution questions answered from real transcripts, generate long-form Ship30for30-style essays, and generate/render interactive HTML/CSS and Markdown artifacts in a split-screen container.

---

## 1. Project Overview & Key Features

* **ChatGPT-Style UI/UX**: Responsive interface with message history, active mode tabs, live LLM provider selector, sidebar session management, and suggested prompts.
* **Transcript-Grounded RAG**: SQLite vector store storing transcript chunks and embeddings with cosine similarity search.
* **AgentRouter Architecture**: Fast-path keyword router + explicit UI mode selection + LLM fallback classifier for ambiguous requests.
* **3 Dedicated Execution Modes**:
  1. **Chat Mode**: Transcript-grounded Q&A with strict speaker attribution and real source citations.
  2. **Artifacts Mode**: Structured HTML/CSS and Markdown artifact generation rendered inside a sandboxed iframe preview.
  3. **Ship30for30 Mode**: Synthesizes long-form (~1250 words), highly skimmable essays based on podcast transcript insights.
* **Live LLM Provider Switching**: Switch between **Google Gemini**, **Anthropic Claude**, and local **Ollama** models directly from the top navigation bar without reloading the app or resetting chat sessions.
* **Hosted Database**: Supabase PostgreSQL database integration powered by SQLAlchemy 2.0 and Alembic migrations.
* **Anti-Hallucination Protection**: Refuses to answer out-of-scope questions (e.g. quantum computing) when relevant transcript evidence is missing.

---

## 2. Modes of Operation

### 💬 Chat Mode (Grounded Q&A)
* Answers product and growth queries using retrieved transcript passages (`top_k=3`, `RAG_CHUNK_WORD_LIMIT=300`).
* **Strict Speaker Attribution**: Distinguishes between **Lenny Rachitsky** (the host) and **podcast guests** (interviewees).
* When guest advice is present for questions asking what Lenny says, the assistant explicitly states:
  > *"The available transcripts don't contain a direct statement from Lenny on this specific question. However, related podcast guests discuss this topic in these ways:"*
* Every answer contains deduplicated episode title and episode ID citations.

### 🎨 Artifacts Mode
* Generates full, self-contained HTML/CSS templates, dashboards, and markdown documents.
* **ArtifactViewer**: Renders HTML/CSS artifacts side-by-side in a sandboxed iframe container for safe live interaction.

### ✍️ Ship30for30 Mode
* Generates structured, skimmable essays (~1250 words) with attention-grabbing hooks, bolded key terms, short paragraphs, and actionable takeaways grounded in transcript evidence.

---

## 3. LLM Provider Switching

The top navigation bar features a dynamic provider selector pill tabs: `LLM: [ Gemini ] [ Anthropic ] [ Ollama ]`.

* **Gemini**: Targets Google Gemini REST API (`gemini-1.5-flash`). Maps max tokens to `maxOutputTokens`.
* **Anthropic**: Targets Anthropic Claude API (`claude-3-5-sonnet-20241022`). Maps max tokens to `max_tokens`.
* **Ollama**: Targets local Ollama instance (`llama3.1:8b`). Maps max tokens to `num_predict`.

Evaluators and testers can configure their own Gemini or Anthropic API keys via `backend/.env`. Switching providers is zero-reload and preserves chat state.

---

## 4. Tech Stack

* **Backend**: FastAPI, Python 3.10+, SQLAlchemy 2.0, Alembic, PostgreSQL (`psycopg2`), SQLite (Vector Store), `httpx`, Pydantic v2.
* **Frontend**: React 18, Vite, Tailwind CSS, Lucide React, `react-router-dom`, `axios`.
* **Database**: Hosted Supabase PostgreSQL.

---

## 5. Environment Configuration

Create a `backend/.env` file based on `backend/.env.example`.

> [!IMPORTANT]
> **Never commit `backend/.env` or expose API keys/database credentials.**

### Safe Example Configuration (`backend/.env`)

```env
ENVIRONMENT=development

# Database Connection (Supabase PostgreSQL)
DATABASE_URL=postgresql+psycopg2://postgres:<PASSWORD>@<SUPABASE_HOST>:5432/postgres

# Active Default Provider
LLM_PROVIDER=gemini

# Google Gemini Configuration
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
GEMINI_MODEL=gemini-1.5-flash

# Anthropic Configuration
ANTHROPIC_API_KEY=<YOUR_ANTHROPIC_API_KEY>
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Local Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# RAG Configuration
RAG_CHUNK_WORD_LIMIT=300
```

---

## 6. Setup & Installation Instructions

### Prerequisites
* Python 3.10+
* Node.js 18+
* Ollama (optional, for local model testing)

### 1. Backend Setup

```powershell
# Navigate to backend directory
cd backend

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Migrations

Run Alembic migrations to initialize tables in Supabase PostgreSQL:

```powershell
venv\Scripts\python -m alembic upgrade head
```

### 3. Transcript Ingestion (RAG Vector Store)

Ingest podcast transcripts into the local vector store (`lenny_vector_store.db`):

```powershell
venv\Scripts\python -m app.utils.ingest
```

### 4. Run Backend Server

```powershell
venv\Scripts\python -m uvicorn app.main:app --reload
```
* Backend API: `http://localhost:8000`
* Health Check: `http://localhost:8000/health`

### 5. Frontend Setup

```powershell
# Open a new terminal in frontend directory
cd frontend

# Install Node packages
npm install

# Start Vite development server
npm run dev
```
* Frontend Application: `http://localhost:5173`

---

## 7. Ollama Setup (Local LLM)

To run locally with Ollama:

1. Install Ollama from [https://ollama.com](https://ollama.com).
2. Pull the configured `llama3.1:8b` model:
   ```powershell
   ollama pull llama3.1:8b
   ```
3. Set `LLM_PROVIDER=ollama` in `backend/.env` or select **Ollama** in the UI header.

---

## 8. Automated Testing & Build Verification

### Run Backend Unit Tests

```powershell
cd backend
venv\Scripts\python -m pytest app/tests -v
```
* **Verified Result**: `37 passed` (100% pass rate).

### Build Frontend Production Bundle

```powershell
cd frontend
npm run build
```
* **Verified Result**: Clean Vite build.

---

## 9. Demo Prompts

Try these suggested prompts to verify all features:

1. **Grounded Q&A (Speaker Attribution)**:
   > *"What does Lenny say about finding product-market fit?"*
   * *Verifies speaker distinction between Lenny and podcast guests.*

2. **Growth Lessons**:
   > *"What are the most important lessons about product growth from Lenny's podcast?"*
   * *Verifies top-k RAG retrieval with source citations.*

3. **Artifact Generation**:
   > *"Create an HTML growth experiment dashboard template with CSS styling."*
   * *Verifies Artifacts mode and iframe ArtifactViewer preview.*

4. **Ship30for30 Essay**:
   > *"Write a Ship30for30-style essay on metrics that actually matter for product managers."*
   * *Verifies long-form essay synthesis skill.*

5. **Anti-Hallucination Test**:
   > *"What does Lenny's podcast say about quantum computing?"*
   * *Verifies that the assistant explicitly refuses to answer when transcript evidence is missing.*

---

## 10. Security & Privacy

* `backend/.env` is local-only and listed in `.gitignore`.
* Private API keys (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) and database credentials are never logged, committed, or exposed to the React frontend.
* Provider validation restricts requests to an approved allowlist (`{"ollama", "gemini", "anthropic"}`).

---

## 11. Repository Project Structure

```
lenny-growth-assistant/
├── backend/
│   ├── alembic/              # Database migration scripts & env.py
│   ├── app/
│   │   ├── agents/           # AgentRouter & skill modules (qa, essay, artifact)
│   │   ├── api/              # FastAPI route handlers (auth, chat, health)
│   │   ├── core/             # Configuration & security settings
│   │   ├── database/         # SQLAlchemy session setup
│   │   ├── models/           # SQLAlchemy DB models (User, ChatSession, Message, Artifact)
│   │   ├── schemas/          # Pydantic validation schemas
│   │   ├── services/         # LLM service, RAG vector store, message services
│   │   ├── tests/            # Pytest test suite (37 tests)
│   │   ├── utils/            # Ingestion script (ingest.py)
│   │   └── main.py           # FastAPI entrypoint
│   ├── .env.example          # Safe environment template
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/       # UI Components (Navbar, Sidebar, ChatBox, ArtifactViewer)
│   │   ├── context/          # React AuthContext
│   │   ├── pages/            # React pages (Chat, Login, Register)
│   │   ├── services/         # Axios API clients (chatService, authService)
│   │   └── App.jsx           # Root application router
│   ├── package.json          # Frontend dependencies
│   └── vite.config.js        # Vite configuration
└── README.md                 # Project documentation
```

---

## 12. Verification Status Summary

* **Backend Pytest**: `37 passed in 6.22s`.
* **Frontend Vite Build**: Clean build.
* **Database**: Supabase PostgreSQL + SQLAlchemy 2.0 + Alembic.
* **LLM Providers**: Gemini (`gemini-1.5-flash`), Anthropic (`claude-3-5-sonnet-20241022`), Ollama (`llama3.1:8b`).
* **Modes**: Chat (Grounded Q&A), Artifacts (HTML/CSS), Ship30for30 (Essays).
* **Grounding & Citations**: Intact with guest vs host attribution & anti-hallucination refusal.
