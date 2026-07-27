const chatLog = document.querySelector("#chat-log");
const chatForm = document.querySelector("#chat-form");
const messageInput = document.querySelector("#message-input");
const backendStatus = document.querySelector("#backend-status");
const backendDot = document.querySelector("#backend-dot");
const ollamaStatus = document.querySelector("#ollama-status");
const commandPreview = document.querySelector("#command-preview");
const commandText = document.querySelector("#command-text");
const commandWarning = document.querySelector("#command-warning");
const confirmCommand = document.querySelector("#confirm-command");
const cancelCommand = document.querySelector("#cancel-command");
const sendButton = document.querySelector(".send-button");

let sessionId = null;
let pendingActionId = null;

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

function addDetails(items, label) {
  if (!items || items.length === 0) return;
  const lines = items.map((item) => (
    typeof item === "string" ? item : JSON.stringify(item)
  ));
  addMessage(`${label}:\n${lines.join("\n")}`, "assistant");
}

function showPendingAction(action) {
  if (!action) {
    pendingActionId = null;
    commandPreview.hidden = true;
    return;
  }
  pendingActionId = action.id;
  commandText.textContent = action.display_command;
  commandWarning.textContent = action.warning;
  commandPreview.hidden = false;
}

async function checkHealth() {
  try {
    const response = await fetch("/api/health", { headers: { Accept: "application/json" } });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const health = await response.json();
    backendStatus.textContent = `Backend ${health.version}: hoạt động`;
    backendDot.className = "status-dot online";
    ollamaStatus.textContent = `Ollama: ${health.ollama.status === "available" ? "sẵn sàng" : "không khả dụng — dùng rule-based"}`;
  } catch {
    backendStatus.textContent = "Backend: không kết nối";
    backendDot.className = "status-dot offline";
  }
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  addMessage(message, "user");
  messageInput.value = "";
  sendButton.disabled = true;
  messageInput.disabled = true;
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ message, session_id: sessionId }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    sessionId = payload.session_id;
    addMessage(payload.message, "assistant");
    addDetails(payload.results, "Kết quả");
    addDetails(payload.recommendations, "Đề xuất");
    if (payload.warning) addMessage(`Lưu ý: ${payload.warning}`, "assistant");
    showPendingAction(payload.pending_action);
  } catch (error) {
    addMessage(`Không thể xử lý yêu cầu: ${error.message}`, "assistant");
  } finally {
    sendButton.disabled = false;
    messageInput.disabled = false;
    messageInput.focus();
  }
});

document.querySelectorAll("[data-message]").forEach((button) => {
  button.addEventListener("click", () => {
    messageInput.value = button.dataset.message;
    messageInput.focus();
  });
});

async function completePendingAction(action) {
  if (!pendingActionId) return;
  confirmCommand.disabled = true;
  cancelCommand.disabled = true;
  try {
    const response = await fetch(`/api/actions/${pendingActionId}/${action}`, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
    addMessage(payload.message, "assistant");
    showPendingAction(null);
  } catch (error) {
    addMessage(`Không thể xử lý hành động: ${error.message}`, "assistant");
  } finally {
    confirmCommand.disabled = false;
    cancelCommand.disabled = false;
  }
}

confirmCommand.addEventListener("click", () => completePendingAction("confirm"));
cancelCommand.addEventListener("click", () => completePendingAction("cancel"));

checkHealth();
