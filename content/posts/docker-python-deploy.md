---
title: Docker 部署 Python 应用
date: 2026-05-28
slug: docker-python-deploy
tags: [Docker, Python, 部署]
---

本文演示如何使用 Docker 容器化部署一个 Python Web 应用，并展示多语言代码高亮效果。

## 项目结构

```
myapp/
├── app.py          # Flask 应用
├── requirements.txt
└── Dockerfile
```

## Python 代码示例

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/api/health")
def health():
    """健康检查接口"""
    return jsonify({"status": "ok", "version": "1.0.0"})

@app.route("/api/users")
def list_users():
    users = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    return jsonify(users)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
```

## Dockerfile 示例

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
EXPOSE 8080

CMD ["python", "app.py"]
```

## Shell 命令

```bash
# 构建镜像
docker build -t myapp:latest .

# 运行容器
docker run -d -p 8080:8080 --name myapp myapp:latest

# 查看日志
docker logs -f myapp

# 查看运行状态
curl http://localhost:8080/api/health
```

## YAML 配置

`docker-compose.yml` 示例：

```yaml
version: "3.8"
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=info
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/api/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## JSON 配置示例

```json
{
  "app": {
    "name": "myapp",
    "version": "1.0.0",
    "debug": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8080,
    "workers": 4
  },
  "database": {
    "host": "db.example.com",
    "port": 5432,
    "name": "myapp_db"
  }
}
```

## 部署流程

整个流程分为三步：

| 步骤 | 操作 | 预计时间 |
|------|------|----------|
| 1 | 构建 Docker 镜像 | ~2 分钟 |
| 2 | 推送到镜像仓库 | ~1 分钟 |
| 3 | 服务器拉取并运行 | ~30 秒 |

> **提示**：生产环境建议使用 `docker compose` 管理多容器服务，配合 Nginx 反向代理和 HTTPS。

## 小结

Docker 让 Python 应用的部署变得简单可靠。通过本文的示例，你可以快速将一个 Flask 应用容器化并部署到任意支持 Docker 的服务器上。