"""Capture layer: find the value the agent asked for, check it, and decide save / confirm / ask.

Smart double-check: instead of re-asking everything, EarIQ asks only about the part it is
unsure of (low recogniser confidence) or that fails a format check. It never invents
missing information.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from difflib import SequenceMatcher, get_close_matches

from .normalize import TLDS, Tok, detok, format_tokens

FIELDS = {"phone": "phone number", "email": "email", "name": "name", "id": "order / reference ID",
          "any": "details"}
CONFIRM_BELOW = 0.50  # min word confidence inside a value; chosen on the synthetic dev set (<=20% asked)
# Popular providers + reserved example domains: snap near-misses ("gmial.com", "examal.com")
KNOWN_DOMAINS = ["gmail.com", "yahoo.com", "yahoo.co.in", "outlook.com", "hotmail.com", "icloud.com",
                 "rediffmail.com", "protonmail.com", "live.com", "example.com", "example.in",
                 "example.org", "mail.example.com"]

EMAIL = re.compile(r"^[a-z0-9._%+-]+@[a-z0-9-]+(\.[a-z0-9-]+)*\.([a-z]{2,24})$")
URL = re.compile(r"(?i)^(https?://|www\.)\S+$")
NAME_CUE = re.compile(r"(?i)\b(?:my name is|name is|this is|i am|i'm|naam hai|मेरा नाम)\s+"
                      r"((?:[A-Z][a-zA-Z'-]+\s?){1,3})")


@dataclass
class Value:
    type: str
    value: str
    confidence: float
    valid: bool = True
    issue: str = ""
    src: list = field(default_factory=list)
    weak_part: str = ""  # the least-confident piece, for a targeted question


def _conf(src, words):
    probs = [words[i]["prob"] for i in src if i < len(words) and "prob" in words[i]]
    return round(min(probs), 3) if probs else 1.0


def _weak_part(tok: Tok, words) -> str:
    """Text of the least-confident source word, converted to its written form."""
    if not tok.src or not words:
        return ""
    worst = min(tok.src, key=lambda i: words[i].get("prob", 1.0))
    return detok(format_tokens([words[worst]["word"]])).strip(".,")


def classify(text: str) -> str | None:
    t = text.strip(".,")
    if EMAIL.match(t.lower()):
        return "email"
    if URL.match(t):
        return "url"
    digits = re.sub(r"[\s+()-]", "", t)
    if digits.isdigit():
        return "phone" if 10 <= len(digits) <= 13 or (len(digits) >= 7 and t.startswith("+")) else (
            "number" if len(digits) >= 4 else None)
    if re.search(r"\d", t) and re.search(r"[A-Za-z]", t) and len(t) >= 4:
        return "id"
    if re.fullmatch(r"[A-Z]{2,}", t):
        return "spelled"
    return None


def validate(v: Value) -> Value:
    if v.type == "phone":
        d = re.sub(r"\D", "", v.value)
        ok = (len(d) == 10 or (len(d) == 12 and d.startswith("91"))
              or (len(d) == 11 and d[0] in "01") or (len(d) == 13 and d.startswith("091")))
        if not ok:
            v.valid, v.issue = False, f"I got {len(d)} digits; a phone number needs 10"
    elif v.type == "number":
        n = len(re.sub(r"\D", "", v.value))
        if 7 <= n <= 9:  # too long for a short number, too short for a phone number
            v.type, v.valid, v.issue = "phone", False, f"I got {n} digits; a phone number needs 10"
    elif v.type == "email":
        local, _, dom = v.value.partition("@")
        close = get_close_matches(dom, KNOWN_DOMAINS, n=1, cutoff=0.75)
        if close and close[0] != dom:
            v.value, v.issue = f"{local}@{close[0]}", f"corrected domain {dom} -> {close[0]}"
        m = EMAIL.match(v.value)
        if not m or not (m.group(2) in TLDS or len(m.group(2)) == 2):
            v.valid, v.issue = False, "the email ending doesn't look right"
    elif v.type == "id":
        if len(v.value) < 4 or not re.search(r"\d", v.value):
            v.valid, v.issue = False, "that ID looks incomplete"
    return v


def find_values(toks: list[Tok], words: list[dict]) -> list[Value]:
    vals = []
    for t in toks:
        if t.kind == "punct":
            continue
        typ = classify(t.text)
        if typ:
            text = t.text.strip(".,")
            vals.append(validate(Value(typ, text.lower() if typ == "email" else text,
                                       _conf(t.src, words), src=t.src, weak_part=_weak_part(t, words))))
    return vals


def find_name(toks: list[Tok], words: list[dict]) -> Value | None:
    """Name after a cue ("my name is ..."); a spelled-out version overrides what was heard."""
    text = detok(toks)
    m = NAME_CUE.search(text)
    spelling = "spell" in text.lower()
    spelled = []
    if m or spelling:
        for k, t in enumerate(toks):
            if t.kind == "value" and re.fullmatch(r"[A-Z]{3,}", t.text):
                j = k - 1 - (k >= 2 and toks[k - 1].kind == "punct")  # "K, A-R-A-N" -> "KARAN"
                if j >= 0 and len(toks[j].text) == 1 and toks[j].text.isalpha() and spelled[-1:] != [toks[j]]:
                    t = Tok(toks[j].text.upper() + t.text, toks[j].src + t.src, "value")
                spelled.append(t)
    if not m and not spelled:
        return None
    heard = m.group(1).strip() if m else ""
    parts = heard.split()
    name_toks = [t for t in toks if t.text.strip(".,") in parts]
    conf = min([_conf(t.src, words) for t in name_toks] or [1.0])
    if not spelled:
        return Value("name", heard, conf, src=sorted({i for t in name_toks for i in t.src}),
                     weak_part=heard)
    if len(spelled) >= 2 and spelled[-2].src and spelled[-1].src and \
            spelled[-1].src[0] - spelled[-2].src[-1] <= 1:  # "M-E-E-R-A D-A-S": first + last spelled
        value = f"{spelled[-2].text.title()} {spelled[-1].text.title()}"
        src = spelled[-2].src + spelled[-1].src
    else:
        letters, src = spelled[-1].text, spelled[-1].src
        value = _split_spelling(letters, parts)
    return Value("name", value, _conf(src, words), src=src)


def _split_spelling(letters: str, heard: list[str]) -> str:
    """One run of letters for a two-word name: split where it best matches what was heard."""
    if len(heard) < 2:
        return letters.title()
    if len(letters) <= len(heard[0]):  # only the first name was spelled
        return " ".join([letters.title(), *heard[1:]])
    a, b = heard[0].upper(), heard[-1].upper()
    best = max(range(1, len(letters)), key=lambda k: SequenceMatcher(None, letters[:k], a).ratio()
               + SequenceMatcher(None, letters[k:], b).ratio())
    return f"{letters[:best].title()} {letters[best:].title()}"


def group_digits(v: str) -> str:
    d = re.sub(r"\D", "", v)
    if len(d) == 10:
        return f"{d[:5]} {d[5:]}"
    if len(d) == 12 and d.startswith("91"):
        return f"+91 {d[2:7]} {d[7:]}"
    return v


def capture(words: list[dict], field_name: str = "any") -> dict:
    """ASR words (with prob) -> cleaned transcript, values and the next action."""
    toks = format_tokens([w["word"] for w in words])
    values = find_values(toks, words)
    name = find_name(toks, words)
    if name:
        values.append(name)
    want = {"phone": {"phone"}, "email": {"email"}, "name": {"name"},
            "id": {"id", "number"}, "any": None}[field_name]
    cands = [v for v in values if want is None or v.type in want]
    label = FIELDS[field_name]
    result = {"transcript": detok(toks), "field": field_name,
              "values": [asdict(v) for v in values], "value": None, "display": None,
              "confidence": None, "action": "ask", "question": None, "highlight": None}
    if not cands:
        result["question"] = f"Sorry, I didn't catch your {label}. Could you say it again?"
        return result
    best = cands[-1]  # people self-correct ("…no wait, it's …"): the last mention wins
    display = group_digits(best.value) if best.type == "phone" else best.value
    result.update(value=best.value, display=display, confidence=best.confidence, type=best.type)
    if not best.valid:
        result.update(action="ask", question=f"Sorry, {best.issue}. Could you repeat your {label}?")
    elif best.confidence < CONFIRM_BELOW:
        part = best.weak_part or display
        unsure = f" I wasn't sure about the \"{part}\"." if part and part != display else ""
        result.update(action="confirm", highlight=part or display,
                      question=f"Just to confirm, is it {display}?{unsure}")
    else:
        result.update(action="save")
    return result


def baseline_capture(text: str, field_name: str = "any") -> dict:
    """What a typical pipeline does: regex on the raw transcript, no checks, always saves."""
    patterns = {"phone": r"\+?\d[\d\s-]{6,}\d", "email": r"[\w.+-]+@[\w-]+\.[\w.]+",
                "id": r"\b(?=[A-Z0-9-]*\d)[A-Z0-9][A-Z0-9-]{3,}\b",
                "name": r"(?i)(?:my name is|this is|i am|i'm)\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)"}
    value = None
    if field_name in patterns:
        found = re.findall(patterns[field_name], text)
        value = found[-1].strip() if found else None
    return {"transcript": text, "field": field_name, "value": value,
            "action": "save" if value else "missed"}
