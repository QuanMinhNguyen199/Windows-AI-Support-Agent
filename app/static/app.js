const api = window.WinAssistApi;
const state = window.WinAssistState;
const terminalStates = new Set(["completed", "failed", "cancelled", "expired"]);
const categoryNames = { browsers: "Trình duyệt", office_pdf: "Văn phòng & PDF", utilities: "Tiện ích", media: "Đa phương tiện", developer_tools: "Công cụ phát triển" };
let selectedAction = null;
let pollTimer = null;
let pollInProgress = false;
let softwareInventory = new Map();
let softwareScanPromise = null;
let softwareViewLoaded = false;
let softwareNeedsRescan = false;
let softwareEventSource = null;
let softwareEventDebounce = null;
let selectedAudience = "general";
let patchNotesLoaded = false;
let systemSpecsLoaded = false;
let systemSpecsLoading = false;

const byId = (id) => document.getElementById(id);
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
  byId("view-title").textContent = { overview: "Tổng quan máy", chat: "Trợ lý", suggestions: "Tiện ích", diagnostics: "Chẩn đoán", activity: "Hoạt động", patches: "Patch Update" }[name];
  if (name === "overview") loadSystemSpecs();
  if (name === "suggestions" && (!softwareViewLoaded || softwareNeedsRescan || state.activeActions.size)) {
    loadSoftware(!softwareViewLoaded, softwareNeedsRescan);
  }
  if (name === "diagnostics") {
    loadRepairs();
    loadWindowsCapabilities();
  }
  if (name === "activity") loadActivity();
  if (name === "patches") loadLatestPatch();
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
  const allowedViews = new Set(["overview", "chat", "suggestions", "diagnostics", "activity", "patches"]);
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
  byId("command-text").textContent = action.display_command;
  byId("command-warning").textContent = action.warning;
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
          if (status.action.kind === "software_install" || status.action.kind === "software_uninstall") {
            rescanSoftware = true;
            softwareNeedsRescan = true;
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
    byId("backend-status").textContent = `Backend ${health.version} hoạt động`;
    byId("backend-dot").className = "status-dot online";
    byId("ollama-status").textContent = health.ollama.status === "available"
      ? "Trợ lý: sẵn sàng"
      : "Trợ lý: chế độ cơ bản";
  } catch {
    byId("backend-status").textContent = "Backend không kết nối";
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
    const activeByResource = new Map(actions.filter((item) => !terminalStates.has(item.action.state)).map((item) => [item.action.resource_id, item]));
    activeByResource.forEach((item) => state.trackAction(item.action.id));
    const groups = new Map();
    software
      .filter((item) => item.audience === selectedAudience)
      .forEach((item) => { if (!groups.has(item.category)) groups.set(item.category, []); groups.get(item.category).push(item); });
    root.replaceChildren();
    groups.forEach((items, category) => {
      const section = element("section", "software-section");
      section.append(element("h2", "", categoryNames[category] || category));
      const grid = element("div", "software-grid");
      items.forEach((item) => grid.append(softwareCard(item, activeByResource.get(item.id), softwareInventory.get(item.id))));
      section.append(grid);
      root.append(section);
    });
    softwareViewLoaded = true;
    if (shouldScan) softwareNeedsRescan = false;
    const liveStatus = byId("software-live-text");
    if (liveStatus) {
      liveStatus.textContent = activeByResource.size
        ? `Đang theo dõi ${activeByResource.size} thao tác`
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
      ? "Backend đang chạy phiên bản cũ. Hãy khởi động lại WinAssist để tải Patch Update."
      : `Không thể tải thông tin phiên bản: ${error.message}`;
    const errorBox = element("div", "patch-error");
    errorBox.append(element("p", "error-text", message));
    const retry = element("button", "secondary", "Thử lại");
    retry.addEventListener("click", loadLatestPatch);
    errorBox.append(retry);
    root.replaceChildren(errorBox);
  }
}

function softwareCard(item, active, inventory) {
  const card = element("article", "software-card");
  const head = element("div", "software-head");
  const title = element("div");
  title.append(element("h3", "", item.display_name), element("p", "muted", item.publisher));
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
  remove.addEventListener("click", () => prepareSoftware(item, "uninstall"));
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
    const result = operation === "install" ? await api.installSoftware(item.id) : await api.uninstallSoftware(item.id);
    if (result.pending_action) openAction(result.pending_action, `${operation === "install" ? "Cài" : "Gỡ"} ${item.display_name}`);
    else {
      addMessage(result.message);
      showToast(result.message, "info");
      await loadSoftware(true, true);
    }
  } catch (error) { addMessage(`Không thể chuẩn bị thao tác: ${error.message}`); switchView("chat"); }
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
    root.replaceChildren(...capabilities.map((capability) => {
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
    grid.append(
      detailItem("Dịch vụ cập nhật", data.service_status || "Không xác định", `Chế độ khởi động: ${data.start_type || "không xác định"}`),
      detailItem("Khởi động lại", data.reboot_pending ? "Đang chờ khởi động lại" : "Không yêu cầu"),
    );
    if (data.latest_hotfix) {
      grid.append(detailItem(
        "Bản vá gần nhất",
        data.latest_hotfix.HotFixID || "Không xác định",
        data.latest_hotfix.InstalledOn ? `Cài ngày ${new Date(data.latest_hotfix.InstalledOn).toLocaleDateString("vi-VN")}` : "",
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
      [["Download", `${result.measurement.download_mbps ?? "—"} Mbps`], ["Upload", `${result.measurement.upload_mbps ?? "—"} Mbps`], ["Ping", `${result.measurement.ping_ms ?? "—"} ms`], ["Jitter", `${result.measurement.jitter_ms ?? "—"} ms`]].forEach(([key, value]) => { const metric = element("div", "metric"); metric.append(element("small", "", key), element("strong", "", value)); metrics.append(metric); });
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

async function loadActivity() {
  const root = byId("activity-list");
  try {
    const actions = await api.actions();
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
      info.append(element("strong", "", item.action.display_command), element("p", "muted", `${item.message} · ${elapsed(item.action.created_at)}`));
      const badge = element("span", `badge ${item.action.state}`, stateNames[item.action.state] || item.action.state);
      row.append(info, badge);
      if (item.indeterminate) { const progress = element("div", "progress wide"); progress.append(element("span", "indeterminate")); row.append(progress); }
      return row;
    }));
  } catch (error) { root.replaceChildren(element("p", "error-text", error.message)); }
}

document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.view)));
document.querySelectorAll("[data-view-target]").forEach((button) => button.addEventListener("click", () => switchView(button.dataset.viewTarget)));
document.querySelectorAll("[data-message]").forEach((button) => button.addEventListener("click", () => { byId("message-input").value = button.dataset.message; byId("message-input").focus(); }));
document.querySelectorAll(".diagnostic-run").forEach((button) => button.addEventListener("click", () => runDiagnostic(button.dataset.diagnostic, button)));
byId("refresh-software").addEventListener("click", () => loadSoftware(true, true));
document.querySelectorAll(".audience-tab").forEach((button) => {
  button.addEventListener("click", () => {
    selectedAudience = button.dataset.audience;
    document.querySelectorAll(".audience-tab").forEach((tab) => {
      const selected = tab === button;
      tab.classList.toggle("active", selected);
      tab.setAttribute("aria-selected", String(selected));
    });
    loadSoftware(false, false);
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
    const response = await api.chat(message, state.sessionId);
    state.setSession(response.session_id);
    addMessage(response.message);
    addChatSuggestions(response.suggestions);
    (response.recommendations || []).forEach((item) => addMessage(item));
    if (response.warning) addMessage(`Lưu ý: ${response.warning}`);
    if (response.pending_action) openAction(response.pending_action);
  } catch (error) { addMessage(`Không thể xử lý: ${error.message}`); } finally { input.disabled = false; input.focus(); }
});

byId("confirm-command").addEventListener("click", async (event) => {
  event.preventDefault();
  if (!selectedAction) return;
  try {
    const response = await api.confirmAction(selectedAction.id);
    state.trackAction(selectedAction.id);
    addMessage(response.message);
    byId("action-dialog").close();
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

document.querySelectorAll("[data-icon]").forEach((container) => {
  container.replaceChildren(iconSvg(container.dataset.icon));
});
checkHealth();
loadSystemSpecs();
startSoftwareEventStream();
startPolling();
