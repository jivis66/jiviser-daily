#!/bin/bash
# Daily Agent Docker 入口脚本

set -e

# 检查是否需要初始化
if [ ! -f "data/daily.db" ]; then
    echo "🚀 Daily Agent 首次启动"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 初始化数据库
    python -c "
import asyncio
from src.database import init_db
asyncio.run(init_db())
"
    echo "✓ 数据库初始化完成"
    
    # 根据环境变量选择启动模式
    if [ "$STARTUP_MODE" = "fast" ] || [ "$SETUP_TEMPLATE" != "" ]; then
        echo "⚡ Fast 模式启动"
        if [ "$SETUP_TEMPLATE" != "" ]; then
            echo "  应用模板: $SETUP_TEMPLATE"
            python -c "
import asyncio
from src.setup_wizard import apply_template
asyncio.run(apply_template('$SETUP_TEMPLATE'))
" 2>/dev/null || echo "  模板应用失败，使用默认配置"
        fi
        echo ""
        echo "✅ Fast 模式启动成功！"
        echo ""
        echo "📖 提示：如需完整配置，请运行："
        echo "  docker exec -it daily-agent python -m src.cli setup wizard"
        
    elif [ "$STARTUP_MODE" = "configure" ]; then
        echo "🔧 Configure 模式"
        echo "注意: Docker 环境下请在本地运行配置向导，然后挂载配置到容器"
        echo ""
    else
        echo ""
        echo "💡 提示：使用 Fast 模式启动，设置环境变量:"
        echo "  STARTUP_MODE=fast         # 零配置快速启动"
        echo "  SETUP_TEMPLATE=tech_developer  # 使用预设模板"
        echo ""
        echo "或使用 docker-compose 在本地完成配置后挂载到容器。"
        echo ""
    fi
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
fi

# 根据命令执行不同操作
case "$1" in
    start)
        # 检查是否有 Fast 模式或模板设置
        if [ "$STARTUP_MODE" = "fast" ] || [ "$SETUP_TEMPLATE" != "" ]; then
            echo "🚀 以 Fast 模式启动服务..."
        else
            echo "🚀 启动 Daily Agent 服务..."
        fi
        exec uvicorn src.main:app --host 0.0.0.0 --port 8080
        ;;
    configure)
        echo "🔧 运行配置向导..."
        exec python -m src.cli setup wizard
        ;;
    generate)
        echo "📰 生成日报..."
        exec python -m src.cli generate
        ;;
    collect)
        echo "📥 触发采集..."
        exec python -m src.cli collect
        ;;
    status)
        exec python -m src.cli status
        ;;
    *)
        # 执行传入的命令
        exec "$@"
        ;;
esac
