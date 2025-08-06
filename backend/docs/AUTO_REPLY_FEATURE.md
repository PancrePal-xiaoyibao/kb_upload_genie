# IMAP邮件附件上传系统自动回复功能

## 功能概述

本功能为现有的IMAP邮件附件上传系统增加了自动回复能力。当用户通过邮件上传附件后，系统会自动发送包含Tracker ID的确认邮件，让用户能够跟踪附件的处理状态。

## 核心功能

### 1. 自动回复邮件
- ✅ 附件上传成功后自动发送确认邮件
- ✅ 包含唯一的Tracker ID
- ✅ 提供状态查询指引
- ✅ 支持HTML和纯文本双格式

### 2. 邮件模板系统
- ✅ 专业的HTML邮件模板
- ✅ 响应式设计，支持各种邮件客户端
- ✅ 中文本地化支持
- ✅ 可配置的系统信息

### 3. 状态更新通知
- ✅ 处理完成时自动发送通知
- ✅ 处理失败时发送错误信息
- ✅ 包含详细的状态说明

## 技术实现

### 文件结构
```
backend/
├── app/
│   ├── services/
│   │   ├── email_service.py          # 邮件服务（已增强）
│   │   └── tracker_service.py        # 跟踪服务（已增强）
│   ├── templates/
│   │   └── email_templates.py        # 邮件模板管理器
│   └── core/
│       └── config.py                 # 配置文件（已增强）
└── test_auto_reply.py                # 功能测试脚本
```

### 核心组件

#### 1. EmailTemplateManager
位置：`app/templates/email_templates.py`

负责管理所有邮件模板，包括：
- Tracker ID确认邮件模板
- 上传成功通知模板
- 上传失败通知模板

#### 2. TrackerService增强
位置：`app/services/tracker_service.py`

新增方法：
- `send_tracker_confirmation_email()` - 发送Tracker确认邮件
- `send_status_update_email()` - 发送状态更新邮件
- `_send_email()` - 内部邮件发送方法

#### 3. EmailService集成
位置：`app/services/email_service.py`

修改的方法：
- `save_email_records()` - 集成自动回复功能
- `_send_confirmation_emails()` - 批量发送确认邮件

## 配置选项

在 `app/core/config.py` 中新增的配置项：

```python
# 邮件模板配置
SYSTEM_NAME: str = "知识库上传系统"
SUPPORT_EMAIL: str = "support@example.com"
FRONTEND_URL: str = "http://localhost:3000"

# 自动回复邮件配置
AUTO_REPLY_ENABLED: bool = True
TRACKER_EMAIL_ENABLED: bool = True
STATUS_UPDATE_EMAIL_ENABLED: bool = True
```

## 邮件模板示例

### Tracker确认邮件
- **主题**：文件上传确认 - Tracker ID: {tracker_id}
- **内容**：包含跟踪ID、文件信息、查询方法、处理时间说明
- **格式**：HTML + 纯文本双格式

### 状态更新邮件
- **成功通知**：处理完成确认
- **失败通知**：包含错误信息和解决建议

## 工作流程

1. **邮件接收**：IMAP服务接收用户邮件
2. **附件处理**：提取并验证附件
3. **数据保存**：保存到数据库并生成Tracker ID
4. **自动回复**：发送确认邮件给用户
5. **状态跟踪**：用户可通过Tracker ID查询状态
6. **状态更新**：处理完成后发送更新通知

## 测试验证

运行测试脚本验证功能：

```bash
cd backend
source .venv/bin/activate
python test_auto_reply.py
```

### 测试覆盖
- ✅ 邮件模板生成
- ✅ TrackerService邮件方法
- ✅ 邮件服务集成
- ✅ 配置项验证
- ✅ 邮件处理流程模拟
- ✅ SMTP连接配置

## 部署说明

### 1. 环境变量配置
确保以下环境变量已正确配置：

```env
# SMTP配置
SMTP_HOST=your_smtp_host
SMTP_PORT=587
SMTP_USER=your_email@domain.com
SMTP_PASSWORD=your_password
SMTP_TLS=true

# 系统配置
SYSTEM_NAME=知识库上传系统
SUPPORT_EMAIL=support@yourdomain.com
FRONTEND_URL=https://your-frontend-url.com

# 功能开关
AUTO_REPLY_ENABLED=true
TRACKER_EMAIL_ENABLED=true
STATUS_UPDATE_EMAIL_ENABLED=true
```

### 2. 启动服务
```bash
cd backend
source .venv/bin/activate
python main.py
```

### 3. 验证功能
1. 发送带附件的邮件到系统邮箱
2. 检查是否收到Tracker ID确认邮件
3. 使用Tracker ID查询状态
4. 验证状态更新通知

## 安全考虑

1. **邮件频率限制**：已集成现有的频率限制机制
2. **域名白名单**：支持域名过滤
3. **附件验证**：文件类型和大小限制
4. **错误处理**：完善的异常处理和日志记录

## 监控和日志

系统会记录以下关键事件：
- 确认邮件发送成功/失败
- 状态更新邮件发送
- SMTP连接状态
- 邮件模板生成错误

查看日志：
```bash
tail -f logs/email_service.log
```

## 故障排除

### 常见问题

1. **邮件发送失败**
   - 检查SMTP配置
   - 验证邮件服务器连接
   - 查看错误日志

2. **模板渲染错误**
   - 检查配置项是否完整
   - 验证模板文件完整性

3. **Tracker ID生成失败**
   - 检查数据库连接
   - 验证tracker_utils模块

### 调试命令
```bash
# 测试邮件模板
python -c "from app.templates.email_templates import email_template_manager; print('模板系统正常')"

# 测试SMTP连接
python -c "from app.services.email_service import email_service; import asyncio; asyncio.run(email_service.connect_smtp())"
```

## 更新日志

### v1.0.0 (2024-01-06)
- ✅ 实现基础自动回复功能
- ✅ 创建邮件模板系统
- ✅ 集成现有邮件处理流程
- ✅ 添加配置选项和测试脚本
- ✅ 完成功能测试验证

## 后续优化

1. **邮件模板编辑器**：Web界面管理邮件模板
2. **多语言支持**：支持英文等其他语言
3. **邮件统计**：发送成功率统计
4. **模板个性化**：根据用户偏好定制模板
5. **批量操作**：批量状态更新通知

---

**注意**：此功能已完全集成到现有系统中，无需额外的数据库迁移或服务重启。启用功能只需要配置相应的环境变量即可。