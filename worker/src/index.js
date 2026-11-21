// 我的探店之旅：收「聯絡我們」留言的 Cloudflare Worker，留言存進 D1 資料庫 food_contact
// 網站表單 POST 到 /submit_contact_form（application/x-www-form-urlencoded）

const ALLOWED_ORIGINS = [
  "https://jim10182004.github.io",
  "http://localhost:8831",
  "http://localhost:3000",
];
const LIMITS = { name: 50, email: 254, message: 2000 };
const PER_IP_PER_HOUR = 5;

function cors(origin) {
  const h = { "Vary": "Origin" };
  if (ALLOWED_ORIGINS.includes(origin)) {
    h["Access-Control-Allow-Origin"] = origin;
    h["Access-Control-Allow-Methods"] = "POST, OPTIONS";
    h["Access-Control-Allow-Headers"] = "Content-Type";
  }
  return h;
}

function reply(status, body, origin) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", ...cors(origin) },
  });
}

async function sha256(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors(origin) });
    }
    if (url.pathname !== "/submit_contact_form") {
      return new Response("我的探店之旅：留言收件服務", { headers: { "Content-Type": "text/plain; charset=utf-8" } });
    }
    if (request.method !== "POST") return reply(405, { ok: false, error: "method" }, origin);
    if (!ALLOWED_ORIGINS.includes(origin)) return reply(403, { ok: false, error: "origin" }, origin);

    let form;
    try { form = await request.formData(); } catch { return reply(400, { ok: false, error: "form" }, origin); }

    // 隱藏欄位：真人看不到，有填的多半是機器人，假裝成功就好
    if ((form.get("website") || "").toString().trim()) return reply(200, { ok: true }, origin);

    const name = (form.get("name") || "").toString().trim();
    const email = (form.get("email") || "").toString().trim();
    const message = (form.get("message") || "").toString().trim();
    if (!name || !email || !message) return reply(400, { ok: false, error: "missing" }, origin);
    if (name.length > LIMITS.name || email.length > LIMITS.email || message.length > LIMITS.message) {
      return reply(400, { ok: false, error: "too_long" }, origin);
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return reply(400, { ok: false, error: "email" }, origin);

    // 同一個 IP 一小時最多 5 則；只存 IP 的雜湊，不存原本的 IP
    const ip = request.headers.get("CF-Connecting-IP") || "";
    const ipHash = await sha256("food-contact:" + ip);
    const { n } = await env.DB.prepare(
      "SELECT COUNT(*) AS n FROM messages WHERE ip_hash = ? AND created_at > datetime('now', '-1 hour')"
    ).bind(ipHash).first();
    if (n >= PER_IP_PER_HOUR) return reply(429, { ok: false, error: "rate" }, origin);

    await env.DB.prepare(
      "INSERT INTO messages (created_at, name, email, message, ip_hash) VALUES (datetime('now'), ?, ?, ?, ?)"
    ).bind(name, email, message, ipHash).run();

    return reply(200, { ok: true }, origin);
  },
};
