# Product Requirement Document (PRD) - Lenny Growth Assistant

## 1. Problem
Product managers, founders, and growth operators want actionable advice grounded in actual industry experience rather than generic AI advice. Lenny's Podcast transcripts represent the gold standard of product strategy and growth advice. This application provides a conversational interface to explore this grounded knowledge, synthesize it into essays, and generate interactive artifacts.

## 2. Target User
- Product Managers (looking for specific frameworks and case studies)
- Startup Founders & Operators (looking for acquisition, retention, and monetization playbooks)
- Growth Marketers (looking for distribution strategy benchmarks)

## 3. User Stories
- As a user, I want to ask questions and receive answers strictly grounded in Lenny's Podcast transcripts so I do not get hallucinated advice.
- As a user, I want to generate Ship30for30-style essays on product management topics so I can quickly skim and share synthesized advice.
- As a user, I want to generate structured artifacts like HTML roadmaps, growth spreadsheets, and metrics calculators that render interactively.
- As a user, I want a sidebar containing my previous chat history so I can return to past conversations.

## 4. Technical Requirements
- FastAPI backend with SQLAlchemy and SQLite/Postgres.
- React frontend (Vite, Tailwind CSS, Lucide icons).
- Modular LLM service supporting Ollama (local), Anthropic, and OpenAI.
- SQLite vector database utilizing Cosine Similarity for RAG search.
- Interactive HTML and Markdown Artifact Viewer side-by-side with chat.
