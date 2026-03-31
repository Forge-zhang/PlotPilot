"""FastAPI 主应用

提供 RESTful API 接口。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interfaces.api.v1 import novels, chapters, bible, ai
from web.routers.stats import create_stats_router
from web.services.stats_service import StatsService
from web.repositories.stats_repository import StatsRepository


# 创建 FastAPI 应用
app = FastAPI(
    title="aitext API",
    version="2.0.0",
    description="AI 小说创作平台 API"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册新架构路由
app.include_router(novels.router, prefix="/api/v1")
app.include_router(chapters.router, prefix="/api/v1")
app.include_router(bible.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")

# 注册统计路由（临时保留旧实现）
from pathlib import Path
books_root = Path("./data")  # 使用与新架构相同的数据目录
stats_repository = StatsRepository(books_root)
stats_service = StatsService(stats_repository)
stats_router = create_stats_router(stats_service)
app.include_router(stats_router, prefix="/api/stats", tags=["statistics"])


@app.get("/")
async def root():
    """根路径

    Returns:
        欢迎消息
    """
    return {"message": "aitext API v2.0"}


@app.get("/health")
async def health_check():
    """健康检查

    Returns:
        健康状态
    """
    return {"status": "healthy"}
