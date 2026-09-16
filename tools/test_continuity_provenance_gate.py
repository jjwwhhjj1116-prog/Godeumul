#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Synthetic tests; no Flow calls and no production asset mutation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from continuity_provenance_gate import validate


class ContinuityGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.ep = Path(self.tmp.name)
        contract = {
            "scene_count": 2,
            "shared_frames": [
                {"n": 1, "file": "images_shared/F001.png", "visible_state": "석재 문턱"},
                {"n": 2, "file": "images_shared/F002.png", "visible_state": "실제 사리기가 드러난 사리공"},
                {"n": 3, "file": "images_shared/F003.png", "visible_state": "금판 공개"},
            ],
            "route": [
                {"n": 1, "era_place": "west tower", "entry": "stone rim", "exit": "cavity", "narration_evidence": "reliquary"},
                {"n": 2, "era_place": "west tower", "entry": "cavity", "exit": "plate", "narration_evidence": "gold plate"},
            ],
            "links": [{"after": 1, "type": "SPATIAL_CONTINUE", "b_anchor": "cavity", "a_anchor": "cavity", "visible_match": "same corner", "narration_motivation": "there beside it"}],
            "graphics": [
                {"n": 1, "kind": "NONE", "owner": "FLOW_VEO", "reason": "enter stone cavity"},
                {"n": 2, "kind": "DISCOVERY_EDGE", "owner": "FLOW_VEO", "anchor": "plate edge", "cue": "gold plate", "action": "line follows real edge"},
            ],
        }
        (self.ep / "02G.연속탐방계약.json").write_text(json.dumps(contract), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_valid_plan_is_only_structural_pass(self) -> None:
        self.assertEqual(validate(self.ep, "plan"), [])

    def test_unmatched_boundary_blocks_plan(self) -> None:
        path = self.ep / "02G.연속탐방계약.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract["links"][0]["a_anchor"] = "different room"
        path.write_text(json.dumps(contract), encoding="utf-8")
        self.assertTrue(any("A 앵커" in item for item in validate(self.ep, "plan")))

    def test_local_preview_blocks_selection(self) -> None:
        selected = {"visuals": [{"n": 1, "source": "videos/001_remotion_preview.mp4"}, {"n": 2, "source": "videos/002.mp4"}]}
        (self.ep / "04Q.선택영상_22컷.json").write_text(json.dumps(selected), encoding="utf-8")
        self.assertTrue(any("LOCAL_GRAPHIC_IN_MASTER" in item for item in validate(self.ep, "selection")))

    def test_missing_shared_frame_blocks_plan(self) -> None:
        path = self.ep / "02G.연속탐방계약.json"
        contract = json.loads(path.read_text(encoding="utf-8"))
        contract["shared_frames"].pop()
        path.write_text(json.dumps(contract), encoding="utf-8")
        self.assertTrue(any("공유 프레임" in item for item in validate(self.ep, "plan")))

    def test_different_next_start_asset_blocks_selection(self) -> None:
        selected = {"visuals": [
            {"n": 1, "source": "videos/001.mp4", "source_kind": "FLOW_VEO_I2V", "flow_result_id": "v1", "a_file": "images_shared/F001.png", "b_file": "images_shared/F002.png", "a_asset_id": "a1", "b_asset_id": "a2", "a_sha256": "aa", "b_sha256": "bb", "video_sha256": "cc"},
            {"n": 2, "source": "videos/002.mp4", "source_kind": "FLOW_VEO_I2V", "flow_result_id": "v2", "a_file": "images_shared/F002.png", "b_file": "images_shared/F003.png", "a_asset_id": "different", "b_asset_id": "a3", "a_sha256": "bb", "b_sha256": "dd", "video_sha256": "ee"},
        ]}
        (self.ep / "04Q.선택영상_22컷.json").write_text(json.dumps(selected), encoding="utf-8")
        self.assertTrue(any("Flow 이미지 자산 ID" in item for item in validate(self.ep, "selection")))


if __name__ == "__main__":
    unittest.main()
