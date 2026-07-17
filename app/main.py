"""
Recruitment Technical Assessment - Main FastAPI Application
Handles PDF CV processing and Tavily news search endpoints.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.routers import cv_router, news_router

# Initialize FastAPI app
app = FastAPI(
    title="Recruitment Assessment API",
    description=(
        "API for CV/Resume PDF summarization using LLM "
        "and news search using Tavily."
    ),
    version="1.0.0",
)

# Allow all origins for assessment purposes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(cv_router.router, prefix="/cv", tags=["CV Processing"])
app.include_router(news_router.router, prefix="/news", tags=["News Search"])


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "ok",
        "message": "Recruitment Assessment API is running.",
        "docs": "/docs",
    }
