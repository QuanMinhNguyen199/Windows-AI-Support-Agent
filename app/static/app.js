const api = window.WinAssistApi;
const state = window.WinAssistState;
const terminalStates = new Set(["completed", "failed", "cancelled", "expired"]);
const categoryNames = { browsers: "Trình duyệt", office_pdf: "Văn phòng & PDF", utilities: "Tiện ích", media: "Đa phương tiện", developer_tools: "Công cụ phát triển" };
let selectedAction = null;
let pollTimer = null;
let pollInProgress = false;
let softwareInventory = new Map();
let softwareScanPromise = null;
let selectedAudience = "general";

const byId = (id) => document.getElementById(id);
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
  byId("view-title").textContent = { overview: "Tổng quan máy", chat: "Trợ lý", suggestions: "Tiện ích", diagnostics: "Chẩn đoán", activity: "Hoạt động" }[name];
  if (name === "overview") loadSystemSpecs();
  if (name === "suggestions") loadSoftware();
  if (name === "diagnostics") loadRepairs();
  if (name === "activity") loadActivity();
}

function specCard(label, value, detail = "") {
  const card = element("article", "spec-card");
  card.append(element("small", "", label), element("strong", "", value || "Không khả dụng"));
  if (detail) card.append(element("span", "", detail));
  return card;
}

async function loadSystemSpecs() {
  const root = byId("specs-content");
  const loading = element("div", "spec-loading");
  loading.append(element("div", "loader"), element("p", "", "Đang đọc thông số máy…"));
  root.replaceChildren(loading);
  try {
    const response = await api.systemSpecs();
    if (!response.available || !response.specs) throw new Error(response.message);
    const specs = response.specs;
    const identity = element("section", "device-summary");
    const deviceIcon = element("span", "device-icon", "▣");
    const name = element("div");
    name.append(
      element("h2", "", specs.device_name || "Máy tính Windows"),
      element("p", "muted", [specs.manufacturer, specs.model].filter(Boolean).join(" · ") || "Không có thông tin hãng/model"),
    );
    identity.append(deviceIcon, name);
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
  } catch (error) {
    const errorBox = element("div", "spec-error");
    errorBox.append(element("h3", "", "Không đọc được thông số máy"), element("p", "", error.message));
    root.replaceChildren(errorBox);
  }
}

function addMessage(text, role = "assistant") {
  const article = element("article", `message ${role}`);
  const avatar = element("div", "avatar", role === "user" ? "Bạn" : "WA");
  const bubble = element("div", "bubble");
  bubble.append(element("p", "", text));
  article.append(avatar, bubble);
  byId("chat-log").append(article);
  byId("chat-log").scrollTop = byId("chat-log").scrollHeight;
}

function openAction(action, title = "Kiểm tra command") {
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
          if (status.action.kind === "software_install" || status.action.kind === "software_uninstall") {
            rescanSoftware = true;
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
    byId("ollama-status").textContent = health.ollama.status === "available" ? "AI local: sẵn sàng" : "AI local: rule-based fallback";
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
      element("p", "muted", "Danh sách sẽ hiện sau khi kiểm tra xong toàn bộ catalog."),
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
  } catch (error) { root.replaceChildren(element("p", "error-text", `Không thể tải catalog: ${error.message}`)); }
}

function softwareCard(item, active, inventory) {
  const card = element("article", "software-card");
  const head = element("div", "software-head");
  const icon = element("span", "software-icon", item.display_name.slice(0, 1));
  const title = element("div");
  title.append(element("h3", "", item.display_name), element("p", "muted", item.publisher));
  head.append(icon, title);
  const statusText = active
    ? `${active.message} · ${elapsed(active.action.created_at)}`
    : (inventory?.status || "Không xác định");
  const status = element("p", `software-status ${inventory?.installed ? "installed" : "not-installed"}`, statusText);
  const actions = element("div", "icon-actions");
  const install = element("button", "icon-button", "↓");
  install.title = `Cài ${item.display_name}`;
  install.setAttribute("aria-label", install.title);
  install.addEventListener("click", () => prepareSoftware(item, "install"));
  install.disabled = Boolean(inventory?.installed) || Boolean(active);
  const remove = element("button", "icon-button remove", "×");
  remove.title = `Gỡ ${item.display_name}`;
  remove.setAttribute("aria-label", remove.title);
  remove.addEventListener("click", () => prepareSoftware(item, "uninstall"));
  remove.disabled = !inventory?.installed || Boolean(active);
  actions.append(install, remove);
  if (active) {
    const cancel = element("button", "icon-button cancel", "■");
    cancel.title = active.action.state === "pending"
      ? "Hủy yêu cầu đang chờ"
      : "Không thể hủy an toàn khi installer đã bắt đầu";
    cancel.setAttribute("aria-label", cancel.title);
    cancel.disabled = active.action.state !== "pending";
    cancel.addEventListener("click", async () => {
      cancel.disabled = true;
      try {
        await api.cancelAction(active.action.id);
        state.finishAction(active.action.id);
      } catch (error) {
        addMessage(`Không thể hủy: ${error.message}`);
      }
      await loadSoftware(false, false);
    });
    actions.prepend(cancel);
    card.append(head, status);
    if (active.action.state === "executing") {
      const progress = element("div", "progress");
      progress.append(element("span", "indeterminate"));
      card.append(progress);
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
      card.append(element("span", "card-icon", "↻"), element("h3", "", repair.display_name), element("p", "", repair.description));
      const button = element("button", "secondary", "Chuẩn bị");
      button.addEventListener("click", async () => {
        try { const response = await api.requestRepair(repair.id); openAction(response.pending_action, repair.display_name); }
        catch (error) { showDiagnosticError(error); }
      });
      card.append(button); return card;
    }));
  } catch (error) { root.replaceChildren(element("p", "error-text", error.message)); }
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
    root.replaceChildren(...actions.map((item) => {
      const row = element("article", "activity-row");
      const info = element("div");
      info.append(element("strong", "", item.action.display_command), element("p", "muted", `${item.message} · ${elapsed(item.action.created_at)}`));
      const badge = element("span", `badge ${item.action.state}`, item.action.state);
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
byId("refresh-software").addEventListener("click", () => loadSoftware());
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
byId("refresh-specs").addEventListener("click", loadSystemSpecs);

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
    if (document.querySelector("#view-suggestions.active")) await loadSoftware(false, false);
    if (document.querySelector("#view-activity.active")) await loadActivity();
  } catch (error) { addMessage(`Không thể hủy: ${error.message}`); }
  byId("action-dialog").close();
});

checkHealth();
loadSystemSpecs();
startPolling();
