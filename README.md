# Duck2API-py

基于 **Python** 与 **Playwright 原生浏览器引擎** 构建的现代化 DuckDuckGo AI Chat 转 OpenAI 兼容 API 网关。

[![Docker Build & Publish](https://github.com/html5syt/duck2api-py/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/html5syt/duck2api-py/actions/workflows/docker-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

---

## 🌟 核心优势：彻底告别 418 风控拦截

传统的 DuckDuckGo 逆向项目多采用纯 HTTP 客户端配合轻量 JS 模拟器（如 Goja 等）执行 VQD JSA 挑战。由于缺少真实的浏览器 DOM 布局、真实 `crypto.subtle` 原生实现、WebGL/Canvas 渲染树与完备的同源上下文，**极易被 DuckDuckGo 的反爬与风控系统识别并抛出 HTTP 418（I'm a teapot）/ 429 错误**。

**Duck2API-py** 采用全新架构：
1. **原生 Playwright Chromium 引擎**：在纯正真实的现代浏览器上下文中完成 JSA 动态算力挑战与原生网络调度，特征与真实用户完全一致，根治 418 拦截。
2. **连接池预热与毫秒级复用**：内置异步 Page 实例连接池，服务启动即预热完成；挑战计算时延低至数十毫秒，极大兼顾了**高可靠性**与**高响应效率**。
3. **真实用户轨迹信号模拟**：自动注入合规的 `x-fe-signals` 行为流与 `x-ddg-journey-id` 追踪，保障长生命周期稳定性。
4. **全套 OpenAI 规范端点兼容**：无缝对接 NextChat、LobeChat、ChatGPT-Next-Web、Cursor、沉浸式翻译等主流客户端。

---

## 📋 功能概览

| 功能分类 | 端点 | 说明 |
|---|---|---|
| **Chat Completions** | `POST /v1/chat/completions` | 标准流式/非流式对话，支持推理模式、联网搜索与文件上下文 |
| **Responses API** | `POST /v1/responses` | OpenAI Responses 协议兼容端点 |
| **模型列表** | `GET /v1/models` | 实时同步 DuckDuckGo 上游可用模型，提供常用别名 |
| **图像生成** | `POST /v1/images/generations` | 文生图（Base64 纯净图片返回，内置行缓冲重组） |
| **图像编辑** | `POST /v1/images/edits` | 图生图 / 改图（支持表单文件上传或 JSON Base64） |
| **文件管理** | `POST /v1/files`<br>`GET /v1/files`<br>`GET /DELETE /v1/files/:id` | 上传文档用于对话问答引用，支持元数据查询与原始内容下载 |
| **语音识别** | `POST /v1/audio/transcriptions` | Whisper 兼容听写接口（WebM/WAV/MP3/OGG） |
| **健康检查** | `GET /`、`GET /ping` | 存活探针与轻量心跳检查 |

---

## 🚀 快速开始

### 方式一：Docker Compose 部署（推荐）

1. 下载 `docker-compose.yml` 或克隆本仓库：
```bash
git clone https://github.com/html5syt/duck2api-py.git
cd duck2api-py
```

2. 启动服务：
```bash
docker compose up -d
```

服务默认将在 `http://localhost:8080` 启动就绪。

### 方式二：本地 Python 源码运行

推荐使用极速包管理器 [uv](https://github.com/astral-sh/uv)：

```bash
# 1. 克隆代码
git clone https://github.com/html5syt/duck2api-py.git
cd duck2api-py

# 2. 安装依赖并下载 Playwright Chromium 浏览器
uv sync
uv run playwright install --with-deps chromium

# 3. 运行服务
uv run python main.py
```

---

## 🧪 全量 API 接口 curl 测试命令清单

> 以下命令均以默认本地地址 `http://localhost:8080` 为例。若设置了 `AUTHORIZATION` 鉴权密钥，请在请求中添加 `-H "Authorization: Bearer <your_key>"`。

### 1. 健康检查

#### 根路径欢迎探针
```bash
curl -X GET http://localhost:8080/
```
**期望返回**：`{"message":"Hello, world!"}`

#### 轻量心跳检测
```bash
curl -X GET http://localhost:8080/ping
```
**期望返回**：`{"message":"pong"}`

---

### 2. 模型列表接口

#### 获取可用模型列表
```bash
curl -X GET http://localhost:8080/v1/models
```

---

### 3. 对话补全 (Chat Completions)

#### (1) 基础非流式对话
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {"role": "user", "content": "你好，请用一句话介绍你自己"}
    ],
    "stream": false
  }'
```

#### (2) 实时流式对话 (SSE 流)
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {"role": "user", "content": "请从 1 数到 5"}
    ],
    "stream": true
  }'
```

#### (3) 深度思考/推理模式 (Reasoning)
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {"role": "user", "content": "证明勾股定理的几何原理"}
    ],
    "reasoning_effort": "high",
    "stream": false
  }'
```

#### (4) 联网搜索模式 (Web Search)
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-luna",
    "messages": [
      {"role": "user", "content": "今天有哪些重要的科技新闻？"}
    ],
    "web_search": true,
    "stream": false
  }'
```

#### (5) 附加已上传文件的上下文问答
```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {"role": "user", "content": "总结一下我上传的文件核心内容"}
    ],
    "file_ids": ["file-xxxxxxxxxxxx"],
    "stream": false
  }'
```

---

### 4. OpenAI Responses API

#### 创建 Responses 响应
```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "input": "请起草一份项目交付通知",
    "instructions": "你是一位专业的项目主管",
    "stream": false
  }'
```

---

### 5. 图像生成与编辑 (Images API)

#### (1) 文本生成图像 (文生图)
```bash
curl -X POST http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只戴着宇航员头盔的猫咪在火星表面漫步",
    "model": "gpt-5.4-mini"
  }'
```
**期望返回**：标准 Base64 编码的 JPEG 图像数据：
```json
{
  "created": 1792225858,
  "data": [
    {
      "b64_json": "/9j/4AAQSkZJRgABAQAAAQABAAD/61U6SlACEQ...",
      "revised_prompt": ""
    }
  ]
}
```

#### (2) 图像编辑/图生图（Multipart 文件上传方式）
```bash
curl -X POST http://localhost:8080/v1/images/edits \
  -F "image=@cat.png" \
  -F "prompt=将猫咪换成一只可爱的柴犬" \
  -F "model=gpt-5.4-mini"
```

#### (3) 图像编辑/图生图（JSON Base64 方式）
```bash
curl -X POST http://localhost:8080/v1/images/edits \
  -H "Content-Type: application/json" \
  -d '{
    "image": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
    "prompt": "在画面中心添加一轮明月",
    "model": "gpt-5.4-mini"
  }'
```

---

### 6. 文件管理 (Files API)

#### (1) 上传文件
```bash
curl -X POST http://localhost:8080/v1/files \
  -F "file=@demo.txt" \
  -F "purpose=assistants"
```
**返回示例**：`{"id":"file-xxxx","object":"file","bytes":1024,"filename":"demo.txt","purpose":"assistants"}`

#### (2) 获取文件列表
```bash
curl -X GET http://localhost:8080/v1/files
```

#### (3) 查询单个文件信息
```bash
curl -X GET http://localhost:8080/v1/files/file-xxxxxxxxxxxx
```

#### (4) 下载文件原始内容
```bash
curl -X GET http://localhost:8080/v1/files/file-xxxxxxxxxxxx/content \
  --output downloaded_file.txt
```

#### (5) 删除指定文件
```bash
curl -X DELETE http://localhost:8080/v1/files/file-xxxxxxxxxxxx
```

---

### 7. 语音转文字 (Whisper API)

#### 上传音频文件进行听写转录
```bash
curl -X POST http://localhost:8080/v1/audio/transcriptions \
  -F "file=@recording.webm" \
  -F "model=whisper-1"
```
**返回示例**：`{"text":"转录出来的文字内容"}`

---

## 🤖 支持的模型

系统自动动态同步 DuckDuckGo 当前可用模型并提供常见 OpenAI 别名映射：

| 官方模型 ID | 提供方 | 描述 |
|---|---|---|
| `gpt-6-luna` | OpenAI | 最新一代通用对话旗舰模型 |
| `gpt-5.4-mini` | OpenAI | 轻量高效模型，支持推理模式与多模态 |
| `claude-haiku-4-5` | Anthropic | 极速响应通用对话模型 |
| `mistral-small-2603` | Mistral AI | 优秀的开源指令对齐模型 |
| `tinfoil/gpt-oss-120b` | Tinfoil / OpenAI | GPT-1.5 120B 开源权重模型 |
| `tinfoil/gemma4-31b` | Tinfoil / Google | Gemma 4 31B 高性能模型 |

**内置别名映射**：
- `gpt-4o-mini`、`gpt-4`、`gpt-3.5-turbo` 自动映射为 `gpt-5.4-mini`
- `gpt-4o` 自动映射为 `gpt-6-luna`
- `claude-3-haiku`、`claude-3.5-haiku` 自动映射为 `claude-haiku-4-5`

---

## ⚙️ 环境变量配置

所有配置项均支持通过环境变量或根目录 `.env` 文件指定：

| 变量名 | 说明 | 默认值 | 示例 |
|---|---|---|---|
| `PORT` | 服务监听端口 | `8080` | `8080` |
| `HOST` | 服务监听地址 | `0.0.0.0` | `0.0.0.0` |
| `AUTHORIZATION` | API 鉴权 Token (Bearer) | 无（开放模式） | `Bearer your_secret_token` |
| `PROXY_URL` | 上游网络代理地址 | 无 | `http://127.0.0.1:3605` |
| `PREFIX` | 全局路由前缀 | 无 | `/api` |
| `BROWSER_HEADLESS` | 浏览器无头模式 | `true` | `true` |
| `PAGE_POOL_SIZE` | 浏览器页面并发池大小 | `3` | `3` |
| `BROWSER_TIMEOUT_MS` | 页面请求超时时间 (毫秒) | `60000` | `60000` |

---

## 🏗️ 架构设计

```
duck2api-py/
├── duck2api/
│   ├── config/             # 配置管理（Pydantic Settings）
│   ├── core/               # 核心引擎（Playwright 浏览器池、VQD 挑战求解器、遥测信号）
│   ├── schemas/            # 协议数据模型（OpenAI 标准规范 & DuckGo 内部规范）
│   ├── services/           # 业务逻辑服务层（Chat、Responses、Models、Images、Files、Audio）
│   ├── api/                # API 路由层（FastAPI Routers、中间件与鉴权依赖）
│   └── utils/              # 通用工具（Token 计算、加密哈希、结构化日志）
├── tests/                  # 自动化测试用例集
├── .github/workflows/      # GitHub Actions 自动化 CI/CD 构建发布镜像
├── Dockerfile              # 生产级 Dockerfile（含 Playwright Chromium 优化层）
└── docker-compose.yml      # 一键容器编排配置
```

---

## 📄 License

[MIT License](LICENSE)