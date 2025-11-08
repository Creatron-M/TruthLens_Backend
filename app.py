from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

from routers import api_router
from services import periodic_analysis, perform_analysis

def create_app() -> FastAPI:
    app = FastAPI(
        title="TruthLens Oracle API",
        description="AI-powered credibility and manipulation risk analysis for crypto prediction markets",
        version="1.0.0",
    )

    # Enable CORS for web frontend (configure properly for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount routers
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup_event():
        """Run initial analysis on startup and schedule periodic analysis."""
        print("🚀 TruthLens FastAPI Oracle starting...")
        # Kick off initial analysis without blocking
        asyncio.create_task(perform_analysis())
        # Schedule periodic analysis (every 30 minutes)
        asyncio.create_task(periodic_analysis())

    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
