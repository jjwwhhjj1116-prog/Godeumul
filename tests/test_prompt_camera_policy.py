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


if __name__ == "__main__":
    unittest.main()
