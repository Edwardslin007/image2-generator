/**
 * Cloudflare Worker - API Proxy for GPT-Image-2 (chat.completions style)
 *
 * Endpoints:
 *   POST /v1/chat/completions    主：支持参考图（vision 多模态）
 *   POST /v1/images/generations  兼容：旧的纯文生图接口
 *   GET  /proxy/img?url=<encoded>  下载远端图片（避开图床的 UA / CORS 限制）
 *
 * 部署需要在 Cloudflare Dashboard / wrangler.toml 配置 secret：
 *   OPENAI_API_KEY      （必需）
 *   OPENAI_BASE_URL     （可选，默认 https://api.opus5.xyz）
 *
 * 设置 secret 示例：
 *   wrangler secret put OPENAI_API_KEY
 */

const DEFAULT_BASE_URL = "https://api.opus5.xyz";

const ALLOWED_API_PATHS = new Set([
    "/v1/chat/completions",
    "/v1/images/generations",
]);

export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        if (request.method === "OPTIONS") {
            return new Response(null, {
                headers: {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                },
            });
        }

        const apiKey = env.OPENAI_API_KEY;
        const baseUrl = env.OPENAI_BASE_URL || DEFAULT_BASE_URL;

        if (request.method === "POST" && ALLOWED_API_PATHS.has(url.pathname)) {
            if (!apiKey) {
                return jsonError(500, "OPENAI_API_KEY is not configured on the worker");
            }
            const body = await request.text();
            const resp = await fetch(`${baseUrl}${url.pathname}`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${apiKey}`,
                    "Content-Type": "application/json",
                },
                body,
            });
            const respBody = await resp.text();
            return new Response(respBody, {
                status: resp.status,
                headers: {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "application/json",
                },
            });
        }

        if (request.method === "GET" && url.pathname === "/proxy/img") {
            const target = url.searchParams.get("url");
            if (!target) return new Response("missing url", { status: 400 });
            const r = await fetch(target, {
                headers: { "User-Agent": "Mozilla/5.0" },
            });
            return new Response(r.body, {
                status: r.status,
                headers: {
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": r.headers.get("Content-Type") || "image/png",
                    "Cache-Control": "public, max-age=86400",
                },
            });
        }

        return new Response("Not Found", { status: 404 });
    },
};

function jsonError(status, msg) {
    return new Response(JSON.stringify({ error: msg }), {
        status,
        headers: {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json",
        },
    });
}
