"""Smart listening: decide how long to wait at a pause before treating the turn as finished.

A fixed silence timeout cuts people off while they pause inside a phone number or an email.
EarIQ waits longer when a value is still in progress (entity-aware rules), when the
sentence is grammatically hanging, or when the trained completion model says the speaker
is not done. Decisions only use words heard *before* the pause (causal).
"""
from __future__ import annotations

import pickle
import re
from pathlib import Path

from .normalize import DIGIT_WORDS, REPEAT

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "completion.pkl"
# v2: retrained with real conversational pauses (LiveKit dev half); used when present
MODEL_V2_PATH = MODEL_PATH.with_name("completion_v2.pkl")
CONNECTOR_WORDS = {"plus", "at", "dot", "underscore", "dash", "hyphen", "slash", "colon", "double",
                   "triple", "hundred", "thousand", "@"}
HANGING = {"um", "uh", "umm", "uhh", "hmm", "er", "ah", "and", "or", "but", "so", "because", "the",
           "a", "an", "my", "is", "to", "of", "with", "like", "for", "in", "on", "your", "our",
           "their", "his", "her", "that", "which", "who", "then", "also", "if", "when", "was", "are",
           "और", "या", "लेकिन", "तो", "कि", "का", "की", "के", "को", "में", "से", "पर", "मेरा",
           "मेरी", "मेरे", "जो", "क्योंकि", "अगर"}
FIELD_CUES = [("phone", r"phone|mobile|contact number|call you|callback|फ़ोन|फोन|नंबर|number"),
              ("email", r"e-?mail|ईमेल"),
              ("name", r"\bname\b|spell|नाम"),
              ("id", r"\b(id|code|reference|order|booking|confirmation|pnr|account|policy|member)\b")]
DEFAULT_POLICY = {"short": 0.6, "long": 1.5, "rules": True, "hanging": True, "model": True,
                  "model_threshold": 0.2}  # updated from the dev-half selection in results/endpointing.json

_model = None


def clean(w: str) -> str:
    return re.sub(r"[^\w@'ऀ-ॿ-]", "", w.lower())


def expected_field(prior_messages) -> str | None:
    """What the agent just asked for (from the previous assistant message)."""
    last = next((m.get("content") or "" for m in reversed(prior_messages or [])
                 if m.get("role") == "assistant"), "")
    for name, pat in FIELD_CUES:
        if re.search(pat, last, re.I):
            return name
    return None


def value_in_progress(words: list[str], field: str | None = None) -> bool:
    """True only when a value is provably unfinished (v2). A number at the end of a turn is
    often a complete answer, so a trailing digit alone is not enough (that was v1's mistake)."""
    if not words:
        return False
    last = clean(words[-1])
    if last in CONNECTOR_WORDS:  # "...at", "...dot", "plus", "double" can't end a value
        return True
    if words[-1].rstrip()[-1:] in {"-", "_", "@", "/", ":"}:  # "ORD-" … value continues
        return True
    if field == "id" and last and not any(c.isdigit() for c in last) and words[-1].strip(".,").isupper():
        return True  # "ORD" … an ID needs its digits
    if field == "name" and re.fullmatch(r"[A-Z](?:[-. ]?[A-Z])*", words[-1].strip(".,")):
        return True  # spelling still in progress
    if field == "phone":
        run = 0  # digits in the trailing run of number words / digit tokens
        for w in reversed([clean(x) for x in words[-16:]]):
            if w.isdigit():
                run += len(w)
            elif w in DIGIT_WORDS:
                run += 1
            elif w in REPEAT:
                run += REPEAT[w] - 1
            else:
                break
        return 0 < run < 10
    if field == "email":
        recent = " ".join(clean(w) for w in words[-12:])
        return bool(re.search(r"\bat\b|@", recent)) and not re.search(r"(com|in|org|net|co|io)$", recent)
    return False


def hanging(words: list[str]) -> bool:
    return bool(words) and clean(words[-1]) in HANGING


def load_model():
    global _model
    if _model is None:
        path = MODEL_V2_PATH if MODEL_V2_PATH.exists() else MODEL_PATH
        if path.exists():
            with path.open("rb") as f:
                _model = pickle.load(f)
    return _model


def completion_prob(words: list[str]) -> float:
    m = load_model()
    if m is None or not words:
        return 1.0
    return float(m.predict_proba([prefix_text(words)])[0][1])


def prefix_text(words: list[str]) -> str:
    """Feature text for the completion model: the last few words, without punctuation."""
    return " ".join(clean(w) for w in words[-6:] if clean(w))


def wait_time(words: list[str], policy: dict, field: str | None = None) -> float:
    """Seconds of silence to wait before ending the turn, given words heard so far."""
    if policy.get("fixed") is not None:
        return policy["fixed"]
    incomplete = ((policy.get("rules") and value_in_progress(words, field))
                  or (policy.get("hanging") and hanging(words))
                  or (policy.get("model") and completion_prob(words) < policy.get("model_threshold", 0.5)))
    return policy["long"] if incomplete else policy["short"]


def simulate(words: list[dict], policy: dict, field: str | None = None, min_gap: float = 0.15):
    """Replay a recording: return (cut_index, cut_time) where the policy would end the turn early,
    or (None, None) if it waits through every pause. words: [{word, start, end}]."""
    for k in range(len(words) - 1):
        gap = words[k + 1]["start"] - words[k]["end"]
        if gap >= min_gap and gap > wait_time([w["word"] for w in words[:k + 1]], policy, field):
            return k, words[k]["end"]
    return None, None


def simulate_audio(pieces: list[dict], pauses: list[dict], policy: dict, field: str | None = None):
    """Replay using real audio pauses. Returns (index of last piece heard, pause start) for an
    early stop, or (None, None) if the policy waits through every pause."""
    for p in pauses:
        heard = [w for w in pieces if w["end"] <= p["end"] - 0.05]
        if heard and len(heard) < len(pieces) and p["length"] > wait_time(_written(heard), policy, field):
            return len(heard) - 1, p["start"]
    return None, None


def _written(pieces: list[dict]) -> list[str]:
    """Pieces -> written words ("R", "-I", "-N" -> "R-I-N") using Whisper's word-start flags."""
    out = []
    for w in pieces:
        if out and w.get("joined"):
            out[-1] += w["word"]
        else:
            out.append(w["word"])
    return out
