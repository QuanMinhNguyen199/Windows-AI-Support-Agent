const chatLog = document.querySelector("#chat-log");
const chatForm = document.querySelector("#chat-form");
const messageInput = document.querySelector("#message-input");
const backendStatus = document.querySelector("#backend-status");
const backendDot = document.querySelector("#backend-dot");
const ollamaStatus = document.querySelector("#ollama-status");

function addMessage(text, role) {
  const article = document.createElement("article");
  article.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "Bạn" : "WA";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  bubble.appendChild(paragraph);
  article.append(avatar, bubble);
  chatLog.appendChild(article);
  chatLog.scrollTop = chatLog.scrollHeight;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    backendStatus.textContent = `Backend ${health.version}: hoạt động`;
    backendDot.className = "status-dot online";
    ollamaStatus.textContent = `Ollama: ${health.ollama.status === "not_checked" ? "chưa kiểm tra" : health.ollama.status}`;
  } catch {
    backendStatus.textContent = "Backend: không kết nối";
    backendDot.className = "status-dot offline";
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  addMessage(message, "user");
  addMessage("Chat API sẽ được triển khai cùng intent router ở giai đoạn tiếp theo.", "assistant");
  messageInput.value = "";
  messageInput.focus();
});

document.querySelectorAll("[data-message]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.message;
    messageInput.focus();
  });
});

checkHealth();
