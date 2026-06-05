# ResearchMind

ResearchMind is a production-grade agentic AI research assistant built with FastAPI, LangGraph, Groq, ChromaDB, HuggingFace local embeddings, Supabase-compatible SQL, Next.js 15, TypeScript, Tailwind, and shadcn-style UI components.

## Architecture

- Backend: FastAPI async API with service layer, repositories, rate limiting, structured JSON logging, and PDF export.
- Agents: LangGraph workflow with planner, web search, document intelligence, RAG retrieval, citation, and writer responsibilities.
- Inference: Groq chat completions through `GROQ_API_KEY`, with retries, timeout handling, and streaming support.
- Documents: PyMuPDF and pdfplumber extract PDF text, LangChain splitters chunk it, `BAAI/bge-small-en-v1.5` creates local embeddings, and ChromaDB stores vectors.
- Frontend: Next.js 15 App Router, TypeScript, Tailwind, dark mode, markdown rendering, code copy, upload, history, source and citation panels.
- Research Gap Detector: Multi-paper PDF analysis, theme synthesis, contradiction detection, gap inventory, innovation scoring, and React Flow knowledge graph visualization.
- Database: SQLAlchemy models match the Supabase schema in `supabase/schema.sql`.

## Folder Structure

```text
backend/
  app/
    agents/
    api/
    core/
    db/
    models/
    repositories/
    schemas/
    services/
    utils/
  Dockerfile
  requirements.txt
frontend/
  app/
  components/
  lib/
  Dockerfile
  package.json
supabase/
  schema.sql
docker-compose.yml
.env.example
```

## Local Setup

1. Copy environment variables:

```bash
cp .env.example .env
```

2. Add your free Groq API key:

```bash
GROQ_API_KEY=your_groq_key
```

3. Start the backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

4. Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

5. Open `http://localhost:3000`.

## Docker Compose

```bash
docker compose up --build
```

The frontend runs on `http://localhost:3000` and the backend on `http://localhost:8000`.

## Supabase Free Tier

1. Create a Supabase project.
2. Open SQL Editor.
3. Run `supabase/schema.sql`.
4. Use the connection pooler URI as `DATABASE_URL`, converted for SQLAlchemy async Postgres:

```text
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/postgres
```

5. Set `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_ROLE_KEY` in your backend environment.

SQLite is configured by default for local development so the app runs without paid services.

## Render Backend Deployment

1. Create a free Render Web Service from this repository.
2. Root directory: `backend`.
3. Environment: Docker.
4. Add environment variables from `.env.example`.
5. Set `DATABASE_URL` to Supabase Postgres or leave SQLite for ephemeral demos.
6. Deploy and copy the backend URL.

## Vercel Frontend Deployment

1. Import the repository into Vercel.
2. Root directory: `frontend`.
3. Add `NEXT_PUBLIC_API_URL` with your Render backend URL.
4. Deploy.

## API

- `POST /research` runs the full LangGraph research workflow.
- `POST /research/stream` streams a Groq response using server-sent events.
- `POST /upload` ingests PDF documents into ChromaDB.
- `GET /history` lists sessions.
- `GET /report/{report_id}` returns a report.
- `GET /report/{report_id}/pdf` exports a report PDF.
- `GET /citations/{session_id}` returns verified references.
- `POST /search` runs DuckDuckGo search.
- `POST /gap-detector/upload` uploads multiple papers for gap detection.
- `POST /gap-detector/analyze` runs the Research Gap Detector LangGraph workflow.
- `GET /gap-detector/history` lists prior gap analyses.
- `GET /gap-detector/{analysis_id}` returns a gap report with visualizations.
- `GET /gap-detector/{analysis_id}/pdf` exports the gap report.

## Notes

The app uses only free-tier compatible services. Groq, Supabase, Render, and Vercel all offer free tiers at the time this project was authored. ChromaDB and HuggingFace embeddings run locally in the backend container.
