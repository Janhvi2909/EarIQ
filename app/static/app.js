const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
const QUESTIONS = {
  phone: "What's the best number to reach you?",
  email: "What's your email address?",
  name: "Can I have your full name? Please spell it for me.",
  id: "What's your order ID?",
};
const LABEL = { phone: "phone number", email: "email", name: "name", id: "order ID" };
const ICON = {
  ok: '<svg viewBox="0 0 24 24"><path d="m5 12 5 5 9-10"/></svg>',
  warn: '<svg viewBox="0 0 24 24"><path d="M12 7v6M12 17v.01"/></svg>',
};
let field = "phone";
let ready = false;
let busy = false;
let lastId = null;

const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

/* ---------- model status ---------- */
async function pollHealth() {
  try {
    const h = await (await fetch("/api/v1/health")).json();
    ready = h.status === "ok";
    $("#status").className = "status " + (ready ? "ready" : h.error ? "down" : "");
    $("#status span").textContent = ready ? "Ready · runs on this device" : h.error ? "Model unavailable" : "Loading model…";
  } catch {
    $("#status").className = "status down";
    $("#status span").textContent = "Offline";
  }
  if (!ready) setTimeout(pollHealth, 2500);
}

/* ---------- field picker ---------- */
function setField(f) {
  field = f;
  $$("#fields .chip").forEach((c) => c.classList.toggle("active", c.dataset.field === f));
  $("#agent-q").textContent = QUESTIONS[f];
}
$$("#fields .chip").forEach((c) => c.addEventListener("click", () => setField(c.dataset.field)));

/* ---------- recording (WAV, 16 kHz mono, in the browser) ---------- */
const meter = $("#meter");
for (let i = 0; i < 28; i++) meter.appendChild(document.createElement("i"));
let rec = null;

async function startRec() {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: false } });
  } catch {
    return showError("Microphone access was blocked. Allow it in your browser, or play a sample.");
  }
  const ctx = new AudioContext();
  const src = ctx.createMediaStreamSource(stream);
  const proc = ctx.createScriptProcessor(4096, 1, 1);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 64;
  const chunks = [];
  proc.onaudioprocess = (e) => chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
  src.connect(analyser);
  src.connect(proc);
  proc.connect(ctx.destination);
  const started = performance.now();
  const bars = [...meter.children];
  const data = new Uint8Array(analyser.frequencyBinCount);
  const tick = () => {
    if (!rec) return;
    analyser.getByteFrequencyData(data);
    bars.forEach((b, i) => (b.style.height = 4 + (data[i % data.length] / 255) * 22 + "px"));
    const s = ((performance.now() - started) / 1000).toFixed(1);
    $("#rec-title").textContent = `Listening… ${s}s`;
    if (s > 30) stopRec();
    else requestAnimationFrame(tick);
  };
  rec = { stream, ctx, proc, chunks };
  $("#mic").classList.add("rec");
  meter.classList.add("live");
  $("#rec-sub").textContent = "Tap again when you're done";
  tick();
}

function stopRec() {
  if (!rec) return;
  const { stream, ctx, proc, chunks } = rec;
  rec = null;
  proc.disconnect();
  stream.getTracks().forEach((t) => t.stop());
  const rate = ctx.sampleRate;
  ctx.close();
  $("#mic").classList.remove("rec");
  meter.classList.remove("live");
  [...meter.children].forEach((b) => (b.style.height = "4px"));
  $("#rec-title").textContent = "Tap to speak";
  $("#rec-sub").textContent = "Try pausing in the middle. EarIQ will wait.";
  const len = chunks.reduce((n, c) => n + c.length, 0);
  const pcm = new Float32Array(len);
  let o = 0;
  chunks.forEach((c) => { pcm.set(c, o); o += c.length; });
  send(toWav(downsample(pcm, rate, 16000), 16000), field);
}

function downsample(buf, from, to) {
  if (from === to) return buf;
  const ratio = from / to, out = new Float32Array(Math.floor(buf.length / ratio));
  for (let i = 0; i < out.length; i++) {
    const a = Math.floor(i * ratio), b = Math.min(buf.length, Math.floor((i + 1) * ratio));
    let s = 0;
    for (let j = a; j < b; j++) s += buf[j];
    out[i] = s / Math.max(1, b - a);
  }
  return out;
}

function toWav(samples, rate) {
  const v = new DataView(new ArrayBuffer(44 + samples.length * 2));
  const w = (o, s) => [...s].forEach((c, i) => v.setUint8(o + i, c.charCodeAt(0)));
  w(0, "RIFF"); v.setUint32(4, 36 + samples.length * 2, true); w(8, "WAVE"); w(12, "fmt ");
  v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
  v.setUint32(24, rate, true); v.setUint32(28, rate * 2, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true);
  w(36, "data"); v.setUint32(40, samples.length * 2, true);
  samples.forEach((s, i) => v.setInt16(44 + i * 2, Math.max(-1, Math.min(1, s)) * 0x7fff, true));
  return new Blob([v], { type: "audio/wav" });
}

$("#mic").addEventListener("click", () => (rec ? stopRec() : !busy && startRec()));

/* ---------- samples ---------- */
$$(".sample").forEach((b) =>
  b.addEventListener("click", async () => {
    if (busy) return;
    setField(b.dataset.field);
    const blob = await (await fetch(`/static/samples/${b.dataset.sample}.wav`)).blob();
    const p = $("#player");
    p.src = URL.createObjectURL(blob);
    p.play().catch(() => {});
    send(blob, b.dataset.field, b.dataset.gold);
  })
);

/* ---------- request ---------- */
function setBusy(v) {
  busy = v;
  $$(".sample, .chip").forEach((b) => (b.disabled = v));
  $("#mic").disabled = v;
}

function showError(msg) {
  $("#out").hidden = false;
  $("#loading").hidden = true;
  $("#compare").hidden = true;
  $("#error").hidden = false;
  $("#error").textContent = msg;
  $("#meta").textContent = "";
}

async function send(blob, f, gold) {
  setBusy(true);
  $("#out").hidden = false;
  $("#error").hidden = true;
  $("#compare").hidden = true;
  $("#loading").hidden = false;
  $("#meta").textContent = "";
  const steps = $$(".progress li");
  steps.forEach((s, i) => (s.className = i ? "" : "on"));
  const timers = [setTimeout(() => { steps[0].className = "done"; steps[1].className = "on"; }, 1600),
                  setTimeout(() => { steps[1].className = "done"; steps[2].className = "on"; }, 2600)];
  $("#out").scrollIntoView({ behavior: "smooth", block: "start" });
  const fd = new FormData();
  fd.append("audio", blob, "speech.wav");
  fd.append("field", f);
  try {
    const r = await fetch("/api/v1/capture", { method: "POST", body: fd });
    const j = await r.json();
    if (!r.ok || j.status === "error") showError(j.message || "Something went wrong. Please try again.");
    else if (j.status === "no_speech") showError(j.message);
    else render(j, gold);
  } catch {
    showError("Can't reach the EarIQ server. Is it running?");
  } finally {
    timers.forEach(clearTimeout);
    setBusy(false);
  }
}

/* ---------- rendering ---------- */
function timeline(el, res, side, wait) {
  const end = res.end_at;
  const dur = Math.max(res.duration_s, end + wait + 0.3);
  const pct = (t) => `${(100 * t) / dur}%`;
  const stop = side.stop_at;
  let html = stop != null ? `<div class="after" style="left:${pct(stop)}"></div>` : "";
  res.speech.forEach(([a, b]) => {
    const lost = stop != null && a >= stop ? " lost" : "";
    html += `<div class="w${lost}" style="left:${pct(a)};width:max(3px,${pct(b - a)})"></div>`;
  });
  res.pauses.filter((p) => p.length >= 0.4).forEach((p) => {
    html += `<div class="gap" style="left:${pct((p.start + p.end) / 2)}">${p.length.toFixed(1)}s pause</div>`;
  });
  html += stop != null
    ? `<div class="cut" style="left:${pct(stop)}"><span>✂ Stopped listening</span></div>`
    : `<div class="end" style="left:${pct(Math.min(end + wait, dur - 0.05))}"><span>Heard you out ✓</span></div>`;
  el.innerHTML = html;
}

function heardText(side, formatted) {
  let text = esc(formatted);
  const v = side.value;
  if (v && formatted && formatted.includes(v)) text = text.replace(esc(v), `<mark>${esc(v)}</mark>`);
  return text + (side.missed ? ` <span class="missed">${esc(side.missed)}</span>` : "");
}

const norm = (f, v) => {
  if (!v) return "";
  if (f === "phone") return v.replace(/\D/g, "").slice(-10);
  if (f === "email") return v.toLowerCase();
  return v.replace(/[\s-]/g, "").toLowerCase();
};
const markGold = (f, v, gold) =>
  gold ? (norm(f, v) === norm(f, gold) ? '<span class="mark right">Correct</span>' : '<span class="mark wrong">Wrong</span>') : "";

function render(res, gold) {
  lastId = res.request_id;
  const f = res.field, n = res.normal_ai, e = res.eariq;
  $("#loading").hidden = true;
  $("#compare").hidden = false;

  // typical voice AI
  timeline($("#n-tl"), res, n, res.policy.normal_wait_s);
  $("#n-text").innerHTML = heardText(n, n.transcript);
  const nv = $("#n-value");
  nv.className = "value" + (n.value ? "" : " none");
  nv.innerHTML = n.value ? esc(n.value) + markGold(f, n.value, gold) : "Nothing captured" + (gold ? '<span class="mark wrong">Missed</span>' : "");
  const np = $("#n-pill");
  if (n.stop_at != null) { np.className = "pill bad"; np.textContent = "Cut you off"; }
  else if (n.value) { np.className = "pill neutral"; np.textContent = "Saved, unchecked"; }
  else { np.className = "pill bad"; np.textContent = "Missed it"; }
  $("#n-reply").textContent = n.value ? `Got it, ${n.value}. Thanks!` : "Sorry, I didn't catch that. Could you repeat everything?";

  // EarIQ
  timeline($("#e-tl"), res, e, res.policy.eariq_short_s);
  $("#e-text").innerHTML = heardText(e, e.transcript);
  const ev = $("#e-value");
  if (e.display) {
    let shown = esc(e.display);
    if (e.action === "confirm" && e.highlight && e.display.includes(e.highlight) && e.highlight !== e.display)
      shown = shown.replace(esc(e.highlight), `<span class="hl">${esc(e.highlight)}</span>`);
    ev.className = "value";
    ev.innerHTML = shown + markGold(f, e.value, gold);
  } else {
    ev.className = "value none";
    ev.textContent = "Not sure yet";
  }
  const ep = $("#e-pill");
  ep.className = "pill " + (e.action === "save" ? "ok" : "warn");
  ep.textContent = { save: "Saved", confirm: "Quick check", ask: "Asking again" }[e.action];
  $("#e-reply").textContent = e.action === "save" ? `Got it, ${e.display}. Thanks!` : e.question;
  $("#e-confirm").hidden = e.action !== "confirm";

  // checks
  const checks = [];
  if (e.stop_at == null) {
    if (n.stop_at != null) {
      const p = res.pauses.find((p) => p.start === n.cut_at);
      checks.push(["ok", `Waited through your <b>${p ? p.length.toFixed(1) + "s" : ""} pause</b>`]);
    } else checks.push(["ok", "Heard you to the end"]);
  } else checks.push(["warn", "Stopped at a long pause"]);
  const best = (e.values || []).filter((v) => v.value === e.value).pop();
  if (best) {
    if (!best.valid) checks.push(["warn", esc(best.issue)]);
    else if (best.issue && best.issue.startsWith("corrected")) checks.push(["ok", `Fixed a likely typo: <b>${esc(best.issue.replace("corrected domain ", ""))}</b>`]);
    else if (f === "phone") checks.push(["ok", `Valid phone format · <b>${e.value.replace(/\D/g, "").length} digits</b>`]);
    else if (f === "email") checks.push(["ok", "Valid email format"]);
    else if (f === "name") checks.push(["ok", "Matched to your spelling"]);
    else checks.push(["ok", "Valid ID format"]);
  }
  if (e.confidence != null) {
    const pctc = Math.round(e.confidence * 100);
    if (e.action === "confirm") checks.push(["warn", `Unsure about <b>"${esc(e.highlight)}"</b> · ${pctc}% confident`]);
    else checks.push(["ok", `Confident · <b>${pctc}%</b>`]);
  }
  $("#e-checks").innerHTML = checks.map(([c, t]) => `<li class="${c}"><span class="ic">${ICON[c]}</span><span>${t}</span></li>`).join("");

  const lat = res.latency_ms;
  $("#meta").textContent = `Processed in ${(lat.total / 1000).toFixed(1)}s · speech model ${(lat.asr / 1000).toFixed(1)}s · EarIQ layer ${lat.layer} ms · runs on this device, audio not stored`;
}

$$("#e-confirm .btn").forEach((b) =>
  b.addEventListener("click", async () => {
    const ok = b.dataset.ok === "1";
    const fd = new FormData();
    fd.append("request_id", lastId);
    fd.append("correct", ok);
    fetch("/api/v1/feedback", { method: "POST", body: fd }).catch(() => {});
    $("#e-confirm").hidden = true;
    $("#e-pill").className = "pill " + (ok ? "ok" : "warn");
    $("#e-pill").textContent = ok ? "Confirmed" : "Fixing";
    $("#e-reply").textContent = ok ? "Perfect, saved. Thanks!" : `No problem. Could you say your ${LABEL[field]} once more?`;
  })
);

/* ---------- measured results ---------- */
async function loadProof() {
  try {
    const b = await (await fetch("/api/v1/benchmarks")).json();
    const cards = [];
    const s = b.entities?.strict;
    if (s) cards.push([`−${Math.round(s.relative_error_reduction * 100)}%`, "Wrong values",
      `${(s.normal_ai_entity_acc * 100).toFixed(1)}% → ${(s.eariq_entity_acc * 100).toFixed(1)}% exact on ${b.entities.n_recordings} real recordings`]);
    const d = b.dev_synthetic?.smart_listening_dictation;
    if (d && d.cut_off_normal_ai) cards.push([`−${Math.round((1 - d.cut_off_eariq / d.cut_off_normal_ai) * 100)}%`, "Cut-offs while dictating",
      `${(d.cut_off_normal_ai * 100).toFixed(1)}% → ${(d.cut_off_eariq * 100).toFixed(1)}% on test calls with pauses`]);
    const q = b.entities?.double_check;
    if (q) cards.push([`${q.questions_per_5_values.toFixed(1)} / 5`, "Follow-up questions", "Asks about 1 in 5 answers or fewer, as targeted"]);
    if (cards.length) {
      $("#proof").innerHTML = cards.map(([big, cap, sub]) =>
        `<div class="card stat"><div class="big">${big}</div><div class="cap">${cap}</div><div class="sub">${sub}</div></div>`).join("");
      $("#proof-note").textContent = "Same speech model with and without EarIQ. Exact values: VoiceCodeBench (external test). Dictation: synthetic Indian-English test calls.";
    }
  } catch {}
}

setField("phone");
pollHealth();
loadProof();
