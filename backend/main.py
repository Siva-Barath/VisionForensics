"""Application entry point — run with: uvicorn main:app --reload"""

from app import app
from app.config.settings import get_settings

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
