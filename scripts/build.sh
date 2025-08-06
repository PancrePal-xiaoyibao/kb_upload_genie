#!/bin/bash

# KB Upload Genie - 本地构建脚本
# 用于在本地构建Docker镜像

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
REGISTRY="ghcr.io"
REPO_NAME="your-username/kb-upload-genie"  # 请替换为你的GitHub用户名/仓库名
FRONTEND_IMAGE="${REGISTRY}/${REPO_NAME}/kb-frontend"
BACKEND_IMAGE="${REGISTRY}/${REPO_NAME}/kb-backend"
TAG=${1:-latest}

echo -e "${GREEN}🚀 开始构建 KB Upload Genie Docker 镜像...${NC}"

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 构建前端镜像
echo -e "${YELLOW}📦 构建前端镜像...${NC}"
cd frontend
docker build -t kb_frontend .
docker tag kb_frontend ${FRONTEND_IMAGE}:${TAG}
cd ..

# 构建后端镜像
echo -e "${YELLOW}📦 构建后端镜像...${NC}"
cd backend
docker build -t kb_backend .
docker tag kb_backend ${BACKEND_IMAGE}:${TAG}
cd ..

# 显示构建的镜像
echo -e "${GREEN}✅ 镜像构建完成！${NC}"
echo -e "${YELLOW}本地镜像:${NC}"
docker images | grep -E "(kb_frontend|kb_backend)"

echo -e "${YELLOW}远程镜像标签:${NC}"
echo "  前端: ${FRONTEND_IMAGE}:${TAG}"
echo "  后端: ${BACKEND_IMAGE}:${TAG}"

# 测试镜像
echo -e "${YELLOW}🧪 测试镜像...${NC}"
docker compose up -d
sleep 10

# 检查容器状态
if docker compose ps | grep -q "Up"; then
    echo -e "${GREEN}✅ 容器启动成功！${NC}"
    echo -e "${YELLOW}访问地址: http://localhost:3000${NC}"
else
    echo -e "${RED}❌ 容器启动失败${NC}"
    docker compose logs
    exit 1
fi

# 清理测试容器
docker compose down

echo -e "${GREEN}🎉 构建完成！使用 './scripts/push.sh ${TAG}' 推送到远程仓库${NC}"