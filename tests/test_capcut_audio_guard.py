from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capcut_audio_guard import audit_draft, db_to_linear, sanitize_draft  # noqa: E402


def sample_draft() -> dict:
    return {
        "enhance_voice_segid_list": ["video-segment"],
        "normalize_loudness_segid_list": [],
        "normalize_loudness_audio_denoise_segid_list": [],
        "materials": {
            "videos": [{"id": "video-material", "has_audio": True}],
            "loudnesses": [
                {"id": "video-loudness", "enable": False, "target_loudness": -23.0},
                {"id": "tts-loudness", "enable": True, "target_loudness": -23.0},
            ],
            "vocal_beautifys": [{"id": "beautify", "enable": True}],
            "vocal_separations": [{"id": "separation"}],
            "realtime_denoises": [{"id": "denoise"}],
            "audio_effects": [{"id": "audio-effect"}],
            "material_animations": [
                {"id": "fade", "animations": [{"name": "페이드 인"}]},
                {"id": "zoom", "animations": [{"name": "줌 1"}]},
                {"id": "bounce", "animations": [{"name": "반동 1"}]},
            ],
            "transitions": [{"id": "transition", "name": "왼쪽으로 밀기"}],
        },
        "tracks": [
            {"type": "video", "flag": 0, "segments": [{
                "id": "video-segment", "material_id": "video-material", "volume": 0.0,
                "source_timerange": {"start": 0, "duration": 6_000_000},
                "extra_material_refs": ["video-loudness", "beautify", "zoom", "transition"],
            }]},
            {"type": "audio", "segments": [{
                "id": "audio-segment", "volume": 1.0,
                "source_timerange": {"start": 0, "duration": 6_000_000},
                "extra_material_refs": ["tts-loudness", "separation", "denoise", "audio-effect"],
            }]},
            {"type": "text", "segments": [{"id": "caption", "extra_material_refs": ["fade", "bounce"]}]},
        ],
    }


class CapCutAudioGuardTests(unittest.TestCase):
    def test_audit_rejects_voice_processing_and_wrong_mix(self) -> None:
        report = audit_draft(sample_draft())
        self.assertFalse(report.passed)
        self.assertEqual(report.forbidden_refs["vocal_beautifys"], 1)
        self.assertEqual(report.normalization_mismatches, 1)
        self.assertEqual(report.narration_volume_mismatches, 1)
        self.assertEqual(report.video_volume_mismatches, 1)

    def test_sanitize_keeps_transitions_and_enables_only_normalization(self) -> None:
        original = sample_draft()
        animations = copy.deepcopy(original["materials"]["material_animations"])
        transitions = copy.deepcopy(original["materials"]["transitions"])
        cleaned = sanitize_draft(original)
        report = audit_draft(cleaned)
        self.assertTrue(report.passed, report.as_dict())
        self.assertEqual(cleaned["materials"]["material_animations"], animations)
        self.assertEqual(cleaned["materials"]["transitions"], transitions)
        self.assertIn("transition", cleaned["tracks"][0]["segments"][0]["extra_material_refs"])
        self.assertIn("zoom", cleaned["tracks"][0]["segments"][0]["extra_material_refs"])
        self.assertEqual(cleaned["tracks"][0]["segments"][0]["volume"], db_to_linear(-15.0))
        self.assertEqual(cleaned["tracks"][1]["segments"][0]["volume"], db_to_linear(5.0))
        self.assertTrue(all(item["enable"] for item in cleaned["materials"]["loudnesses"]))

    def test_capcut_dormant_vocal_separation_metadata_is_not_an_active_effect(self) -> None:
        cleaned = sanitize_draft(sample_draft())
        dormant = {
            "id": "dormant-separation", "type": "vocal_separation", "choice": 0,
            "removed_sounds": [], "time_range": None, "production_path": "",
        }
        cleaned["materials"]["vocal_separations"] = [dormant]
        cleaned["tracks"][0]["segments"][0]["extra_material_refs"].append(dormant["id"])
        report = audit_draft(cleaned)
        self.assertTrue(report.passed, report.as_dict())


if __name__ == "__main__":
    unittest.main()
