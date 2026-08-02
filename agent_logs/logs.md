# Agent Execution Logs & Engineering Diary

This file documents failed implementation attempts, debugging steps, and optimizations made by the AI coding agent during the project's completion.

## Log Entry 1: Cosine Similarity Float Precision Failure
- **Issue**: Standard assertion in `test_cosine_similarity` compared exact floating point values (e.g. `assert cosine_similarity([1, 1], [1, 1]) == 1.0`). Pytest failed with: `assert 0.9999999999999998 == 1.0`.
- **Correction**: Replaced assertions to use `pytest.approx(1.0)` or threshold comparisons to handle floating point noise.

## Log Entry 2: Ingestion Pipeline Slow Down (Ollama Offline Timeouts)
- **Issue**: The ingestion task took ~4.4 seconds per chunk when Ollama was offline because it kept attempting HTTP requests to `localhost:11434` twice per chunk and waiting for connections to time out.
- **Correction**: Optimized `RAGService` by caching the offline state using a class-level flag `_ollama_offline = True` at the first connection failure. Subsequent chunks skip the Ollama connection attempts immediately, speeding up the offline index build from 15 minutes to under **48 seconds** for over 100 transcript files.
