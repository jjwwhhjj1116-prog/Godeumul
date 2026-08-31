import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "prompt_check.py"
FIXTURE = ROOT / "tests" / "fixtures" / "prompt_check_i2v_locked"


class PromptCameraPolicyTests(unittest.TestCase):
    def run_episode(self, episode: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), str(episode)],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )

    def test_accepts_locked_camera_path_and_miniature_cues(self) -> None:
        result = self.run_episode(FIXTURE)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_new_episode_without_camera_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "EP_TEST"
            shutil.copytree(FIXTURE, episode)
            path = episode / "02a.장면구분.json"
            scenes = json.loads(path.read_text(encoding="utf-8"))
            scenes[0].pop("camera_path")
            path.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            result = self.run_episode(episode)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("카메라 경로", result.stdout)

    def test_accepts_ten_second_generation_with_safe_slow_playback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "EP_TEST"
            shutil.copytree(FIXTURE, episode)
            path = episode / "02a.장면구분.json"
            scenes = json.loads(path.read_text(encoding="utf-8"))
            scenes[0]["tts"] = 11.0
            scenes[0]["omni"] = 10
            scenes[0]["playback_speed"] = round(10 / 11, 4)
            scenes[0]["long_scene_review"] = "One continuous claim in one physical location with timed camera interruptions."
            scenes[0]["tts_beats"][-1]["end"] = 11.0
            scenes[0]["visual_states"] = [
                {"time": 0.0, "composition": "opening", "camera_pose": "wide forward", "visible_anchors": ["outer marker"]},
                {"time": 3.3, "composition": "first travel state", "camera_pose": "wide forward", "visible_anchors": ["route"]},
                {"time": 6.6, "composition": "second travel state", "camera_pose": "wide forward", "visible_anchors": ["ridge"]},
                {"time": 10.0, "composition": "final hold", "camera_pose": "wide settled", "visible_anchors": ["boundary"]},
            ]
            path.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            result = self.run_episode(episode)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_accepts_t2v_only_for_non_identifiable_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "EP_TEST"
            shutil.copytree(FIXTURE, episode)
            path = episode / "02a.장면구분.json"
            scenes = json.loads(path.read_text(encoding="utf-8"))
            scene = scenes[0]
            scene["ct"] = "HISTORICAL_RECONSTRUCTION"
            scene["generation_mode"] = "T2V_CONTEXT"
            scene["artifact_visibility"] = "NONE"
            scene["motion_owner"] = "GENERATED_PHYSICS"
            scene["camera_path"].pop("start_frame_anchor_visible")
            scene["camera_path"].pop("start_frame_anchor_evidence")
            scene["camera_path"]["opening_state_evidence"] = (
                "Period-correct workers cross the documented landscape; no hero artifact is visible."
            )
            scene["vid"] = (
                "Single continuous 8-second T2V text-to-video context shot. "
                "Do not show the named hero artifact in identifiable form. "
                "Start anchor: period-correct workers. Mid anchor: the earth ridge. "
                "Final anchor: the sealed boundary. Last frame: hold there. "
                "Never return to the opening composition. No cut, reset, loop, replay, "
                "teleport or restart. No floating HUD, no text, no hard cut."
            )
            path.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            result = self.run_episode(episode)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rejects_identifiable_artifact_in_t2v(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "EP_TEST"
            shutil.copytree(FIXTURE, episode)
            path = episode / "02a.장면구분.json"
            scenes = json.loads(path.read_text(encoding="utf-8"))
            scenes[0]["ct"] = "HISTORICAL_RECONSTRUCTION"
            scenes[0]["generation_mode"] = "T2V_CONTEXT"
            scenes[0]["artifact_visibility"] = "IDENTIFIABLE"
            scenes[0]["camera_path"].pop("start_frame_anchor_visible")
            scenes[0]["camera_path"].pop("start_frame_anchor_evidence")
            scenes[0]["camera_path"]["opening_state_evidence"] = "hero artifact in full view"
            scenes[0]["vid"] = (
                "Single continuous 8-second T2V text-to-video context shot. "
                "Do not show the named hero artifact in identifiable form. "
                "Start anchor: artifact. Mid anchor: artifact. Final anchor: artifact. "
                "Last frame: hold there. Never return. No cut, reset, loop or restart. "
                "No floating HUD, no text, no hard cut."
            )
            path.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            result = self.run_episode(episode)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("식별 유물 I2V 잠금", result.stdout)

    def test_accepts_identifiable_i2v_with_hashed_form_owner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory) / "EP_TEST"
            shutil.copytree(FIXTURE, episode)
            reference_dir = episode / "references"
            reference_dir.mkdir()
            reference = reference_dir / "artifact.jpg"
            reference.write_bytes(b"immutable-form-owner")
            digest = hashlib.sha256(reference.read_bytes()).hexdigest().upper()
            (episode / "02c.유물레퍼런스.json").write_text(
                json.dumps({"references": [{
                    "id": "FORM_OWNER",
                    "file": "references/artifact.jpg",
                    "sha256": digest,
                }]}),
                encoding="utf-8",
            )
            path = episode / "02a.장면구분.json"
            scenes = json.loads(path.read_text(encoding="utf-8"))
            scene = scenes[0]
            scene["artifact_visibility"] = "IDENTIFIABLE"
            scene["artifact_form_policy"] = "SOURCE_PHOTO_GEOMETRY_LOCK"
            scene["artifact_reference_ids"] = ["FORM_OWNER"]
            scene["allowed_artifact_changes"] = ["camera", "lighting", "focus"]
            scene["forbidden_artifact_changes"] = [
                "silhouette", "proportion", "part_count", "ornament_layout"
            ]
            scene["vid"] += (
                " Preserve the exact supplied reference artifact pixel geometry and silhouette."
                " The artifact remains completely rigid and unchanged. No redesign."
                " No changed part count."
            )
            path.write_text(json.dumps(scenes, ensure_ascii=False), encoding="utf-8")
            result = self.run_episode(episode)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
