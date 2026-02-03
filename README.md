# Academic Researcher Discovery Platform

A production-grade Flask application that helps students and researchers discover professors worldwide whose work aligns with their interests. The platform ingests resumes or personal websites, refines interests using LLMs, searches open research sources, and ranks scholars based on semantic similarity and contextual signals.

## Features
- Resume + website ingestion with topic extraction
- Pluggable LLM adapters (Gemini, OpenAI, Groq, HuggingFace, Ollama)
- arXiv + Semantic Scholar discovery engine
- Researcher enrichment via web search and profile scraping (robots.txt compliant)
- Matching engine with sentence-transformers embeddings
- Cold email generator
- Research graph visualization
- Weekly alert system (local scheduler)
- Session storage (no API keys stored)
- Export to CSV/PDF

## Architecture (ASCII)
```
+------------------+     +----------------+     +----------------+
|  Flask UI Layer  | --> |  NLP Pipeline  | --> | Discovery APIs |
| (Jinja/Bootstrap)|     | (resume parse) |     | arXiv/S2/WEB   |
+------------------+     +----------------+     +----------------+
          |                        |                       |
          v                        v                       v
+------------------+     +----------------+     +----------------+
|  LLM Router      |     | Embedding/Rank |     | Scraper/Cache  |
| (Adapters)       |     | (Similarity)   |     | Robots + Rate  |
+------------------+     +----------------+     +----------------+
          |                        |                       |
          +------------------------+-----------------------+
                                   |
                                   v
                          +------------------+
                          | SQLite Sessions  |
                          +------------------+
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000`.

## Security & Privacy
- API keys are stored only in Flask session memory and never persisted.
- No analytics, tracking, or third-party logging.

## Example Data
See `example_data/sample_session.json` for a sample session structure.
