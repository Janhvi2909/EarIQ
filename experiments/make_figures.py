"""Report / slide figures from the results files. Palette validated (dataviz validator, light mode):
normal AI = #eb6834 (orange), EarIQ = #6250d6 (violet). Static PNGs; every number also appears in a table."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "figures"
NORMAL, EARIQ = "#eb6834", "#6250d6"
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8a85", "#e6e6e3", "#fcfcfb"
GROUPS = {
    "Contact & routing": ["email_address", "phone_number", "phone_extension", "person_or_team_name", "postal_address"],
    "IDs & codes": ["reference_id", "product_code", "account_or_record_number"],
    "Web & network": ["url", "ip_address", "port_number"],
    "Code & system": ["command", "cli_flag", "file_path", "environment_variable", "code_symbol", "version"],
    "Numbers & dates": ["currency_amount", "percentage", "measurement", "plain_number", "date", "time"],
    "Spelled & acronyms": ["acronym_or_initialism", "spelled_sequence", "domain_term"],
}
PRIORITY = {"Phone numbers": ["phone_number"], "Emails": ["email_address"],
            "Names (spelled)": ["spelled_sequence", "person_or_team_name"],
            "IDs & account nos.": ["reference_id", "product_code", "account_or_record_number"]}

plt.rcParams.update({"font.family": ["Helvetica Neue", "Arial"], "font.size": 10,
                     "axes.edgecolor": GRID, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF})


def _style(ax):
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def paired_hbars(labels, a, b, title, fname, xlabel="Exact values captured (%)", note=None):
    fig, ax = plt.subplots(figsize=(7.2, 0.62 * len(labels) + 1.4), dpi=200)
    h = 0.36
    ys = list(range(len(labels)))[::-1]
    for y, va, vb in zip(ys, a, b):
        ax.barh(y + h / 2 + 0.01, va, h - 0.02, color=NORMAL)  # 2px-style gap between paired bars
        ax.barh(y - h / 2 - 0.01, vb, h - 0.02, color=EARIQ)
        ax.text(va + 1, y + h / 2, f"{va:.0f}%", va="center", fontsize=8.5, color=INK2)
        ax.text(vb + 1, y - h / 2, f"{vb:.0f}%", va="center", fontsize=8.5, color=INK, fontweight="bold")
    ax.set_yticks(ys, labels)
    ax.set_xlim(0, 108)
    ax.set_xlabel(xlabel)
    _style(ax)
    ax.set_title(title, loc="left", fontsize=11.5, color=INK, fontweight="bold", pad=22)
    ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=NORMAL), plt.Rectangle((0, 0), 1, 1, color=EARIQ)],
              labels=["Normal AI (Whisper as-is)", "EarIQ (same Whisper + capture layer)"],
              loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, frameon=False, fontsize=8.5, handlelength=1.2)
    if note:
        fig.text(0.01, 0.01, note, fontsize=7.5, color=MUTED)
    fig.tight_layout()
    fig.savefig(OUT / fname)
    plt.close(fig)


def entity_figures():
    rows = [json.loads(l) for l in (ROOT / "results/entities_rows.jsonl").open()]
    by = defaultdict(list)
    for r in rows:
        by[r["type"]].append(r)

    def acc(types, k):
        rs = [r for t in types for r in by[t]]
        return 100 * sum(r[k] for r in rs) / len(rs), len(rs)

    labels, a, b = [], [], []
    for g, types in GROUPS.items():
        va, n = acc(types, "base_strict")
        vb, _ = acc(types, "ours_strict")
        labels.append(f"{g}  (n={n})"), a.append(va), b.append(vb)
    paired_hbars(labels, a, b, "Exact values by entity group · VoiceCodeBench (300 recordings)", "entity_groups.png",
                 note="Strict scorer: the exact written value must appear. Same speech-model run for both systems.")
    labels, a, b = [], [], []
    for g, types in PRIORITY.items():
        va, n = acc(types, "base_strict")
        vb, _ = acc(types, "ours_strict")
        labels.append(f"{g}  (n={n})"), a.append(va), b.append(vb)
    paired_hbars(labels, a, b, "The fields voice agents ask for most", "priority_fields.png")


def robustness_figure():
    p = ROOT / "results/robustness.json"
    if not p.exists():
        return
    r = json.loads(p.read_text())
    names = {"clean": "Clean audio", "background_noise_10db": "Background noise (10 dB SNR)",
             "phone_line_8khz": "Phone line (8 kHz)", "speech_15pct_faster": "Speech 15% faster"}
    labels = [names[k] for k in names if k in r]
    paired_hbars(labels, [100 * r[k]["normal_ai"] for k in names if k in r], [100 * r[k]["eariq"] for k in names if k in r],
                 f"Robustness · {r['n_recordings']} recordings under harder audio", "robustness.png")


def speed_figure():
    p = ROOT / "results/speed.json"
    if not p.exists():
        return
    s = json.loads(p.read_text())["configs"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6), dpi=200)
    for name, m in s.items():
        chosen = "chosen" in name
        ax.scatter(m["x_faster_than_realtime"], 100 * m["eariq_exact"], s=90 if chosen else 55, color=EARIQ,
                   edgecolor=SURF, linewidth=2, zorder=3)
        ax.annotate(name.replace(" (chosen)", "  ← chosen"), (m["x_faster_than_realtime"], 100 * m["eariq_exact"]),
                    xytext=(8, -3), textcoords="offset points", fontsize=8.2, color=INK if chosen else INK2,
                    fontweight="bold" if chosen else "normal")
    ax.set_xlabel("Speed (× faster than real time, higher is better)")
    ax.set_ylabel("EarIQ exact values (%)")
    ax.grid(color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(length=0)
    xs = [m["x_faster_than_realtime"] for m in s.values()]
    ax.set_xlim(0, max(xs) * 1.6)
    ax.set_title("Accuracy vs speed of the speech model behind EarIQ", loc="left", fontsize=11.5, color=INK,
                 fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "speed_accuracy.png")
    plt.close(fig)


def architecture_figure():
    fig, ax = plt.subplots(figsize=(9, 3.0), dpi=200)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 32)
    ax.axis("off")

    def box(x, y, w, h, title, sub, fill, edge, tc=INK):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=2.2", fc=fill, ec=edge, lw=1.2))
        ax.text(x + w / 2, y + h * 0.63, title, ha="center", va="center", fontsize=9.6, fontweight="bold", color=tc)
        ax.text(x + w / 2, y + h * 0.3, sub, ha="center", va="center", fontsize=7.6, color=INK2 if tc == INK else tc)

    def arrow(x1, x2, y=16):
        ax.annotate("", (x2, y), (x1, y), arrowprops=dict(arrowstyle="-|>", color=MUTED, lw=1.2))

    box(1, 10, 13, 12, "Caller audio", "mic / phone line", "#ffffff", GRID)
    arrow(14.8, 18.2)
    box(19, 10, 15, 12, "Speech model", "Whisper large-v3-turbo\nwords + timing + confidence", "#ffffff", GRID)
    arrow(34.8, 38.2)
    ax.add_patch(FancyBboxPatch((38.5, 2), 42, 28, boxstyle="round,pad=0.4,rounding_size=2.5", fc="#f3f1ff", ec=EARIQ, lw=1.4))
    ax.text(59.5, 27.6, "EarIQ capture layer", ha="center", fontsize=10.5, fontweight="bold", color=EARIQ)
    box(40.5, 4, 12, 19, "Smart\nlistening", "wait while a\nvalue is coming", "#ffffff", "#d7d1ff")
    box(54, 4, 12, 19, "Format-aware\nhearing", "spoken → exact\nvalue + checks", "#ffffff", "#d7d1ff")
    box(67.5, 4, 12, 19, "Smart\ndouble-check", "ask only about\nthe unsure part", "#ffffff", "#d7d1ff")
    arrow(81.2, 84.6)
    box(85, 10, 14, 12, "Agent / CRM", "save · confirm\n· ask again", "#ffffff", GRID)
    fig.tight_layout()
    fig.savefig(OUT / "architecture.png")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    architecture_figure()
    entity_figures()
    robustness_figure()
    speed_figure()
    print("figures written to", OUT)
