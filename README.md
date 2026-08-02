# Lenny Growth Assistant

An AI-powered conversational application grounded in Lenny's Podcast transcripts. Ask product management, growth, and startup execution questions strictly answered from Lenny's transcripts, write Ship30for30-style essays, and generate interactive HTML/CSS and Markdown artifacts side-by-side.

## 1. Project Overview & Features
- **ChatGPT-like UI/UX**: Polished chat, auto-scroll, sidebar session history, suggested prompts.
- **RAG Engine**: Pure Python SQLite-based vector storage implementing cosine similarity search.
- **Agentic Router**: Dynamic routing layer that classifies user questions and executes specialized skills.
- **Grounded Q&A**: Answers product/growth questions using cited podcast sources.
- **Ship30for30 Essays**: Long-form, skimmable essay synthesizer based on transcript insights.
- **Artifact Generator & Viewer**: Split-screen preview executing HTML/CSS code safely within sandboxed iframe containers.
- **Provider Abstraction**: Switch between local Ollama (local model), Anthropic, and OpenAI APIs.

## 2. Tech Stack
- **Backend**: FastAPI, SQLAlchemy, SQLite/Postgres, Alembic, Pydantic, httpx
- **Frontend**: React (Vite), Tailwind CSS (v4), react-router-dom, react-markdown, Lucide React

## 3. Prerequisites
- Python 3.10+
- Node.js 18+
- Git (optional, for manual cloning)

## 4. Setup Instructions

### Environment Variables
Configure `backend/.env` (using `backend/.env.example` as a template):
```env
ENVIRONMENT=development
DATABASE_URL=sqlite:///./lenny_growth_assistant.db
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Ingestion & Database Migration
1. Run database migrations:
   ```bash
   cd backend
   venv\Scripts\python -m alembic upgrade head
   ```
2. Run transcript ingestion:
   ```bash
   venv\Scripts\python -m app.utils.ingest
   ```

### Running Backend
```bash
cd backend
venv\Scripts\python -m uvicorn app.main:app --reload
```
API runs at `http://localhost:8000`. Health check: `http://localhost:8000/health`.

### Running Frontend
```bash
cd frontend
npm install
npm run dev
```
Client runs at `http://localhost:5173`.

## 5. Switchable Providers & Local Ollama Setup
1. Download Ollama from `https://ollama.com`.
2. Pull the configured model:
   ```bash
   ollama pull llama3
   ```
3. Update `LLM_PROVIDER=ollama` in `.env`.
