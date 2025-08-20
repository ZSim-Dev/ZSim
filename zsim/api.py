"""
此处为api入口文件，负责启动FastAPI应用，不要在这里定义路由或写其他业务逻辑。
所有路由应在api_src/routes目录下定义。
业务逻辑应在api_src/service目录下实现。
请确保在运行此文件时，FastAPI能够正确加载所有路由和服务。
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

app = FastAPI(
    title="ZSim API",
    description="ZSim API for simulation management and control",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.getenv("ZSIM_DISABLE_ROUTES") != "1":
    from zsim.api_src.routes import (
        router as api_router,
    )  # defer import to avoid side effects in tests

    app.include_router(api_router, prefix="/api", tags=["ZSim API"])




@app.get("/health")
async def health_check():
    """
    Health check endpoint for the ZSim API.

    Returns:
        dict: A simple message indicating the API is running.
    """
    return {"message": "ZSim API is running!"}


if __name__ == "__main__":
    import uvicorn
    import socket

    def get_free_port():
        """获取一个可用的端口号"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            s.listen(1)
            port = s.getsockname()[1]
        return port

    # 获取端口号，优先使用环境变量，否则自动查找可用端口
    port = int(os.getenv("ZSIM_API_PORT", 0))
    if port == 0:
        port = get_free_port()
    
    host = os.getenv("ZSIM_API_HOST", "127.0.0.1")
    
    print(f"Starting FastAPI HTTP server on {host}:{port}")
    uvicorn.run(
        "zsim.api:app",
        host=host,
        port=port,
        log_level="info",
        reload=True,
        access_log=True,
    )
