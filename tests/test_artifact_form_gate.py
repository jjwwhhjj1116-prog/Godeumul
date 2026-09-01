import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from artifact_form_gate import validate_artifact_release_gate, validate_reference_lock  # noqa: E402


class ArtifactFormGateTests(unittest.TestCase):
    @staticmethod
    def make_episode(root: Path) -> None:
        (root / "references").mkdir()
        diorama = b"locked-diorama"
        (root / "references" / "diorama.png").write_bytes(diorama)
        digest = hashlib.sha256(diorama).hexdigest().upper()
        (root / "02c.유물레퍼런스.json").write_text(json.dumps({
            "artifact_name_ko": "백제금동대향로",
        }, ensure_ascii=False), encoding="utf-8")
        (root / "02e.FLOW유물참조잠금.json").write_text(json.dumps({
            "version": 1,
            "artifact_name_ko": "백제금동대향로",
            "prompt_anchor": "백제금동대향로",
            "approved_diorama": {
                "file": "references/diorama.png",
                "sha256": digest,
                "derived_from_reference_ids": ["FORM_OWNER"],
                "shape_identity_review": "PASS",
            },
            "flow_reference": {
                "asset_name": "백제금동대향로",
                "prompt_token": "@백제금동대향로",
                "preferred_binding": "INGREDIENT",
            },
        }, ensure_ascii=False), encoding="utf-8")
        (root / "02d.유물장면라우팅.json").write_text(json.dumps({
            "scenes": {
                "1": {"artifact_visibility": "IDENTIFIABLE"},
                "2": {"artifact_visibility": "NONE"},
            }
        }, ensure_ascii=False), encoding="utf-8")
        (root / "04.FLOW참조첨부기록.json").write_text(json.dumps({
            "version": 1,
            "artifact_name_ko": "백제금동대향로",
            "asset_name": "백제금동대향로",
            "diorama_sha256": digest,
            "flow_project_id": "project-id",
            "scenes": {
                "1": {"attached": True, "asset_name": "백제금동대향로", "binding": "INGREDIENT"}
            },
        }, ensure_ascii=False), encoding="utf-8")
        (root / "04.유물형태키프레임검수.json").write_text(json.dumps({
            "overall_status": "ARTIFACT_FORM_PASS",
            "scenes": [{"scene": 1, "status": "PASS"}],
        }, ensure_ascii=False), encoding="utf-8")

    def test_reference_and_release_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            self.make_episode(episode)
            self.assertTrue(validate_reference_lock(episode).passed)
            self.assertTrue(validate_artifact_release_gate(episode).passed)

    def test_missing_actual_attachment_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            self.make_episode(episode)
            binding_path = episode / "04.FLOW참조첨부기록.json"
            binding = json.loads(binding_path.read_text(encoding="utf-8"))
            binding["scenes"]["1"]["attached"] = False
            binding_path.write_text(json.dumps(binding, ensure_ascii=False), encoding="utf-8")
            report = validate_artifact_release_gate(episode)
            self.assertFalse(report.passed)
            self.assertTrue(any("실제 첨부" in failure for failure in report.failures))

    def test_failed_keyframe_qa_blocks_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            episode = Path(directory)
            self.make_episode(episode)
            qa_path = episode / "04.유물형태키프레임검수.json"
            qa = json.loads(qa_path.read_text(encoding="utf-8"))
            qa["overall_status"] = "ARTIFACT_FORM_FAIL"
            qa["scenes"][0]["status"] = "FAIL"
            qa_path.write_text(json.dumps(qa, ensure_ascii=False), encoding="utf-8")
            report = validate_artifact_release_gate(episode)
            self.assertFalse(report.passed)
            self.assertTrue(any("형태 QA" in failure for failure in report.failures))


if __name__ == "__main__":
    unittest.main()
