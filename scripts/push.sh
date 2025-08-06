#!/bin/bash

# KB Upload Genie - 推送脚本
# 用于推送Docker镜像到远程仓库

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

echo -e "${GREEN}🚀 开始推送 KB Upload Genie Docker 镜像...${NC}"

# 检查是否已登录
if ! docker info | grep -q "Username"; then
    echo -e "${YELLOW}⚠️  请先登录到容器仓库:${NC}"
    echo "  GitHub Container Registry: docker login ghcr.io"
    echo "  Docker Hub: docker login"
    exit 1
fi

# 检查镜像是否存在
if ! docker images | grep -q "${FRONTEND_IMAGE}"; then
    echo -e "${RED}❌ 前端镜像不存在，请先运行构建脚本${NC}"
    exit 1
fi

if ! docker images | grep -q "${BACKEND_IMAGE}"; then
    echo -e "${RED}❌ 后端镜像不存在，请先运行构建脚本${NC}"
    exit 1
fi

# 推送前端镜像
echo -e "${YELLOW}📤 推送前端镜像...${NC}"
docker push ${FRONTEND_IMAGE}:${TAG}

# 推送后端镜像
echo -e "${YELLOW}📤 推送后端镜像...${NC}"
docker push ${BACKEND_IMAGE}:${TAG}

echo -e "${GREEN}✅ 镜像推送完成！${NC}"
echo -e "${YELLOW}推送的镜像:${NC}"
echo "  前端: ${FRONTEND_IMAGE}:${TAG}"
echo "  后端: ${BACKEND_IMAGE}:${TAG}"

# 生成部署用的docker-compose.yml
echo -e "${YELLOW}📝 生成部署配置...${NC}"
cat > docker-compose.prod.yml << EOF
services:
  # 后端服务
  backend:
    image: ${BACKEND_IMAGE}:${TAG}
    container_name: kb-backend
    env_file:
      - backend/.env
    environment:
      - PYTHONPATH=/app
    volumes:
      - backend_data:/app/data
      - backend_data:/app/uploads
      - backend_logs:/app/logs
    networks:
      - kb-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 前端服务
  frontend:
    image: ${FRONTEND_IMAGE}:${TAG}
    container_name: kb-frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    networks:
      - kb-network
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

# 数据卷
volumes:
  backend_data:
    driver: local
  backend_logs:
    driver: local

# 网络
networks:
  kb-network:
    driver: bridge
    name: kb-upload-genie-network
EOF

echo -e "${GREEN}🎉 推送完成！${NC}"
echo -e "${YELLOW}部署说明:${NC}"
echo "1. 将 docker-compose.prod.yml 和 backend/.env 复制到服务器"
echo "2. 在服务器上运行: docker compose -f docker-compose.prod.yml up -d"
echo "3. 访问: http://your-server:3000"