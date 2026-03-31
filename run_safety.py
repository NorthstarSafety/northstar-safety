from __future__ import annotations

import uvicorn

from northstar_safety.app import app
from northstar_safety.config import settings


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        reload=False,
    )
