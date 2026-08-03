window.WinAssistApi = {
  async request(path, options = {}) {
    const { timeoutMs = 30000, ...fetchOptions } = options;
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(path, {
        ...fetchOptions,
        signal: controller.signal,
        headers: { Accept: "application/json", ...(fetchOptions.body ? { "Content-Type": "application/json" } : {}), ...fetchOptions.headers },
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(payload.detail || `HTTP ${response.status}`);
      return payload;
    } catch (error) {
      if (error.name === "AbortError") throw new Error("Backend phản hồi quá thời gian cho phép.");
      throw error;
    } finally {
      clearTimeout(timer);
    }
  },
  health: () => window.WinAssistApi.request("/api/health"),
  systemSpecs: () => window.WinAssistApi.request("/api/system/specs"),
  graphicsDriver: () => window.WinAssistApi.request("/api/system/graphics-driver"),
  openGraphicsApp: (vendor) => window.WinAssistApi.request(`/api/system/graphics-driver/${encodeURIComponent(vendor)}/open`, { method: "POST" }),
  chat: (message, sessionId) => window.WinAssistApi.request("/api/chat", { method: "POST", body: JSON.stringify({ message, session_id: sessionId }) }),
  software: () => window.WinAssistApi.request("/api/software"),
  scanSoftware: () => window.WinAssistApi.request("/api/software/scan", { method: "POST" }),
  softwareEvents: () => new EventSource("/api/software/events"),
  checkSoftware: (softwareId) => window.WinAssistApi.request("/api/software/check", { method: "POST", body: JSON.stringify({ software_id: softwareId }) }),
  installSoftware: (softwareId) => window.WinAssistApi.request("/api/software/install", { method: "POST", body: JSON.stringify({ software_id: softwareId }) }),
  uninstallSoftware: (softwareId) => window.WinAssistApi.request("/api/software/uninstall", { method: "POST", body: JSON.stringify({ software_id: softwareId }) }),
  actions: () => window.WinAssistApi.request("/api/actions"),
  actionStatus: (id) => window.WinAssistApi.request(`/api/actions/${id}/status`),
  confirmAction: (id) => window.WinAssistApi.request(`/api/actions/${id}/confirm`, { method: "POST" }),
  cancelAction: (id) => window.WinAssistApi.request(`/api/actions/${id}/cancel`, { method: "POST" }),
  repairs: () => window.WinAssistApi.request("/api/repairs"),
  requestRepair: (id) => window.WinAssistApi.request(`/api/repairs/${id}`, { method: "POST" }),
  network: () => window.WinAssistApi.request("/api/diagnostics/network", { method: "POST", timeoutMs: 120000 }),
  speedtest: () => window.WinAssistApi.request("/api/diagnostics/speedtest", { method: "POST", timeoutMs: 140000 }),
  windowsCapabilities: () => window.WinAssistApi.request("/api/windows/capabilities"),
  windowsOverview: () => window.WinAssistApi.request("/api/windows/overview", { method: "POST", timeoutMs: 90000 }),
  inspectWindows: (id) => window.WinAssistApi.request(`/api/windows/${id}`, { method: "POST" }),
  openWindowsUpdate: () => window.WinAssistApi.request("/api/windows/update/open", { method: "POST" }),
  latestPatch: () => window.WinAssistApi.request("/api/patches/latest"),
  updateStatus: () => window.WinAssistApi.request("/api/patches/update-status", { timeoutMs: 12000 }),
};
