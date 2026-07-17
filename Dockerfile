# ============================================================
# Dockerfile — Recruitment Assessment API
# Python 3.12 slim base for a lean image
# ============================================================

FROM python:3.12-slim

# Metadata
LABEL maintainer="recruitment-assessment"
LABEL description="CV PDF Summarization + Tavily News Search API"

# Set working directory inside container
WORKDIR /app

# ---- System dependencies ----
# libgl1 is required by PyMuPDF for PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# ---- Python dependencies ----
# Copy requirements first for Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Application code ----
COPY . .

# Expose the API port
EXPOSE 8000

# Health check — verifies the API is up every 30 seconds
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/').raise_for_status()"

# Run the app (reads from .env file if present)
CMD ["python", "run.py"]
