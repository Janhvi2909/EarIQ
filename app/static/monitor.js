const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const NAMES = { p95_latency_s: "p95 latency", error_rate: "Error rate", ask_rate: "Ask-again rate", confirm_rate: "Confirm rate" };
const OUTCOME = { save: ["Saved", "ok"], confirm: ["Quick check", "warn"], ask: ["Asked again", "warn"] };

function fmt(name, v) {
  if (v == null) return "–";
  return name.endsWith("_s") ? `${v.toFixed(1)}s` : `${(v * 100).toFixed(0)}%`;
}

function bars(el, counts) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  el.innerHTML = rows.length
    ? rows.map(([k, n]) => `<div class="bar"><span>${esc(OUTCOME[k]?.[0] || k)}</span><span class="t"><i style="width:${(100 * n) / total}%"></i></span><span>${n}</span></div>`).join("")
    : '<div class="empty">No data yet</div>';
}

function spark(series) {
  const svg = $("#spark");
  svg.querySelectorAll("path,text").forEach((p) => p.remove());
  if (series.length < 2) return;
  const max = Math.max(...series) * 1.15, W = 600, H = 120;
  const pts = series.map((v, i) => [(i / (series.length - 1)) * W, H - (v / max) * (H - 10)]);
  const d = pts.map((p, i) => (i ? "L" : "M") + p[0].toFixed(1) + " " + p[1].toFixed(1)).join(" ");
  svg.insertAdjacentHTML("beforeend", `<path class="a" d="${d} L${W} ${H} L0 ${H}Z"/><path class="l" d="${d}"/>`);
}

async function refresh() {
  try {
    const m = await (await fetch("/api/v1/metrics")).json();
    $("#status").className = "status " + (m.model_ready ? "ready" : "");
    $("#status span").textContent = m.model_ready ? "Healthy" : "Loading model";
    $("#uptime").textContent = `Live · up ${Math.round(m.uptime_s / 60)} min · refreshes every 3s`;
    $("#k-req").textContent = m.requests;
    $("#k-lat").textContent = m.p50_latency_s != null ? `${m.p50_latency_s.toFixed(1)}s / ${m.p95_latency_s.toFixed(1)}s` : "–";
    $("#k-layer").textContent = `EarIQ layer p95 ${m.layer_ms_p95 != null ? m.layer_ms_p95 + " ms" : "–"}`;
    $("#k-ask").textContent = `${Math.round((m.ask_rate + m.confirm_rate) * 100)}%`;
    $("#k-ask-d").textContent = `${Math.round(m.confirm_rate * 100)}% confirm · ${Math.round(m.ask_rate * 100)}% ask again`;
    $("#k-err").textContent = m.errors;
    $("#k-err-d").textContent = `${m.fallbacks} fallbacks · ${(m.error_rate * 100).toFixed(1)}% rate`;
    spark(m.latency_series);
    $("#alerts").innerHTML = m.alerts.map((a) =>
      `<li><span>${NAMES[a.name]} <span class="muted">≤ ${fmt(a.name, a.threshold)}</span></span><span class="pill ${a.status === "ok" ? "ok" : "bad"}">${a.status === "ok" ? "OK" : "Alert"} · ${fmt(a.name, a.value)}</span></li>`).join("");
    const rows = m.recent.filter((r) => r.status !== "feedback").slice(0, 10);
    $("#recent").innerHTML = rows.length
      ? rows.map((r) => {
          const [label, cls] = r.status === "ok" ? OUTCOME[r.action] || [r.action, "neutral"] : [r.status, "bad"];
          return `<tr><td>${new Date(r.t * 1000).toLocaleTimeString()}</td><td>${esc(r.field)}</td><td><span class="pill ${cls}">${esc(label)}</span></td><td>${esc(r.value || "–")}</td><td>${r.latency_s ? r.latency_s.toFixed(1) + "s" : "–"}</td></tr>`;
        }).join("")
      : '<tr><td colspan="5" class="empty">No requests yet. Try the demo.</td></tr>';
    bars($("#bars"), m.actions);
    bars($("#langs"), m.languages);
  } catch {
    $("#status").className = "status down";
    $("#status span").textContent = "Server offline";
  }
}
refresh();
setInterval(refresh, 3000);
