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
| **图像生成** | `POST /v1/images/generations` | 文生图（Base64 返回） |
| **图像编辑** | `POST /v1/images/edits` | 图生图 / 改图（支持表单或 JSON Base64） |
| **文件管理** | `POST /v1/files`<br>`GET /v1/files`<br>`GET /DELETE /v1/files/:id` | 上传文档用于对话问答引用，支持查询与删除 |
| **语音识别** | `POST /v1/audio/transcriptions` | Whisper 兼容听写接口（WebM/WAV/MP3/OGG） |
| **健康检查** | `GET /`、`GET /ping` | 存活探针与心跳检查 |

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

## 💡 使用示例

### 1. 基础对话 (流式 / 非流式)

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [{"role": "user", "content": "你好，请用一句话介绍你自己"}],
    "stream": true
  }'
```

### 2. 深度推理模式 (Reasoning)

使用 `reasoning_effort` 参数控制思考深度（支持 `low`、`medium`、`high`）：

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [{"role": "user", "content": "求解方程 x^2 - 5x + 6 = 0 的根并详细说明"}],
    "reasoning_effort": "high"
  }'
```

### 3. 联网搜索 (Web Search)

设置 `web_search: true` 启用实时联网搜索能力：

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [{"role": "user", "content": "今天有哪些重要的科技新闻？"}],
    "web_search": true
  }'
```

### 4. 文本生成图像 (Image Generations)

```bash
curl http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一只戴着宇航员头盔的小橘猫漫步在月球表面",
    "model": "gpt-5.4-mini"
  }'
```

### 5. 文件上传与上下文问答 (Files & Chat)

```bash
# 1. 上传文件
curl http://localhost:8080/v1/files \
  -F "file=@report.txt" \
  -F "purpose=assistants"

# 返回: {"id": "file-xxxx", "object": "file", ...}

# 2. 携带文件 ID 发起对话
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [{"role": "user", "content": "请分析总结该文档的核心要点"}],
    "file_ids": ["file-xxxx"]
  }'
```

### 6. 语音转文字 (Audio Transcriptions)

```bash
curl http://localhost:8080/v1/audio/transcriptions \
  -F "file=@recording.webm" \
  -F "model=whisper-1"
```

更多 API 详细说明请参阅 [API.md](API.md)。

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
| `BROWSER_TIMEOUT_MS` | 页面请求超时时间 (毫秒) | `30000` | `30000` |

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
