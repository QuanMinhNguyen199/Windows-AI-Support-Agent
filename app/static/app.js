const api = window.WinAssistApi;
const state = window.WinAssistState;
const SUPPORT_ENDPOINT = "https://winassist-support.minhquanpro65.workers.dev/";
const terminalStates = new Set(["completed", "failed", "cancelled", "expired"]);
const categoryNames = { student: "Học tập cho sinh viên", browsers: "Trình duyệt", office_pdf: "Văn phòng & PDF", utilities: "Tiện ích", media: "Đa phương tiện", entertainment: "Game & giải trí", developer_tools: "Công cụ phát triển" };
const advancedGroupNames = { developer: "Dành cho lập trình", marketing: "Marketing", design: "Thiết kế", accounting: "Kế toán", ai: "Công cụ AI", office: "Văn phòng chuyên sâu", system: "Quản trị hệ thống" };
let selectedAction = null;
let selectedUninstallItem = null;
let pollTimer = null;
let pollInProgress = false;
let softwareInventory = new Map();
let softwareScanPromise = null;
let softwareViewLoaded = false;
let softwareNeedsRescan = false;
let softwareEventSource = null;
let softwareEventDebounce = null;
let selectedAudience = "general";
let softwareCatalog = [];
let activeSoftwareActions = new Map();
let softwareSearchQuery = "";
let softwareSearchTimer = null;
let patchNotesLoaded = false;
let systemSpecsLoaded = false;
let systemSpecsLoading = false;
let updateCheckStarted = false;
let updateProgressTimer = null;
let updateRetryTimer = null;
let pendingSupportDiagnostic = null;
let latestHealth = null;
let localAiPromptShown = false;

const byId = (id) => document.getElementById(id);

function reportClientError(errorType, message, source = null, line = null) {
  fetch("/api/debug/client-error", {
    method: "POST",
    keepalive: true,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      error_type: String(errorType || "JavaScriptError").slice(0, 80),
      message: String(message || "Lỗi giao diện không xác định").slice(0, 500),
      source: source ? String(source).split("/").pop().slice(0, 200) : null,
      line: Number.isInteger(line) && line >= 0 ? line : null,
    }),
  }).catch(() => {});
}

window.addEventListener("error", (event) => {
  reportClientError(event.error?.name, event.message, event.filename, event.lineno);
});
window.addEventListener("unhandledrejection", (event) => {
  const reason = event.reason;
  reportClientError(reason?.name || "UnhandledPromiseRejection", reason?.message || String(reason));
});

window.WinAssistDesktop = {
  showCloseDialog() {
    const dialog = byId("close-dialog");
    if (!dialog.open) dialog.showModal();
    return true;
  },
};
const iconPaths = {
  home: ["M3 10.5 12 3l9 7.5", "M5 9.5V21h14V9.5", "M9 21v-7h6v7"],
  chat: ["M4 5.5A2.5 2.5 0 0 1 6.5 3h11A2.5 2.5 0 0 1 20 5.5v8a2.5 2.5 0 0 1-2.5 2.5H10l-5 4v-4.5A2.5 2.5 0 0 1 4 13.5z"],
  apps: ["M4 4h6v6H4z", "M14 4h6v6h-6z", "M4 14h6v6H4z", "M14 14h6v6h-6z"],
  pulse: ["M3 12h4l2.2-5 4.2 10 2.1-5H21"],
  history: ["M4 5v5h5", "M5.5 17.5A8 8 0 1 0 5 7", "M12 7v5l3 2"],
  device: ["M4 5h16v11H4z", "M9 20h6", "M12 16v4"],
  battery: ["M5 7h13v10H5z", "M18 10h2v4h-2", "M8 10v4"],
  storage: ["M5 5h14v14H5z", "M8 15h8", "M15 9h1"],
  devices: ["M3 5h13v10H3z", "M7 19h5", "M9.5 15v4", "M19 8v8", "M17 10h4"],
  printer: ["M6 9V4h12v5", "M6 17H4V9h16v8h-2", "M6 14h12v6H6z", "M17 11h1"],
  update: ["M20 7v5h-5", "M4 17v-5h5", "M18.5 10A7 7 0 0 0 6 7.5L4 10", "M5.5 14A7 7 0 0 0 18 16.5l2-2.5"],
  clock: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18", "M12 7v5l3 2"],
  startup: ["M12 3v13", "m7 8 5-5 5 5", "M5 14v6h14v-6"],
  network: ["M5 9a10 10 0 0 1 14 0", "M8 12a6 6 0 0 1 8 0", "M11 15a2 2 0 0 1 2 0", "M12 19h.01"],
  speed: ["M4 17a8 8 0 1 1 16 0", "m12 14 4-4", "M8 17h8"],
  repair: ["M14 6a4 4 0 0 0-5 5L4 16l4 4 5-5a4 4 0 0 0 5-5l-3 1-2-2z"],
  download: ["M12 4v11", "m8 11 4 4 4-4", "M5 20h14"],
  trash: ["M5 7h14", "M9 7V4h6v3", "M7 7l1 13h8l1-13", "M10 11v5", "M14 11v5"],
  stop: ["M7 7h10v10H7z"],
  patch: ["M6 3h12v18H6z", "M9 8h6", "M9 12h6", "M9 16h4"],
  support: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18", "M9.8 9a2.3 2.3 0 1 1 3.4 2c-.8.5-1.2 1-1.2 2", "M12 17h.01"],
  cleanup: ["M4 7h16", "M7 7l1 13h8l1-13", "M9 4h6l1 3", "M10 11v5", "M14 11v5"],
};
function iconSvg(name, className = "") {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("aria-hidden", "true");
  svg.setAttribute("focusable", "false");
  if (className) svg.setAttribute("class", className);
  (iconPaths[name] || iconPaths.apps).forEach((pathData) => {
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pathData);
    svg.append(path);
  });
  return svg;
}
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function elapsed(createdAt) {
  const seconds = Math.max(0, Math.floor((Date.now() - new Date(createdAt).getTime()) / 1000));
  return seconds < 60 ? `${seconds} giây` : `${Math.floor(seconds / 60)} phút ${seconds % 60} giây`;
}

function switchView(name) {
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("active", view.id === `view-${name}`));
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === name));
  byId("view-title").textContent = { overview: "Tổng quan máy", chat: "Trợ lý", suggestions: "Tiện ích", diagnostics: "Chẩn đoán", cleanup: "Dọn dẹp máy", graphics: "Card màn hình", "windows-update": "Cập nhật Windows", activity: "Hoạt động", patches: "Cập nhật WinAssist", support: "Hỗ trợ", uninstall: "Gỡ WinAssist" }[name];
  if (name === "overview") loadSystemSpecs();
  if (name === "suggestions" && (!softwareViewLoaded || softwareNeedsRescan || state.activeActions.size)) {
    loadSoftware(!softwareViewLoaded, softwareNeedsRescan);
  }
  if (name === "diagnostics") {
    loadRepairs();
    loadWindowsCapabilities();
  }
  if (name === "activity") loadActivity();
  if (name === "cleanup") updateCleanupSelection();
  if (name === "patches") {
    loadLatestPatch();
    checkForUpdates();
  }
  if (name === "uninstall") loadUninstallStatus();
  if (name === "chat") promptForLocalAi();
}

async function promptForLocalAi() {
  if (localAiPromptShown || latestHealth?.ollama?.status === "available") return;
  localAiPromptShown = true;
  const dialog = byId("local-ai-dialog");
  const bridge = window.pywebview?.api;
  if (!dialog || dialog.open || !bridge) return;
  const nativeStatus = await bridge.local_ai_status().catch(() => ({}));
  byId("local-ai-title").textContent = nativeStatus.installed
    ? "Hoàn tất thiết lập Local AI"
    : "Cài trợ lý AI để dùng trợ lý thông minh";
  byId("install-local-ai").textContent = nativeStatus.installed
    ? "Khởi động và chuẩn bị model"
    : "Cài trợ lý AI";
  byId("local-ai-message").textContent = nativeStatus.installed
    ? "Ollama đã có trên máy. WinAssist chỉ cần khởi động Ollama và kiểm tra model AI."
    : (latestHealth?.ollama?.detail || "Chưa kiểm tra được trạng thái Ollama và model AI.");
  dialog.showModal();
}

async function installLocalAi() {
  const bridge = window.pywebview?.api;
  const button = byId("install-local-ai");
  const message = byId("local-ai-message");
  if (!bridge) {
    message.textContent = "Bản chạy này không có bộ cài native. Hãy dùng bản WinAssist đã cài bằng Setup.";
    return;
  }
  button.disabled = true;
  const backgroundButton = byId("skip-local-ai");
  backgroundButton.disabled = false;
  backgroundButton.textContent = "Chạy nền";
  try {
    const started = await bridge.install_local_ai();
    if (!started.success) throw new Error(started.message);
    const poll = async () => {
      const status = await bridge.local_ai_status();
      message.textContent = status.message;
      button.textContent = status.state === "pulling"
        ? status.message
        : (status.percent ? `${status.message} ${status.percent}%` : status.message);
      if (status.state === "ready") {
        byId("local-ai-dialog").close();
        backgroundButton.textContent = "Tiếp tục không dùng AI";
        showToast("Local AI đã sẵn sàng.", "success");
        try { latestHealth = await api.health(); } catch { latestHealth = null; }
        return;
      }
      if (status.state === "failed") {
        button.disabled = false;
        backgroundButton.textContent = "Đóng";
        button.textContent = "Thử cài lại";
        showToast(status.message, "error");
        return;
      }
      setTimeout(poll, 1000);
    };
    await poll();
  } catch (error) {
    message.textContent = `Không thể bắt đầu cài Local AI: ${error.message}`;
    button.disabled = false;
    backgroundButton.disabled = false;
    backgroundButton.textContent = "Đóng";
  }
}

async function loadUninstallStatus() {
  const button = byId("request-uninstall");
  const status = byId("uninstall-status");
  const bridge = window.pywebview?.api;
  if (!bridge) {
    button.disabled = true;
    status.textContent = "Chức năng này chỉ có trong ứng dụng WinAssist đã cài trên Windows.";
    return;
  }
  try {
    const response = await bridge.uninstall_status();
    button.disabled = !response.available;
    status.textContent = response.message;
  } catch (error) {
    button.disabled = true;
    status.textContent = "Không thể kiểm tra bộ gỡ cài đặt.";
  }
}

function specCard(label, value, detail = "") {
  const card = element("article", "spec-card");
  card.append(element("small", "", label), element("strong", "", value || "Không khả dụng"));
  if (detail) card.append(element("span", "", detail));
  return card;
}

async function loadSystemSpecs(force = false) {
  if (systemSpecsLoading || (!force && systemSpecsLoaded)) return;
  systemSpecsLoading = true;
  const refreshButton = byId("refresh-specs");
  refreshButton.disabled = true;
  refreshButton.textContent = "Đang đọc…";
  const root = byId("specs-content");
  const loading = element("div", "spec-loading");
  loading.append(element("div", "loader"), element("p", "", "Đang đọc thông số máy…"));
  root.replaceChildren(loading);
  try {
    const response = await api.systemSpecs();
    if (!response.available || !response.specs) throw new Error(response.message);
    const specs = response.specs;
    const identity = element("section", "device-summary");
    const name = element("div");
    name.append(
      element("h2", "", specs.device_name || "Máy tính Windows"),
      element("p", "muted", [specs.manufacturer, specs.model].filter(Boolean).join(" · ") || "Không có thông tin hãng/model"),
    );
    identity.append(name);
    const grid = element("div", "spec-grid");
    grid.append(
      specCard("Hệ điều hành", specs.os_name, [specs.architecture, specs.os_build ? `Build ${specs.os_build}` : ""].filter(Boolean).join(" · ")),
      specCard("Bộ xử lý", specs.cpu_name, specs.physical_cores != null ? `${specs.physical_cores} nhân · ${specs.logical_processors ?? "—"} luồng` : ""),
      specCard("Bộ nhớ RAM", specs.memory_gb != null ? `${specs.memory_gb} GB` : null),
      specCard("Đồ họa", specs.gpu_names?.join(" · ") || null),
      specCard(`Ổ hệ thống ${specs.system_drive || ""}`, specs.disk_size_gb != null ? `${specs.disk_size_gb} GB` : null, specs.disk_free_gb != null ? `Còn trống ${specs.disk_free_gb} GB` : ""),
      specCard("Phiên bản Windows", specs.os_version),
    );
    root.replaceChildren(identity, grid);
    systemSpecsLoaded = true;
  } catch (error) {
    const errorBox = element("div", "spec-error");
    errorBox.append(element("h3", "", "Không đọc được thông số máy"), element("p", "", error.message));
    root.replaceChildren(errorBox);
  } finally {
    systemSpecsLoading = false;
    refreshButton.disabled = false;
    refreshButton.textContent = "Đọc lại thông số";
  }
}

function addMessage(text, role = "assistant") {
  const article = element("article", `message ${role}`);
  const avatar = element("div", "avatar", role === "user" ? "Bạn" : "W");
  const bubble = element("div", "bubble");
  bubble.append(element("p", "", text));
  article.append(avatar, bubble);
  byId("chat-log").append(article);
  byId("chat-log").scrollTop = byId("chat-log").scrollHeight;
}

function addChatSuggestions(suggestions) {
  if (!suggestions?.length) return;
  const article = element("article", "message assistant");
  const avatar = element("div", "avatar", "W");
  const bubble = element("div", "bubble suggestion-bubble");
  bubble.append(element("p", "suggestion-title", "Bạn có thể chọn:"));
  const actions = element("div", "chat-suggestions");
  const allowedViews = new Set(["overview", "chat", "suggestions", "diagnostics", "cleanup", "graphics", "windows-update", "activity", "patches", "support"]);
  suggestions.forEach((suggestion) => {
    if (!suggestion.message && !allowedViews.has(suggestion.view)) return;
    const button = element("button", "chat-suggestion", suggestion.label);
    button.addEventListener("click", () => {
      if (suggestion.message) {
        byId("message-input").value = suggestion.message;
        byId("chat-form").requestSubmit();
      } else {
        switchView(suggestion.view);
      }
    });
    actions.append(button);
  });
  bubble.append(actions);
  article.append(avatar, bubble);
  byId("chat-log").append(article);
  byId("chat-log").scrollTop = byId("chat-log").scrollHeight;
}

function showToast(text, type = "info") {
  const toast = element("div", `toast ${type}`, text);
  byId("toast-region").append(toast);
  setTimeout(() => toast.remove(), 6500);
}

function openAction(action, title = "Xem lại thao tác") {
  selectedAction = action;
  state.trackAction(action.id);
  byId("action-title").textContent = title;
  const actionName = title === "Xem lại thao tác"
    ? "ứng dụng này"
    : title.replace(/^(Cài|Gỡ)\s+/i, "");
  const gameInstallIds = new Set([
    "steam", "epic-games", "gog-galaxy", "discord", "ea-app",
    "ubisoft-connect", "league-of-legends", "valorant",
  ]);
  const gameInstallSummary = `WinAssist sẽ tải và chạy installer chính thức của ${actionName} ngay trên máy. Sau khi cài launcher, bạn có thể cần đăng nhập và tải thêm dữ liệu game.`;
  const summaries = {
    software_install: action.resource_id === "microsoft-365"
      ? "WinAssist sẽ cài bộ Word, Excel và PowerPoint chính thức. Bạn cần tài khoản Microsoft 365 có bản quyền; WinAssist không kích hoạt bản quyền thay bạn."
      : (gameInstallIds.has(action.resource_id)
        ? gameInstallSummary
        : `WinAssist sẽ tải và cài ${actionName} từ nguồn ứng dụng Windows đã kiểm tra.`),
    software_uninstall: `WinAssist sẽ gỡ ${actionName} khỏi máy. Dữ liệu riêng của ứng dụng có thể vẫn được giữ lại.`,
    software_purge: `WinAssist sẽ gỡ ${actionName} và dọn file cài đặt còn sót. Tài khoản, thiết lập và file cá nhân vẫn được giữ nguyên.`,
    network_repair: "WinAssist sẽ thực hiện thao tác sửa kết nối mạng này.",
    windows_update: "WinAssist sẽ tìm, tải và cài các bản cập nhật Windows phù hợp. Máy sẽ không tự khởi động lại.",
    system_cleanup: "WinAssist chỉ xóa mục bạn đã chọn. File cá nhân vẫn được giữ nguyên.",
  };
  const buttonLabels = {
    software_install: "Cài đặt",
    software_uninstall: "Gỡ cài đặt",
    software_purge: "Gỡ sạch an toàn",
    network_repair: "Thực hiện",
    windows_update: "Bắt đầu cập nhật",
    system_cleanup: "Xác nhận dọn dẹp",
  };
  byId("action-summary").textContent = summaries[action.kind] || "WinAssist sẽ thực hiện thay đổi này trên máy.";
  byId("command-text").textContent = action.display_command;
  byId("command-warning").textContent = action.warning;
  byId("confirm-command").textContent = buttonLabels[action.kind] || "Tiếp tục";
  byId("confirm-command").className = ["software_uninstall", "software_purge"].includes(action.kind) ? "danger" : "primary";
  byId("action-dialog").querySelector("details").open = false;
  byId("action-dialog").showModal();
}

async function pollActions() {
  if (pollInProgress || !state.activeActions.size) return;
  pollInProgress = true;
  try {
    let rescanSoftware = false;
    await Promise.all([...state.activeActions].map(async (id) => {
      try {
        const status = await api.actionStatus(id);
        if (terminalStates.has(status.action.state)) {
          state.finishAction(id);
          const succeeded = status.action.state === "completed";
          showToast(
            `${status.action.resource_id}: ${status.message}`,
            succeeded ? "success" : "error",
          );
          if (["software_install", "software_uninstall", "software_purge"].includes(status.action.kind)) {
            rescanSoftware = true;
            softwareNeedsRescan = true;
          }
          if (status.action.kind === "windows_update" && document.querySelector("#view-windows-update.active")) {
            byId("open-windows-update").disabled = false;
            await scanWindowsUpdate();
          }
          if (status.action.kind === "system_cleanup" && document.querySelector("#view-cleanup.active")) {
            await scanCleanup();
          }
        }
      } catch { state.finishAction(id); }
    }));
    if (document.querySelector("#view-activity.active")) await loadActivity();
    if (document.querySelector("#view-suggestions.active")) await loadSoftware(false, rescanSoftware);
  } finally {
    pollInProgress = false;
  }
}

function startPolling() {
  clearInterval(pollTimer);
  pollTimer = setInterval(pollActions, 750);
  pollActions();
}

async function checkHealth() {
  try {
    const health = await api.health();
    latestHealth = health;
    byId("backend-status").textContent = "WinAssist đã sẵn sàng";
    byId("backend-status").title = `Phiên bản ${health.version}`;
    byId("backend-dot").className = "status-dot online";
    const availableHelp = health.ollama.status === "available"
      ? "Có thể trò chuyện và hỗ trợ máy"
      : "Có thể kiểm tra và cài ứng dụng";
    byId("ollama-status").textContent = `Phiên bản ${health.version} · ${availableHelp}`;
  } catch {
    latestHealth = null;
    byId("backend-status").textContent = "WinAssist chưa sẵn sàng";
    byId("backend-status").title = "";
    byId("ollama-status").textContent = "Hãy chờ một chút hoặc mở lại ứng dụng";
    byId("backend-dot").className = "status-dot offline";
  }
}

async function scanSoftwareInventory() {
  if (!softwareScanPromise) {
    softwareScanPromise = api.scanSoftware().finally(() => { softwareScanPromise = null; });
  }
  const inventory = await softwareScanPromise;
  softwareInventory = new Map(inventory.items.map((item) => [item.software.id, item]));
  return inventory;
}

function normalizeSearchText(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

function softwareMatchesSearch(item, query) {
  if (!query) return true;
  const groupName = item.advanced_group ? advancedGroupNames[item.advanced_group] : "";
  const categoryName = categoryNames[item.category] || "";
  return normalizeSearchText([
    item.display_name, item.publisher, item.description, item.id, groupName, categoryName,
  ].join(" ")).includes(query);
}

function renderSoftwareCatalog() {
  const root = byId("software-groups");
  const query = normalizeSearchText(softwareSearchQuery);
  const visibleSoftware = softwareCatalog
    .filter((item) => selectedAudience === "general"
      ? item.audience === "general"
      : item.audience === "advanced" || Boolean(item.advanced_group))
    .filter((item) => softwareMatchesSearch(item, query));
  const groups = new Map();
  visibleSoftware.forEach((item) => {
    const fallbackAdvancedGroup = item.category === "developer_tools"
      ? "developer"
      : (item.category === "office_pdf" ? "office" : "system");
    const group = selectedAudience === "advanced"
      ? (item.advanced_group || fallbackAdvancedGroup)
      : item.category;
    if (!groups.has(group)) groups.set(group, []);
    groups.get(group).push(item);
  });
  root.replaceChildren();
  const count = byId("software-search-count");
  if (count) count.textContent = query ? `${visibleSoftware.length} ứng dụng phù hợp` : "";
  if (!visibleSoftware.length) {
    const empty = element("div", "empty-state software-search-empty");
    empty.append(
      element("strong", "", "Không tìm thấy ứng dụng phù hợp"),
      element("p", "muted", "Thử tên khác hoặc mô tả việc bạn muốn làm, ví dụ: đọc PDF, chỉnh ảnh, kế toán."),
    );
    root.append(empty);
    return;
  }
  const advancedOrder = ["developer", "marketing", "design", "accounting", "ai", "office", "system"];
  const generalOrder = ["student", "browsers", "utilities", "office_pdf", "media", "entertainment"];
  const orderedGroups = [...groups.entries()].sort(([left], [right]) => {
    const order = selectedAudience === "advanced" ? advancedOrder : generalOrder;
    return order.indexOf(left) - order.indexOf(right);
  });
  orderedGroups.forEach(([category, items]) => {
    const section = element("section", "software-section");
    section.append(element("h2", "", selectedAudience === "advanced"
      ? (advancedGroupNames[category] || category)
      : (categoryNames[category] || category)));
    const grid = element("div", "software-grid");
    const riotItems = items.filter((item) => ["league-of-legends", "valorant"].includes(item.id));
    if (riotItems.length) grid.append(riotGamesCard(riotItems, activeSoftwareActions));
    items
      .filter((item) => !["league-of-legends", "valorant"].includes(item.id))
      .forEach((item) => grid.append(softwareCard(item, activeSoftwareActions.get(item.id), softwareInventory.get(item.id))));
    section.append(grid);
    root.append(section);
  });
}

async function loadSoftware(showLoading = true, rescan = true) {
  const root = byId("software-groups");
  if (showLoading) {
    const scanning = element("div", "inventory-loading");
    scanning.append(element("div", "loader"), element("div", "", ""));
    scanning.lastChild.append(
      element("strong", "", "Đang quét ứng dụng trên máy…"),
      element("p", "muted", "Danh sách sẽ hiện sau khi kiểm tra xong các ứng dụng."),
    );
    root.replaceChildren(scanning);
  }
  try {
    const shouldScan = rescan || softwareInventory.size === 0;
    const [software, actions] = await Promise.all([
      api.software(),
      api.actions(),
      shouldScan ? scanSoftwareInventory() : Promise.resolve(null),
    ]);
    softwareCatalog = software;
    activeSoftwareActions = new Map(actions.filter((item) => !terminalStates.has(item.action.state)).map((item) => [item.action.resource_id, item]));
    activeSoftwareActions.forEach((item) => state.trackAction(item.action.id));
    renderSoftwareCatalog();
    softwareViewLoaded = true;
    if (shouldScan) softwareNeedsRescan = false;
    const liveStatus = byId("software-live-text");
    if (liveStatus) {
      liveStatus.textContent = activeSoftwareActions.size
        ? `Đang theo dõi ${activeSoftwareActions.size} thao tác`
        : `Cập nhật lúc ${new Date().toLocaleTimeString("vi-VN")}`;
    }
  } catch (error) { root.replaceChildren(element("p", "error-text", `Không thể tải danh sách ứng dụng: ${error.message}`)); }
}

function startSoftwareEventStream() {
  if (softwareEventSource) return;
  softwareEventSource = api.softwareEvents();
  softwareEventSource.addEventListener("ready", (event) => {
    const payload = JSON.parse(event.data);
    const liveStatus = byId("software-live-text");
    if (liveStatus && !payload.watching) {
      liveStatus.textContent = "Theo dõi Registry chưa khả dụng";
    }
  });
  softwareEventSource.addEventListener("software_inventory_changed", () => {
    softwareNeedsRescan = true;
    const liveStatus = byId("software-live-text");
    if (liveStatus) liveStatus.textContent = "Windows vừa thay đổi ứng dụng…";
    clearTimeout(softwareEventDebounce);
    softwareEventDebounce = setTimeout(async () => {
      if (document.querySelector("#view-suggestions.active")) {
        await loadSoftware(false, true);
      }
    }, 600);
  });
  softwareEventSource.onerror = () => {
    const liveStatus = byId("software-live-text");
    if (liveStatus) liveStatus.textContent = "Đang kết nối lại theo dõi trực tiếp…";
  };
}

async function loadLatestPatch() {
  if (patchNotesLoaded) return;
  const root = byId("patch-content");
  try {
    const release = await api.latestPatch();
    const hero = element("article", "patch-hero");
    const version = element("span", "patch-version", `Phiên bản ${release.version}`);
    hero.append(
      version,
      element("h2", "", release.title),
      element("p", "", release.summary),
      element("small", "", `Phát hành ngày ${new Date(release.released_at).toLocaleDateString("vi-VN")}`),
    );
    const sections = element("div", "patch-grid");
    [
      ["Điểm mới", release.highlights],
      ["Đã sửa", release.fixes],
      ["An toàn", release.security],
    ].forEach(([title, items]) => {
      if (!items?.length) return;
      const card = element("section", "patch-card");
      card.append(element("h3", "", title));
      const list = element("ul");
      items.forEach((item) => list.append(element("li", "", item)));
      card.append(list);
      sections.append(card);
    });
    root.replaceChildren(hero, sections);
    patchNotesLoaded = true;
  } catch (error) {
    const message = error.message === "Not Found"
      ? "Backend đang chạy phiên bản cũ. Hãy khởi động lại WinAssist để kiểm tra cập nhật."
      : `Không thể tải thông tin phiên bản: ${error.message}`;
    const errorBox = element("div", "patch-error");
    errorBox.append(element("p", "error-text", message));
    const retry = element("button", "secondary", "Thử lại");
    retry.addEventListener("click", loadLatestPatch);
    errorBox.append(retry);
    root.replaceChildren(errorBox);
  }
}

async function checkForUpdates(showLoading = true) {
  if (updateCheckStarted && !showLoading) return;
  updateCheckStarted = true;
  const root = byId("update-status");
  const button = byId("check-update");
  if (showLoading) {
    button.disabled = true;
    button.textContent = "Đang kiểm tra…";
  }
  try {
    const status = await api.updateStatus();
    clearTimeout(updateRetryTimer);
    updateRetryTimer = null;
    if (status.update_required) showRequiredUpdate(status);
    const text = element("div");
    text.append(
      element("strong", "", status.update_available ? `Có WinAssist ${status.latest_version}` : "Trạng thái cập nhật"),
      element("p", "muted", status.message),
    );
    root.replaceChildren(text);
    if (status.update_available && status.installer_available) {
      const bridge = window.pywebview?.api;
      if (bridge && status.installer_sha256) {
        const update = element("button", "primary update-download", "Cập nhật ngay");
        update.addEventListener("click", () => startInAppUpdate(status, root));
        root.append(update);
      } else {
        const download = element("a", "primary update-download", "Tải bộ cài");
        download.href = status.installer_url;
        download.target = "_blank";
        download.rel = "noopener noreferrer";
        root.append(download);
      }
    } else {
      const retry = element("button", "secondary", "Kiểm tra lại");
      retry.addEventListener("click", () => checkForUpdates(true));
      root.append(retry);
    }
  } catch (error) {
    updateCheckStarted = false;
    root.firstElementChild?.querySelector("p")?.replaceChildren(`Không thể kiểm tra cập nhật: ${error.message}`);
    if (!showLoading && !updateRetryTimer) {
      updateRetryTimer = setTimeout(() => checkForUpdates(false), 30000);
    }
  } finally {
    button.disabled = false;
    button.textContent = "Kiểm tra ngay";
  }
}

function updateProgressView(root, progress, allowCancel = true) {
  const box = element("div", "self-update-progress");
  const row = element("div", "self-update-row");
  row.append(
    element("strong", "", progress.state === "ready" ? "Đã tải xong" : "Đang cập nhật WinAssist"),
    element("span", "", progress.total_bytes ? `${progress.percent}%` : "Đang tải dữ liệu…"),
  );
  const track = element("div", "self-update-track");
  const fill = element("span", progress.total_bytes ? "" : "indeterminate");
  if (progress.total_bytes) fill.style.width = `${progress.percent}%`;
  track.append(fill);
  box.append(row, track, element("p", "muted", progress.message));
  if (progress.state === "downloading" && allowCancel) {
    const cancel = element("button", "secondary self-update-cancel", "Hủy tải");
    cancel.addEventListener("click", async () => {
      cancel.disabled = true;
      await window.pywebview.api.cancel_update();
    });
    box.append(cancel);
  }
  root.replaceChildren(box);
}

function showUpdateFailure(root, status, error, required = false) {
  const controls = element("div", "dialog-actions");
  const retry = element("button", "secondary", "Thử lại");
  retry.addEventListener("click", () => checkForUpdates(true));
  controls.append(retry);
  if (required && status.installer_url) {
    const download = element("button", "primary", "Tải từ trang chính thức");
    download.addEventListener("click", () => {
      window.open(status.installer_url, "_blank", "noopener,noreferrer");
      download.textContent = "Đã mở trang tải";
    });
    controls.append(download);
  }
  root.replaceChildren(
    element("p", "error-text", `Không thể cập nhật: ${error.message}`),
    controls,
  );
}

async function startInAppUpdate(status, root, allowCancel = true) {
  const bridge = window.pywebview?.api;
  if (!bridge) return;
  root.replaceChildren(element("div", "inventory-loading"));
  root.firstElementChild.append(element("div", "loader"), element("p", "", "Đang chuẩn bị tải an toàn…"));
  try {
    const started = await bridge.start_update(status.installer_url, status.latest_version, status.installer_sha256);
    if (!started.success) throw new Error(started.message);
    clearInterval(updateProgressTimer);
    updateProgressTimer = setInterval(async () => {
      try {
        const progress = await bridge.update_status();
        updateProgressView(root, progress, allowCancel);
        if (progress.state === "ready") {
          clearInterval(updateProgressTimer);
          updateProgressTimer = null;
          root.querySelector("p").textContent = "Đã kiểm tra an toàn. WinAssist sẽ đóng và tự mở lại sau khi cập nhật.";
          const installed = await bridge.install_update();
          if (!installed.success) throw new Error(installed.message);
        } else if (["failed", "cancelled"].includes(progress.state)) {
          clearInterval(updateProgressTimer);
          updateProgressTimer = null;
          const retry = element("button", "secondary", "Thử lại");
          retry.addEventListener("click", () => checkForUpdates(true));
          root.append(retry);
        }
      } catch (error) {
        clearInterval(updateProgressTimer);
        updateProgressTimer = null;
        showUpdateFailure(root, status, error, !allowCancel);
      }
    }, 500);
  } catch (error) {
    showUpdateFailure(root, status, error, !allowCancel);
  }
}

function showRequiredUpdate(status) {
  const dialog = byId("required-update-dialog");
  const message = byId("required-update-message");
  const action = byId("required-update-action");
  const progress = byId("required-update-progress");
  message.textContent = `Phiên bản ${status.latest_version} là bản bắt buộc. Hãy cập nhật để tiếp tục sử dụng WinAssist.`;
  progress.replaceChildren();
  action.disabled = false;
  action.hidden = false;
  action.textContent = window.pywebview?.api && status.installer_sha256 ? "Cập nhật ngay" : "Tải bản mới nhất";
  action.onclick = async () => {
    if (window.pywebview?.api && status.installer_sha256) {
      action.hidden = true;
      await startInAppUpdate(status, progress, false);
      return;
    }
    window.open(status.installer_url, "_blank", "noopener,noreferrer");
    action.textContent = "Đang chờ bạn cài bản mới";
  };
  if (!dialog.open) dialog.showModal();
}

async function scanGraphicsDriver() {
  const button = byId("scan-graphics-driver");
  const root = byId("graphics-driver-result");
  button.disabled = true;
  button.textContent = "Đang kiểm tra…";
  const loading = element("div", "inventory-loading");
  loading.append(element("div", "loader"), element("p", "", "Đang kiểm tra card màn hình và phiên bản hiện tại…"));
  root.replaceChildren(loading);
  try {
    const response = await api.graphicsDriver();
    if (!response.available || !response.adapters.length) {
      root.replaceChildren(element("div", "driver-notice", response.message));
      return;
    }
    const notice = element("div", "driver-notice");
    notice.append(
      element("strong", "", "Đã nhận diện card màn hình"),
      element("p", "muted", "WinAssist không tự cài driver ở bước này. Công cụ chính hãng có thể mở cửa sổ hoặc trình duyệt riêng để hoàn tất cập nhật. Với laptop, hãy ưu tiên bản do hãng máy hoặc Windows Update đề xuất."),
    );
    const grid = element("div", "driver-grid");
    const toolNames = {
      NVIDIA: "NVIDIA App",
      AMD: "AMD Software",
      Intel: "Intel Driver Assistant",
    };
    response.adapters.forEach((adapter) => {
      const card = element("article", "driver-card");
      const toolName = toolNames[adapter.vendor] || `công cụ ${adapter.vendor}`;
      card.append(
        element("h3", "", adapter.name),
        element("p", "driver-version", adapter.driver_version ? `Phiên bản hiện tại: ${adapter.driver_version}` : "Chưa đọc được phiên bản hiện tại"),
        element("p", `driver-tool-status ${adapter.management_app_installed ? "installed" : "missing"}`, adapter.management_app_installed ? `${toolName} đã có trên máy` : `${toolName} chưa có trên máy`),
        element("p", "muted", adapter.recommendation),
      );
      if (adapter.management_app_installed) {
        const open = element("button", "primary driver-download", `Mở ${toolName}`);
        open.addEventListener("click", async () => {
          open.disabled = true;
          try {
            const response = await api.openGraphicsApp(adapter.vendor);
            showToast(response.message, response.success ? "success" : "error");
          } catch (error) {
            showToast(`Không thể mở ứng dụng: ${error.message}`, "error");
          } finally { open.disabled = false; }
        });
        card.append(open);
      } else {
        const link = element("a", "primary driver-download", "Mở trang tải chính hãng");
        link.href = adapter.download_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        card.append(link);
      }
      grid.append(card);
    });
    root.replaceChildren(notice, grid);
  } catch (error) {
    root.replaceChildren(element("p", "error-text", `Không thể kiểm tra card màn hình: ${error.message}`));
  } finally {
    button.disabled = false;
    button.textContent = "Kiểm tra lại";
  }
}

function riotGamesCard(items, activeByResource) {
  const card = element("article", "software-card riot-group-card");
  const head = element("div", "software-head");
  const title = element("div");
  title.append(
    element("h3", "", "Riot Games"),
    element("p", "muted", "League of Legends và VALORANT dùng chung Riot Client"),
  );
  head.append(title);
  const options = element("div", "riot-game-options");
  items.forEach((item) => {
    const option = softwareCard(
      item,
      activeByResource.get(item.id),
      softwareInventory.get(item.id),
    );
    option.classList.add("riot-game-option");
    options.append(option);
  });
  card.append(head, options);
  return card;
}

function softwareCard(item, active, inventory) {
  const card = element("article", "software-card");
  const head = element("div", "software-head");
  const title = element("div");
  title.append(
    element("h3", "", item.display_name),
    element("p", "muted", item.publisher),
    element("p", "software-description", item.description),
  );
  head.append(title);
  const statusText = active
    ? `${active.message} · ${elapsed(active.action.created_at)}`
    : (inventory?.status || "Không xác định");
  const status = element("p", `software-status ${inventory?.installed ? "installed" : "not-installed"}`, statusText);
  const actions = element("div", "icon-actions");
  const install = element("button", "icon-button");
  install.append(iconSvg("download"), element("span", "", "Cài"));
  install.title = `Cài ${item.display_name}`;
  install.setAttribute("aria-label", install.title);
  install.addEventListener("click", () => prepareSoftware(item, "install"));
  install.disabled = Boolean(inventory?.installed) || Boolean(active);
  const remove = element("button", "icon-button remove");
  remove.append(iconSvg("trash"), element("span", "", "Gỡ"));
  remove.title = `Gỡ ${item.display_name}`;
  remove.setAttribute("aria-label", remove.title);
  remove.addEventListener("click", () => {
    if (item.cleanup_available) openUninstallChoice(item);
    else prepareSoftware(item, "uninstall");
  });
  remove.disabled = !inventory?.installed || Boolean(active);
  actions.append(install, remove);
  if (active) {
    const cancel = element("button", "icon-button cancel");
    cancel.append(iconSvg("stop"), element("span", "", "Hủy"));
    cancel.title = active.action.state === "pending"
      ? "Hủy yêu cầu đang chờ"
      : (active.action.state === "cancelling"
        ? "Installer đang được dừng"
        : "Dừng installer đang chạy");
    cancel.setAttribute("aria-label", cancel.title);
    cancel.disabled = active.action.state === "cancelling";
    cancel.addEventListener("click", async () => {
      cancel.disabled = true;
      try {
        const response = await api.cancelAction(active.action.id);
        if (terminalStates.has(response.action.state)) {
          state.finishAction(active.action.id);
        } else {
          state.trackAction(active.action.id);
        }
        showToast(`${item.display_name}: ${response.message}`, "info");
      } catch (error) {
        addMessage(`Không thể hủy: ${error.message}`);
      }
      await loadSoftware(false, false);
    });
    actions.prepend(cancel);
    card.append(head, status);
    if (active.action.state === "executing" || active.action.state === "cancelling") {
      const progress = element("div", "progress");
      progress.append(element(
        "span",
        active.action.state === "cancelling"
          ? "indeterminate cancelling"
          : "indeterminate",
      ));
      card.append(progress);
      if (active.action.state === "cancelling") {
        card.append(element("p", "pending-label", "Đang dừng installer…"));
      }
    } else {
      card.append(element("p", "pending-label", "Đang chờ xác nhận — chưa tải xuống"));
    }
    card.append(actions);
  } else card.append(head, status, actions);
  return card;
}

async function prepareSoftware(item, operation) {
  try {
    const result = operation === "install"
      ? await api.installSoftware(item.id)
      : (operation === "purge" ? await api.purgeSoftware(item.id) : await api.uninstallSoftware(item.id));
    if (result.pending_action) openAction(result.pending_action, `${operation === "install" ? "Cài" : "Gỡ"} ${item.display_name}`);
    else {
      addMessage(result.message);
      showToast(result.message, "info");
      await loadSoftware(true, true);
    }
  } catch (error) { addMessage(`Không thể chuẩn bị thao tác: ${error.message}`); switchView("chat"); }
}

function openUninstallChoice(item) {
  selectedUninstallItem = item;
  byId("uninstall-choice-title").textContent = `Gỡ ${item.display_name}`;
  const normal = document.querySelector('input[name="uninstall-choice"][value="uninstall"]');
  if (normal) normal.checked = true;
  byId("uninstall-choice-dialog").showModal();
}

async function loadRepairs() {
  const root = byId("repair-list");
  try {
    const repairs = await api.repairs();
    root.replaceChildren(...repairs.map((repair) => {
      const card = element("article", "card");
      card.append(element("h3", "", repair.display_name), element("p", "", repair.description));
      const button = element("button", "secondary", "Chuẩn bị");
      button.addEventListener("click", async () => {
        try { const response = await api.requestRepair(repair.id); openAction(response.pending_action, repair.display_name); }
        catch (error) { showDiagnosticError(error); }
      });
      card.append(button); return card;
    }));
  } catch (error) { root.replaceChildren(element("p", "error-text", error.message)); }
}

async function loadWindowsCapabilities() {
  const root = byId("windows-capabilities");
  root.replaceChildren(element("p", "muted", "Đang chuẩn bị các mục kiểm tra…"));
  try {
    const capabilities = await api.windowsCapabilities();
    root.replaceChildren(...capabilities.filter((capability) => capability.id !== "update").map((capability) => {
      const card = element("article", "card windows-card");
      card.dataset.capabilityId = capability.id;
      const title = element("div", "windows-card-title");
      title.append(
        element("h3", "", capability.title),
        element("span", "read-only-badge", "Chỉ đọc"),
      );
      const header = element("div", "windows-card-header");
      header.append(title);
      card.append(
        header,
        element("p", "windows-card-description", "Xem trạng thái và lời giải thích dễ hiểu mà không thay đổi thiết lập."),
      );
      const button = element("button", "secondary windows-check-button", "Kiểm tra ngay");
      const result = element("div", "windows-inline-result");
      result.hidden = true;
      button.addEventListener("click", () => runWindowsCapability(capability.id, button, result));
      card.append(button, result);
      return card;
    }));
  } catch (error) {
    root.replaceChildren(element("p", "error-text", error.message));
  }
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 MB";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${new Intl.NumberFormat(window.WinAssistI18n?.language === "en" ? "en-US" : "vi-VN", { maximumFractionDigits: unit < 2 ? 0 : 1 }).format(value)} ${units[unit]}`;
}

function updateCleanupSelection() {
  const selected = [...document.querySelectorAll("[data-cleanup-category]:checked")];
  const bytes = selected.reduce((total, input) => total + Number(input.dataset.bytes || 0), 0);
  byId("cleanup-total").textContent = selected.length
    ? `Đã chọn ${selected.length} mục · khoảng ${formatBytes(bytes)}`
    : "Chưa chọn mục nào";
  byId("request-cleanup").disabled = selected.length === 0;
}

async function scanCleanup() {
  const button = byId("scan-cleanup");
  const root = byId("cleanup-result");
  button.disabled = true;
  button.textContent = "Đang kiểm tra…";
  root.replaceChildren(element("div", "inventory-loading", "Đang kiểm tra…"));
  try {
    const response = await api.scanCleanup();
    const fragment = document.createDocumentFragment();
    response.categories.forEach((category) => {
      const label = element("label", "cleanup-option");
      const input = document.createElement("input");
      input.type = "checkbox";
      input.dataset.cleanupCategory = category.id;
      input.dataset.bytes = category.bytes;
      input.disabled = category.file_count === 0;
      input.addEventListener("change", updateCleanupSelection);
      const copy = element("span", "cleanup-option-copy");
      copy.append(
        element("strong", "", category.title),
        element("span", "", category.description),
        element("small", "", category.file_count
          ? `${category.file_count} file · ${formatBytes(category.bytes)}`
          : "Không có mục cần xóa"),
      );
      label.append(input, copy);
      fragment.append(label);
    });
    root.replaceChildren(fragment);
    updateCleanupSelection();
  } catch (error) {
    root.replaceChildren(element("div", "driver-notice", `Không thể kiểm tra: ${error.message}`));
  } finally {
    button.disabled = false;
    button.textContent = "Kiểm tra lại";
  }
}

async function requestCleanup() {
  const categories = [...document.querySelectorAll("[data-cleanup-category]:checked")]
    .map((input) => input.dataset.cleanupCategory);
  if (!categories.length) return;
  try {
    const response = await api.requestCleanup(categories);
    openAction(response.pending_action, "Dọn dẹp máy");
  } catch (error) {
    showToast(`Không thể chuẩn bị dọn dẹp: ${error.message}`, "error");
  }
}

function windowsResultTarget(capabilityId) {
  const card = document.querySelector(
    `.windows-card[data-capability-id="${CSS.escape(capabilityId)}"]`,
  );
  return card?.querySelector(".windows-inline-result") || null;
}

function renderWindowsResult(capability, target = windowsResultTarget(capability.id)) {
  if (!target) return;
  target.hidden = false;
  const block = element("div", `capability-result ${capability.state}`);
  const heading = element("div", "capability-heading");
  heading.append(
    element("span", `capability-badge ${capability.state}`, {
      available: "Bình thường",
      warning: "Cần chú ý",
      unavailable: "Không có trên máy",
      error: "Không kiểm tra được",
    }[capability.state] || capability.state),
  );
  block.append(
    heading,
    element("p", "", capability.summary),
    renderCapabilityDetails(capability),
  );
  (capability.recommendations || []).forEach((recommendation) => {
    block.append(element("p", "friendly-recommendation", `Đề xuất: ${recommendation}`));
  });
  const details = element("details");
  details.append(
    element("summary", "", "Xem dữ liệu kỹ thuật"),
    element("pre", "", JSON.stringify(capability.data, null, 2)),
  );
  block.append(details);
  target.replaceChildren(block);
}

function renderWindowsResults(capabilities) {
  capabilities.forEach((capability) => renderWindowsResult(capability));
}

function detailItem(label, value, note = "") {
  const item = element("div", "friendly-detail");
  item.append(element("small", "", label), element("strong", "", value || "Không xác định"));
  if (note) item.append(element("span", "", note));
  return item;
}

function formatCapacity(bytes) {
  if (bytes == null || Number.isNaN(Number(bytes))) return "Không xác định";
  return `${(Number(bytes) / (1024 ** 3)).toFixed(1)} GB`;
}

function formatUpdateDate(value) {
  if (!value) return "Không rõ ngày cài";
  const legacy = String(value).match(/^\/Date\((\d+)(?:[+-]\d+)?\)\/$/);
  const date = new Date(legacy ? Number(legacy[1]) : value);
  return Number.isNaN(date.getTime()) ? "Không rõ ngày cài" : `Cài ngày ${date.toLocaleDateString("vi-VN")}`;
}

function renderCapabilityDetails(capability) {
  const grid = element("div", "friendly-grid");
  const data = capability.data || {};
  if (capability.id === "battery") {
    const statusNames = { 1: "Đang xả pin", 2: "Đang cắm sạc", 3: "Đã sạc đầy", 6: "Đang sạc", 7: "Đang sạc và mức cao", 8: "Đang sạc và mức thấp" };
    (data.batteries || []).forEach((battery, index) => {
      grid.append(detailItem(
        battery.Name || `Pin ${index + 1}`,
        battery.EstimatedChargeRemaining != null ? `${battery.EstimatedChargeRemaining}%` : "Không đọc được mức pin",
        statusNames[battery.BatteryStatus] || "Windows chưa xác định trạng thái sạc",
      ));
    });
  } else if (capability.id === "storage") {
    (data.drives || []).forEach((drive) => {
      const percent = drive.Size ? Math.round((Number(drive.FreeSpace) / Number(drive.Size)) * 100) : null;
      grid.append(detailItem(
        `Ổ ${drive.DeviceID || ""} ${drive.VolumeName || ""}`.trim(),
        `Còn ${formatCapacity(drive.FreeSpace)}`,
        `${percent ?? "—"}% trống trên tổng ${formatCapacity(drive.Size)}`,
      ));
    });
  } else if (capability.id === "devices") {
    const classNames = { AudioEndpoint: "Âm thanh / microphone", Media: "Thiết bị media", Camera: "Camera", Image: "Thiết bị hình ảnh", Bluetooth: "Bluetooth" };
    (data.devices || []).forEach((device) => {
      const healthy = String(device.Status || "").toLowerCase() === "ok";
      grid.append(detailItem(
        classNames[device.Class] || device.Class || "Thiết bị",
        device.FriendlyName || "Không có tên thiết bị",
        healthy ? "Hoạt động bình thường" : `Cần kiểm tra · trạng thái ${device.Status || "không xác định"}`,
      ));
    });
  } else if (capability.id === "printers") {
    (data.printers || []).forEach((printer) => {
      grid.append(detailItem(
        printer.Name || "Máy in",
        `${printer.JobCount || 0} lệnh đang chờ`,
        `${printer.DriverName || "Không rõ driver"} · ${printer.PrinterStatus || "Không rõ trạng thái"}`,
      ));
    });
  } else if (capability.id === "update") {
    if (data.update_check_succeeded) {
      const count = Number(data.available_update_count || 0);
      grid.append(detailItem(
        "Bản cập nhật mới",
        count ? `${count} bản đang chờ` : "Không có",
        count ? "Bạn có thể xem và cài bằng nút bên dưới." : "Máy đang dùng các bản cập nhật mới nhất mà Windows tìm thấy.",
      ));
      (data.available_updates || []).forEach((update, index) => {
        const kb = Array.isArray(update.kb) && update.kb.length
          ? `KB${update.kb.join(", KB")}`
          : "Windows không cung cấp mã KB";
        grid.append(detailItem(
          `Bản cập nhật ${index + 1}`,
          update.title || "Bản cập nhật Windows",
          update.severity ? `${kb} · Mức độ: ${update.severity}` : kb,
        ));
      });
    } else {
      grid.append(detailItem(
        "Bản cập nhật mới",
        "Chưa kiểm tra được",
        "Hãy thử kiểm tra lại hoặc mở Windows Update.",
      ));
    }
    grid.append(detailItem(
      "Máy có cần khởi động lại?",
      data.reboot_pending ? "Có" : "Không",
      data.reboot_pending ? "Hãy lưu công việc trước khi khởi động lại." : "Bạn có thể tiếp tục sử dụng máy bình thường.",
    ));
    if (data.latest_hotfix) {
      grid.append(detailItem(
        "Lần cập nhật gần nhất",
        data.latest_hotfix.HotFixID || "Không xác định",
        formatUpdateDate(data.latest_hotfix.InstalledOn),
      ));
    }
  } else if (capability.id === "datetime") {
    const local = data.local_time ? new Date(data.local_time).toLocaleString("vi-VN") : "Không xác định";
    grid.append(
      detailItem("Ngày giờ hiện tại", local),
      detailItem("Múi giờ", data.timezone_name || data.timezone_id, `Độ lệch UTC: ${data.utc_offset || "—"}`),
    );
  } else if (capability.id === "startup") {
    (data.apps || []).forEach((app) => {
      grid.append(detailItem(app.Name || "Ứng dụng không có tên", "Tự chạy cùng Windows"));
    });
  }
  if (!grid.children.length) {
    grid.append(element("p", "friendly-empty", "Không phát hiện thành phần nào trong nhóm này."));
  }
  return grid;
}

async function runWindowsCapability(id, button, target) {
  button.disabled = true;
  target.hidden = false;
  target.replaceChildren(element("div", "loader"), element("p", "", "Đang kiểm tra…"));
  try {
    renderWindowsResult(await api.inspectWindows(id), target);
  } catch (error) {
    target.replaceChildren(element("p", "error-text", `Không thể chạy: ${error.message}`));
  } finally {
    button.disabled = false;
  }
}

async function scanWindowsUpdate() {
  const button = byId("scan-windows-update");
  const target = byId("windows-update-result");
  button.disabled = true;
  button.textContent = "Đang kiểm tra…";
  target.replaceChildren(element("div", "loader"), element("p", "", "Đang tìm các bản cập nhật mới… Việc này có thể mất vài phút."));
  try {
    renderWindowsResult(await api.inspectWindows("update"), target);
  } catch (error) {
    target.replaceChildren(element("p", "error-text", `Không thể kiểm tra: ${error.message}`));
  } finally {
    button.disabled = false;
    button.textContent = "Kiểm tra lại";
  }
}

async function installWindowsUpdates() {
  const button = byId("open-windows-update");
  button.disabled = true;
  try {
    const response = await api.installWindowsUpdates();
    openAction(response.pending_action, "Cập nhật Windows");
  } catch (error) {
    showToast(`Chưa thể chuẩn bị cập nhật: ${error.message}`, "error");
  } finally { button.disabled = false; }
}

function formatNetworkNumber(value, maximumFractionDigits = 1) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
  const locale = window.WinAssistI18n?.language === "en" ? "en-US" : "vi-VN";
  return new Intl.NumberFormat(locale, { maximumFractionDigits }).format(Number(value));
}

async function runDiagnostic(type, button) {
  const panel = byId("diagnostic-result");
  button.disabled = true;
  panel.hidden = false;
  panel.replaceChildren(element("div", "loader"), element("p", "", "Đang chạy kiểm tra…"));
  try {
    const result = type === "network" ? await api.network() : await api.speedtest();
    panel.replaceChildren(element("h3", "", result.summary || result.message));
    if (result.measurement) {
      const metrics = element("div", "metrics");
      [
        ["Tốc độ tải xuống", `${formatNetworkNumber(result.measurement.download_mbps)} Mbps`, "Càng cao càng nhanh"],
        ["Tốc độ tải lên", `${formatNetworkNumber(result.measurement.upload_mbps)} Mbps`, "Càng cao càng nhanh"],
        ["Độ trễ (Ping)", `${formatNetworkNumber(result.measurement.ping_ms)} ms`, "Càng thấp càng phản hồi nhanh"],
        ["Độ dao động (Jitter)", `${formatNetworkNumber(result.measurement.jitter_ms)} ms`, "Càng thấp càng ổn định"],
      ].forEach(([key, value, hint]) => {
        const metric = element("div", "metric");
        metric.append(element("small", "", key), element("strong", "", value), element("span", "metric-hint", hint));
        metrics.append(metric);
      });
      panel.append(metrics);
    }
    (result.findings || []).forEach((finding) => panel.append(element("p", "", `${finding.title}: ${finding.detail}`)));
    if (result.install_software_id) {
      const install = element("button", "primary", "Cài Speedtest để đo");
      install.addEventListener("click", async () => {
        install.disabled = true;
        try {
          const prepared = await api.installSoftware(result.install_software_id);
          if (prepared.pending_action) {
            openAction(prepared.pending_action, `Cài ${prepared.software.display_name}`);
          } else {
            panel.append(element("p", "", prepared.message));
          }
        } catch (error) {
          panel.append(element("p", "error-text", `Không thể chuẩn bị cài Speedtest: ${error.message}`));
        } finally {
          install.disabled = false;
        }
      });
      panel.append(install);
    }
  } catch (error) { showDiagnosticError(error); } finally { button.disabled = false; }
}
function showDiagnosticError(error) { const panel = byId("diagnostic-result"); panel.hidden = false; panel.replaceChildren(element("p", "error-text", `Không thể chạy: ${error.message}`)); }

function activityTitle(item, catalogNames) {
  const resource = item.action.resource_id;
  const appName = catalogNames.get(resource)
    || resource.replace(/^cleanup:/, "").replaceAll("-", " ");
  const titles = {
    software_install: `Cài ${appName}`,
    software_uninstall: `Gỡ ${appName}`,
    software_purge: `Gỡ sạch ${appName}`,
    windows_update: "Cập nhật Windows",
    system_cleanup: "Dọn dẹp máy",
  };
  if (titles[item.action.kind]) return titles[item.action.kind];
  if (item.action.kind === "network_repair") {
    return {
      "flush-dns": "Làm mới kết nối tên miền",
      "release-ip": "Làm mới địa chỉ mạng",
      "renew-ip": "Xin lại địa chỉ mạng",
    }[resource] || "Sửa kết nối mạng";
  }
  return "Thao tác trên máy";
}

function activityMessage(item) {
  if (item.action.state === "expired") {
    return "Bạn chưa xác nhận kịp thời nên WinAssist đã tự hủy yêu cầu. Máy không bị thay đổi.";
  }
  if (item.action.state === "cancelled") return "Yêu cầu đã được hủy. Máy không bị thay đổi thêm.";
  if (item.action.state === "completed" && item.message === "Thao tác đã hoàn tất.") {
    return {
      software_install: "Ứng dụng đã được cài và WinAssist đã kiểm tra lại trạng thái.",
      software_uninstall: "Ứng dụng đã được gỡ và WinAssist đã kiểm tra lại trạng thái.",
      software_purge: "Ứng dụng và các dữ liệu an toàn đã chọn đã được dọn.",
      network_repair: "Đã hoàn thành thao tác sửa kết nối mạng.",
      windows_update: "Windows đã hoàn thành tác vụ cập nhật. Hãy xem tab Cập nhật Windows để biết có cần khởi động lại không.",
      system_cleanup: "Đã xóa mục bạn chọn.",
    }[item.action.kind] || "Thao tác đã hoàn tất.";
  }
  return item.message;
}

function activityTechnicalDetails(item) {
  const details = element("details", "technical-details activity-technical-details");
  details.append(element("summary", "", "Thông tin kỹ thuật"));
  const list = element("dl", "activity-debug-list");
  const add = (label, value) => {
    list.append(element("dt", "", label), element("dd", "", String(value)));
  };
  add("Mã hành động", item.action.id);
  add("Loại thao tác", item.action.kind);
  add("Mã lệnh", item.action.command_id);
  if (item.result) {
    add("Kết quả", item.result.exit_code ?? "Không có mã trả về");
    if (item.result.timed_out) add("Thời gian", "Đã quá thời gian chờ");
  }
  details.append(list);
  const commandDetails = element("details", "activity-command-details");
  commandDetails.append(
    element("summary", "", "Xem lệnh hệ thống"),
    element("code", "activity-command", item.action.display_command),
  );
  details.append(commandDetails);
  if (item.result?.stderr) {
    const errorDetails = element("details", "activity-command-details");
    errorDetails.append(
      element("summary", "", "Chi tiết lỗi"),
      element("code", "activity-command", item.result.stderr.slice(0, 2000)),
    );
    details.append(errorDetails);
  }
  return details;
}

async function loadActivity() {
  const root = byId("activity-list");
  try {
    const actions = await api.actions();
    const catalog = await api.software().catch(() => []);
    const catalogNames = new Map(catalog.map((software) => [software.id, software.display_name]));
    if (!actions.length) { root.replaceChildren(element("div", "empty-state", "Chưa có hoạt động nào.")); return; }
    const stateNames = {
      pending: "Chờ xác nhận",
      executing: "Đang chạy",
      cancelling: "Đang hủy",
      completed: "Hoàn tất",
      failed: "Thất bại",
      cancelled: "Đã hủy",
      expired: "Hết hạn",
    };
    root.replaceChildren(...actions.map((item) => {
      const row = element("article", "activity-row");
      const info = element("div");
      const created = new Date(item.action.created_at).toLocaleString(
        window.WinAssistI18n?.language === "en" ? "en-US" : "vi-VN",
        { dateStyle: "short", timeStyle: "short" },
      );
      info.append(
        element("strong", "activity-title", activityTitle(item, catalogNames)),
        element("p", "activity-message", activityMessage(item)),
        element("p", "muted activity-time", `Bắt đầu lúc ${created} · cách đây ${elapsed(item.action.created_at)}`),
      );
      if (item.failure_summary) {
        const explanation = element("div", "activity-failure");
        explanation.append(element("strong", "", item.failure_summary));
        (item.failure_suggestions || []).forEach((suggestion) => explanation.append(element("p", "", suggestion)));
        const failureActions = element("div", "activity-failure-actions");
        const details = element("details", "technical-details");
        details.append(
          element("summary", "", "Xem mã lỗi"),
          element("code", "", `Exit code: ${item.result?.exit_code ?? "không có"}${item.result?.timed_out ? " · quá thời gian" : ""}`),
        );
        const report = element("button", "secondary", "Báo lỗi này");
        report.addEventListener("click", () => prepareFailedActionReport(item));
        failureActions.append(details, report);
        explanation.append(failureActions);
        info.append(explanation);
      }
      info.append(activityTechnicalDetails(item));
      const badge = element("span", `badge ${item.action.state}`, stateNames[item.action.state] || item.action.state);
      row.append(info, badge);
      if (item.indeterminate) { const progress = element("div", "progress wide"); progress.append(element("span", "indeterminate")); row.append(progress); }
      return row;
    }));
  } catch (error) { root.replaceChildren(element("p", "error-text", error.message)); }
}

function prepareFailedActionReport(item) {
  pendingSupportDiagnostic = {
    action_id: item.action.id,
    action_kind: item.action.kind,
    resource_id: item.action.resource_id,
    command_id: item.result?.command_id || item.action.command_id,
    exit_code: item.result?.exit_code ?? null,
    timed_out: Boolean(item.result?.timed_out),
    failure_summary: item.failure_summary || "Thao tác không hoàn tất.",
  };
  byId("support-issue-type").value = ["software_uninstall", "software_purge"].includes(item.action.kind) ? "uninstall" : "install";
  byId("support-description").value = `Tôi gặp lỗi khi dùng WinAssist: ${pendingSupportDiagnostic.failure_summary}\n\nMô tả thêm: `;
  byId("support-diagnostic-note").hidden = false;
  switchView("support");
  byId("support-description").focus();
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
document.querySelectorAll("[data-view-target]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.viewTarget)));
document.querySelectorAll("[data-message]").forEach((button) => button.addEventListener("click", () => { byId("message-input").value = button.dataset.message; byId("message-input").focus(); }));
document.querySelectorAll(".diagnostic-run").forEach((button) => button.addEventListener("click", () => runDiagnostic(button.dataset.diagnostic, button)));
byId("scan-graphics-driver").addEventListener("click", scanGraphicsDriver);
byId("scan-windows-update").addEventListener("click", scanWindowsUpdate);
byId("scan-cleanup").addEventListener("click", scanCleanup);
byId("request-cleanup").addEventListener("click", requestCleanup);
byId("open-windows-update").addEventListener("click", installWindowsUpdates);
byId("confirm-uninstall-choice").addEventListener("click", async (event) => {
  event.preventDefault();
  if (!selectedUninstallItem) return;
  const choice = document.querySelector('input[name="uninstall-choice"]:checked')?.value || "uninstall";
  const item = selectedUninstallItem;
  selectedUninstallItem = null;
  byId("uninstall-choice-dialog").close();
  await prepareSoftware(item, choice);
});
byId("check-update").addEventListener("click", () => checkForUpdates(true));
byId("required-update-dialog").addEventListener("cancel", (event) => event.preventDefault());
byId("refresh-software").addEventListener("click", () => loadSoftware(true, true));
byId("software-search-input").addEventListener("input", (event) => {
  softwareSearchQuery = event.currentTarget.value;
  clearTimeout(softwareSearchTimer);
  softwareSearchTimer = setTimeout(renderSoftwareCatalog, 180);
});
document.querySelectorAll(".audience-tab").forEach((button) => {
  button.addEventListener("click", () => {
    selectedAudience = button.dataset.audience;
    document.querySelectorAll(".audience-tab").forEach((tab) => {
      const selected = tab === button;
      tab.classList.toggle("active", selected);
      tab.setAttribute("aria-selected", String(selected));
    });
    if (softwareCatalog.length) renderSoftwareCatalog();
    else loadSoftware(false, false);
  });
});
byId("refresh-activity").addEventListener("click", loadActivity);
byId("refresh-specs").addEventListener("click", () => loadSystemSpecs(true));
byId("run-windows-overview").addEventListener("click", async (event) => {
  const button = event.currentTarget;
  button.disabled = true;
  button.classList.add("is-loading");
  button.setAttribute("aria-busy", "true");
  button.replaceChildren(
    element("span", "button-spinner"),
    element("span", "", "Đang quét…"),
  );
  document.querySelectorAll(".windows-inline-result").forEach((target) => {
    target.hidden = false;
    target.replaceChildren(element("div", "loader"), element("p", "", "Đang kiểm tra…"));
  });
  try {
    const response = await api.windowsOverview();
    renderWindowsResults(response.capabilities);
  } catch (error) {
    document.querySelectorAll(".windows-inline-result").forEach((target) => {
      target.replaceChildren(element("p", "error-text", `Không thể chạy: ${error.message}`));
    });
  } finally {
    button.disabled = false;
    button.classList.remove("is-loading");
    button.removeAttribute("aria-busy");
    button.textContent = "Quét tất cả";
  }
});

byId("chat-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = byId("message-input");
  const message = input.value.trim();
  if (!message) return;
  addMessage(message, "user"); input.value = ""; input.disabled = true;
  try {
    const response = await api.chat(message, state.sessionId, window.WinAssistI18n?.language || "vi");
    state.setSession(response.session_id);
    addMessage(response.message);
    addChatSuggestions(response.suggestions);
    (response.recommendations || []).forEach((item) => addMessage(item));
    if (response.warning) addMessage(`Lưu ý: ${response.warning}`);
    if (response.pending_action) openAction(response.pending_action);
  } catch (error) { addMessage(`Không thể xử lý: ${error.message}`); } finally { input.disabled = false; input.focus(); }
});

byId("skip-local-ai").addEventListener("click", () => byId("local-ai-dialog").close());
byId("install-local-ai").addEventListener("click", installLocalAi);

byId("message-input").addEventListener("keydown", (event) => {
  if (event.key !== "Enter" || event.shiftKey || event.isComposing) return;
  event.preventDefault();
  byId("chat-form").requestSubmit();
});

byId("confirm-command").addEventListener("click", async (event) => {
  event.preventDefault();
  if (!selectedAction) return;
  const confirmedAction = selectedAction;
  try {
    const response = await api.confirmAction(confirmedAction.id);
    state.trackAction(confirmedAction.id);
    addMessage(response.message);
    byId("action-dialog").close();
    if (confirmedAction.kind === "windows_update") {
      const target = byId("windows-update-result");
      byId("open-windows-update").disabled = true;
      target.replaceChildren(
        element("div", "loader"),
        element("strong", "", "Windows đang cập nhật…"),
        element("p", "muted", "Bạn có thể tiếp tục dùng WinAssist. Không cần mở hoặc đóng cửa sổ nào khác."),
      );
    }
    if (document.querySelector("#view-suggestions.active")) await loadSoftware(false, false);
    if (document.querySelector("#view-activity.active")) await loadActivity();
    startPolling();
  } catch (error) { addMessage(`Không thể xác nhận: ${error.message}`); byId("action-dialog").close(); }
});
byId("cancel-command").addEventListener("click", async (event) => {
  event.preventDefault();
  if (!selectedAction) return byId("action-dialog").close();
  try {
    await api.cancelAction(selectedAction.id);
    state.finishAction(selectedAction.id);
    showToast("Đã hủy yêu cầu; installer chưa được chạy.", "info");
    if (document.querySelector("#view-suggestions.active")) await loadSoftware(false, false);
    if (document.querySelector("#view-activity.active")) await loadActivity();
  } catch (error) { addMessage(`Không thể hủy: ${error.message}`); }
  byId("action-dialog").close();
});

byId("confirm-close").addEventListener("click", async (event) => {
  event.preventDefault();
  const bridge = window.pywebview?.api;
  if (!bridge) return byId("close-dialog").close();
  const choice = document.querySelector('input[name="close-choice"]:checked')?.value;
  if (choice === "exit") return bridge.exit_app();
  const response = await bridge.close_to_tray();
  if (response.success) byId("close-dialog").close();
  else showToast(response.message, "error");
});

byId("request-uninstall").addEventListener("click", () => {
  byId("uninstall-dialog").showModal();
});

byId("cancel-uninstall").addEventListener("click", (event) => {
  event.preventDefault();
  byId("uninstall-dialog").close();
});

byId("confirm-uninstall").addEventListener("click", async (event) => {
  event.preventDefault();
  const button = event.currentTarget;
  const bridge = window.pywebview?.api;
  if (!bridge) {
    byId("uninstall-dialog").close();
    return showToast("Chỉ có thể gỡ từ ứng dụng WinAssist đã cài.", "error");
  }
  button.disabled = true;
  button.textContent = "Đang gỡ…";
  try {
    const response = await bridge.uninstall_app();
    if (!response.success) {
      button.disabled = false;
      button.textContent = "Gỡ WinAssist";
      showToast(response.message, "error");
    }
  } catch (error) {
    button.disabled = false;
    button.textContent = "Gỡ WinAssist";
    showToast("Không thể mở bộ gỡ cài đặt.", "error");
  }
});

function readAttachment(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(",", 2)[1]);
    reader.onerror = () => reject(new Error("Không thể đọc ảnh đính kèm."));
    reader.readAsDataURL(file);
  });
}

const supportEmail = byId("support-email");
supportEmail.addEventListener("input", () => {
  const hasEmail = Boolean(supportEmail.value.trim());
  byId("support-reply-consent-row").hidden = !hasEmail;
  byId("support-reply-consent").required = hasEmail;
  if (!hasEmail) byId("support-reply-consent").checked = false;
});

byId("support-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const button = byId("submit-ticket");
  const result = byId("support-ticket-result");
  const file = byId("support-attachment").files[0];
  if (file && (file.size > 5 * 1024 * 1024 || !["image/png", "image/jpeg", "image/webp"].includes(file.type))) {
    return showToast("Chỉ chọn ảnh PNG, JPG hoặc WebP không quá 5 MB.", "error");
  }
  button.disabled = true;
  button.textContent = "Đang gửi…";
  result.hidden = true;
  try {
    const attachment = file ? {
      filename: file.name,
      content_type: file.type,
      content: await readAttachment(file),
    } : null;
    const response = await fetch(SUPPORT_ENDPOINT, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        issue_type: byId("support-issue-type").value,
        description: byId("support-description").value.trim(),
        contact_email: supportEmail.value.trim() || null,
        consent_to_reply: byId("support-reply-consent").checked,
        client_version: latestHealth?.version || null,
        client_language: window.WinAssistI18n?.language || "vi",
        diagnostic: pendingSupportDiagnostic,
        website: byId("support-website").value,
        attachment,
      }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok || !body.ticket_id) throw new Error(body.error || "Máy chủ hỗ trợ chưa sẵn sàng.");
    result.replaceChildren(
      element("h3", "", `Đã gửi ${body.ticket_id}`),
      element("p", "", body.reply_available
        ? "WinAssist sẽ phản hồi qua email bạn đã cung cấp. Hãy lưu mã ticket để đối chiếu."
        : "Hãy lưu mã này để đối chiếu khi cần hỗ trợ tiếp."),
    );
    result.hidden = false;
    form.reset();
    pendingSupportDiagnostic = null;
    byId("support-diagnostic-note").hidden = true;
    byId("support-reply-consent-row").hidden = true;
  } catch (error) {
    showToast(`Không thể gửi báo cáo: ${error.message}`, "error");
  } finally {
    button.disabled = false;
    button.textContent = "Gửi báo cáo";
  }
});

document.querySelectorAll("[data-icon]").forEach((container) => {
  container.replaceChildren(iconSvg(container.dataset.icon));
});
checkHealth();
loadSystemSpecs();
checkForUpdates(false);
startSoftwareEventStream();
startPolling();
