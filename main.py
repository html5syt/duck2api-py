"""Duck2API 启动脚本入口。"""

import uvicorn
from duck2api.config.settings import settings
from duck2api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "duck2api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
    )
