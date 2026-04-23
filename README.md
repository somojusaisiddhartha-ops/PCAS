# Project Collision Avoidance System (PCAS) Backend

FastAPI backend for checking project originality by comparing uploaded project content or raw text against an existing dataset using NLP, TF-IDF vectorization, and cosine similarity.

## Features

- `POST /analyze` accepts:
  - `multipart/form-data` with a `file`
  - `application/json` with `title`, `abstract`, or `text`
- DOCX parsing for Word document uploads
- Text normalization and TF-IDF similarity scoring
- Top-N similar project matches
- Uniqueness score, risk classification, and explanation summary
- SQLite-backed dataset with in-memory vector cache for fast lookups
- Startup seeding from CSV sample dataset
- Logging and health check endpoint

## Folder Structure

```text
app/
  api/
  models/
  services/
  utils/
  main.py
data/
```

## Quick Start

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Copy the environment file:

```powershell
Copy-Item .env.example .env
```

3. Run the API:

```powershell
uvicorn app.main:app --reload
```

4. Open the docs:

- Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Health check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## API Usage

### 1. Analyze raw JSON text

**Request**

```http
POST /analyze
Content-Type: application/json
```

```json
{
  "title": "AI-powered crop monitoring",
  "abstract": "A machine learning system that detects crop disease from drone imagery.",
  "top_n": 5
}
```

### 2. Analyze Word document upload

Use `multipart/form-data`:

- `file`: DOCX
- `top_n`: optional integer from 1 to 10
- `title`: optional supplemental title
- `abstract`: optional supplemental abstract

### Example response

```json
{
  "uniqueness_score": 82.4,
  "risk_level": "Low",
  "summary": "Your project appears relatively unique. The highest overlap is 17.6% with existing records, which suggests low duplication risk.",
  "similar_projects": [
    {
      "title": "AI Chatbot for Student Support",
      "similarity": 17.6,
      "domain": "AI",
      "year": 2023
    }
  ],
  "analysis_meta": {
    "max_similarity": 17.6,
    "matched_projects": 5,
    "input_length": 109
  }
}
```

## Sample Dataset Format

CSV columns:

```csv
title,abstract,domain,year
AI Chatbot for Student Support,Conversational assistant for answering campus queries using NLP and retrieval,AI,2023
```

Replace `data/projects.csv` with your full project archive to improve results.

## Postman Testing

### JSON body

1. Create a `POST` request to `http://127.0.0.1:8000/analyze`
2. Set `Body -> raw -> JSON`
3. Paste:

```json
{
  "title": "Blockchain-powered supply tracking",
  "abstract": "A system to monitor logistics milestones using smart contracts.",
  "top_n": 5
}
```

### Word document upload

1. Create a `POST` request to `http://127.0.0.1:8000/analyze`
2. Set `Body -> form-data`
3. Add:
   - `file` as type `File`
   - `top_n` as type `Text`
   - `title` as type `Text` (optional)
   - `abstract` as type `Text` (optional)

## Notes

- The WhatsApp PDF files referenced in the request were not present at the provided paths in this environment, so I included a working sample dataset in `data/projects.csv`.
- The implementation is ready for swapping to PostgreSQL by changing `DATABASE_URL`.
- If you want better semantic matching later, add `sentence-transformers` and extend the vector service with embeddings.
- This build uses a pure-Python TF-IDF engine to avoid Windows/Python 3.14 native build issues that can occur with `scikit-learn` or `numpy` wheels.
