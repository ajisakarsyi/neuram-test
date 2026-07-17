# Recruitment Assessment API

A FastAPI application that provides two features:
1. **CV/Resume PDF Summarization** — Upload a PDF resume and get structured JSON output (name, location, work experience) via an LLM on OpenRouter.
2. **News Search** — Search for recent news articles on any topic using the Tavily API.

---

## Tech Stack

| Component | Library |
|-----------|---------|
| Web framework | FastAPI + Uvicorn |
| PDF extraction | PyMuPDF (`fitz`) |
| HTTP client | `httpx` (async) |
| LLM integration | OpenRouter API (OpenAI-compatible) |
| News search | Tavily Search API |
| Containerization | Docker + Docker Compose |

---

## Prerequisites

- Python 3.11+ **or** Docker (for containerized run)
- An [OpenRouter](https://openrouter.ai/) API key (free tier available)
- A [Tavily](https://tavily.com/) API key (free tier available)

---

## Quick Start

### Option A — Run with Docker (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/ajisakarsyi/neuram-test.git
cd neuram-test

# 2. Set up environment variables
cp .env.example .env
# Edit .env and fill in your API keys

# 3. Build and start
docker-compose up --build

# API is now available at http://localhost:8000
```

### Option B — Run Locally with Python

```bash
# 1. Clone the repository
git clone https://github.com/ajisakarsyi/neuram-test.git
cd recruitment-api

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and fill in your API keys

# 5. Start the server
python run.py

# API is now available at http://localhost:8000
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free   # optional
TAVILY_API_KEY=your_tavily_api_key_here
```

### Getting API Keys

**OpenRouter** (for LLM):
1. Go to [https://openrouter.ai/](https://openrouter.ai/)
2. Sign up and go to **Keys** in your dashboard
3. Click **Create Key** — copy the key to `OPENROUTER_API_KEY`

**Tavily** (for news search):
1. Go to [https://tavily.com/](https://tavily.com/)
2. Sign up and go to your **API Keys** section
3. Copy the key to `TAVILY_API_KEY`

---

## API Endpoints

Once running, visit **http://localhost:8000/docs** for the interactive Swagger UI.

### `GET /`
Health check.

**Response:**
```json
{
  "status": "ok",
  "message": "Recruitment Assessment API is running.",
  "docs": "/docs"
}
```

---

### `POST /cv/upload`
Upload a CV/Resume PDF and receive a structured JSON summary.

**Request:** `multipart/form-data` with a `file` field (PDF only)

**Example with curl:**
```bash
curl -X POST "http://localhost:8000/cv/upload" \
  -H "accept: application/json" \
  -F "file=@/path/to/resume.pdf"
```

**Successful Response:**
```json
{
  "filename": "resume.pdf",
  "character_count": 4821,
  "summary": {
    "name": "Jane Doe",
    "location": "Jakarta, Indonesia",
    "work_experience_summary": "Jane has over 7 years of experience in software engineering..."
  }
}
```

**Error Responses:**
| Status | Reason |
|--------|--------|
| 400 | File is not a PDF, or file is empty |
| 422 | PDF has no extractable text (image-based PDF) |
| 500 | Missing `OPENROUTER_API_KEY` |
| 502 | OpenRouter API returned an error |
| 504 | OpenRouter API timed out |

---

### `GET /news/search`
Search for recent news articles on a topic.

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ | — | Topic to search (e.g., "AI developments") |
| `max_results` | int | ❌ | 5 | Number of articles (1–20) |

**Example with curl:**
```bash
curl "http://localhost:8000/news/search?query=AI+developments&max_results=5"
```

**Example with Python:**
```python
import httpx
response = httpx.get(
    "http://localhost:8000/news/search",
    params={"query": "Indonesia tech startup", "max_results": 3}
)
print(response.json())
```

**Successful Response:**
```json
{
  "query": "AI developments",
  "total_results": 5,
  "articles": [
    {
      "title": "OpenAI Announces New Model",
      "summary": "OpenAI has released a new generation of language models...",
      "url": "https://techcrunch.com/2025/07/17/openai-new-model",
      "published_date": "2025-07-17",
      "source": "techcrunch.com",
      "relevance_score": 0.9821
    }
  ]
}
```

---

## Project Structure

```
recruitment-api/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app + router registration
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── cv_router.py         # POST /cv/upload
│   │   └── news_router.py       # GET /news/search
│   └── services/
│       ├── __init__.py
│       ├── pdf_service.py       # PDF text extraction (PyMuPDF)
│       ├── llm_service.py       # OpenRouter LLM integration
│       └── tavily_service.py    # Tavily news search integration
├── .env.example                 # Environment variable template
├── .gitignore
├── docker-compose.yml           # One-command Docker deployment
├── Dockerfile                   # Container image definition
├── README.md
├── requirements.txt
└── run.py                       # App entry point
```

---

## Assumptions & Limitations

1. **PDF must be text-based** — Image-only PDFs (scanned documents without OCR) will return a 422 error since no text can be extracted. A future improvement would integrate an OCR library like `pytesseract`.

2. **LLM response format** — The LLM is prompted to return strict JSON. If the model misbehaves and returns free text instead, the API returns a 422 with the raw response for debugging.

3. **CV truncation** — CVs longer than ~12,000 characters (~3,000 tokens) are truncated before sending to the LLM to stay within free-tier token limits. This covers the vast majority of real-world CVs.

4. **OpenRouter free model** — The default model (`meta-llama/llama-3.1-8b-instruct:free`) is free but may have rate limits. Switch to a paid model via the `OPENROUTER_MODEL` env var for production use.

5. **Tavily `published_date`** — Some articles may return `null` for `published_date` if Tavily could not determine the publication date from the source page.

6. **No authentication** — This API has no auth layer. For production, add API key middleware or OAuth2.

---

## Running Tests (Manual)

After starting the server:

```bash
# Health check
curl http://localhost:8000/

# CV upload (replace with path to a real PDF)
curl -X POST "http://localhost:8000/cv/upload" -F "file=@resume.pdf"

# News search
curl "http://localhost:8000/news/search?query=machine+learning&max_results=3"
```
