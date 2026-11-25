"""Fast unit tests for the capture layer and failure handling (no speech model needed)."""
import io
import sys
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eariq.capture import capture  # noqa: E402
from eariq.endpointing import DEFAULT_POLICY, simulate_audio, value_in_progress  # noqa: E402
from eariq.normalize import format_text  # noqa: E402
from eariq.vad import speech_segments  # noqa: E402


def W(text, low=()):
    return [{"word": w, "prob": 0.3 if i in low else 0.95} for i, w in enumerate(text.split())]


class Formatting(unittest.TestCase):
    def test_spoken_values(self):
        cases = {
            "four one five dash five five five dash oh one zero one": "415-555-0101",
            "my email is john dot doe at the rate gmail dot com": "my email is john.doe@gmail.com",
            "O R D dash eight nine three dash four four B": "ORD-893-44B",
            "all caps payment underscore gateway underscore key": "PAYMENT_GATEWAY_KEY",
            "three hundred twenty four items": "324 items",
        }
        for spoken, written in cases.items():
            self.assertEqual(format_text(spoken), written)

    def test_ordinary_words_untouched(self):
        self.assertEqual(format_text("I have one question about two or three things."),
                         "I have one question about two or three things.")


class Capture(unittest.TestCase):
    def test_save_valid_phone(self):
        r = capture(W("My number is nine eight seven six five four three two one zero"), "phone")
        self.assertEqual((r["action"], r["display"]), ("save", "98765 43210"))

    def test_never_invents_missing_digit(self):
        r = capture(W("My number is nine eight seven six five four three two one"), "phone")
        self.assertEqual(r["action"], "ask")
        self.assertIn("9 digits", r["question"])

    def test_low_confidence_asks_targeted(self):
        r = capture(W("My number is nine eight seven six five four three two one zero", low=(9,)), "phone")
        self.assertEqual(r["action"], "confirm")

    def test_spelling_overrides_mishearing(self):
        r = capture(W("This is Reena Kell, and the spelling is R-I-N-A-K-E-L-L."), "name")
        self.assertEqual(r["value"], "Rina Kell")

    def test_self_correction_last_wins(self):
        r = capture(W("call me on 98765 43210, no sorry, 98765 43219"), "phone")
        self.assertEqual(r["display"], "98765 43219")

    def test_nothing_heard(self):
        self.assertEqual(capture(W("hello there"), "email")["action"], "ask")


class Listening(unittest.TestCase):
    def test_waits_inside_number(self):
        self.assertTrue(value_in_progress(["my", "number", "is", "98765"], "phone"))
        self.assertFalse(value_in_progress(["my", "number", "is", "9876543210."], "phone"))

    def test_policy_waits_where_timeout_cuts(self):
        pieces = [{"word": "is", "start": 0, "end": 0.4}, {"word": "98765", "start": 0.4, "end": 1.6},
                  {"word": "43210", "start": 2.6, "end": 3.6, "joined": False}]
        pauses = [{"start": 1.6, "end": 2.6, "length": 1.0}]
        self.assertIsNotNone(simulate_audio(pieces, pauses, {"fixed": 0.6}, "phone")[0])
        self.assertIsNone(simulate_audio(pieces, pauses, DEFAULT_POLICY, "phone")[0])

    def test_vad_finds_pause(self):
        sr = 16000
        tone = 0.3 * np.sin(np.linspace(0, 2 * np.pi * 220, sr))
        audio = np.concatenate([tone, np.zeros(sr), tone]).astype(np.float32)
        speech, pauses = speech_segments(audio, sr)
        self.assertEqual(len(speech), 2)
        self.assertAlmostEqual(pauses[0]["length"], 1.0, delta=0.05)


class ApiFailures(unittest.TestCase):
    """Input validation runs before the model, so these need no GPU."""

    @classmethod
    def setUpClass(cls):
        from fastapi.testclient import TestClient
        from app import server
        server.STATE["model_ready"] = True  # validation happens before recognition
        cls.client = TestClient(server.app)

    def post(self, data: bytes):
        return self.client.post("/api/v1/capture", files={"audio": ("a.wav", data)}, data={"field": "phone"})

    def test_empty_audio(self):
        self.assertEqual(self.post(b"").status_code, 400)

    def test_corrupt_audio(self):
        r = self.post(b"not a wav file at all")
        self.assertEqual(r.status_code, 400)
        self.assertIn("Couldn't read", r.json()["message"])

    def test_silence(self):
        buf = io.BytesIO()
        sf.write(buf, np.zeros(16000 * 2, dtype=np.float32), 16000, format="WAV")
        self.assertEqual(self.post(buf.getvalue()).json()["status"], "no_speech")

    def test_too_long(self):
        buf = io.BytesIO()
        sf.write(buf, (0.1 * np.ones(16000 * 70)).astype(np.float32), 16000, format="WAV")
        self.assertEqual(self.post(buf.getvalue()).status_code, 400)


if __name__ == "__main__":
    unittest.main()
