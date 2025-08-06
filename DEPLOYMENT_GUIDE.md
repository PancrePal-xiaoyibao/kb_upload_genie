# 资源上传跟踪系统部署指南

## 📋 项目概述

本项目为现有的知识库上传系统增加了完整的资源跟踪功能，用户可以通过Tracker ID查询上传文件的处理状态。

## 🛠 技术栈

- **后端**: FastAPI + SQLAlchemy + PostgreSQL
- **前端**: React + TypeScript + Tailwind CSS
- **数据库**: PostgreSQL with 新增跟踪字段

## 📁 项目结构

```
kb_upload_genie/
├── backend/                    # 后端代码
│   ├── app/
│   │   ├── api/v1/
│   │   │   └── tracker.py     # 跟踪查询API
│   │   ├── models/
│   │   │   └── article.py     # 扩展的Article模型
│   │   ├── schemas/
│   │   │   └── tracker.py     # 跟踪相关数据模型
│   │   ├── services/
│   │   │   └── tracker_service.py  # 跟踪服务层
│   │   └── utils/
│   │       └── tracker_utils.py    # 跟踪工具函数
│   ├── migrations/
│   │   └── add_tracker_fields.py   # 数据库迁移脚本
│   └── test_*.py              # 测试文件
├── frontend/                   # 前端代码
│   ├── src/
│   │   ├── components/
│   │   │   ├── StatusIndicator.tsx  # 状态指示器
│   │   │   ├── Toast.tsx           # 通知系统
│   │   │   └── ErrorBoundary.tsx   # 错误边界
│   │   ├── pages/
│   │   │   ├── TrackerQuery.tsx    # 跟踪查询页面
│   │   │   └── TrackerTest.tsx     # 测试页面
│   │   └── services/
│   │       └── tracker.ts          # 跟踪服务API
│   └── verify_frontend.js      # 前端验证脚本
└── DEPLOYMENT_GUIDE.md        # 本文档
```

## 🚀 部署步骤

### 1. 环境准备

确保系统已安装：
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (可选，用于缓存)

### 2. 后端部署

#### 2.1 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

#### 2.2 配置环境变量
复制并编辑环境配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件，确保包含：
```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

#### 2.3 运行数据库迁移
```bash
python migrations/add_tracker_fields.py full
```

#### 2.4 启动后端服务
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端部署

#### 3.1 安装依赖
```bash
cd frontend
npm install
```

#### 3.2 验证前端组件
```bash
node verify_frontend.js
```

#### 3.3 启动开发服务器
```bash
npm run dev
```

#### 3.4 构建生产版本
```bash
npm run build
```

### 4. 验证部署

#### 4.1 运行后端测试
```bash
cd backend
python test_tracker_integration.py
python test_backward_compatibility.py
```

#### 4.2 访问应用
- 主站: http://localhost:3000
- 跟踪查询: http://localhost:3000/tracker
- 测试页面: http://localhost:3000/tracker-test
- API文档: http://localhost:8000/docs

## 🔧 配置说明

### 数据库配置

新增的数据库字段：
- `articles.method`: 上传方法 (EMAIL, SIMPLE, API等)
- `articles.tracker_id`: 跟踪ID (格式: TRK-XXXXXXXX-XXXX)
- `articles.processing_status`: 处理状态 (pending, processing, completed, rejected)

### API端点

新增的API端点：
- `GET /api/v1/tracker/health` - 健康检查
- `GET /api/v1/tracker/status/{tracker_id}` - 查询跟踪状态
- `POST /api/v1/tracker/query` - POST方式查询状态

### 前端路由

新增的前端路由：
- `/tracker` - 跟踪查询页面
- `/tracker-test` - 简化测试页面

## 📱 使用说明

### 用户使用流程

1. **文件上传**: 用户通过任意方式上传文件
2. **获取Tracker ID**: 系统返回格式为 `TRK-XXXXXXXX-XXXX` 的跟踪ID
3. **状态查询**: 用户访问 `/tracker` 页面输入跟踪ID
4. **查看状态**: 系统显示处理状态、进度和详细信息

### 状态说明

- **⏳ 待处理**: 文件已接收，等待处理
- **🔄 处理中**: 正在分析和处理文件
- **✅ 已完成**: 文件处理完成，可以正常使用
- **❌ 已拒绝**: 文件处理失败或被拒绝

## 🔍 故障排除

### 常见问题

#### 1. 前端模块导入错误
```
The requested module '/src/utils/request.ts' does not provide an export named 'request'
```
**解决方案**: 检查导入语句，使用默认导入：
```typescript
import request from '@/utils/request';  // 正确
// import { request } from '@/utils/request';  // 错误
```

#### 2. 组件渲染错误
```
Uncaught TypeError: orig.toString.bind is not a function
```
**解决方案**: 检查组件导入和函数定义，确保所有依赖正确导入。

#### 3. API连接失败
**解决方案**: 
- 检查后端服务是否启动 (http://localhost:8000)
- 检查数据库连接是否正常
- 验证环境变量配置

#### 4. 数据库迁移失败
**解决方案**:
- 检查数据库连接权限
- 确保PostgreSQL服务正在运行
- 手动执行SQL语句添加字段

### 日志查看

#### 后端日志
```bash
# 查看应用日志
tail -f logs/app.log

# 查看数据库查询日志
tail -f logs/db.log
```

#### 前端日志
打开浏览器开发者工具查看控制台输出。

## 🧪 测试

### 单元测试
```bash
cd backend
python -m pytest tests/ -v
```

### 集成测试
```bash
python test_tracker_integration.py
```

### 向后兼容性测试
```bash
python test_backward_compatibility.py
```

### 前端测试
```bash
cd frontend
npm test
```

## 📊 监控和维护

### 性能监控
- 监控API响应时间
- 检查数据库查询性能
- 观察内存和CPU使用情况

### 数据维护
- 定期清理过期的跟踪记录
- 备份重要数据
- 监控存储空间使用

### 安全考虑
- 定期更新依赖包
- 检查安全漏洞
- 监控异常访问

## 🔄 更新和升级

### 代码更新
```bash
# 拉取最新代码
git pull origin main

# 更新后端依赖
cd backend && pip install -r requirements.txt

# 更新前端依赖
cd frontend && npm install

# 重启服务
```

### 数据库迁移
```bash
# 运行新的迁移脚本
python migrations/new_migration.py
```

## 📞 支持和联系

如遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查系统日志
3. 运行测试脚本诊断问题
4. 联系系统管理员

---

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✅ 添加资源上传跟踪功能
- ✅ 实现Tracker ID查询系统
- ✅ 创建前端状态查询界面
- ✅ 集成错误处理和通知系统
- ✅ 保证向后兼容性

---

**部署完成后，请访问 http://localhost:3000/tracker 测试跟踪查询功能！** 🎉