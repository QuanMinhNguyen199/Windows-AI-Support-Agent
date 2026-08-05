const ALLOWED_ORIGINS = new Set([
  "http://127.0.0.1:8000",
  "http://localhost:8000",
  "https://quanminhnguyen199.github.io",
]);
const ISSUE_TYPES = new Set([
  "startup", "install", "uninstall", "diagnostics", "updates", "assistant", "interface", "other",
]);
const IMAGE_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);
const MAX_ATTACHMENT_BYTES = 5 * 1024 * 1024;

function response(body, status, origin) {
  return new Response(status === 204 ? null : JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      "access-control-allow-origin": origin,
      "access-control-allow-methods": "GET, POST, OPTIONS",
      "access-control-allow-headers": "content-type",
      "vary": "Origin",
    },
  });
}

function ticketNumber() {
  const values = new Uint32Array(1);
  crypto.getRandomValues(values);
  return String(10_000_000 + (values[0] % 90_000_000));
}

function validImage(contentType, content) {
  if (!IMAGE_TYPES.has(contentType) || typeof content !== "string") return false;
  const estimatedBytes = Math.floor(content.length * 0.75);
  if (!content || estimatedBytes > MAX_ATTACHMENT_BYTES) return false;
  if (contentType === "image/png") return content.startsWith("iVBOR");
  if (contentType === "image/jpeg") return content.startsWith("/9j/");
  return content.startsWith("UklGR");
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get("origin") || "";
    if (!ALLOWED_ORIGINS.has(origin)) return response({ error: "Origin not allowed" }, 403, "null");
    if (request.method === "OPTIONS") return response({}, 204, origin);
    if (request.method === "GET") return response({ status: "ready", service: "WinAssist Support" }, 200, origin);
    if (request.method !== "POST") return response({ error: "Method not allowed" }, 405, origin);
    if (!request.headers.get("content-type")?.includes("application/json")) {
      return response({ error: "Invalid content type" }, 415, origin);
    }

    let payload;
    try { payload = await request.json(); } catch { return response({ error: "Invalid request" }, 400, origin); }
    const issueType = String(payload.issue_type || "");
    const description = String(payload.description || "").trim();
    if (!ISSUE_TYPES.has(issueType) || description.length < 10 || description.length > 4000) {
      return response({ error: "Please check the ticket details" }, 400, origin);
    }
    if (payload.website) return response({ error: "Invalid request" }, 400, origin);

    let attachments = [];
    if (payload.attachment) {
      const file = payload.attachment;
      if (!validImage(String(file.content_type), file.content)) {
        return response({ error: "Only PNG, JPG or WebP images up to 5 MB are accepted" }, 400, origin);
      }
      const safeName = String(file.filename || "screenshot").replace(/[^a-zA-Z0-9._-]/g, "_").slice(0, 100);
      attachments = [{ filename: safeName || "screenshot", content: file.content }];
    }

    const ticketId = `Ticket#${ticketNumber()}`;
    const emailResponse = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: {
        authorization: `Bearer ${env.RESEND_API_KEY}`,
        "content-type": "application/json",
        "idempotency-key": ticketId,
      },
      body: JSON.stringify({
        from: env.SUPPORT_FROM || "WinAssist Beta <onboarding@resend.dev>",
        to: [env.SUPPORT_EMAIL],
        subject: `[${ticketId}] WinAssist Beta - ${issueType}`,
        text: `Mã ticket: ${ticketId}\nNhóm lỗi: ${issueType}\n\nMô tả:\n${description}`,
        attachments,
      }),
    });
    if (!emailResponse.ok) {
      console.error("Resend rejected support ticket", emailResponse.status);
      return response({ error: "Ticket could not be delivered" }, 502, origin);
    }
    return response({ success: true, ticket_id: ticketId }, 201, origin);
  },
};
