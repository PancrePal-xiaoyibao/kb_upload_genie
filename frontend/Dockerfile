# 前端容器 - KB Upload Genie Frontend
FROM node:18-alpine AS builder

WORKDIR /app

# 复制依赖文件
COPY package*.json ./
COPY yarn.lock* ./

# 安装依赖
RUN npm ci

# 复制源码
COPY . .

# 构建应用 (添加调试信息)
RUN echo "开始构建前端应用..." && \
    echo "当前工作目录: $(pwd)" && \
    echo "文件列表:" && ls -la && \
    echo "src目录内容:" && ls -la src/ && \
    echo "检查vite.config.ts:" && cat vite.config.ts && \
    echo "检查tsconfig.json:" && cat tsconfig.json && \
    echo "开始Vite构建..." && \
    npx vite build --mode production

# 生产环境镜像
FROM nginx:alpine

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制Nginx配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]
