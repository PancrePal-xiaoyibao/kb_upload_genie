# IMAP邮件附件上传系统自动回复功能

## Core Features

- 邮件附件上传完成自动回复

- 生成唯一Tracker ID

- 发送状态查询指引邮件

- 集成现有邮件处理流程

- 及时回复邮件发送

## Tech Stack

{
  "backend": "Python FastAPI",
  "database": "SQLAlchemy ORM",
  "email": "IMAP协议",
  "existing_modules": "tracker_service.py、邮件服务、通知服务"
}

## Design

基于现有邮件处理流程，在附件保存成功后自动触发Tracker ID确认邮件发送。使用HTML和纯文本双格式邮件模板，提供友好的用户体验和查询指引。

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] 分析现有邮件处理流程，确定自动回复触发点

[X] 设计回复邮件模板和Tracker ID生成逻辑

[X] 扩展tracker_service.py，添加回复邮件发送功能

[X] 修改邮件上传处理流程，集成自动回复功能

[X] 创建回复邮件模板和配置文件

[X] 实现邮件回复发送服务

[X] 测试自动回复功能和邮件发送

[X] 验证Tracker ID生成和状态查询流程
