from __future__ import annotations

import sys
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capcut_build import Cloner, FORBIDDEN_AUDIO_PROCESSING_BUCKETS  # noqa: E402


class CapCutAudioInheritanceTests(unittest.TestCase):
    def test_builder_does_not_clone_template_audio_ai_materials(self) -> None:
        template = {
            "materials": {
                "speeds": [{"id": "speed", "speed": 1.0}],
                "sound_channel_mappings": [{"id": "mapping"}],
                "loudnesses": [{"id": "loudness", "enable": True}],
                "vocal_beautifys": [{"id": "beautify", "enable": True}],
                "vocal_separations": [{"id": "separation"}],
                "realtime_denoises": [{"id": "denoise"}],
                "audio_effects": [{"id": "effect"}],
            }
        }
        segment = {
            "extra_material_refs": [
                "speed", "mapping", "loudness", "beautify", "separation", "denoise", "effect"
            ]
        }
        cloner = Cloner(template)
        refs = cloner.clone_extras(
            segment, exclude_buckets=FORBIDDEN_AUDIO_PROCESSING_BUCKETS
        )
        self.assertEqual(len(refs), 3)
        self.assertEqual(len(cloner.out["speeds"]), 1)
        self.assertEqual(len(cloner.out["sound_channel_mappings"]), 1)
        self.assertEqual(len(cloner.out["loudnesses"]), 1)
        for bucket in FORBIDDEN_AUDIO_PROCESSING_BUCKETS:
            self.assertEqual(cloner.out[bucket], [])


if __name__ == "__main__":
    unittest.main()
