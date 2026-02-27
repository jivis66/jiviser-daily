#!/bin/bash
# Daily Agent 启动脚本

echo "Starting Daily Agent..."

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "警告: .env 文件不存在，使用默认配置"
    echo "请复制 .env.example 为 .env 并配置"
fi

# 创建数据目录
mkdir -p data/cache data/exports data/logs

# 启动方式选择
if [ "$1" = "docker" ]; then
    echo "使用 Docker 启动..."
    docker-compose up -d
    echo "服务已启动，访问 http://localhost:8080"
    echo "查看日志: docker-compose logs -f"
elif [ "$1" = "dev" ]; then
    echo "使用开发模式启动..."
    source venv/bin/activate 2>/dev/null || echo "请激活虚拟环境"
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
else
    echo "使用生产模式启动..."
    uvicorn src.main:app --host 0.0.0.0 --port 8080
fi
