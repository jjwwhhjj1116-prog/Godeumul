import copy
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from capcut_motion_finish import attach, material_name_index, validate_policy  # noqa: E402


def animation(material_id: str, name: str) -> dict:
    return {"id": material_id, "animations": [{"name": name, "start": 0, "duration": 1}]}


def transition(material_id: str, name: str) -> dict:
    return {"id": material_id, "name": name, "duration": 500_000}


class MotionPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = {
            "materials": {
                "material_animations": [
                    animation("zoom-source", "줌 1"),
                    animation("bounce-source", "반동 1"),
                ],
                "transitions": [
                    transition("left-source", "왼쪽으로 밀기"),
                    transition("fake-source", "페이크 줌"),
                ],
            }
        }
        self.document = {
            "materials": copy.deepcopy(self.source["materials"]),
            "tracks": [{
                "type": "video",
                "flag": 0,
                "segments": [
                    {
                        "target_timerange": {"duration": 4_000_000},
                        "extra_material_refs": ["bounce-source", "fake-source"],
                    },
                    {"target_timerange": {"duration": 4_000_000}, "extra_material_refs": []},
                ],
            }],
        }

    def test_zoom_and_left_on_separate_segments_survive(self) -> None:
        result = attach(self.document, self.source, zoom_scenes=[2], left_joins=[1])
        validate_policy(result)
        names = material_name_index(result)
        first_refs = result["tracks"][0]["segments"][0]["extra_material_refs"]
        second_refs = result["tracks"][0]["segments"][1]["extra_material_refs"]
        self.assertEqual([names[ref] for ref in first_refs], ["왼쪽으로 밀기"])
        self.assertEqual([names[ref] for ref in second_refs], ["줌 1"])

    def test_attach_rejects_animation_transition_overlap(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "겹친 장면: 1"):
            attach(self.document, self.source, zoom_scenes=[1], left_joins=[1])

    def test_policy_rejects_disallowed_animation(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "비허용 영상 애니메이션"):
            validate_policy(self.document)


if __name__ == "__main__":
    unittest.main()
