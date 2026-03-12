#!/bin/bash
# ==============================================
# Text-to-SQL Agent 启动脚本
# 一键启动后端 (FastAPI) + 前端 (Vite)
# ==============================================

set -e

# 配置 Hugging Face 国内加速镜像源，解决网络连通性导致的各种启动卡顿
export HF_ENDPOINT=https://hf-mirror.com

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 Text-to-SQL Agent 启动中...${NC}"

# 检查 .env 是否存在
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 文件不存在！请先复制模板：cp .env.example .env${NC}"
    exit 1
fi

# 清理占用的端口
kill_port() {
    local port=$1
    local pid=$(lsof -ti :$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo -e "${YELLOW}⚠️  端口 $port 被占用 (PID: $pid)，正在释放...${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
        echo -e "${GREEN}   端口 $port 已释放${NC}"
    fi
}

kill_port 8000
kill_port 5173

# 检查 Redis
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✅ Redis 已运行${NC}"
    else
        echo -e "${YELLOW}⚠️  Redis 未启动，多轮对话功能将不可用${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未安装 redis-cli，跳过 Redis 检查${NC}"
fi

# 启动后端（后台运行）
echo -e "${GREEN}📦 启动后端 (FastAPI)...${NC}"
uv run api_server.py &
BACKEND_PID=$!
echo -e "${GREEN}   后端 PID: ${BACKEND_PID}，端口: 8000${NC}"

# 等待后端完全启动（循环检测 8000 端口）
echo -e "${YELLOW}⏳ 等待后端完全启动（等待内部的 RAG 模型加载）...${NC}"
while ! curl -s http://localhost:8000/docs > /dev/null; do
    sleep 1
done
echo -e "${GREEN}✅ 后端服务已就绪！${NC}"

# 启动前端（后台运行）
echo -e "${GREEN}🎨 启动前端 (Vite)...${NC}"
cd frontend && npm run dev &
FRONTEND_PID=$!
echo -e "${GREEN}   前端 PID: ${FRONTEND_PID}，端口: 5173${NC}"
cd ..

echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}✅ 服务已全部启动！${NC}"
echo -e "${GREEN}   后端: http://localhost:8000${NC}"
echo -e "${GREEN}   前端: http://localhost:5173${NC}"
echo -e "${GREEN}   按 Ctrl+C 停止所有服务${NC}"
echo -e "${GREEN}============================================${NC}"

# 捕获 Ctrl+C，同时关闭前后端
cleanup() {
    echo -e "\n${YELLOW}🛑 正在停止所有服务...${NC}"
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✅ 已停止${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待子进程
wait
