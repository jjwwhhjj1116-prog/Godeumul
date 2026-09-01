import json
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_hybrid_flow_pack import build_pack, verify_pack  # noqa: E402


class HybridFlowPackTests(unittest.TestCase):
    @staticmethod
    def write_inputs(episode: Path, scenes: list[dict], routes: dict[str, dict]) -> None:
        (episode / "audio").mkdir()
        (episode / "references").mkdir()
        (episode / "02a.장면구분.json").write_text(
            json.dumps(scenes, ensure_ascii=False), encoding="utf-8"
        )
        (episode / "02d.유물장면라우팅.json").write_text(
            json.dumps({"version": 2, "scenes": routes}, ensure_ascii=False), encoding="utf-8"
        )
        (episode / "audio" / "durations.json").write_text(
            json.dumps({"scenes": {str(row["n"]): {"duration": 4.0} for row in scenes}}),
            encoding="utf-8",
        )
        form_owner = b"official-artifact-photo"
        diorama = b"approved-exact-form-diorama"
        (episode / "references" / "form.jpg").write_bytes(form_owner)
        (episode / "references" / "diorama.png").write_bytes(diorama)
        diorama_hash = hashlib.sha256(diorama).hexdigest().upper()
        (episode / "02c.유물레퍼런스.json").write_text(json.dumps({
            "artifact_name_ko": "백제금동대향로",
            "references": [{"id": "REF", "file": "references/form.jpg"}],
        }, ensure_ascii=False), encoding="utf-8")
        (episode / "02e.FLOW유물참조잠금.json").write_text(json.dumps({
            "version": 1,
            "artifact_name_ko": "백제금동대향로",
            "prompt_anchor": "백제금동대향로",
            "approved_diorama": {
                "file": "references/diorama.png",
                "sha256": diorama_hash,
                "derived_from_reference_ids": ["REF"],
                "shape_identity_review": "PASS",
            },
            "flow_reference": {
                "asset_name": "백제금동대향로",
                "prompt_token": "@백제금동대향로",
                "preferred_binding": "INGREDIENT",
            },
        }, ensure_ascii=False), encoding="utf-8")

    def test_splits_modes_and_keeps_original_scene_numbers(self) -> None:
        scenes = [
            {"n": 1, "ct": "ARTIFACT_MACRO", "generation_mode": "I2V_LOCKED", "artifact_visibility": "IDENTIFIABLE", "img_v2": "image one", "vid": "video one"},
            {"n": 2, "ct": "DISCOVERY_ACTION", "generation_mode": "T2V_CONTEXT", "artifact_visibility": "NONE", "img_v2": "preview only", "vid": "T2V video two. Do not show the named hero artifact in identifiable form."},
            {"n": 3, "ct": "SPATIAL_MAP", "generation_mode": "I2V_LOCKED", "artifact_visibility": "NONE", "img_v2": "image three", "vid": "video three"},
        ]
        routes = {
            "1": {"generation_mode": "I2V_LOCKED", "artifact_visibility": "IDENTIFIABLE", "artifact_reference_ids": ["REF"], "routing_reason": "실물 유물의 전체 형태를 관객이 식별하는 장면"},
            "2": {"generation_mode": "T2V_CONTEXT", "artifact_visibility": "NONE", "artifact_reference_ids": [], "routing_reason": "유물 없이 발견 행동과 시대 맥락만 전달하는 장면"},
            "3": {"generation_mode": "I2V_LOCKED", "artifact_visibility": "NONE", "artifact_reference_ids": [], "routing_reason": "공식 공간 배치를 잠근 시작 프레임이 필요한 장면"},
        }
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            self.write_inputs(episode, scenes, routes)
            plan = build_pack(episode)
            self.assertEqual(plan["i2v_count"], 2)
            self.assertEqual(plan["t2v_count"], 1)
            self.assertEqual([row["download_name"] for row in plan["mapping"]], ["001.mp4", "002.mp4", "003.mp4"])
            generated_images = (episode / "flow_i2v_images.txt").read_text(encoding="utf-8")
            generated_videos = (episode / "flow_i2v_videos.txt").read_text(encoding="utf-8")
            self.assertIn("@백제금동대향로", generated_images)
            self.assertIn("immutable form owner", generated_images)
            self.assertIn("@백제금동대향로", generated_videos)
            self.assertTrue(generated_images.endswith("\n\nimage three\n"))
            self.assertEqual((episode / "flow_t2v_videos.txt").read_text(encoding="utf-8"), "T2V video two. Do not show the named hero artifact in identifiable form.\n")
            self.assertEqual(plan["version"], 3)
            self.assertEqual(plan["gate"], "PASS")
            self.assertEqual(plan["fixed_order"], ["1Q", "2a", "3", "2c", "2e", "2d", "2b/2v", "2G", "4"])
            self.assertIn("02a.장면구분.json", plan["source_hashes"])
            self.assertEqual(verify_pack(episode)["gate"], "PASS")

            scenes[0]["vid"] = "changed after gate"
            (episode / "02a.장면구분.json").write_text(
                json.dumps(scenes, ensure_ascii=False), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "원본 변경"):
                verify_pack(episode)

    def test_rejects_missing_routing_reason(self) -> None:
        scenes = [{"n": 1, "ct": "ARTIFACT_MACRO", "generation_mode": "I2V_LOCKED", "artifact_visibility": "IDENTIFIABLE", "img_v2": "@백제금동대향로 image", "vid": "@백제금동대향로 video"}]
        routes = {"1": {"generation_mode": "I2V_LOCKED", "artifact_visibility": "IDENTIFIABLE", "artifact_reference_ids": ["REF"]}}
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            self.write_inputs(episode, scenes, routes)
            with self.assertRaisesRegex(ValueError, "routing_reason"):
                build_pack(episode)

    def test_rejects_identifiable_t2v(self) -> None:
        scenes = [{"n": 1, "ct": "DISCOVERY_ACTION", "generation_mode": "T2V_CONTEXT", "artifact_visibility": "IDENTIFIABLE", "vid": "T2V. Do not show the named hero artifact in identifiable form."}]
        routes = {"1": {"generation_mode": "T2V_CONTEXT", "artifact_visibility": "IDENTIFIABLE", "artifact_reference_ids": ["REF"], "routing_reason": "식별 유물을 잘못 T2V로 배정한 실패 테스트 장면"}}
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            self.write_inputs(episode, scenes, routes)
            with self.assertRaisesRegex(ValueError, "식별 유물"):
                build_pack(episode)


if __name__ == "__main__":
    unittest.main()
