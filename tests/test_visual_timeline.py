import json
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

from visual_timeline import load_visual_timeline  # noqa: E402


def test_visual_timeline_supports_multiple_visuals_for_one_audio(tmp_path):
    audio = {
        "1": {"duration": 4.0},
        "2": {"duration": 6.0},
    }
    storyboard = [
        {
            "n": 1, "audio_scene": 1, "audio_part": "1/1",
            "timeline_start": 0.0, "timeline_end": 4.0,
            "audio_offset_start": 0.0, "audio_offset_end": 4.0,
        },
        {
            "n": 2, "audio_scene": 2, "audio_part": "1/2",
            "timeline_start": 4.0, "timeline_end": 7.0,
            "audio_offset_start": 0.0, "audio_offset_end": 3.0,
        },
        {
            "n": 3, "audio_scene": 2, "audio_part": "2/2",
            "timeline_start": 7.0, "timeline_end": 10.0,
            "audio_offset_start": 3.0, "audio_offset_end": 6.0,
        },
    ]
    (tmp_path / "02a.장면구분.json").write_text(
        json.dumps(storyboard), encoding="utf-8"
    )

    plan = load_visual_timeline(tmp_path, audio)

    assert [row["visual_scene"] for row in plan] == [1, 2, 3]
    assert [row["audio_scene"] for row in plan] == [1, 2, 2]
    assert [row["duration"] for row in plan] == [4.0, 3.0, 3.0]
    assert plan[-1]["timeline_end"] == 10.0


def test_visual_timeline_rejects_missing_audio_scene(tmp_path):
    audio = {"1": {"duration": 4.0}, "2": {"duration": 6.0}}
    storyboard = [{
        "n": 1, "audio_scene": 1, "audio_part": "1/1",
        "timeline_start": 0.0, "timeline_end": 4.0,
        "audio_offset_start": 0.0, "audio_offset_end": 4.0,
    }]
    (tmp_path / "02a.장면구분.json").write_text(
        json.dumps(storyboard), encoding="utf-8"
    )

    try:
        load_visual_timeline(tmp_path, audio)
    except ValueError as exc:
        assert "TTS 장면 매핑 불일치" in str(exc)
    else:
        raise AssertionError("missing audio-scene mapping must fail")

