"""
Entry point — loads .env and starts the FastAPI server with uvicorn.
"""

import os
from dotenv import load_dotenv
import uvicorn

# Load environment variables from .env file before starting the app
load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True during local development for hot-reload
    )
