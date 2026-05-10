# Changelog

## v1.0.0 — 2026-05-10

首个正式版本。

### Added
- **参考图支持**：单图编辑、多图融合，前端可批量上传，自动转 base64 内联
- **本地一键启动**：新增 `serve.py`，提供静态托管 + API 反代 + 图床下载代理
- **响应解析新格式**：兼容上游返回的 `chat.completion`（markdown 形式 image URL）
- **下载代理 `/proxy/img`**：绕开图床的 UA / CORS 限制，让前端 `<img>` 与下载按钮都能用
- **README + CHANGELOG**：文档化用法、部署步骤、API 约定、已知限制

### Changed
- **接入新上游**：从 `2030.wujixian.fun` 切到 `https://api.opus5.xyz`
- **Worker 路由白名单扩展**：新增 `/v1/chat/completions`，旧的 `/v1/images/generations` 保留兼容
- **API key 改用环境变量**：`worker.js` 通过 Cloudflare secret，`serve.py` 通过 `OPENAI_API_KEY`
- **分辨率自动升级**：带参考图时上游自动从 1k 升至 2k

### Removed
- 移除前端 prompt 里的 `[size: ...]` 后缀（会触发上游 `bad_response_status_code`）
- 清理调试期临时脚本（`probe_*.py`、`test_local.py`）
- 删除硬编码的 API key
