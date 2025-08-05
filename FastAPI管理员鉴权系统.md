# FastAPI管理员鉴权系统

## Core Features

- 环境变量配置管理员信息

- 数据库管理员用户创建

- JWT身份验证

- 权限验证中间件

- 登录接口

- 管理员测试接口

## Tech Stack

{
  "backend": "Python FastAPI",
  "orm": "SQLAlchemy",
  "auth": "JWT + bcrypt",
  "env": "python-dotenv"
}

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] 配置环境变量文件，添加管理员邮箱和密码设置

[X] 创建数据库初始化脚本，实现管理员用户自动创建

[X] 实现JWT令牌生成和验证工具函数

[X] 创建用户认证相关的API接口（登录、验证）

[X] 实现权限验证中间件和装饰器

[X] 集成到主应用并测试鉴权功能
