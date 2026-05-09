// Cloudflare Worker - API Proxy for gpt-image-2
// Deploy: https://workers.cloudflare.com

const API_KEY = "sk-af901a02722e771b17623f78735c021d14b66bdccb6b70a40db6e75d1116805b";
const BASE_URL = "https://2030.wujixian.fun";

export default {
    async fetch(request) {
        // Handle CORS preflight
        if (request.method === "OPTIONS") {
            return new Response(null, {
                headers: {
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type",
                },
            });
        }

        // Only proxy POST /v1/images/generations
        if (request.method === "POST" && new URL(request.url).pathname === "/v1/images/generations") {
            const body = await request.text();

            const resp = await fetch(`${BASE_URL}/v1/images/generations`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${API_KEY}`,
                    "Content-Type": "application/json",
                },
                body: body,
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

        return new Response("Not Found", { status: 404 });
    },
};
