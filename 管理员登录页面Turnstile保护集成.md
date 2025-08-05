# 管理员登录页面Turnstile保护集成

## Core Features

- Cloudflare Turnstile人机验证

- 登录安全保护

- 防机器人攻击

- 参考Upload页面实现

## Tech Stack

{
  "Web": {
    "arch": "react",
    "component": "antd"
  },
  "frontend": "React + TypeScript",
  "ui": "Ant Design",
  "security": "Cloudflare Turnstile"
}

## Design

在管理员登录页面集成Turnstile验证组件，用户需要先完成人机验证才能提交登录表单。验证成功后将token发送到后端进行二次验证。

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] 分析Upload页面的Turnstile实现方式

[X] 在Login.tsx中导入必要的Turnstile相关依赖

[X] 在登录表单中添加Turnstile验证组件

[X] 修改登录提交逻辑，增加Turnstile验证检查

[X] 处理Turnstile验证失败的错误状态

[X] 后端添加管理员登录接口的Turnstile验证

[X] 测试登录页面的Turnstile集成功能
