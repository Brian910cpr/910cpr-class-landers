(function (root) {
  "use strict";

  const API_BASE = "https://schedule.910cpr.com/admin";
  const PUBLIC_SITE_ORIGIN = root.location?.protocol === "file:" ? "https://www.910cpr.com" : "";
  const MAX_FILE_BYTES = 15 * 1024 * 1024;
  const ALLOWED_EXTENSIONS = new Set(["pdf", "xlsx", "xls", "csv", "docx", "png", "jpg", "jpeg"]);

  function freshness(publishedAt, nowMs = Date.now()) {
    if (!publishedAt) return { text: "Publish time unavailable", detail: "", state: "bad" };
    const parsed = new Date(publishedAt);
    if (Number.isNaN(parsed.getTime())) return { text: "Publish time unavailable", detail: "", state: "bad" };
    const deltaMs = nowMs - parsed.getTime();
    const minutes = deltaMs < -5 * 60_000 ? 0 : Math.max(0, Math.floor(deltaMs / 60_000));
    let age = "just now";
    if (minutes >= 2 && minutes < 60) age = `${minutes} minutes ago`;
    else if (minutes === 1) age = "1 minute ago";
    else if (minutes >= 60 && minutes < 1440) {
      const hours = Math.floor(minutes / 60);
      const remainder = minutes % 60;
      age = `${hours} hour${hours === 1 ? "" : "s"}${remainder ? ` ${remainder} minute${remainder === 1 ? "" : "s"}` : ""} ago`;
    } else if (minutes >= 1440) {
      const days = Math.floor(minutes / 1440);
      age = `${days} day${days === 1 ? "" : "s"} ago`;
    }
    return {
      text: `Published ${age}`,
      detail: parsed.toLocaleString(),
      state: minutes <= 45 ? "good" : minutes <= 120 ? "warn" : "bad",
    };
  }

  function validateUpload(file) {
    const extension = String(file.name || "").split(".").pop().toLowerCase();
    if (!ALLOWED_EXTENSIONS.has(extension)) return "Unsupported file type.";
    if (!Number.isFinite(file.size) || file.size <= 0) return "The file is empty.";
    if (file.size > MAX_FILE_BYTES) return "File exceeds the 15 MB limit.";
    return "";
  }

  function authHeaders(contentType) {
    const key = sessionStorage.getItem("hotSyncAdminKey") || "";
    const headers = { "X-Hot-Sync-Admin-Key": key };
    if (contentType) headers["Content-Type"] = contentType;
    return headers;
  }

  function requireKey() {
    const key = sessionStorage.getItem("hotSyncAdminKey") || document.getElementById("adminKeyInput")?.value.trim() || "";
    if (key) {
      sessionStorage.setItem("hotSyncAdminKey", key);
      updateUnlockPanel(true);
    } else {
      updateUnlockPanel(false, "Enter the admin key below, then click Unlock.");
      document.getElementById("adminKeyInput")?.focus();
    }
    return key;
  }

  function updateUnlockPanel(unlocked, message = "") {
    const input = document.getElementById("adminKeyInput");
    const unlock = document.getElementById("adminUnlockBtn");
    const forget = document.getElementById("adminForgetBtn");
    const help = document.getElementById("adminUnlockHelp");
    if (input) {
      input.value = "";
      input.hidden = unlocked;
    }
    if (unlock) unlock.hidden = unlocked;
    if (forget) forget.hidden = !unlocked;
    if (help) help.textContent = message || (unlocked ? "Admin tools are unlocked for this tab." : "Enter the LanderWare admin key once. It stays only in this browser tab and is cleared when the tab closes.");
  }

  async function unlockAdmin() {
    if (!requireKey()) return;
    try {
      await loadHotSyncRecords();
      await loadInbox().catch(() => {});
      updateUnlockPanel(true, "Admin tools are unlocked for this tab.");
    } catch (error) {
      if (error.status === 401 || error.status === 403) {
        sessionStorage.removeItem("hotSyncAdminKey");
        updateUnlockPanel(false, "That key was not accepted. Check it and try again.");
        document.getElementById("adminKeyInput")?.focus();
      }
      throw error;
    }
  }

  async function jsonRequest(url, options = {}) {
    const response = await fetch(url, { cache: "no-store", ...options });
    let payload = {};
    try { payload = await response.json(); } catch (_) { /* safe empty response */ }
    if (!response.ok) {
      const error = new Error(payload.error || payload.message || `${response.status} ${response.statusText}`);
      error.status = response.status;
      error.code = payload.code || "";
      throw error;
    }
    return payload;
  }

  function setConnection(id, text, state) {
    const element = document.getElementById(id);
    if (!element) return;
    element.textContent = text;
    element.className = `status ${state}`;
  }

  async function updateFreshness() {
    try {
      const response = await fetch(`${PUBLIC_SITE_ORIGIN}/data/admin_availability.json`, { cache: "no-store" });
      if (!response.ok) throw new Error("availability unavailable");
      const payload = await response.json();
      const value = freshness(payload.generated_at);
      const element = document.getElementById("calendarFreshness");
      if (element) {
        element.textContent = value.text;
        element.className = `status ${value.state}`;
        element.title = value.detail;
        element.setAttribute("aria-label", value.detail ? `${value.text}. Published ${value.detail}` : value.text);
      }
    } catch (_) {
      const element = document.getElementById("calendarFreshness");
      if (element) {
        element.textContent = "Publish time unavailable";
        element.className = "status bad";
        element.removeAttribute("title");
      }
    }
  }

  function classifyConnectionError(error, target) {
    if (error.status === 401 || error.status === 403) {
      setConnection(target, "Authentication required", "warn");
      sessionStorage.removeItem("hotSyncAdminKey");
      updateUnlockPanel(false, "That key was not accepted. Check it and try again.");
      return;
    }
    setConnection(target, target === "hotSyncConnection" ? "HOT_SYNC unavailable" : "LanderWare Inbox is not connected", "bad");
  }

  async function loadHotSyncRecords(promptForKey = false) {
    if (promptForKey && !requireKey()) throw Object.assign(new Error("Authentication required."), { status: 401 });
    if (!sessionStorage.getItem("hotSyncAdminKey")) {
      setConnection("hotSyncConnection", "Authentication required", "warn");
      throw Object.assign(new Error("Authentication required."), { status: 401 });
    }
    try {
      const payload = await jsonRequest(`${API_BASE}/hot-sync`, { headers: authHeaders() });
      setConnection("hotSyncConnection", "HOT_SYNC connected", "good");
      renderRecords(Array.isArray(payload.records) ? payload.records : []);
      return payload.records || [];
    } catch (error) {
      classifyConnectionError(error, "hotSyncConnection");
      throw error;
    }
  }

  function renderRecords(serverRecords) {
    const host = document.getElementById("recordList");
    if (!host) return;
    const drafts = typeof root.getDrafts === "function" ? root.getDrafts() : [];
    const persisted = serverRecords.map((record) => {
      const when = record.start ? new Date(record.start).toLocaleString() : "No time";
      return `<div class="recordRow"><div><b>${root.esc(record.course_display_name || "Untitled class")}</b><div class="muted">${root.esc(when)} · ${root.esc(record.client_name || "No client")} · ${root.esc(record.location_name || "No location")}</div><div><span class="pill class">${root.esc(record.status || "unknown")}</span> <span class="pill">${root.esc(record.visibility || "hidden")}</span></div></div><div class="actions"><button class="btn small" data-server-edit="${root.esc(record.id)}">Edit</button><button class="btn small danger" data-server-delete="${root.esc(record.id)}">Cancel/delete</button></div></div>`;
    });
    const local = drafts.map((record) => `<div class="recordRow"><div><b>${root.esc(record.course_display_name || "Untitled class")}</b><div class="muted">Saved only in this browser · ${root.esc(record.start || "No time")}</div></div><button class="btn small" data-draft-edit="${root.esc(record.id)}">Edit draft</button></div>`);
    host.innerHTML = persisted.concat(local).join("") || '<div class="emptymsg">No persisted HOT_SYNC records or browser drafts.</div>';
    host.querySelectorAll("[data-server-edit]").forEach((button) => {
      button.onclick = () => {
        const record = serverRecords.find((item) => item.id === button.dataset.serverEdit);
        if (record) root.setFields(record);
      };
    });
    host.querySelectorAll("[data-draft-edit]").forEach((button) => {
      button.onclick = () => {
        const record = drafts.find((item) => item.id === button.dataset.draftEdit);
        if (record) root.setFields(record);
      };
    });
    host.querySelectorAll("[data-server-delete]").forEach((button) => {
      button.onclick = async () => {
        if (!confirm("Cancel this class and remove its availability block? The audit record will be preserved.")) return;
        try {
          await jsonRequest(`${API_BASE}/hot-sync/${encodeURIComponent(button.dataset.serverDelete)}`, { method: "DELETE", headers: authHeaders() });
          root.showSaveMessage("Class cancelled in HOT_SYNC. Its audit history was preserved.", "good");
          await loadHotSyncRecords();
          await root.load();
        } catch (error) {
          setConnection("hotSyncConnection", "Last save failed", "bad");
          root.showSaveMessage(`Save failed: ${error.message}`, "bad");
        }
      };
    });
  }

  async function saveHotSyncOperational() {
    let record;
    try { record = JSON.parse(document.getElementById("hsJson").value); }
    catch (_) { root.showSaveMessage("The JSON record is invalid.", "bad"); return; }
    const missing = root.validateRecord(record);
    if (missing.length) { root.showSaveMessage(`Missing: ${missing.join(", ")}.`, "bad"); return; }
    if (!requireKey()) { root.showSaveMessage("Save failed: authentication is required.", "bad"); return; }
    try {
      const method = record.id ? "PUT" : "POST";
      const endpoint = record.id ? `${API_BASE}/hot-sync/${encodeURIComponent(record.id)}` : `${API_BASE}/hot-sync`;
      const payload = await jsonRequest(endpoint, { method, headers: authHeaders("application/json"), body: JSON.stringify(record) });
      if (typeof root.removeDraft === "function") root.removeDraft(record.id);
      root.showSaveMessage(payload.blocking ? "Saved to HOT_SYNC. This committed class is now blocking availability." : "Saved to HOT_SYNC. This record is not currently blocking availability.", "good");
      await loadHotSyncRecords();
      await root.load();
    } catch (error) {
      if (typeof root.putDraft === "function") root.putDraft(record);
      setConnection("hotSyncConnection", "Last save failed", "bad");
      root.showSaveMessage(`Save failed: ${error.message}. Saved only in this browser; availability was not changed.`, "bad");
    }
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function uploadOne(file) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE}/inbox`);
      xhr.setRequestHeader("X-Hot-Sync-Admin-Key", sessionStorage.getItem("hotSyncAdminKey") || "");
      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return;
        document.getElementById("uploadStatus").textContent = `Uploading ${file.name}: ${Math.round(event.loaded * 100 / event.total)}%`;
        document.getElementById("uploadStatus").className = "saveMessage warn";
      };
      xhr.onload = () => {
        let payload = {};
        try { payload = JSON.parse(xhr.responseText); } catch (_) { /* handled below */ }
        if (xhr.status >= 200 && xhr.status < 300) resolve(payload);
        else reject(Object.assign(new Error(payload.error || `Upload failed (${xhr.status}).`), { status: xhr.status }));
      };
      xhr.onerror = () => reject(new Error("Upload failed because the server could not be reached."));
      const form = new FormData();
      form.append("file", file, file.name);
      form.append("category", document.getElementById("inboxCategory").value);
      form.append("association", document.getElementById("inboxAssociation").value);
      form.append("notes", document.getElementById("inboxNotes").value);
      xhr.send(form);
    });
  }

  async function uploadFiles(files) {
    const selected = Array.from(files || []);
    if (!selected.length) return;
    for (const file of selected) {
      const validation = validateUpload(file);
      if (validation) {
        document.getElementById("uploadStatus").textContent = `${file.name}: ${validation}`;
        document.getElementById("uploadStatus").className = "saveMessage bad";
        continue;
      }
      try {
        await uploadOne(file);
        document.getElementById("uploadStatus").textContent = `${file.name} uploaded and persisted.`;
        document.getElementById("uploadStatus").className = "saveMessage good";
      } catch (error) {
        document.getElementById("uploadStatus").textContent = `${file.name}: ${error.message}`;
        document.getElementById("uploadStatus").className = "saveMessage bad";
      }
    }
    await loadInbox().catch(() => {});
  }

  async function loadInbox(promptForKey = false) {
    if (promptForKey && !requireKey()) throw Object.assign(new Error("Authentication required."), { status: 401 });
    if (!sessionStorage.getItem("hotSyncAdminKey")) {
      setConnection("inboxConnection", "Authentication required", "warn");
      return;
    }
    try {
      const payload = await jsonRequest(`${API_BASE}/inbox`, { headers: authHeaders() });
      const button = document.getElementById("chooseInboxFiles");
      button.disabled = false;
      document.getElementById("inboxDropZone").setAttribute("aria-disabled", "false");
      setConnection("inboxConnection", "LanderWare Inbox connected", "good");
      renderUploads(payload.files || []);
    } catch (error) {
      document.getElementById("chooseInboxFiles").disabled = true;
      document.getElementById("inboxDropZone").setAttribute("aria-disabled", "true");
      classifyConnectionError(error, "inboxConnection");
      throw error;
    }
  }

  function renderUploads(files) {
    const host = document.getElementById("recentUploads");
    host.innerHTML = files.length ? files.map((file) => `<div class="recordRow"><div><b>${root.esc(file.original_filename)}</b><div class="muted">${root.esc(file.category || "Other")} · ${root.esc(new Date(file.uploaded_at).toLocaleString())} · ${formatBytes(file.file_size)}</div><div class="muted">${root.esc(file.processing_status || "stored")}</div></div><div class="actions"><button class="btn small" data-download="${root.esc(file.id)}">Download</button><button class="btn small" data-upload-edit="${root.esc(file.id)}">Edit details</button><button class="btn small danger" data-upload-delete="${root.esc(file.id)}">Delete</button></div></div>`).join("") : '<div class="emptymsg">No recent uploads.</div>';
    host.querySelectorAll("[data-download]").forEach((button) => {
      button.onclick = async () => {
        try {
          const response = await fetch(`${API_BASE}/inbox/${encodeURIComponent(button.dataset.download)}/content`, { headers: authHeaders(), cache: "no-store" });
          if (!response.ok) throw new Error(`Download failed (${response.status}).`);
          const blobUrl = URL.createObjectURL(await response.blob());
          const link = document.createElement("a");
          link.href = blobUrl;
          link.download = files.find((file) => file.id === button.dataset.download)?.original_filename || "download";
          link.click();
          setTimeout(() => URL.revokeObjectURL(blobUrl), 30_000);
        } catch (error) {
          document.getElementById("uploadStatus").textContent = error.message;
          document.getElementById("uploadStatus").className = "saveMessage bad";
        }
      };
    });
    host.querySelectorAll("[data-upload-delete]").forEach((button) => {
      button.onclick = async () => {
        if (!confirm("Permanently delete this private file and its metadata?")) return;
        try {
          await jsonRequest(`${API_BASE}/inbox/${encodeURIComponent(button.dataset.uploadDelete)}`, { method: "DELETE", headers: authHeaders() });
          await loadInbox();
        } catch (error) {
          document.getElementById("uploadStatus").textContent = `Delete failed: ${error.message}`;
          document.getElementById("uploadStatus").className = "saveMessage bad";
        }
      };
    });
    host.querySelectorAll("[data-upload-edit]").forEach((button) => {
      button.onclick = async () => {
        const file = files.find((item) => item.id === button.dataset.uploadEdit);
        if (!file) return;
        const category = prompt("Category:", file.category || "Other");
        if (category === null) return;
        const notes = prompt("Notes:", file.notes || "");
        if (notes === null) return;
        try {
          await jsonRequest(`${API_BASE}/inbox/${encodeURIComponent(file.id)}`, {
            method: "PATCH",
            headers: authHeaders("application/json"),
            body: JSON.stringify({ category, notes, class_association: file.class_association || "" }),
          });
          await loadInbox();
        } catch (error) {
          document.getElementById("uploadStatus").textContent = `Update failed: ${error.message}`;
          document.getElementById("uploadStatus").className = "saveMessage bad";
        }
      };
    });
  }

  function initialize() {
    updateFreshness();
    setInterval(updateFreshness, 15_000);
    const freshnessElement = document.getElementById("calendarFreshness");
    if (freshnessElement && typeof MutationObserver !== "undefined") {
      new MutationObserver(() => {
        if (/\b\d+m ago\b/.test(freshnessElement.textContent || "") || /Publish time unknown/.test(freshnessElement.textContent || "")) updateFreshness();
      }).observe(freshnessElement, { childList: true, characterData: true, subtree: true });
    }
    document.getElementById("saveHotSyncBtn").onclick = saveHotSyncOperational;
    document.getElementById("viewRecordsBtn").onclick = async () => {
      const box = document.getElementById("recordBrowser");
      box.style.display = box.style.display === "none" ? "block" : "none";
      if (box.style.display === "block") await loadHotSyncRecords(true).catch((error) => root.showSaveMessage(error.message, "bad"));
    };
    document.getElementById("hotSyncConnection").onclick = () => loadHotSyncRecords(true).catch((error) => root.showSaveMessage(error.message, "bad"));
    document.getElementById("inboxConnection").onclick = () => loadInbox(true).catch((error) => {
      document.getElementById("uploadStatus").textContent = error.message;
      document.getElementById("uploadStatus").className = "saveMessage bad";
    });
    const input = document.getElementById("inboxFileInput");
    const adminKeyInput = document.getElementById("adminKeyInput");
    document.getElementById("adminUnlockBtn").onclick = () => unlockAdmin().catch((error) => root.showSaveMessage(`Unlock failed: ${error.message}`, "bad"));
    document.getElementById("adminForgetBtn").onclick = () => {
      sessionStorage.removeItem("hotSyncAdminKey");
      updateUnlockPanel(false, "The key was forgotten. Enter it again to use admin tools.");
      setConnection("hotSyncConnection", "Authentication required", "warn");
      setConnection("inboxConnection", "Authentication required", "warn");
      adminKeyInput?.focus();
    };
    if (adminKeyInput) adminKeyInput.onkeydown = (event) => { if (event.key === "Enter") document.getElementById("adminUnlockBtn").click(); };
    const choose = document.getElementById("chooseInboxFiles");
    choose.onclick = () => input.click();
    input.onchange = () => uploadFiles(input.files);
    const drop = document.getElementById("inboxDropZone");
    drop.ondragover = (event) => { event.preventDefault(); };
    drop.ondrop = (event) => {
      event.preventDefault();
      if (drop.getAttribute("aria-disabled") === "true") return;
      uploadFiles(event.dataTransfer.files);
    };
    if (sessionStorage.getItem("hotSyncAdminKey")) {
      updateUnlockPanel(true);
      loadHotSyncRecords().catch(() => {});
      loadInbox().catch(() => {});
    } else {
      updateUnlockPanel(false);
      setConnection("hotSyncConnection", "Authentication required", "warn");
      setConnection("inboxConnection", "Authentication required", "warn");
    }
  }

  const api = { freshness, validateUpload, MAX_FILE_BYTES };
  root.DashboardOps = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (typeof document !== "undefined") initialize();
})(typeof window !== "undefined" ? window : globalThis);
