from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from capcut_build import CAPTION_FADE_DURATION_US, set_caption_fade_in  # noqa: E402


class CapCutCaptionAnimationTests(unittest.TestCase):
    def test_replaces_only_referenced_caption_animation_with_fade_in(self) -> None:
        target = {"id": "target", "animations": [{"name": "하나씩"}]}
        untouched = {"id": "other", "animations": [{"name": "하나씩"}]}
        cloner = SimpleNamespace(out={"material_animations": [target, untouched]})

        set_caption_fade_in(cloner, ["target"])

        self.assertEqual(target["animations"][0]["name"], "페이드 인")
        self.assertEqual(target["animations"][0]["duration"], CAPTION_FADE_DURATION_US)
        self.assertEqual(target["animations"][0]["type"], "in")
        self.assertEqual(untouched["animations"][0]["name"], "하나씩")


if __name__ == "__main__":
    unittest.main()
