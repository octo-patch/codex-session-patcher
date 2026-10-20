"""
FastAPI 主入口
"""

import os
import mimetypes
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from codex_session_patcher import __version__
from codex_session_patcher.output import safe_print

# 修复 Windows 上 .js 文件 MIME 类型错误的问题
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

from .api import router
from .security import LOCAL_ORIGIN_REGEX, is_allowed_origin, is_loopback_host


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    # 启动时
    safe_print("🚀 Codex Session Patcher Web UI 启动中...")
    yield
    # 关闭时
    safe_print("👋 Codex Session Patcher Web UI 已关闭")


app = FastAPI(
    title="Codex Session Patcher",
    description="清理 AI 拒绝回复，恢复会话",
    version=__version__,
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=LOCAL_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def enforce_local_request(request: Request, call_next):
    """拒绝非本机客户端和非本机浏览器来源。"""
    client_host = request.client.host if request.client else None
    if not is_loopback_host(client_host):
        return JSONResponse(status_code=403, content={"detail": "仅允许本机访问"})
    if not is_allowed_origin(request.headers.get("origin")):
        return JSONResponse(status_code=403, content={"detail": "不允许的请求来源"})
    return await call_next(request)

# API 路由
app.include_router(router, prefix="/api")

# 静态文件（前端构建产物）
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")


def run_server(host: str = "127.0.0.1", port: int = 47832):
    """启动服务器"""
    import uvicorn
    safe_print(f"📍 访问地址: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
