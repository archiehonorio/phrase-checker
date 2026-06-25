"use strict";

const input = document.getElementById("input");
const out = document.getElementById("out");

function esc(s) {
  return (s || "").replace(/[&<>]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])
  );
}

function grow() {
  input.style.height = "auto";
  input.style.height = input.scrollHeight + "px";
}
input.addEventListener("input", grow);

function norm(s) {
  return (s || "").replace(/\s+/g, " ").trim().toLowerCase();
}

async function copyText(text, el) {
  try {
    await navigator.clipboard.writeText(text);
  } catch {
    const ta = document.createElement("textarea");
    ta.value = text;
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    ta.remove();
  }
  if (el) {
    const old = el.textContent;
    el.textContent = "[copied]";
    el.classList.add("ok");
    setTimeout(() => {
      el.textContent = old;
      el.classList.remove("ok");
    }, 1200);
  }
}

// ---- main output -------------------------------------------------------- //

function render(ai, aiErr, original) {
  const o = norm(original);
  let html = "";
  if (ai) {
    html += block("auto", ai, norm(ai) === o);
  } else if (aiErr === "no key") {
    html += `<div class="block"><span class="label">auto:</span> <span class="err">no api key — type:  key YOUR_API_KEY</span></div>`;
  } else if (aiErr) {
    html += `<div class="block"><span class="label">auto:</span> <span class="err">${esc(aiErr)}</span></div>`;
  }
  out.innerHTML = html;
  out.querySelectorAll(".copy").forEach((el) =>
    el.addEventListener("click", () =>
      copyText(document.getElementById(el.dataset.for).textContent, el)
    )
  );
}

function block(label, text, unchanged) {
  const id = "b" + Math.floor(performance.now() * 1000) + "_" + label;
  const tag = unchanged ? ` <span class="ok">(already good)</span>` : "";
  return (
    `<div class="block"><span class="label">${label}:</span>${tag} ` +
    `<span class="copy" data-for="${id}">[copy]</span>\n` +
    `<span class="text" id="${id}">${esc(text)}</span></div>`
  );
}

// ---- panels ------------------------------------------------------------- //

const settingsPanel = document.getElementById("settings");
const logPanel = document.getElementById("log");
const styleBox = document.getElementById("styleBox");
const styleMsg = document.getElementById("styleMsg");
const styleList = document.getElementById("styleList");
const logSearch = document.getElementById("logSearch");
const logList = document.getElementById("logList");
const logMsg = document.getElementById("logMsg");

function hidePanels() {
  settingsPanel.classList.add("hidden");
  logPanel.classList.add("hidden");
}

function clearAll() {
  input.value = "";
  out.innerHTML = "";
  hidePanels();
  grow();
  input.focus();
}

// ---- settings (saved style examples) ------------------------------------ //

async function openSettings(prefill) {
  hidePanels();
  out.innerHTML = "";
  styleBox.value = prefill || "";
  styleMsg.textContent = "";
  settingsPanel.classList.remove("hidden");
  await refreshStyles();
  styleBox.focus();
}

async function refreshStyles() {
  try {
    const d = await (await fetch("/api/styles")).json();
    const items = d.styles || [];
    if (!items.length) {
      styleList.innerHTML = `<div class="empty">no examples saved yet.</div>`;
      return;
    }
    styleList.innerHTML =
      `<div class="label">saved (${items.length}):</div>` +
      items
        .map(
          (it) =>
            `<div class="item"><span class="id">#${it.id}</span> ` +
            `<span class="copy" data-del-style="${it.id}">[delete]</span>\n` +
            `<span class="in">${esc(it.text)}</span></div>`
        )
        .join("");
    styleList.querySelectorAll("[data-del-style]").forEach((el) =>
      el.addEventListener("click", async () => {
        await fetch("/api/styles/delete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id: Number(el.dataset.delStyle) }),
        });
        refreshStyles();
      })
    );
  } catch {
    styleList.innerHTML = `<div class="err">could not load saved examples</div>`;
  }
}

document.getElementById("styleSave").addEventListener("click", async () => {
  const text = styleBox.value.trim();
  if (!text) {
    styleMsg.textContent = "nothing to save";
    return;
  }
  try {
    const r = await fetch("/api/styles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const d = await r.json();
    if (d.ok) {
      styleBox.value = "";
      styleMsg.textContent = "saved.";
      refreshStyles();
    } else {
      styleMsg.textContent = d.error || "could not save";
    }
  } catch {
    styleMsg.textContent = "could not save";
  }
});

document.getElementById("styleClearAll").addEventListener("click", async () => {
  await fetch("/api/styles/clear", { method: "POST" });
  styleMsg.textContent = "all cleared.";
  refreshStyles();
});

document.getElementById("styleClose").addEventListener("click", () => {
  hidePanels();
  input.focus();
});

// ---- log (history) ------------------------------------------------------ //

async function openLog() {
  hidePanels();
  out.innerHTML = "";
  logSearch.value = "";
  logMsg.textContent = "";
  logPanel.classList.remove("hidden");
  await refreshLog("");
  logSearch.focus();
}

async function refreshLog(q) {
  try {
    const d = await (await fetch("/api/log?q=" + encodeURIComponent(q || ""))).json();
    const items = d.items || [];
    if (!items.length) {
      logList.innerHTML = `<div class="empty">${q ? "no matches." : "no history yet."}</div>`;
      return;
    }
    logList.innerHTML =
      `<div class="label">${items.length} entr${items.length === 1 ? "y" : "ies"}:</div>` +
      items
        .map((it) => {
          const oid = "o" + it.id;
          return (
            `<div class="item"><span class="id">${esc(it.created)}</span> ` +
            `<span class="copy" data-use="${it.id}">[use]</span> ` +
            `<span class="copy" data-del-log="${it.id}">[delete]</span>\n` +
            `<span class="in">> ${esc(it.input)}</span>\n` +
            `<span class="ai" id="${oid}">${esc(it.output)}</span> ` +
            `<span class="copy" data-copy="${oid}">[copy]</span></div>`
          );
        })
        .join("");
    bindLog(items);
  } catch {
    logList.innerHTML = `<div class="err">could not load log</div>`;
  }
}

function bindLog(items) {
  logList.querySelectorAll("[data-copy]").forEach((el) =>
    el.addEventListener("click", () =>
      copyText(document.getElementById(el.dataset.copy).textContent, el)
    )
  );
  logList.querySelectorAll("[data-use]").forEach((el) =>
    el.addEventListener("click", () => {
      const it = items.find((x) => String(x.id) === el.dataset.use);
      if (it) {
        input.value = it.input;
        hidePanels();
        grow();
        input.focus();
      }
    })
  );
  logList.querySelectorAll("[data-del-log]").forEach((el) =>
    el.addEventListener("click", async () => {
      await fetch("/api/log/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: Number(el.dataset.delLog) }),
      });
      refreshLog(logSearch.value);
    })
  );
}

let logTimer = null;
logSearch.addEventListener("input", () => {
  clearTimeout(logTimer);
  logTimer = setTimeout(() => refreshLog(logSearch.value), 180);
});

document.getElementById("logClearAll").addEventListener("click", async () => {
  await fetch("/api/log/clear", { method: "POST" });
  logMsg.textContent = "all cleared.";
  refreshLog("");
});

document.getElementById("logClose").addEventListener("click", () => {
  hidePanels();
  input.focus();
});

// ---- run + commands ----------------------------------------------------- //

async function run() {
  const text = input.value.trim();
  if (!text) return;

  // cls (alone) or "-cls" anywhere -> clear everything
  if (/^cls$/i.test(text) || /-cls/i.test(text)) {
    clearAll();
    return;
  }

  // -settings -> manage saved style examples
  if (/^-?settings\b/i.test(text)) {
    const rest = text.replace(/^-?settings\b[ \t]*\r?\n?/i, "").trim();
    input.value = "";
    grow();
    await openSettings(rest);
    return;
  }

  // -log -> history with search
  if (/^-?log\b/i.test(text)) {
    input.value = "";
    grow();
    await openLog();
    return;
  }

  // key AIza... -> save api key
  if (/^key\s+/i.test(text)) {
    const k = text.replace(/^key\s+/i, "").trim();
    out.innerHTML = `<span class="busy">saving key...</span>`;
    try {
      const r = await fetch("/api/key", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: k }),
      });
      const d = await r.json();
      out.innerHTML = d.ok
        ? `<span class="label">key saved.</span>`
        : `<span class="err">${esc(d.error || "could not save")}</span>`;
    } catch {
      out.innerHTML = `<span class="err">could not save key</span>`;
    }
    input.value = "";
    grow();
    return;
  }

  hidePanels();
  out.innerHTML = `<span class="busy">...</span>`;
  try {
    const r = await fetch("/api/check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const d = await r.json();
    if (d.error) {
      out.innerHTML = `<span class="err">${esc(d.error)}</span>`;
      return;
    }
    render(d.ai, d.ai_error, text);
  } catch {
    out.innerHTML = `<span class="err">server not reachable</span>`;
  }
}

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    run();
  }
});

grow();
input.focus();
