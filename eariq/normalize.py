"""Format-aware hearing: turn spoken forms into the exact written values software needs.

Operates on ASR word tokens and keeps provenance (which ASR words produced each output
token), so every captured value can carry a confidence score from the recogniser.
The rules are general spoken-form conventions (digits, spelled letters, email/URL/code
connectors). They were designed on our synthetic dev set and never tuned on benchmark
test labels.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

DIGIT_WORDS = {
    "zero": "0", "oh": "0", "o": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    # Hindi / Hinglish digit words (Devanagari + unambiguous romanised forms)
    "शून्य": "0", "ज़ीरो": "0", "जीरो": "0", "एक": "1", "दो": "2", "तीन": "3", "चार": "4",
    "पांच": "5", "पाँच": "5", "छह": "6", "छः": "6", "सात": "7", "आठ": "8", "नौ": "9",
    "shunya": "0", "ek": "1", "teen": "3", "chaar": "4", "paanch": "5", "chhe": "6", "saat": "7",
    "aath": "8", "nau": "9",
}
WEAK_DIGITS = {"oh", "o"}  # only digits when next to other digits
TEENS = {"ten": "10", "eleven": "11", "twelve": "12", "thirteen": "13", "fourteen": "14",
         "fifteen": "15", "sixteen": "16", "seventeen": "17", "eighteen": "18", "nineteen": "19"}
TENS = {"twenty": "2", "thirty": "3", "forty": "4", "fifty": "5", "sixty": "6",
        "seventy": "7", "eighty": "8", "ninety": "9"}
REPEAT = {"double": 2, "triple": 3}
CONNECTORS = {"underscore": "_", "dash": "-", "hyphen": "-", "slash": "/", "backslash": "\\",
              "colon": ":", "dot": ".", "equals": "=", "--": "--", "_": "_", "/": "/", "@": "@"}
IN_NUMBER_CONNECTORS = {"dash": "-", "hyphen": "-", "dot": "."}
PHRASES = [  # multi-word spoken forms -> single symbol / marker
    (("at", "the", "rate", "of"), "@"), (("at", "the", "rate"), "@"), (("at", "sign"), "@"),
    (("double", "dash"), "--"), (("double", "hyphen"), "--"), (("forward", "slash"), "/"),
    (("all", "caps"), "<CAPS>"), (("all", "capitals"), "<CAPS>"), (("per", "cent"), "percent"),
]
STOP_BACK = {"is", "the", "a", "an", "to", "at", "and", "or", "my", "your", "in", "on", "of",
             "from", "use", "run", "with", "for", "its", "it's", "was", "be", "as", "this",
             "that", "by", "into", "type", "enter", "then", "it", "me", "please", "number",
             "email", "id", "code", "address"}
TLDS = {"com", "in", "org", "net", "io", "co", "edu", "gov", "ai", "dev", "app", "uk", "us",
        "info", "biz", "me", "xyz", "tech", "health", "ac"}
WORDLIKE = re.compile(r"[\w.@:/+\-=\\]+")
DOMAIN = re.compile(r"^[a-z0-9-]+(\.[a-z0-9-]+)*\.([a-z]{2,24})$")
LOCAL = re.compile(r"^[A-Za-z0-9._%+-]+$")
PUNCT_TAIL = re.compile(r"^(.*?[\wऀ-ॿ%)])([,.!?;:।]+)$")


@dataclass
class Tok:
    text: str
    src: list = field(default_factory=list)
    kind: str = "word"  # word | punct | value
    open: bool = False  # waiting for the next token to glue on (after a connector)

    @property
    def low(self) -> str:
        return self.text.lower()


def _merge(text, toks, kind="value"):
    src = sorted({i for t in toks for i in t.src})
    return Tok(text, src, kind)


def tokenize(words: list[str]) -> list[Tok]:
    out = []
    for i, w in enumerate(words):
        w = w.strip().strip('"“”')
        if not w:
            continue
        m = PUNCT_TAIL.match(w)
        core, tail = (m.group(1), m.group(2)) if m else (w, "")
        kind = "word"
        if re.fullmatch(r"(?:[A-Za-z][-.]){1,}[A-Za-z]\.?", core):  # R-I-N-A / S.R.E.
            core, kind = re.sub(r"[-.]", "", core).upper(), "value"
        if core:
            out.append(Tok(core, [i], kind))
        for p in tail:
            out.append(Tok(p, [i], "punct"))
    return out


def _phrases(toks):
    out, i = [], 0
    while i < len(toks):
        for pat, rep in PHRASES:
            seg = toks[i:i + len(pat)]
            if len(seg) == len(pat) and all(t.low == p for t, p in zip(seg, pat)):
                out.append(_merge(rep, seg, "word"))
                i += len(pat)
                break
        else:
            out.append(toks[i])
            i += 1
    return out


def _as_in(toks):  # "B as in Bravo" -> "B"
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if (_is_letter(t) and i + 3 < len(toks) and toks[i + 1].low == "as"
                and toks[i + 2].low == "in" and toks[i + 3].kind != "punct"):
            out.append(_merge(t.text.upper(), toks[i:i + 4], "word"))
            i += 4
            continue
        out.append(t)
        i += 1
    return out


def _is_letter(t):
    return t.kind != "punct" and len(t.text) == 1 and t.text.isalpha() and t.text.isascii()


def _spelled(toks):
    """Runs of single letters ("R I N A") -> one uppercase token ("RINA")."""
    out, i = [], 0
    while i < len(toks):
        if not _is_letter(toks[i]):
            out.append(toks[i])
            i += 1
            continue
        j, run = i, []
        while j < len(toks) and (_is_letter(toks[j]) or (toks[j].text in {",", "-"} and run
                                 and j + 1 < len(toks) and _is_letter(toks[j + 1]))):
            if _is_letter(toks[j]):
                run.append(toks[j])
            j += 1
        nxt = toks[j] if j < len(toks) else None
        ok = len(run) >= 3
        if len(run) == 2 and all(t.text.isupper() for t in run):
            ok = not (nxt and nxt.kind != "punct" and nxt.text[:1].islower()
                      and nxt.low not in CONNECTORS and nxt.low not in DIGIT_WORDS)
        if ok:
            out.append(_merge("".join(t.text for t in run).upper(), toks[i:j]))
        else:
            out.extend(toks[i:j])
        i = j
    return out


def _digit_item(toks, i):
    """Return (digits, n_tokens, spoken) for a digit item starting at i, else None."""
    t = toks[i]
    low = t.low
    if t.kind == "punct":
        return None
    raw = re.sub(r"[()]", "", t.text)
    if re.fullmatch(r"\d+(?:-\d+)*", raw):
        return raw, 1, False
    if low in REPEAT and i + 1 < len(toks):
        nxt = _digit_item(toks, i + 1)
        if nxt and len(nxt[0]) == 1:
            return nxt[0] * REPEAT[low], 1 + nxt[1], True
    if low in TEENS:
        return TEENS[low], 1, True
    if low in TENS:
        if i + 1 < len(toks) and toks[i + 1].low in DIGIT_WORDS and toks[i + 1].low not in WEAK_DIGITS \
                and toks[i + 1].low != "zero":
            return TENS[low] + DIGIT_WORDS[toks[i + 1].low], 2, 2
        return TENS[low] + "0", 1, True
    if low in DIGIT_WORDS:
        if i + 1 < len(toks) and toks[i + 1].low == "hundred":  # "three hundred twenty four"
            j = i + 2 + (i + 2 < len(toks) and toks[i + 2].low == "and")
            nxt = toks[j].low if j < len(toks) else ""
            if nxt in TENS or nxt in TEENS or (nxt in DIGIT_WORDS and nxt not in WEAK_DIGITS):
                rest = _digit_item(toks, j)
                if rest and len(rest[0]) <= 2:
                    return DIGIT_WORDS[low] + rest[0].zfill(2), j - i + rest[1], 2
            return DIGIT_WORDS[low] + "00", 2, 2
        return DIGIT_WORDS[low], 1, True
    return None


def _digits(toks):
    """Runs of spoken/written digits ("two one two five") -> "2125"."""
    out, i = [], 0
    while i < len(toks):
        item = _digit_item(toks, i)
        plus = toks[i].low == "plus" and i + 1 < len(toks) and _digit_item(toks, i + 1)
        if not item and not plus:
            out.append(toks[i])
            i += 1
            continue
        start, parts, spoken, n_items = i, ["+"] if plus else [], 0, 0
        if plus:
            i += 1
        while i < len(toks):
            item = _digit_item(toks, i)
            if item:
                d, n, sp = item
                if toks[i].low in WEAK_DIGITS and n_items == 0 and not _digit_item_after(toks, i + n):
                    break
                parts.append(d.replace("-", "") if not sp else d)
                spoken += sp
                n_items += 1
                i += n
                continue
            sep = IN_NUMBER_CONNECTORS.get(toks[i].low)
            if (sep or toks[i].text == ",") and n_items and i + 1 < len(toks) and _digit_item(toks, i + 1):
                if sep:
                    parts.append(sep)
                i += 1
                continue
            break
        seg = toks[start:i]
        total = sum(c.isdigit() for p in parts for c in p)
        before = out[-1].low if out else ""
        after = toks[i].low if i < len(toks) else ""
        technical = (before in IN_NUMBER_CONNECTORS or after in IN_NUMBER_CONNECTORS
                     or after in {"percent", "%"})
        convert = (spoken >= 2 or (spoken >= 1 and n_items >= 2) or (n_items >= 2 and total >= 7)
                   or (spoken == 1 and technical) or plus)
        if convert and n_items:
            out.append(_merge("".join(parts), seg))
        else:
            out.extend(seg)
            if not seg:
                out.append(toks[i])
                i += 1
    return out


def _digit_item_after(toks, i):
    return i < len(toks) and _digit_item(toks, i) is not None


def _gluable_back(t):
    if t.kind == "punct" or not WORDLIKE.fullmatch(t.text):
        return False
    return t.kind == "value" or t.open or t.low not in STOP_BACK


def _connectors(toks):
    """Join code/email/URL pieces: "ch underscore 8492 dot json" -> "ch_8492.json"."""
    out = []
    for t in toks:
        sym = CONNECTORS.get(t.low) if t.kind != "punct" else None
        if t.kind == "punct" and t.text in {"_", "/", "@"}:
            sym = t.text
        if sym:
            prev = out[-1] if out else None
            if prev is not None and sym != "--" and _gluable_back(prev) and not (sym == "." and prev.kind == "punct"):
                prev.text += sym
                prev.src = sorted(set(prev.src) | set(t.src))
                prev.kind, prev.open = "value", True
            else:
                out.append(Tok(sym, list(t.src), "value", True))
            continue
        if out and out[-1].open and t.kind != "punct" and WORDLIKE.fullmatch(t.text) and t.text != "<CAPS>":
            prev = out[-1]
            prev.text += t.text
            prev.src = sorted(set(prev.src) | set(t.src))
            prev.open = False
            continue
        if out:
            out[-1].open = False
        out.append(t)
    for t in out:
        t.open = False
    return out


def _caps(toks):
    out, i = [], 0
    while i < len(toks):
        if toks[i].text == "<CAPS>":
            if i + 1 < len(toks):
                nxt = toks[i + 1]
                out.append(_merge(nxt.text.upper(), [toks[i], nxt]))
                i += 2
                continue
            i += 1
            continue
        out.append(toks[i])
        i += 1
    return out


def _email(toks):
    """local "at"/"@" domain -> one lowercase email token."""
    out, i = [], 0
    while i < len(toks):
        t = toks[i]
        if t.low in {"at", "@"} and out and out[-1].kind != "punct" and LOCAL.match(out[-1].text):
            merged = False
            for k in (1, 2, 3):  # allow "be simple.ai" -> "besimple.ai"
                seg = toks[i + 1:i + 1 + k]
                if len(seg) < k or any(x.kind == "punct" for x in seg):
                    break
                dom = "".join(x.text for x in seg).lower()
                m = DOMAIN.match(dom)
                if m and (m.group(2) in TLDS or len(m.group(2)) == 2):
                    locals_ = [out.pop()]
                    # "Sneha Gupta at …" -> snehagupta@…: take one more name-like word after a cue
                    if (out and out[-1].text.isalpha() and out[-1].text[:1].isupper()
                            and locals_[0].text.isalpha() and len(out) >= 2 and out[-2].low in STOP_BACK):
                        locals_.insert(0, out.pop())
                    local = "".join(x.text for x in locals_)
                    out.append(_merge(f"{local}@{dom}".lower(), [*locals_, t, *seg]))
                    i += 1 + k
                    merged = True
                    break
            if merged:
                continue
        out.append(t)
        i += 1
    return out


def _finish(toks):
    out = []
    for t in toks:
        if out and t.low in {"percent", "%"} and re.fullmatch(r"\d+(\.\d+)?", out[-1].text):
            out[-1] = _merge(out[-1].text + "%", [out[-1], t])
            continue
        if (out and re.fullmatch(r"[A-Z]{1,2}", t.text) and re.fullmatch(r"[A-Z0-9]+(-[A-Z0-9]+)+", out[-1].text)
                and out[-1].text[-1].isdigit()):
            out[-1] = _merge(out[-1].text + t.text, [out[-1], t])
            continue
        if t.kind == "value" and re.match(r"(?i)^(https?:/|www\.)", t.text):
            t.text = re.sub(r"(?i)^https?", lambda m: m.group(0).lower(), t.text)
        out.append(t)
    return out


def format_tokens(words: list[str]) -> list[Tok]:
    toks = tokenize(words)
    for step in (_phrases, _as_in, _spelled, _digits, _connectors, _caps, _email, _finish):
        toks = step(toks)
    return toks


def detok(toks: list[Tok]) -> str:
    s = ""
    for t in toks:
        if t.kind == "punct" and s:
            s += t.text
        else:
            s += (" " if s else "") + t.text
    return s


def format_text(text: str) -> str:
    return detok(format_tokens(text.split()))
