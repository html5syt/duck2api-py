# Duck2API-py 接口详细文档

Duck2API-py 提供与官方 OpenAI API 完全兼容的接口规范，可直接配置在各类支持 OpenAI API 的客户端或开发库中。

## 基础配置

- **Base URL**: `http://localhost:8080/v1`（若配置了 `PREFIX=/api` 则为 `http://localhost:8080/api/v1`）
- **认证方式**: `Authorization: Bearer <your_key>`（仅在配置了 `AUTHORIZATION` 环境变量时需要）
- **默认编码**: `UTF-8`

---

## 目录

1. [Chat Completions](#1-chat-completions)
2. [Responses API](#2-responses-api)
3. [Models API](#3-models-api)
4. [Images API](#4-images-api)
5. [Files API](#5-files-api)
6. [Audio API](#6-audio-api)
7. [健康检查](#7-健康检查)

---

## 1. Chat Completions

### `POST /v1/chat/completions`

创建对话补全任务，支持流式 SSE、非流式、推理深度调节、联网搜索与文件上下文附加。

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `model` | string | 是 | - | 模型名称，如 `gpt-5.4-mini`、`gpt-6-luna`、`claude-haiku-4-5` |
| `messages` | array | 是 | - | 消息列表 `[{"role": "user", "content": "..."}]` |
| `stream` | boolean | 否 | `false` | 是否开启流式传输 |
| `reasoning_effort` | string | 否 | `none` | 思考模式深度：`none`、`low`、`medium`、`high` |
| `web_search` | boolean | 否 | `false` | 是否启用联网搜索功能 |
| `file_ids` | array | 否 | `null` | 已上传文件的 ID 列表，自动提取内容拼装至上下文 |

#### 示例 1：非流式对话
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "messages": [
      {"role": "user", "content": "你好，请解释什么是量子计算"}
    ],
    "stream": false
  }'
```

**响应示例：**
```json
{
  "id": "chatcmpl-e28a59466fe1",
  "object": "chat.completion",
  "created": 1792224000,
  "model": "gpt-5.4-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "量子计算是一种遵循量子力学规律调控量子信息单元进行计算的新型计算模式..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 85,
    "total_tokens": 97
  }
}
```

#### 示例 2：流式联网搜索
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-6-luna",
    "messages": [
      {"role": "user", "content": "今天最新的科技动态"}
    ],
    "web_search": true,
    "stream": true
  }'
```

---

## 2. Responses API

### `POST /v1/responses`

OpenAI Responses 规范兼容接口。

```bash
curl http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-5.4-mini",
    "input": "请帮我写一封感谢信",
    "instructions": "你是一位专业的公文写作秘书"
  }'
```

---

## 3. Models API

### `GET /v1/models`

获取可用模型列表（包含上游实时同步模型与常用别名）。

```bash
curl http://localhost:8080/v1/models
```

**响应示例：**
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-5.4-mini",
      "object": "model",
      "created": 1792224000,
      "owned_by": "openai"
    },
    {
      "id": "gpt-6-luna",
      "object": "model",
      "created": 1792224000,
      "owned_by": "openai"
    },
    {
      "id": "claude-haiku-4-5",
      "object": "model",
      "created": 1792224000,
      "owned_by": "anthropic"
    }
  ]
}
```

---

## 4. Images API

### `POST /v1/images/generations` (文生图)

```bash
curl http://localhost:8080/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "一座在云端之上的未来赛博朋克城市",
    "model": "gpt-5.4-mini"
  }'
```

**响应示例：**
```json
{
  "created": 1792224000,
  "data": [
    {
      "b64_json": "/9j/4AAQSkZJRgABAQAAAQABAAD...",
      "revised_prompt": "一座在云端之上的未来赛博朋克城市"
    }
  ]
}
```

### `POST /v1/images/edits` (图生图 / 图像编辑)

支持 Multipart 表单或 JSON Base64 传递原图：

```bash
curl http://localhost:8080/v1/images/edits \
  -F "image=@origin.png" \
  -F "prompt=将背景改为阳光明媚的海滩"
```

---

## 5. Files API

### 上传文件 `POST /v1/files`

```bash
curl http://localhost:8080/v1/files \
  -F "file=@document.pdf" \
  -F "purpose=assistants"
```

### 获取文件列表 `GET /v1/files`

```bash
curl http://localhost:8080/v1/files
```

### 查询单文件 `GET /v1/files/{file_id}`

```bash
curl http://localhost:8080/v1/files/file-xxxx
```

### 下载文件内容 `GET /v1/files/{file_id}/content`

```bash
curl http://localhost:8080/v1/files/file-xxxx/content --output download.pdf
```

### 删除文件 `DELETE /v1/files/{file_id}`

```bash
curl -X DELETE http://localhost:8080/v1/files/file-xxxx
```

---

## 6. Audio API

### 语音转文字 `POST /v1/audio/transcriptions`

```bash
curl http://localhost:8080/v1/audio/transcriptions \
  -F "file=@speech.webm" \
  -F "model=whisper-1"
```

**响应示例：**
```json
{
  "text": "你好，这是一段转录测试语音。"
}
```

---

## 7. 健康检查

- `GET /`: `{"message": "Hello, world!"}`
- `GET /ping`: `{"message": "pong"}`
