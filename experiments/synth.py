"""Synthetic intake utterances with fictional values (development only, never reported as real-world accuracy).

1. `sentences()` -> spoken-form English intake sentences for training the completion model.
2. `python experiments/synth.py` -> TTS dev set (macOS voices incl. Indian English) in data/synthetic/.

Phone numbers use the US 555-01xx fictional range or random Indian-style digits that are never dialled;
emails use example.* domains; names are random combinations.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPOKEN = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
FIRST = ["Priya", "Rahul", "Ananya", "Vikram", "Sneha", "Arjun", "Meera", "Karan", "Divya", "Rohan",
         "Nisha", "Aditya", "Kavya", "Siddharth", "Pooja", "Neil", "Sara", "David", "Maria", "Leo"]
LAST = ["Sharma", "Iyer", "Mehta", "Reddy", "Kapoor", "Nair", "Joshi", "Gupta", "Rao", "Das",
        "Bose", "Malhotra", "Pillai", "Verma", "Kell", "Voss", "Lark", "Fernandes", "Khan", "Singh"]
DOMAINS = ["example dot com", "example dot in", "example dot org", "mail dot example dot com"]
VOICES = ["Aman", "Rishi", "Tara", "Samantha", "Daniel"]
PAUSE = "[[slnc 900]]"


def _digits(n, rng, first="6789"):
    return rng.choice(first) + "".join(rng.choice("0123456789") for _ in range(n - 1))


def _say_digits(d, groups, pause=False):
    out, i = [], 0
    for g in groups:
        out.append(" ".join(SPOKEN[int(c)] for c in d[i:i + g]))
        i += g
    return (f", {PAUSE} " if pause else ", ").join(out)


def phone(rng, pause=False):
    if rng.random() < 0.6:  # Indian mobile style 5+5
        d = _digits(10, rng)
        spoken = _say_digits(d, [5, 5], pause)
    else:  # US fictional 555-01xx
        d = _digits(3, rng, "2345678") + "55501" + "".join(rng.choice("0123456789") for _ in range(2))
        spoken = _say_digits(d, [3, 3, 4], pause)
    t = rng.choice(["My number is {v}.", "You can call me on {v}.", "It's {v}.",
                    "My phone number is {v}.", "Please call me back at {v}."])
    return "phone", t.format(v=spoken), d


def email(rng, pause=False):
    f, l = rng.choice(FIRST).lower(), rng.choice(LAST).lower()
    dom = rng.choice(DOMAINS)
    at = rng.choice(["at", "at the rate", "at"])
    local = rng.choice([f"{f} dot {l}", f"{f}{l}", f"{f} underscore {l}", f"{f[0]} {l}"])
    sep = f" {PAUSE} " if pause else " "
    spoken = f"{local}{sep}{at} {dom}"
    value = (local.replace(" dot ", ".").replace(" underscore ", "_").replace(" ", "")
             + "@" + dom.replace(" dot ", "."))
    t = rng.choice(["My email is {v}.", "You can email me at {v}.", "It's {v}.",
                    "Send it to {v}."])
    return "email", t.format(v=spoken), value


def name(rng, pause=False):
    f, l = rng.choice(FIRST), rng.choice(LAST)
    spell = " ".join(f.upper()) + (f", {PAUSE} " if pause else " ") + " ".join(l.upper())
    t = rng.choice(["My name is {n}, that's {s}.", "This is {n}, spelled {s}.",
                    "I'm {n}. The spelling is {s}."])
    return "name", t.format(n=f"{f} {l}", s=spell), f"{f} {l}"


def order_id(rng, pause=False):
    pre = rng.choice(["ORD", "TKT", "INV", "PNR", "REF"])
    digits = "".join(rng.choice("0123456789") for _ in range(rng.choice([4, 5, 6])))
    suffix = rng.choice(["", "", rng.choice("ABCKX")])
    sep = f", {PAUSE} " if pause else " "
    spoken = " ".join(pre) + " dash" + sep + " ".join(SPOKEN[int(c)] for c in digits) + (f" {suffix}" if suffix else "")
    t = rng.choice(["My order ID is {v}.", "The reference is {v}.", "It's {v}.", "Booking ID {v}."])
    return "id", t.format(v=spoken), f"{pre}-{digits}{suffix}"


MAKERS = [phone, email, name, order_id]


def sentences(n=2000, seed=7):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        _, text, _ = rng.choice(MAKERS)(rng)
        out.append(text.replace(PAUSE, "").replace(" ,", ","))
    return out


def build_dev_set(n=120, seed=20261125):
    rng = random.Random(seed)
    out_dir = ROOT / "data/synthetic"
    (out_dir / "audio").mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(n):
        maker = MAKERS[i % len(MAKERS)]
        pause = rng.random() < 0.4
        field, text, value = maker(rng, pause)
        voice = VOICES[i % len(VOICES)]
        path = out_dir / "audio" / f"dev_{i:03d}.wav"
        subprocess.run(["say", "-v", voice, "-r", "175", "--data-format=LEI16@16000", "-o", str(path), text],
                       check=True)
        rows.append({"id": f"dev_{i:03d}", "field": field, "voice": voice, "pause_in_value": pause,
                     "spoken": text.replace(PAUSE, "<pause>"), "gold": value,
                     "audio_path": str(path.relative_to(ROOT))})
    with (out_dir / "dev_manifest.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} clips to {out_dir}")


if __name__ == "__main__":
    build_dev_set(int(sys.argv[1]) if len(sys.argv) > 1 else 120)
