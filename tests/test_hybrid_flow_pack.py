import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_hybrid_flow_pack import build_pack  # noqa: E402


class HybridFlowPackTests(unittest.TestCase):
    def test_splits_modes_and_keeps_original_scene_numbers(self) -> None:
        scenes = [
            {"n": 1, "generation_mode": "I2V_LOCKED", "artifact_visibility": "IDENTIFIABLE", "img_v2": "image one", "vid": "video one"},
            {"n": 2, "generation_mode": "T2V_CONTEXT", "artifact_visibility": "NONE", "img_v2": "preview only", "vid": "video two"},
            {"n": 3, "generation_mode": "I2V_LOCKED", "artifact_visibility": "NONE", "img_v2": "image three", "vid": "video three"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            (episode / "02a.장면구분.json").write_text(
                json.dumps(scenes, ensure_ascii=False), encoding="utf-8"
            )
            plan = build_pack(episode)
            self.assertEqual(plan["i2v_count"], 2)
            self.assertEqual(plan["t2v_count"], 1)
            self.assertEqual([row["download_name"] for row in plan["mapping"]], ["001.mp4", "002.mp4", "003.mp4"])
            self.assertEqual((episode / "flow_i2v_images.txt").read_text(encoding="utf-8"), "image one\n\nimage three\n")
            self.assertEqual((episode / "flow_t2v_videos.txt").read_text(encoding="utf-8"), "video two\n")


if __name__ == "__main__":
    unittest.main()
