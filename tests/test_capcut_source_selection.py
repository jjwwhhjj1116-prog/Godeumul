from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from capcut_build import select_visual_sources, selected_source_range, validate_frozen_sources
from semantic_video_gate import sha256_file, validate_draft_sources


class SourceSelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name) / "EP18_test"
        (self.ep / "clips").mkdir(parents=True)
        (self.ep / "video").mkdir()
        (self.ep / "audio").mkdir()
        self.old = self.ep / "clips/001.mp4"
        self.old.write_bytes(b"old rejected source")
        self.fixed = self.ep / "video/fixed.mp4"
        self.fixed.write_bytes(b"new reviewed source")
        self.binding = {"file": "video/fixed.mp4", "sha256": sha256_file(self.fixed),
                        "type": "video", "source_range": {"start": 2000000, "duration": 6000000},
                        "selection_approved": True, "authorization_basis": "test selection"}
        self.contract = {"scenes": {"001": {"accepted_media": self.binding}}}
        self.save()
        (self.ep / "audio/durations.json").write_text(json.dumps({"scenes": {
            "1": {"duration": 9.0, "text": "fixed narration"}}}), encoding="utf-8")

    def save(self):
        (self.ep / "02P.대본화면계약.json").write_text(json.dumps(self.contract), encoding="utf-8")

    def select(self):
        return select_visual_sources(self.ep, [{"visual_scene": 1}])

    def test_builder_selects_corrected_file_not_numbered_old_file(self):
        selected = self.select()[1]
        self.assertEqual(selected["path"], self.fixed.resolve())
        self.assertEqual(selected["source_range"], self.binding["source_range"])

    def test_selected_trim_is_not_reset_to_zero_or_full_duration(self):
        selected = self.select()[1]
        self.assertEqual(selected_source_range(selected, 8.0), self.binding["source_range"])

    def test_missing_or_stale_corrected_file_does_not_fall_back(self):
        self.fixed.write_bytes(b"unreviewed replacement")
        with self.assertRaisesRegex(ValueError, "해시 불일치"):
            self.select()

    def test_overlong_trim_is_rejected(self):
        selected = self.select()[1]
        with self.assertRaisesRegex(ValueError, "초과"):
            selected_source_range(selected, 7.0)

    def test_no_binding_uses_exact_numbered_source(self):
        self.contract["scenes"]["001"] = {}
        self.save()
        self.assertEqual(self.select()[1]["path"], self.old.resolve())

    def test_replacement_after_selection_blocks_save(self):
        selected = self.select()
        self.fixed.write_bytes(b"changed after precheck")
        self.assertTrue(validate_frozen_sources(selected))

    def test_photo_substitution_is_blocked_by_episode_policy(self):
        (self.ep / "02d.영상생성모드.json").write_text(
            json.dumps({"allow_photo_main_track": False}), encoding="utf-8")
        self.binding.update(type="photo", source_range=None)
        self.contract["scenes"]["001"]["evidence_assets"] = [{"file": "photo.jpg"}]
        self.save()
        with self.assertRaisesRegex(ValueError, "사진 본영상 대체 금지"):
            self.select()

    def test_assembled_draft_source_guard_rejects_old_file(self):
        draft = {"materials": {"videos": [{"id": "v", "path": str(self.old), "type": "video"}]},
                 "tracks": [{"type": "video", "flag": 0, "segments": [
                     {"material_id": "v", "target_timerange": {"start": 0, "duration": 9000000},
                      "source_timerange": self.binding["source_range"]}]}]}
        failures = validate_draft_sources(self.ep, draft, require_evidence_layers=False)
        self.assertTrue(any("승인 컷과 다름" in error for error in failures))
        draft["materials"]["videos"][0]["path"] = str(self.fixed)
        self.assertEqual(validate_draft_sources(self.ep, draft, require_evidence_layers=False), [])


class RetiredDraftBuilderTests(unittest.TestCase):
    def test_all_retired_writers_stop_before_source_reads_or_writes(self):
        cases = [("ep18_integrated_diagnostic_v4", []),
                 ("ep18_evidence_diagnostic_v6", []),
                 ("ep18_evidence_diagnostic_v7", []),
                 ("ep18_evidence_diagnostic_v8", []),
                 ("ep18_evidence_diagnostic_v9", ["--build"]),
                 ("ep18_evidence_diagnostic_v10", ["--build"]),
                 ("ep18_comparison_evidence_draft", [])]
        for name, args in cases:
            with self.subTest(builder=name), patch.object(sys, "argv", [name, *args]):
                module = importlib.import_module(name)
                with patch.object(Path, "read_text", side_effect=AssertionError("should not read old draft")):
                    with self.assertRaisesRegex(RuntimeError, "진단 드래프트 생성 경로 폐기"):
                        module.main()


if __name__ == "__main__":
    unittest.main()
