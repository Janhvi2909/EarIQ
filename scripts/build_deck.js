// EarIQ business presentation: node scripts/build_deck.js  (numbers are read from results/*.json)
// Needs pptxgenjs, react-icons, react, react-dom, sharp (npm). NODE_PATH may point at their node_modules.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const lu = require("react-icons/lu");

const ROOT = path.resolve(__dirname, "..");
const OUT = path.join(ROOT, "docs", "EarIQ_Presentation.pptx");
const R = (f) => { const p = path.join(ROOT, "results", f); return fs.existsSync(p) ? JSON.parse(fs.readFileSync(p, "utf8")) : null; };
const ent = R("entities.json"), endp = R("endpointing.json"), dev = R("dev_synthetic.json"), hindi = R("hindi.json");
const rob = R("robustness.json"), speed = R("speed.json"), perf = R("performance.json"), err = R("error_analysis.json");
const rows = fs.readFileSync(path.join(ROOT, "results/entities_rows.jsonl"), "utf8").trim().split("\n").map(JSON.parse);
const logRuns = fs.readFileSync(path.join(ROOT, "results/experiment_log.csv"), "utf8").trim().split("\n").length - 1;

const pct = (x, d = 0) => `${(100 * x).toFixed(d)}%`;
const PRIORITY = { "Phone numbers": ["phone_number"], "Emails": ["email_address"],
  "Names & spellings": ["spelled_sequence", "person_or_team_name"], "IDs & account nos.": ["reference_id", "product_code", "account_or_record_number"] };
const acc = (types, k) => { const rs = rows.filter((r) => types.includes(r.type)); return rs.filter((r) => r[k]).length / rs.length; };
const allPri = Object.values(PRIORITY).flat();

const THEME = { name: "EarIQ", headFontFace: "Calibri", bodyFontFace: "Calibri",
  colors: { dk1: "0D1224", lt1: "FFFFFF", dk2: "4A5270", lt2: "F3F1FF", accent1: "5B4CF0", accent2: "EB6834",
            accent3: "119C4B", accent4: "8B5CF6", accent5: "8A92A8", accent6: "C76A04", hlink: "5B4CF0", folHlink: "8B5CF6" } };
const HEX = { ink: "0D1224", ink2: "4A5270", muted: "8A92A8", brand: "5B4CF0", brandSoft: "F3F1FF", normal: "EB6834",
              ok: "119C4B", line: "E7E9F1", white: "FFFFFF", card: "F7F7FB" };

async function icon(names, color = "#5B4CF0", size = 256) {
  const C = names.map((n) => lu[n]).find(Boolean) || lu.LuCircle;
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(C, { color, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
  pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
  pres.title = "EarIQ: Voice AI that gets the details right";
  pres.author = "Janhvi Yadav, Ronit Choudhary, Asmit Kumar, Vaishnav Verma";
  const C = pres.SchemeColor;

  pres.defineSlideMaster({ title: "DARK", background: { color: HEX.ink },
    objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.8, y: 2.2, w: 11.7, h: 1.4, fontSize: 54, bold: true, color: HEX.white, fontFace: "Calibri", valign: "middle", align: "left", margin: 0 }, text: "" } }] });
  pres.defineSlideMaster({ title: "CONTENT", background: { color: HEX.white },
    objects: [
      { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 0.35, w: 12.1, h: 0.85, fontSize: 34, bold: true, color: HEX.ink, fontFace: "Calibri", valign: "middle", align: "left", margin: 0 }, text: "" } },
      { text: { text: "EarIQ · NLP Industry Track", options: { x: 0.6, y: 7.02, w: 6, h: 0.3, fontSize: 10, color: HEX.muted, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.02, w: 0.5, h: 0.3, fontSize: 10, color: HEX.muted, align: "right" } });

  const kicker = (s, text) => s.addText(text, { x: 0.6, y: 1.18, w: 12.1, h: 0.4, fontSize: 16, color: HEX.ink2, margin: 0, isTextBox: true });
  const card = (s, x, y, w, h, fill = HEX.card) => s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, line: { color: HEX.line, width: 0.75 }, rectRadius: 0.12 });
  const iconDot = async (s, names, x, y, d = 0.62, bg = HEX.brandSoft, fg = "#5B4CF0") => {
    s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg } });
    s.addImage({ data: await icon(names, fg), x: x + d * 0.22, y: y + d * 0.22, w: d * 0.56, h: d * 0.56 });
  };
  const stat = (s, x, y, w, big, label, sub, color = HEX.brand) => {
    s.addText(big, { x, y, w, h: 0.95, fontSize: 48, bold: true, color, margin: 0, isTextBox: true });
    s.addText(label, { x, y: y + 0.95, w, h: 0.4, fontSize: 16, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    if (sub) s.addText(sub, { x, y: y + 1.35, w, h: 0.7, fontSize: 12, color: HEX.ink2, margin: 0, valign: "top", isTextBox: true });
  };
  const sec = (t) => pres.addSection({ title: t });

  // ---------- 1. Title ----------
  sec("Opening");
  let s = pres.addSlide({ masterName: "DARK", sectionTitle: "Opening" });
  s.addImage({ data: await icon(["LuAudioLines", "LuAudioWaveform"], "#8B5CF6"), x: 0.8, y: 1.3, w: 0.8, h: 0.8 });
  s.addText("EarIQ", { placeholder: "title" });
  s.addText("Voice AI that gets the details right.", { x: 0.8, y: 3.55, w: 11.5, h: 0.7, fontSize: 28, color: "CFCBFF", margin: 0, isTextBox: true });
  s.addText([
    { text: "Janhvi Yadav (230117) · Ronit Choudhary (230074) · Asmit Kumar (230063) · Vaishnav Verma (230160)", options: { breakLine: true } },
    { text: "NLP · Industry Track · Final evaluation (Milestones 3–6)" }],
    { x: 0.8, y: 5.4, w: 11.7, h: 0.9, fontSize: 15, color: "B9BED0", margin: 0, isTextBox: true });
  s.addNotes("Voice AI can now talk like a human. It still can't listen like one. EarIQ is our plug-in layer that fixes the details that matter.");

  // ---------- 2. Problem ----------
  sec("Problem");
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem" });
  s.addText("Voice AI still misses the details that matter", { placeholder: "title" });
  kicker(s, "One wrong digit fails the task, even when the rest of the sentence is perfect");
  const probs = [[["LuEarOff", "LuEar"], "Mishears", "Names, numbers, emails and IDs come out wrong"],
                 [["LuScissors"], "Cuts you off", "A fixed silence timeout ends the turn mid-number"],
                 [["LuEyeOff"], "Hides it", "Word Error Rate weights a wrong digit like a wrong \"the\""]];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.95, 3.8, 2.55);
    await iconDot(s, probs[i][0], x + 0.35, 2.25);
    s.addText(probs[i][1], { x: x + 0.35, y: 3.0, w: 3.2, h: 0.45, fontSize: 20, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(probs[i][2], { x: x + 0.35, y: 3.45, w: 3.2, h: 0.9, fontSize: 14, color: HEX.ink2, margin: 0, valign: "top", isTextBox: true });
  }
  stat(s, 0.6, 4.95, 3.8, "55%", "of voice-agent users", "say repeating themselves is their top frustration (AssemblyAI survey)");
  stat(s, 4.7, 4.95, 3.8, "68.7%", "best model, every value right", "Deepgram Nova-3 gets all values in a recording right only ~2 in 3 times (VoiceCodeBench)");
  stat(s, 8.8, 4.95, 3.9, "295.9%", "WER on Gujarati", "GPT-4o Mini Transcribe, Voice of India benchmark: Indian languages are hardest");
  s.addNotes("Three failures: mishearing, cutting people off, and scores that hide both. The numbers are from published sources gathered in M1.");

  // ---------- 3. Users & business case ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem" });
  s.addText("Who pays for this, and how we measure success", { placeholder: "title" });
  kicker(s, "A plug-in layer for voice-AI builders, not a new speech model");
  const users = [[["LuBlocks", "LuBox"], "Voice-AI builders", "Sarvam, Bolna, Vapi-type platforms"],
                 [["LuBuilding2", "LuBuilding"], "Businesses", "Banking, healthcare, commerce, travel"],
                 [["LuUsers"], "End users", "Indian English, Hinglish, Hindi speakers"]];
  for (let i = 0; i < 3; i++) {
    const y = 1.95 + i * 1.12;
    await iconDot(s, users[i][0], 0.6, y);
    s.addText(users[i][1], { x: 1.45, y: y - 0.02, w: 4.3, h: 0.38, fontSize: 17, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(users[i][2], { x: 1.45, y: y + 0.36, w: 4.3, h: 0.35, fontSize: 13, color: HEX.ink2, margin: 0, isTextBox: true });
  }
  card(s, 6.2, 1.95, 6.5, 3.2, HEX.brandSoft);
  s.addText("Targets set in M1", { x: 6.55, y: 2.15, w: 6, h: 0.4, fontSize: 16, bold: true, color: HEX.brand, margin: 0, isTextBox: true });
  const tg = [["−30%", "wrong values"], ["−50%", "cut-offs mid-value"], ["≤ 1 / 5", "follow-up questions"], ["< 200 ms", "added delay"]];
  tg.forEach(([b, l], i) => {
    const x = 6.55 + (i % 2) * 3.1, y = 2.7 + Math.floor(i / 2) * 1.2;
    s.addText(b, { x, y, w: 2.9, h: 0.6, fontSize: 30, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(l, { x, y: y + 0.58, w: 2.9, h: 0.35, fontSize: 13, color: HEX.ink2, margin: 0, isTextBox: true });
  });
  s.addText("Business objective: the right value on the first try, fewer repeats and hand-offs, no noticeable delay.",
    { x: 0.6, y: 5.6, w: 12.1, h: 0.6, fontSize: 16, color: HEX.ink, margin: 0, isTextBox: true });
  s.addNotes("Primary users are voice-AI builders. Targets were fixed in M1, before building, and we report each one honestly at the end.");

  // ---------- 4. Solution ----------
  sec("Solution");
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Solution" });
  s.addText("EarIQ: three small things, done right", { placeholder: "title" });
  kicker(s, "Sits between any speech model and the agent. Runs on a laptop, no paid API, no audio leaves the device");
  s.addImage({ path: path.join(ROOT, "results/figures/architecture.png"), x: 0.6, y: 1.8, w: 12.1, h: 4.03 });
  s.addText([
    { text: "Smart listening ", options: { bold: true, color: HEX.brand } }, { text: "waits while a value is still coming.   " },
    { text: "Format-aware hearing ", options: { bold: true, color: HEX.brand } }, { text: "turns speech into exact values.   " },
    { text: "Smart double-check ", options: { bold: true, color: HEX.brand } }, { text: "asks only about the unsure part." }],
    { x: 0.6, y: 6.05, w: 12.1, h: 0.6, fontSize: 15, color: HEX.ink, margin: 0, isTextBox: true });
  s.addNotes("Audio goes into Whisper large-v3-turbo. EarIQ adds three components, the same three promised in M1.");

  // ---------- 5. Data ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Solution" });
  s.addText("Data: three public datasets, each for one question", { placeholder: "title" });
  kicker(s, "4,202 recordings · 17.2 hours · leak-free splits (M2) · test sets never used for tuning");
  const ds = [[["LuHash"], "VoiceCodeBench", "300 recordings · 1,482 exact values · 26 types", "Exact values (English)"],
              [["LuTimer"], "LiveKit eot-bench", "800 turns · 1,524 pauses + 800 turn ends", "Turn timing (English + Hindi)"],
              [["LuLanguages"], "IndicContextEval Hindi", "3,102 recordings · 124 speakers · 23 domains", "Hindi / Hinglish · train 2,169 / val 466 / test 467"]];
  for (let i = 0; i < 3; i++) {
    const x = 0.6 + i * 4.1;
    card(s, x, 1.95, 3.8, 3.3);
    await iconDot(s, ds[i][0], x + 0.35, 2.25);
    s.addText(ds[i][1], { x: x + 0.35, y: 3.0, w: 3.2, h: 0.45, fontSize: 19, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(ds[i][2], { x: x + 0.35, y: 3.48, w: 3.2, h: 0.7, fontSize: 13, color: HEX.ink2, margin: 0, valign: "top", isTextBox: true });
    s.addText(ds[i][3], { x: x + 0.35, y: 4.3, w: 3.2, h: 0.7, fontSize: 13, bold: true, color: HEX.brand, margin: 0, valign: "top", isTextBox: true });
  }
  s.addText("+ 120 synthetic practice clips (Mac voices Aman, Rishi, Tara; fictional values) used only to design rules and pick thresholds.",
    { x: 0.6, y: 5.6, w: 12.1, h: 0.6, fontSize: 15, color: HEX.ink2, margin: 0, isTextBox: true });
  s.addNotes("M2 recap. The external benchmarks are test-only. Design used a synthetic practice set and the Hindi validation split.");

  // ---------- 6. Models (M3) ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Solution" });
  s.addText("M3: a fair baseline, then better candidates", { placeholder: "title" });
  kicker(s, "Baseline = the same Whisper run without EarIQ, so every gain comes from the layer");
  const tbl = [["Track", "Baseline", "Candidates", "Tested on"].map((t) => ({ text: t, options: { bold: true, color: HEX.brand, fill: { color: HEX.brandSoft } } })),
    ["Exact values", "Whisper as-is", "+ format-aware hearing, + double-check", "VoiceCodeBench (300)"],
    ["Smart listening", "Fixed silence timeout", "Entity rules → + grammar → + trained completion model", "LiveKit held-out half"],
    ["Hindi / Hinglish", "Whisper, no hints", "+ key-term hint list; unrelated hints (check)", "Hindi test (467)"],
    ["Double-check", "Never / always ask", "Ask only on low confidence or failed format", "VoiceCodeBench"]];
  s.addTable(tbl, { x: 0.6, y: 1.9, w: 12.1, colW: [2.2, 2.5, 4.6, 2.8], fontSize: 14, color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line }, rowH: 0.55, valign: "middle" });
  stat(s, 0.6, 5.0, 3.8, String(logRuns), "logged experiment runs", "results/experiment_log.csv: config, metrics, git commit");
  stat(s, 4.7, 5.0, 3.8, "15", "automated tests", "formatting, capture decisions, failure paths");
  stat(s, 8.8, 5.0, 3.9, "1", "trained model", "\"finished speaking?\" TF-IDF + logistic regression");
  s.addNotes("Version-controlled on GitHub with milestone commits; every run is logged with its config and git commit.");

  // ---------- 7. Result: exact values ----------
  sec("Results");
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  const st = ent.strict;
  s.addText("Result 1: far fewer wrong values", { placeholder: "title" });
  kicker(s, `Same speech model, same ${ent.n_recordings} real recordings (${ent.n_entities.toLocaleString()} values). Only difference: EarIQ`);
  stat(s, 0.6, 1.95, 4.2, `−${pct(st.relative_error_reduction)}`, "wrong values (all 26 types)",
    `${pct(st.normal_ai_entity_acc, 1)} → ${pct(st.eariq_entity_acc, 1)} exact · 95% CI of gain +${pct(st.diff_95ci_speaker_bootstrap[0], 1)} to +${pct(st.diff_95ci_speaker_bootstrap[1], 1)} · target −30%`);
  const priB = acc(allPri, "base_strict"), priO = acc(allPri, "ours_strict");
  stat(s, 0.6, 4.3, 4.2, `${pct(priB)} → ${pct(priO)}`, "the fields agents ask for most", "phones, emails, names, IDs: exact on the first try");
  const labels = Object.keys(PRIORITY);
  s.addChart(pres.charts.BAR, [
    { name: "Normal AI", labels, values: labels.map((l) => +(100 * acc(PRIORITY[l], "base_strict")).toFixed(1)) },
    { name: "EarIQ", labels, values: labels.map((l) => +(100 * acc(PRIORITY[l], "ours_strict")).toFixed(1)) }],
    { x: 5.2, y: 1.85, w: 7.5, h: 4.9, barDir: "bar", barGrouping: "clustered", barGapWidthPct: 60, chartColors: [HEX.normal, HEX.brand],
      showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0\"%\"", dataLabelFontSize: 11, dataLabelColor: HEX.ink2,
      catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 13, catAxisOrientation: "maxMin", valAxisHidden: true, valAxisMaxVal: 110, valAxisMinVal: 0,
      valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: true, legendPos: "t", legendFontSize: 12,
      showTitle: true, title: "Exact values captured (%)", titleFontSize: 13, titleColor: HEX.ink,
      catAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt" });
  s.addNotes("Strict scorer: the exact written value must appear. Normal AI and EarIQ use the same Whisper output; the gain is entirely the capture layer.");

  // ---------- 8. Result: smart listening ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  const d = dev.smart_listening_dictation, b8 = endp.budgets["0.8"]["EarIQ (rules+grammar+model)"];
  s.addText("Result 2: it waits while you're still talking", { placeholder: "title" });
  kicker(s, "Measured at the same average waiting time as a fixed timeout, so faster is never traded for fewer cut-offs");
  card(s, 0.6, 1.95, 5.9, 3.55, HEX.brandSoft);
  await iconDot(s, ["LuPhone"], 0.95, 2.25, 0.62, HEX.white);
  s.addText("Dictating a value (agent knows the field)", { x: 1.75, y: 2.3, w: 4.6, h: 0.5, fontSize: 16, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
  stat(s, 0.95, 3.05, 5.3, `−${pct(1 - d.cut_off_eariq / d.cut_off_normal_ai)}`, "cut-offs mid-value",
    `A 0.6 s timeout cut off ${pct(d.cut_off_normal_ai)} of calls with a 0.9 s pause inside the value; EarIQ ${pct(d.cut_off_eariq, 1)} · synthetic voices · target −50%`);
  card(s, 6.8, 1.95, 5.9, 3.55);
  await iconDot(s, ["LuMessagesSquare", "LuMessageSquare"], 7.15, 2.25);
  s.addText("Free conversation (real LiveKit calls)", { x: 7.95, y: 2.3, w: 4.6, h: 0.5, fontSize: 16, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
  stat(s, 7.15, 3.05, 5.3, `${pct(b8.in_value_cutoff_rate)} vs ${pct(b8.baseline_in_value_cutoff_rate)}`, "cut-offs inside a value",
    `Overall cut-offs ${pct(b8.test_cutoff_rate, 1)} vs ${pct(b8.baseline_cutoff_rate, 1)}: no significant gain in open conversation (95% CI includes 0). Honest result; v1 was worse, v2 fixed it.`);
  s.addText("How: wait 0.6 s after a complete answer, 1.5 s only while a value is provably unfinished (e.g. 5 of 10 phone digits, an email with no ending yet).",
    { x: 0.6, y: 5.8, w: 12.1, h: 0.6, fontSize: 15, color: HEX.ink, margin: 0, isTextBox: true });
  s.addNotes("Dictation is where smart listening matters, and there it meets the target. In open conversation it only helps inside values; overall it matches a tuned timeout.");

  // ---------- 9. Result: double-check + Hindi ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  const dc = ent.double_check;
  s.addText("Result 3: asks rarely, and works for Hindi too", { placeholder: "title" });
  kicker(s, "Targeted questions instead of re-asking everything; Hindi and Hinglish speech with key-term hints");
  card(s, 0.6, 1.95, 5.9, 3.55);
  await iconDot(s, ["LuCircleHelp", "LuHelpCircle"], 0.95, 2.25);
  s.addText("Smart double-check", { x: 1.75, y: 2.3, w: 4.6, h: 0.5, fontSize: 16, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
  stat(s, 0.95, 3.05, 5.3, `${dc.questions_per_5_values.toFixed(1)} / 5`, "follow-up questions per 5 values",
    `Target ≤ 1 / 5 (always-confirm = 5 / 5). Catches ${pct(dc.wrong_values_caught)} of remaining wrong values; ${pct(dc.flagged_that_were_wrong)} of its questions point at a real error.`);
  card(s, 6.8, 1.95, 5.9, 3.55);
  await iconDot(s, ["LuLanguages"], 7.15, 2.25);
  s.addText("Hindi / Hinglish (test, 467 clips)", { x: 7.95, y: 2.3, w: 4.6, h: 0.5, fontSize: 16, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
  if (hindi && hindi.test) {
    const h0 = hindi.test.H0_no_hints, best = hindi.chosen_on_validation, hb = hindi.test[best];
    const ht = [["", "WER", "CER", "Borrowed-term error"].map((t) => ({ text: t, options: { bold: true, color: HEX.brand } })),
      ["No hints (baseline)", pct(h0.wer, 1), pct(h0.cer, 1), pct(h0.term_error, 1)]];
    if (best !== "H0_no_hints") ht.push(["Key-term hints", pct(hb.wer, 1), pct(hb.cer, 1), pct(hb.term_error, 1)]);
    s.addTable(ht, { x: 7.15, y: 2.95, w: 5.25, colW: [2.05, 0.9, 0.9, 1.4], fontSize: 13, color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line }, rowH: 0.5 });
    const v6 = hindi.validation_subset.H6_unrelated_terms, v0 = hindi.validation_subset.H0_no_hints;
    s.addText(`Wrong hints (unrelated terms) on validation: WER ${pct(v6.wer, 1)} vs ${pct(v0.wer, 1)} with none.`,
      { x: 7.15, y: 4.6, w: 5.25, h: 0.75, fontSize: 12, color: HEX.ink2, margin: 0, valign: "top", isTextBox: true });
  }
  s.addText("Thresholds and hint settings were chosen on development data; the test sets were scored once.",
    { x: 0.6, y: 5.8, w: 12.1, h: 0.6, fontSize: 15, color: HEX.ink, margin: 0, isTextBox: true });
  s.addNotes("The double-check meets its burden target. Hindi uses the same speech model; key-term hints are what a product would pass from its own vocabulary.");

  // ---------- 10. Error analysis + iterations ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("What still goes wrong, and how we improved", { placeholder: "title" });
  kicker(s, `Of ${err.n_wrong_after_eariq} values still wrong after EarIQ: EarIQ fixed ${err.fixed_by_eariq} and broke ${err.broken_by_eariq}`);
  const cats = [["misheard", "Misheard or missing"], ["near_miss", "Near miss (format variant / 1-letter slip)"], ["heard_not_formatted", "Heard, format not covered"], ["regression", "Broken by EarIQ"]];
  s.addChart(pres.charts.BAR, [{ name: "Share of remaining errors", labels: cats.map((c) => c[1]),
    values: cats.map(([k]) => +(100 * ((err.categories[k] || {}).share_of_errors || 0)).toFixed(1)) }],
    { x: 0.6, y: 1.85, w: 6.0, h: 3.6, barDir: "bar", chartColors: [HEX.brand], showValue: true, dataLabelPosition: "outEnd",
      dataLabelFormatCode: "0\"%\"", dataLabelFontSize: 11, dataLabelColor: HEX.ink2, catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 12,
      catAxisOrientation: "maxMin", valAxisHidden: true, valAxisMaxVal: 100, valGridLine: { style: "none" }, catGridLine: { style: "none" },
      showLegend: false, showTitle: true, title: "Share of remaining errors (%)", titleFontSize: 13, titleColor: HEX.ink,
      catAxisLabelFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt" });
  s.addText("Remedy: the double-check for mishearings; more format rules (dates, times, addresses) for the rest.",
    { x: 0.6, y: 5.6, w: 6.0, h: 0.8, fontSize: 14, color: HEX.ink2, margin: 0, valign: "top", isTextBox: true });
  const its = [["v0", "Word pieces split values (\"INV\" + \"-53554\")", "dev 23% → 74% after re-joining"],
               ["v1", "Emails, domains, spelled names", "two-word names, \"gmial.com\" snapping"],
               ["v1", "Smart listening lost to a timeout", "flagged real turn endings as unfinished"],
               ["v2", "Stricter rules + in-domain model", "dev/test split; mid-value cut-offs ↓"]];
  its.forEach(([v, a, b], i) => {
    const y = 1.95 + i * 1.12;
    s.addShape(pres.shapes.OVAL, { x: 7.0, y, w: 0.55, h: 0.55, fill: { color: HEX.brand }, line: { color: HEX.brand } });
    s.addText(v, { x: 7.0, y, w: 0.55, h: 0.55, fontSize: 12, bold: true, color: HEX.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
    s.addText(a, { x: 7.75, y: y - 0.03, w: 4.95, h: 0.35, fontSize: 15, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(b, { x: 7.75, y: y + 0.33, w: 4.95, h: 0.35, fontSize: 13, color: HEX.ink2, margin: 0, isTextBox: true });
  });
  s.addNotes("Error analysis: most remaining errors are the speech model mishearing, which the double-check targets. Improvement iterations were all made on dev data, never on test.");

  // ---------- 11. Robustness + speed ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Results" });
  s.addText("Robust under harder audio, fast enough to deploy", { placeholder: "title" });
  kicker(s, "Robustness on 25 recordings per condition; speed measured on the team's MacBook (Apple M3, 16 GB)");
  if (rob) {
    const conds = [["clean", "Clean"], ["background_noise_10db", "Noise 10 dB"], ["phone_line_8khz", "Phone line"], ["speech_15pct_faster", "15% faster"]];
    s.addChart(pres.charts.BAR, [
      { name: "Normal AI", labels: conds.map((c) => c[1]), values: conds.map(([k]) => +(100 * rob[k].normal_ai).toFixed(1)) },
      { name: "EarIQ", labels: conds.map((c) => c[1]), values: conds.map(([k]) => +(100 * rob[k].eariq).toFixed(1)) }],
      { x: 0.6, y: 1.85, w: 6.3, h: 4.8, barDir: "col", barGrouping: "clustered", barGapWidthPct: 60, chartColors: [HEX.normal, HEX.brand],
        showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0\"%\"", dataLabelFontSize: 11, dataLabelColor: HEX.ink2,
        catAxisLabelColor: HEX.ink, catAxisLabelFontSize: 12, valAxisHidden: true, valAxisMaxVal: 100, valAxisMinVal: 0,
        valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: true, legendPos: "t", legendFontSize: 12,
        showTitle: true, title: "Exact values under harder audio (%)", titleFontSize: 13, titleColor: HEX.ink,
        catAxisLabelFontFace: "+mn-lt", legendFontFace: "+mn-lt", dataLabelFontFace: "+mn-lt", titleFontFace: "+mn-lt" });
  }
  if (speed) {
    const sp = Object.entries(speed.configs);
    const t = [["Speech model setting", "× real time", "EarIQ exact"].map((x) => ({ text: x, options: { bold: true, color: HEX.brand, fill: { color: HEX.brandSoft } } })),
      ...sp.map(([n, m]) => [n.replace(" (chosen)", " ✓").replace(" (Docker)", " (Docker)"), `${m.x_faster_than_realtime}×`, pct(m.eariq_exact, 1)])];
    s.addTable(t, { x: 7.2, y: 1.95, w: 5.5, colW: [3.1, 1.1, 1.3], fontSize: 12, color: HEX.ink, border: { type: "solid", pt: 0.75, color: HEX.line }, rowH: 0.48 });
  }
  if (perf) stat(s, 7.2, 4.75, 5.5, `${perf.sequential.eariq_layer_ms_p95.toFixed(1)} ms`, "added by EarIQ (p95)",
    `Target < 200 ms · full answer in ${perf.sequential.latency_p50_s.toFixed(1)} s (p50) on a laptop`);
  s.addNotes("EarIQ's gain holds under noise, phone-line audio and fast speech. We chose turbo on the GPU; the Docker build runs the same model on CPU with int8.");

  // ---------- 12. Deployment ----------
  sec("Product");
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("M5: a working product, not a notebook", { placeholder: "title" });
  kicker(s, "Web app + REST API + monitoring + failure handling, deployable with Docker");
  s.addImage({ path: path.join(ROOT, "docs/images/app_name_compare.png"), x: 0.6, y: 1.85, w: 7.0, h: 3.31 });
  const feats = [[["LuServer"], "REST API", "POST /api/v1/capture → value + save / confirm / ask"],
                 [["LuActivity"], "Monitoring", "latency, follow-up rate, errors, alerts; values masked"],
                 [["LuShieldCheck"], "Failure handling", "empty, corrupt, silent, too-long audio, timeouts, busy"],
                 [["LuContainer", "LuBox"], "Deployment", "Docker image; runs offline on one laptop"]];
  for (let i = 0; i < feats.length; i++) {
    const y = 1.9 + i * 1.18;
    await iconDot(s, feats[i][0], 8.0, y, 0.58);
    s.addText(feats[i][1], { x: 8.75, y: y - 0.04, w: 4.0, h: 0.36, fontSize: 16, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(feats[i][2], { x: 8.75, y: y + 0.32, w: 4.0, h: 0.6, fontSize: 12.5, color: HEX.ink2, margin: 0, valign: "top", isTextBox: true });
  }
  if (perf) s.addText(`Measured: ${perf.sequential.latency_p50_s.toFixed(1)} s p50 / ${perf.sequential.latency_p95_s.toFixed(1)} s p95 per answer · ${perf.concurrent_4_users.throughput_req_per_min} answers / min with 4 users · ${pct(perf.sequential.success_rate)} success`,
    { x: 0.6, y: 5.5, w: 7.0, h: 0.8, fontSize: 14, color: HEX.ink, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("Show the live demo next. Everything here is in the GitHub repo.");

  // ---------- 13. Live demo ----------
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Product" });
  s.addImage({ data: await icon(["LuMonitorPlay", "LuMonitor"], "#8B5CF6"), x: 0.8, y: 1.3, w: 0.8, h: 0.8 });
  s.addText("Live demo", { placeholder: "title" });
  s.addText("localhost:8000 · Number with a pause → Spelled name → \"at the rate\" email → your own voice → Monitor",
    { x: 0.8, y: 3.6, w: 11.7, h: 0.9, fontSize: 20, color: "CFCBFF", margin: 0, isTextBox: true });
  s.addNotes("Follow docs/DEMO_SCRIPT.md. Backup: the recorded demo video.");

  // ---------- 14. Business impact ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("What this means for a business", { placeholder: "title" });
  kicker(s, "Illustration for 1,000 captured phones, emails, names and IDs (from the measured priority-field rates)");
  const wb = Math.round((1 - priB) * 1000), wo = Math.round((1 - priO) * 1000);
  stat(s, 0.6, 2.0, 3.8, `${wb} → ${wo}`, "wrong or unusable values", "per 1,000 captured, before any follow-up question");
  stat(s, 4.7, 2.0, 3.8, "₹0", "API cost", "open models on the builder's own hardware; no per-minute fees");
  stat(s, 8.8, 2.0, 3.9, perf ? `${perf.sequential.eariq_layer_ms_p95.toFixed(0)} ms` : "< 200 ms", "added delay", "callers don't notice; no extra round-trip");
  card(s, 0.6, 4.5, 12.1, 1.9, HEX.brandSoft);
  s.addText([
    { text: "Fewer wrong records ", options: { bold: true } }, { text: "→ fewer failed callbacks, deliveries and refunds.  ", options: {} },
    { text: "Fewer repeats ", options: { bold: true } }, { text: "→ fewer frustrated callers and human hand-offs.  " },
    { text: "Plug-in ", options: { bold: true } }, { text: "→ works with any speech model a platform already uses." }],
    { x: 0.95, y: 4.7, w: 11.4, h: 1.5, fontSize: 16, color: HEX.ink, margin: 0, valign: "middle", isTextBox: true });
  s.addNotes("These are illustrations from measured rates, not a pilot with real customers. Real savings need a pilot.");

  // ---------- 15. Limits & next steps ----------
  s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  s.addText("Limits we know, and what's next", { placeholder: "title" });
  kicker(s, "Honest about scope");
  const lim = ["Exact-value test is English workplace speech; only 6 recordings are Indian-accented",
               "Dictation gains use synthetic voices; open conversation shows no overall timing gain",
               "Our strict scorer differs from the official GPT verifier (lower absolute numbers)",
               "Repair after a follow-up question is not measured offline"];
  const nxt = ["Pilot with a voice-agent platform on consented Indian-English / Hinglish calls",
               "Streaming integration (Vapi / LiveKit custom transcriber)",
               "Format rules for dates, times, addresses, currency",
               "N-best re-ranking with format checks; fine-tune on Hindi train split"];
  for (const [i, [items, head, ic]] of [[lim, "Limitations", ["LuTriangleAlert", "LuAlertTriangle"]], [nxt, "Next steps", ["LuRocket"]]].entries()) {
    const x = 0.6 + i * 6.2;
    card(s, x, 1.95, 5.9, 3.9, i ? HEX.brandSoft : HEX.card);
    await iconDot(s, ic, x + 0.35, 2.2, 0.58, i ? HEX.white : HEX.brandSoft);
    s.addText(head, { x: x + 1.1, y: 2.25, w: 4.5, h: 0.45, fontSize: 18, bold: true, color: HEX.ink, margin: 0, isTextBox: true });
    s.addText(items.map((t, k) => ({ text: t, options: { bullet: true, breakLine: k < items.length - 1 } })),
      { x: x + 0.35, y: 2.95, w: 5.25, h: 2.8, fontSize: 14, color: HEX.ink2, paraSpaceAfter: 8, valign: "top", margin: 0, isTextBox: true });
  }
  s.addNotes("Limitations are also in the report's threats-to-validity section.");

  // ---------- 16. Close ----------
  sec("Close");
  s = pres.addSlide({ masterName: "DARK", sectionTitle: "Close" });
  s.addText("Thank you", { placeholder: "title" });
  s.addText("\"We're not building a voice AI that talks better. We're building one that listens better.\"",
    { x: 0.8, y: 3.6, w: 11.7, h: 0.9, fontSize: 22, italic: true, color: "CFCBFF", margin: 0, isTextBox: true });
  s.addText("github.com/Janhvi2909/EarIQ  ·  Questions?", { x: 0.8, y: 5.4, w: 11.7, h: 0.5, fontSize: 16, color: "B9BED0", margin: 0, isTextBox: true });
  s.addNotes("Open for questions. Viva prep: docs/VIVA_PREP.md.");

  await pres.writeFile({ fileName: OUT });
  const { applyTheme } = require(process.env.PPTX_SKILL + "/scripts/apply_theme.js");
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
