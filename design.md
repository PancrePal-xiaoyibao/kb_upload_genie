# GitHub仓库智能上传分类系统设计文档

## 1. 项目概述

### 1.1 项目背景
面向小白用户的GitHub仓库指定目录的上传前端系统，专门用于帮助用户将肿瘤患者相关的高质量文章进行上传，大幅度简化上传过程的技术门槛，减少人工等待时间。

github repo: https://github.com/PancrePal-xiaoyibao/kb_upload_genie.git


### 1.2 项目目标
- 降低技术门槛，让非技术用户也能轻松上传文章到GitHub
- 实现智能分类和自动审核，提高内容质量
- 提供友好的用户界面和流畅的操作体验
- 确保内容合规性和安全性

### 1.3 目标用户
- **主要用户**: 医疗领域的内容贡献者（医生、研究人员、患者家属等）
- **管理用户**: 内容审核员
- **系统管理员**: 技术维护人员

## 2. 功能需求

### 2.1 核心功能
1. **用户注册与登录**
   - 简单的用户注册流程
   - 邮箱验证机制
   - 用户权限管理

2. **文章上传功能**
   - 支持多种格式（Markdown、Word、PDF, PPTX等）
   - 支持选择上传目录下所有文件
   - 富文本编辑器
   - 文件拖拽上传
   - 批量上传支持

3. **智能分类系统**
   - 基于GitHub仓库目录结构的动态分类菜单
   - AI辅助分类建议
   - 手动分类选择

4. **内容审核系统**
   - AI智能审核（优先级高）
   - 人工审核（备用机制）
   - 违规内容自动识别和拦截

5. **GitHub集成**
   - 自动上传到指定GitHub仓库
   - 目录结构动态同步
   - 版本控制和历史记录

6. **版权管理**
   - 自动添加版权信息
   - 提交表单勾选是否：版权授权-无-未知

### 2.2 详细功能描述

#### 2.2.1 用户管理
- **注册功能**: 邮箱注册，基本信息填写
- **登录功能**: 邮箱/用户名登录，记住登录状态
- **权限管理**: 普通用户、审核员、管理员三级权限

#### 2.2.2 文章上传
- **内容编辑**: 支持Markdown和富文本编辑
- **元数据填写**: 标题、作者、摘要、关键词、分类
- **附件上传**: 支持图片、文档等附件
- **预览功能**: 上传前预览最终效果
- **版权管理**: 版权状态选择（已授权/无版权/未知），自动添加版权声明

#### 2.2.3 智能审核
- **内容审核**: 检测违规内容（宗教、政治、法律、违法、邪教、中医、非规范医疗、神医等）
- **格式审核**: 检查文档格式规范性
- **语法审核**: 基本的语法和拼写检查
- **质量评估**: 内容质量评分和改进建议

#### 2.2.4 分类管理
- **动态分类**: 基于GitHub仓库目录结构自动更新
- **分类建议**: AI根据内容自动推荐分类
- **分类维护**: 管理员可以管理分类结构

#### 2.2.5 版权管理
- **版权状态识别**: 自动检测内容的版权状态
- **版权声明生成**: 根据版权状态自动生成相应的版权声明
- **版权合规检查**: 确保上传内容符合版权法规要求
- **版权信息记录**: 完整记录版权相关信息和变更历史

## 3. 系统架构

### 3.1 整体架构
```
前端 (React/Vue) ↔ 后端API (Python/FastAPI) ↔ 数据库 (PostgreSQL)
自定义                                ↓
                    GitHub API + AI服务集群
                                ↓
                OpenAI兼容接口 + GLM4.5系列 + Gemini 2.5系列 + Moonshot Kimi系列 + StepFun Step系列 + 本地模型
```

### 3.2 技术栈选择

#### 3.2.1 前端技术栈
- **框架**: React 18 + TypeScript
- **UI库**: Ant Design / Material-UI
- **状态管理**: Redux Toolkit / Zustand
- **路由**: React Router
- **编辑器**: Monaco Editor (代码) + Quill (富文本)
- **HTTP客户端**: Axios
- **构建工具**: Vite

#### 3.2.2 后端技术栈
- **框架**: Python + FastAPI
- **数据库**: PostgreSQL + SQLAlchemy
- **缓存**: Redis
- **任务队列**: Celery
- **文件存储**: 本地存储 + GitHub
z- **AI服务**: 
  - OpenAI兼容接口 (支持多种模型提供商)
  - GLM4.5系列模型 (智谱AI)
  - 模型管理和负载均衡
  - 本地模型部署支持

#### 3.2.3 部署和运维
- **容器化**: Docker + Docker Compose
- **Web服务器**: Nginx
- **进程管理**: Gunicorn
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack

### 3.3 系统模块

#### 3.3.1 用户模块 (User Module)
- 用户注册、登录、权限管理
- 用户信息维护
- 会话管理

#### 3.3.2 内容模块 (Content Module)
- 文章创建、编辑、删除
- 文件上传和管理
- 内容版本控制

#### 3.3.3 审核模块 (Review Module)
- **AI智能审核引擎**
  - GLM-4.5-flash: 快速内容审核和分类
  - GLM-4.5: 深度内容分析和质量评估
  - Gemini 2.5-flash: 多模态内容理解和快速审核
  - Gemini 2.5-pro: 复杂推理和专业内容评估
  - Step-1V: 视觉内容分析和图文审核
  - Step-2: 中文内容优化和质量提升建议
  - OpenAI兼容模型: 多语言支持和专业领域审核
- **人工审核工作流**
- **审核结果管理**
- **模型切换和负载均衡**

#### 3.3.4 分类模块 (Category Module)
- GitHub目录同步
- 分类管理
- 智能分类推荐

#### 3.3.5 GitHub集成模块 (GitHub Integration)
- GitHub API集成
- 文件上传和管理
- 目录结构同步

#### 3.3.6 版权管理模块 (Copyright Module)
- 版权状态管理
- 版权声明自动生成
- 版权合规性检查
- 版权信息追踪

## 4. 数据库设计

### 4.1 核心数据表

#### 4.1.1 用户表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user', -- user, reviewer, admin
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.2 文章表 (articles)
```sql
CREATE TABLE articles (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    author VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    keywords VARCHAR(500),
    category_id INTEGER REFERENCES categories(id),
    user_id INTEGER REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'draft', -- draft, pending, approved, rejected
    copyright_status VARCHAR(20) DEFAULT 'unknown', -- authorized, none, unknown
    copyright_notice TEXT, -- 自动生成的版权声明
    original_source VARCHAR(500), -- 原始来源
    github_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.3 分类表 (categories)
```sql
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    path VARCHAR(500) NOT NULL,
    parent_id INTEGER REFERENCES categories(id),
    github_path VARCHAR(500),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 4.1.4 审核记录表 (reviews)
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    article_id INTEGER REFERENCES articles(id),
    reviewer_id INTEGER REFERENCES users(id),
    review_type VARCHAR(20), -- ai, human
    status VARCHAR(20), -- approved, rejected, pending
    comments TEXT,
    score INTEGER, -- 0-100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 数据关系
- 用户 1:N 文章
- 分类 1:N 文章
- 文章 1:N 审核记录
- 分类支持树形结构（parent_id自引用）

## 5. API设计

### 5.1 RESTful API规范

#### 5.1.1 用户相关API
```
POST /api/auth/register     # 用户注册
POST /api/auth/login        # 用户登录
POST /api/auth/logout       # 用户登出
GET  /api/auth/profile      # 获取用户信息
PUT  /api/auth/profile      # 更新用户信息
```

#### 5.1.2 文章相关API
```
GET    /api/articles        # 获取文章列表
POST   /api/articles        # 创建文章
GET    /api/articles/{id}   # 获取文章详情
PUT    /api/articles/{id}   # 更新文章
DELETE /api/articles/{id}   # 删除文章
POST   /api/articles/{id}/submit  # 提交审核
```

#### 5.1.3 分类相关API
```
GET  /api/categories        # 获取分类树
POST /api/categories/sync   # 同步GitHub目录
GET  /api/categories/suggest/{article_id}  # AI分类建议
```

#### 5.1.4 审核相关API
```
GET  /api/reviews           # 获取待审核列表
POST /api/reviews/{article_id}  # 提交审核结果
GET  /api/reviews/ai/{article_id}  # 获取AI审核结果
```

#### 5.1.5 版权相关API
```
GET  /api/copyright/status/{article_id}  # 获取文章版权状态
POST /api/copyright/check   # 版权合规性检查
POST /api/copyright/generate-notice  # 生成版权声明
PUT  /api/copyright/update/{article_id}  # 更新版权信息
```

### 5.2 GitHub集成API
```
GET  /api/github/repos      # 获取仓库信息
GET  /api/github/tree       # 获取目录结构
POST /api/github/upload     # 上传文件到GitHub
```

### 5.3 AI服务API
```
POST /api/ai/review         # AI内容审核
POST /api/ai/classify       # AI自动分类
POST /api/ai/quality-check  # AI质量评估
GET  /api/ai/models         # 获取可用模型列表
POST /api/ai/model/switch   # 切换AI模型
```

## 5.4 AI服务详细配置

### 5.4.1 模型配置
#### GLM4.5系列模型
- **GLM4.5-Flash**
  - 用途: 快速内容审核、实时分类建议
  - 特点: 响应速度快，成本低
  - 适用场景: 初步内容过滤、分类预测
  - API配置: 智谱AI官方接口

- **GLM4.5-Plus**
  - 用途: 深度内容分析、质量评估
  - 特点: 分析精度高，理解能力强
  - 适用场景: 详细内容审核、质量打分
  - API配置: 智谱AI官方接口

#### Gemini 2.5系列模型
- **Gemini 2.5-Flash**
  - 用途: 快速多模态内容理解、实时分类
  - 特点: 支持文本+图片，响应速度快
  - 适用场景: 多媒体内容审核、快速分类
  - API配置: Google AI Studio / Vertex AI

- **Gemini 2.5-Pro**
  - 用途: 复杂推理、深度内容分析
  - 特点: 强大的推理能力，支持长文本
  - 适用场景: 复杂内容质量评估、专业领域审核
  - API配置: Google AI Studio / Vertex AI

#### Moonshot Kimi系列模型
- **Kimi-Flash**
  - 用途: 快速文本处理、实时响应
  - 特点: 低延迟，高并发支持
  - 适用场景: 实时内容过滤、快速分类建议
  - API配置: Moonshot AI官方接口

- **Kimi-Plus**
  - 用途: 长文本理解、深度分析
  - 特点: 支持超长上下文，理解能力强
  - 适用场景: 长文档审核、内容质量深度分析
  - API配置: Moonshot AI官方接口

#### StepFun Step系列模型
- **Step-1V**
  - 用途: 多模态内容理解、视觉内容分析
  - 特点: 强大的视觉理解能力，支持图文混合
  - 适用场景: 图文内容审核、多媒体分类
  - API配置: StepFun官方接口

- **Step-3**
  - 用途: 高质量文本生成、内容优化建议
  - 特点: 优秀的中文理解和生成能力
  - 适用场景: 内容质量评估、文本优化建议
  - API配置: StepFun官方接口

#### OpenAI兼容接口
- **支持的模型提供商**
  - OpenAI (GPT系列)
  - Google (Gemini 2.5系列)
  - Moonshot (Kimi系列)
  - StepFun (Step系列)
  - Anthropic (Claude系列)
  - 阿里云通义千问


### 5.4.2 模型使用策略
```python
# AI服务配置示例
AI_CONFIG = {
    "content_review": {
        "primary": "glm4.5-flash",      # 主要审核模型
        "fallback": "gemini-2.5-flash", # 备用模型
        "timeout": 30                    # 超时时间(秒)
    },
    "content_classification": {
        "primary": "step-3",         # 快速分类
        "fallback": "glm4.5-flash",
        "timeout": 15
    },
    "quality_assessment": {
        "primary": "step3",    # 深度质量分析
        "fallback": "gemini-2.5-pro",
        "timeout": 60
    },
    "multimodal_review": {
        "primary": "step-3",  # 多模态内容审核
        "fallback": "gemini-2.5-pro",
        "timeout": 45
    },
    "long_text_analysis": {
        "primary": "step-1-128k",         # 长文本分析
        "fallback": "glm4.5-plus",
        "timeout": 90
    },
    "content_optimization": {
        "primary": "step-3",            # 中文内容优化
        "fallback": "glm4.5-plus",
        "timeout": 60
    },
    "load_balancing": {
        "enabled": True,
        "strategy": "round_robin",       # 负载均衡策略
        "health_check": True,            # 健康检查
        "model_pools": {                 # 模型池配置
            "fast_models": ["glm-4.5-flash", "step-3", "gemini-2.5-flash"],
            "quality_models": ["glm-4.5-plus", "step-3", "gemini-2.5-pro", "step-2","kimi-k2-turbo-preview" ],
            "multimodal_models": ["step-1o-turbo-vision", "gemini-2.5-flash", "gemini-2.5-pro"],
            "chinese_optimized": ["step-3", "glm-4.5-plus","kimi-k2-turbo-preview"]
        }
    }
}
```

### 5.4.3 模型切换和负载均衡
- **自动故障转移**: 主模型不可用时自动切换到备用模型
- **负载均衡**: 支持多个模型实例的负载分配
- **健康检查**: 定期检查模型服务状态
- **性能监控**: 实时监控模型响应时间和成功率

## 6. 安全设计

### 6.1 身份认证
- JWT Token认证
- Token刷新机制
- 密码加密存储（bcrypt）

### 6.2 权限控制
- 基于角色的访问控制（RBAC）
- API接口权限验证
- 前端路由权限控制

### 6.3 数据安全
- SQL注入防护
- XSS攻击防护
- CSRF攻击防护
- 文件上传安全检查

### 6.4 内容安全
- 违规内容检测
- 敏感信息过滤
- 内容审核机制
- 版权合规性检查
- 知识产权保护

## 7. 性能优化

### 7.1 前端优化
- 代码分割和懒加载
- 图片压缩和CDN
- 缓存策略
- 虚拟滚动

### 7.2 后端优化
- 数据库索引优化
- 查询优化
- 缓存机制（Redis）
- 异步任务处理

### 7.3 系统优化
- 负载均衡
- 数据库读写分离
- CDN加速
- 监控和告警

## 8. 部署方案

### 8.1 开发环境
- Docker Compose本地部署
- 热重载开发模式
- 测试数据初始化

### 8.2 生产环境
- Kubernetes集群部署
- 自动化CI/CD流程
- 蓝绿部署策略
- 备份和恢复机制

## 9. 测试策略

### 9.1 单元测试
- 前端组件测试（Jest + React Testing Library）
- 后端API测试（pytest）
- 数据库测试

### 9.2 集成测试
- API集成测试
- 前后端集成测试
- 第三方服务集成测试

### 9.3 端到端测试
- 用户流程测试（Playwright）
- 性能测试
- 安全测试

## 10. 项目计划

### 10.1 开发阶段
1. **第一阶段（2周）**: 基础架构搭建
2. **第二阶段（3周）**: 核心功能开发
3. **第三阶段（2周）**: AI审核集成
4. **第四阶段（2周）**: GitHub集成
5. **第五阶段（1周）**: 测试和优化

### 10.2 里程碑
- MVP版本发布
- Beta版本测试
- 正式版本上线

## 11. 风险评估

### 11.1 技术风险
- GitHub API限制
- AI服务稳定性
- 性能瓶颈

### 11.2 业务风险
- 用户接受度
- 内容质量控制
- 合规性要求

### 11.3 风险缓解
- 备用方案准备
- 监控和告警机制
- 定期风险评估

## 12. 后续扩展

### 12.1 功能扩展
- 多语言支持
- 移动端应用
- 协作编辑功能
- 评论和讨论系统

### 12.2 技术扩展
- 微服务架构
- 机器学习优化
- 区块链集成
- 边缘计算支持

## 13. 用户体验优化

### 13.1 简化交互流程
- **3步完成上传**: 最大限度简化交互流程
  1. 第一步: 上传文章内容
  2. 第二步: 系统自动识别分类和审核
  3. 第三步: 确认并发布到GitHub

### 13.2 智能化功能
- **自动分类识别**: 系统自动识别文章分类，用户无需手动选择
- **配置记忆**: 系统记住用户的上传配置，下次上传时自动应用
- **智能建议**: 基于历史数据提供个性化建议

### 13.3 用户友好设计
- **拖拽上传**: 支持文件拖拽上传
- **实时预览**: 编辑过程中实时预览效果
- **进度提示**: 清晰的上传和处理进度提示
- **错误提示**: 友好的错误信息和解决建议

## 14. 开发规范

### 14.1 代码规范
- **Python**: 遵循PEP 8规范
- **JavaScript/TypeScript**: 使用ESLint + Prettier
- **Git提交**: 使用Conventional Commits规范
- **文档**: 使用Markdown格式，保持更新

### 14.2 开发流程
- **分支管理**: Git Flow工作流
- **代码审查**: Pull Request必须经过审查
- **自动化测试**: CI/CD流程中集成自动化测试
- **版本发布**: 语义化版本控制

### 14.3 质量保证
- **代码覆盖率**: 单元测试覆盖率不低于80%
- **性能监控**: 关键指标实时监控
- **安全扫描**: 定期进行安全漏洞扫描
- **用户反馈**: 建立用户反馈收集机制

---

**文档版本**: v1.0  
**创建日期**: 2024年  
**最后更新**: 2024年  
**维护人员**: 开发团队