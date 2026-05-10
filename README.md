# Image2 Generator

> 一个极简的 GPT-Image-2 网页客户端：**支持参考图（图生图 / 多图融合）**，可本地一键运行，也可一键部署到 Cloudflare Worker。

![version](https://img.shields.io/badge/version-1.0.0-blue) ![license](https://img.shields.io/badge/license-MIT-green)

## 功能特性

- **文生图**：输入提示词直接生成（1024 分辨率）
- **图生图 / 编辑**：上传 1 张参考图 + 修改指令，保留构图与风格做局部修改（自动 2K 分辨率）
- **多图融合**：上传 ≥2 张参考图，按提示词融合元素（人物保留 A 的、配色取 B 的等）
- **极简单文件前端**：纯 HTML，无构建步骤
- **两种运行模式**：
  - 本地一键模式：`python serve.py` 起本地代理 + 静态服务
  - 生产模式：Cloudflare Worker 反代 + 静态托管
- **API key 不暴露给浏览器**：始终走服务端代理，前端只看到同源接口

## 快速开始（本地）

需要：Python 3.8+、一个 OpenAI 兼容的 GPT-Image-2 API key。

```bash
git clone https://github.com/Edwardslin007/image2-generator.git
cd image2-generator

# 1) 设置 API key
#   PowerShell:  $env:OPENAI_API_KEY = "sk-xxxxx"
#   cmd:         set OPENAI_API_KEY=sk-xxxxx
#   bash:        export OPENAI_API_KEY=sk-xxxxx

# 2) 可选：换上游 base_url（默认 https://api.opus5.xyz）
#   export OPENAI_BASE_URL=https://your-provider.example.com

# 3) 启动
python serve.py
# → 自动在浏览器打开 http://127.0.0.1:8765/
```

加 `--no-open` 不自动开浏览器；改端口设环境变量 `PORT=9000`。

## 用法

1. 在 **Prompt** 里写文字描述
2. 可选：点击 **+ 添加图片** 上传一张或多张参考图
3. 点 **Generate**，约 60–90 秒一张

> 不带参考图 → 文生图，后端走 `firefly-gpt-image-2-1k-1x1`
> 带参考图 → 图生图 / 编辑 / 融合，后端自动升级到 `firefly-gpt-image-2-2k-1x1`

### 提示词技巧

- 编辑现有图：`保持其它部分不变，只把 X 改成 Y`
- 融合多图：`Combine the subject from image 1 with the style of image 2`
- 不要在 prompt 里附加 `[size: ...]` 之类的元信息，会触发上游 `bad_response_status_code`

## 部署到 Cloudflare Worker

```bash
npm install -g wrangler
wrangler login

# 把 worker.js 部署成一个 Worker（按提示创建即可）
wrangler init image2-proxy
# 用本仓库的 worker.js 覆盖生成的 src/index.js（或保留 worker.js 并改 wrangler.toml 的 main）

# 注入 secret
wrangler secret put OPENAI_API_KEY
# 可选
wrangler secret put OPENAI_BASE_URL

wrangler deploy
```

部署完成后把 worker URL 填到 `index.html` 的 `API_BASE`：

```js
const API_BASE = "https://image2-proxy.<你的子域>.workers.dev";
```

然后把 `index.html` 静态托管到任意地方（GitHub Pages、Cloudflare Pages、Vercel 都行）。

## 接口约定（被代理的端点）

| 端点 | 说明 |
|---|---|
| `POST /v1/chat/completions` | 主接口（vision 风格 messages，支持参考图） |
| `POST /v1/images/generations` | 兼容旧接口（仅文生图） |
| `GET  /proxy/img?url=<encoded>` | 图床下载代理（绕开 UA / CORS 限制） |

### 请求格式（核心）

```json
POST /v1/chat/completions
{
  "model": "gpt-image-2",
  "messages": [{
    "role": "user",
    "content": [
      { "type": "text", "text": "把头盔玻璃改成红色，其它保持不变" },
      { "type": "image_url", "image_url": { "url": "https://... 或 data:image/png;base64,..." } }
    ]
  }]
}
```

### 响应格式（特殊）

这家上游不是标准 `images.generations` 形态，而是 `chat.completion`，图片 URL 嵌在 markdown 里：

```json
{
  "choices": [{
    "message": {
      "content": "![image](https://ossdown.com/api/v1/media/xxx.png)"
    }
  }]
}
```

前端用正则 `/!\[[^\]]*\]\((https?:\/\/[^)\s]+)\)/` 提取 URL。

## 项目结构

```
image2-generator/
├── index.html          # 单文件前端（UI + 调用逻辑）
├── serve.py            # 本地代理 + 静态服务（开发用）
├── worker.js           # Cloudflare Worker（生产用）
├── README.md
├── CHANGELOG.md
└── .gitignore
```

## 安全提醒

- **绝不要把 API key 写进 `index.html` / `worker.js` / `serve.py`**，本仓库已统一改为环境变量
- 旧版 commit 历史中可能残留过期 key（`sk-af90...` 已废弃），请勿复用
- 如果在公网部署 Worker，建议加 origin 白名单或 rate limiting，否则会被薅羊毛

## 已知限制

- 单张图生成约 60–90 秒，纯网络/上游耗时
- 上游不支持 `size` 字段（会被忽略且可能触发 502），分辨率由后端决定
- 上游不支持 `mask` 字段，编辑区域只能用提示词描述
- 输出图片托管在 `ossdown.com`，需要 `User-Agent` 才能下载（`/proxy/img` 已处理）

## License

MIT
