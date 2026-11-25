"""Checks for material risks: value corruption, future-label leakage and split overlap."""
import copy
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from prepare_data import text_normalise, audit
from src.listening_data import iter_inputs, iter_supervised

class DataIntegrity(unittest.TestCase):
    def test_identity_bearing_values_survive(self):
        for value in ["001204", "RX-7704132", "A.B+tag@example.com", "0.5 mg", "सार्वजनिक नाम", "--dry-run", "St. John's"]:
            self.assertEqual(text_normalise(value),value)

    def test_transcript_and_timing_gold_never_in_inputs(self):
        forbidden={"reference_nfc","reference_verbatim","entities","words","silence_spans","pause_labels","entity_glosses","canonical_transcript"}
        for split in ["train","validation","test","external_entity_test","external_timing_test"]:
            for row in iter_inputs(split):
                self.assertFalse(forbidden & row.keys(),(split,row["id"]))

    def test_heldout_gold_requires_evaluation_optin(self):
        for split in ["test","external_entity_test","external_timing_test"]:
            with self.assertRaises(ValueError):
                next(iter_supervised(split))

    def test_one_context_condition_only(self):
        row=next(iter_inputs("train",context_level=1))
        self.assertEqual(row["context_level"],1)
        self.assertIn("context_prompt",row)
        self.assertFalse(any(f"l{i}_prompt" in row for i in range(7)))
        with self.assertRaises(ValueError):
            next(iter_inputs("external_entity_test",context_level=5))

    def test_overlap_detection_rejects_corruption(self):
        a={"id":"a","split":"train","speaker_group":"speaker_a","reference_sha256":"text_a","audio_sha256":"audio_a","split_component":"comp_a"}
        b={"id":"b","split":"test","speaker_group":"speaker_b","reference_sha256":"text_b","audio_sha256":"audio_b","split_component":"comp_b"}
        audit([a,b])
        for field in ["speaker_group","reference_sha256","audio_sha256","split_component"]:
            bad=copy.deepcopy(b); bad[field]=a[field]
            with self.assertRaises(AssertionError): audit([a,bad])

if __name__=="__main__": unittest.main()
