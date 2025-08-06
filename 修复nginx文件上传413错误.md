# 修复nginx文件上传413错误

## Core Features

- 修复client_max_body_size配置

- 优化大文件上传支持

- 简化nginx反向代理配置

- docker部署配置更新

## Tech Stack

{
  "后端": "FastAPI (Python)",
  "前端": "HTML/JavaScript",
  "Web服务器": "Nginx",
  "部署": "Docker Compose"
}

## Design

修复了nginx配置中的文件上传大小限制问题，添加client_max_body_size 100M解决413错误，并简化了代理配置以适配外部反向代理环境

## Plan

Note: 

- [ ] is holding
- [/] is doing
- [X] is done

---

[X] 分析当前nginx配置文件结构和client_max_body_size设置

[X] 修复docker/nginx.conf中的文件上传大小限制

[X] 修复frontend/nginx.conf中的文件上传大小限制

[X] 添加相关的nginx配置优化项以支持大文件上传

[X] 更新docker-compose配置确保nginx配置生效

[X] 提供测试验证方案
