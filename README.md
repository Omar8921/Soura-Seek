# Vector Lens

Image search and captioning with **FastAPI** + **SentenceTransformers**. Stores embeddings in **pgvector** (recommended) or as **float32 BLOBs**. Lightweight HTML/CSS/JS frontend.

## Features
- Upload an image → get a caption
- Search by **description** (text → embedding) or **image**
- Cosine similarity over stored embeddings
- Works with SQLite3 DB via BLOBs

## Stack
- Backend: FastAPI, SQLAlchemy, sentence-transformers (`all-MiniLM-L6-v2`)
- DB: PostgreSQL (+ `pgvector`) or SQLite (BLOB fallback)
- Frontend: vanilla HTML/CSS/JS (no build step)
