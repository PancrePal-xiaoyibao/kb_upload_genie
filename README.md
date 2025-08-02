# KB Upload Genie - GitHub上传分类智能前端系统

## 项目概述

KB Upload Genie 是一个智能化的GitHub仓库内容上传分类系统，专为小白用户设计，集成多种AI模型进行内容审核、自动分类和质量评估。

## 核心功能

- 🤖 **AI智能审核**: 集成GLM4.5、Gemini 2.5、Moonshot Kimi、StepFun Step系列模型
- 📁 **自动分类**: 基于内容智能推荐分类目录
- 📊 **质量评估**: 内容质量打分和改进建议
- 🔒 **版权管理**: 版权状态检测和合规性检查
- 🚀 **GitHub集成**: 自动上传到指定GitHub仓库
- 👥 **用户友好**: 专为小白用户设计的简洁界面

## 技术栈

### 前端
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design 5.x
- **构建工具**: Vite
- **状态管理**: Zustand
- **编辑器**: Monaco Editor + Quill
- **HTTP客户端**: Axios + React Query

### 后端
- **框架**: FastAPI + Python 3.11
- **数据库**: PostgreSQL + SQLAlchemy
- **缓存**: Redis
- **异步任务**: Celery
- **认证**: JWT + OAuth2

### DevOps
- **容器化**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack

## 快速开始

### 环境要求

- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### 开发环境启动

1. **克隆项目**
   ```bash
   git clone https://github.com/PancrePal-xiaoyibao/kb_upload_genie.git
   cd kb_upload_genie
   ```

2. **环境配置**
   ```bash
   # 复制环境变量配置文件
   cp .env.example .env
   # 编辑配置文件，填入必要的API密钥
   ```

3. **使用Docker启动**
   ```bash
   # 启动所有服务
   docker-compose up -d
   
   # 查看服务状态
   docker-compose ps
   ```

4. **访问应用**
   - 前端: http://localhost:3000
   - 后端API: http://localhost:8000
   - API文档: http://localhost:8000/docs
   - Celery监控: http://localhost:5555

### 手动启动 (开发模式)

1. **后端启动**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **前端启动**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## 项目结构

```
kb_upload_genie/
├── frontend/                 # 前端React应用
│   ├── src/
│   │   ├── components/      # 可复用组件
│   │   ├── pages/          # 页面组件
│   │   ├── hooks/          # 自定义Hook
│   │   ├── utils/          # 工具函数
│   │   └── styles/         # 样式文件
│   ├── public/             # 静态资源
│   └── package.json
├── backend/                  # 后端FastAPI应用
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   ├── ai_services/    # AI服务集成
│   │   └── auth/           # 认证模块
│   ├── tests/              # 测试文件
│   └── requirements.txt
├── docker/                   # Docker配置
│   ├── nginx/              # Nginx配置
│   └── postgres/           # PostgreSQL初始化
├── docs/                     # 项目文档
├── tests/                    # 集成测试
├── .github/workflows/        # CI/CD配置
├── docker-compose.yml        # 开发环境
├── docker-compose.prod.yml   # 生产环境
└── README.md
```

## 开发指南

### 代码规范

- **前端**: ESLint + Prettier + TypeScript
- **后端**: Black + isort + flake8 + mypy
- **提交**: Conventional Commits

### 测试策略

- **单元测试**: Jest (前端) + pytest (后端)
- **集成测试**: API测试 + 数据库测试
- **端到端测试**: Playwright
- **覆盖率要求**: 80%+

### Git工作流

1. 从 `develop` 分支创建功能分支
2. 完成开发并通过所有测试
3. 创建Pull Request到 `develop`
4. 代码审查通过后合并
5. 定期从 `develop` 合并到 `main` 进行发布

## 部署说明

### 开发环境
```bash
docker-compose up -d
```

### 生产环境
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目地址: https://github.com/PancrePal-xiaoyibao/kb_upload_genie
- 问题反馈: https://github.com/PancrePal-xiaoyibao/kb_upload_genie/issues

## 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新详情。