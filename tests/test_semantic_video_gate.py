from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from semantic_video_gate import sha256_file, validate, validate_contract, validate_draft_sources  # noqa: E402


class SemanticVideoGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name) / "EP18_test"
        (self.ep / "audio").mkdir(parents=True)
        (self.ep / "clips").mkdir()
        (self.ep / "01.대본.txt").write_text("승인 대본", encoding="utf-8")
        (self.ep / "02.시각화.txt").write_text("장면표", encoding="utf-8")
        scenes = {}
        for n in (1, 2):
            name = f"{n:03d}"
            scenes[str(n)] = {"file": f"{name}.mp3", "text": f"나레이션 {n}", "duration": 2.0}
            (self.ep / "audio" / f"{name}.mp3").write_bytes(f"audio{n}".encode())
            (self.ep / "clips" / f"{name}.mp4").write_bytes(f"video{n}".encode())
            (self.ep / f"02v.{name}.txt").write_text(f"shot {n}", encoding="utf-8")
        (self.ep / "audio/durations.json").write_text(
            json.dumps({"scenes": scenes}), encoding="utf-8"
        )
        self.contract = {
            "version": 1,
            "script_sha256": sha256_file(self.ep / "01.대본.txt"),
            "visual_sha256": sha256_file(self.ep / "02.시각화.txt"),
            "scenes": {
                f"{n:03d}": {
                    "narration": f"나레이션 {n}",
                    "must_show": [f"증거 {n}"],
                    "arrival": f"증거 {n} 근접",
                    "prompt": f"02v.{n:03d}.txt",
                    "prompt_sha256": sha256_file(self.ep / f"02v.{n:03d}.txt"),
                } for n in (1, 2)
            },
        }
        self.contract_path = self.ep / "02P.대본화면계약.json"
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.review = {
            "version": 1,
            "contract_sha256": sha256_file(self.contract_path),
            "scenes": {
                f"{n:03d}": {
                    "status": "PASS",
                    "full_clip_playback_reviewed": True,
                    "narration_sync": "PASS",
                    "camera_motion": "PASS",
                    "audio_sha256": sha256_file(self.ep / "audio" / f"{n:03d}.mp3"),
                    "clip_sha256": sha256_file(self.ep / "clips" / f"{n:03d}.mp4"),
                    "evidence_checks": [{
                        "required": f"증거 {n}", "observed": f"증거 {n} 확인",
                        "visible_at_s": 1.0, "status": "PASS",
                    }],
                } for n in (1, 2)
            },
            "boundaries": [{"pair": "001>002", "status": "PASS", "observed": "같은 전시대"}],
        }
        self.review_path = self.ep / "04Q.대본영상의미검수.json"
        self._save_review()

    def _save_review(self) -> None:
        self.review_path.write_text(json.dumps(self.review), encoding="utf-8")

    def test_passes_complete_hash_bound_review(self) -> None:
        self.assertEqual(validate(self.ep), [])

    def _accept_alternative(self):
        alt=self.ep/'clips/repair.mp4';alt.write_bytes(b'reviewed alternative')
        binding={'file':'clips/repair.mp4','sha256':sha256_file(alt),'type':'video',
                 'source_range':{'start':0,'duration':2000000},'selection_approved':True,
                 'authorization_basis':'Explicit test source selection, not playback QA'}
        self.contract['scenes']['001']['accepted_media']=binding
        self.contract_path.write_text(json.dumps(self.contract),encoding='utf8')
        self.review['contract_sha256']=sha256_file(self.contract_path)
        self.review['scenes']['001']['accepted_media']=copy.deepcopy(binding)
        self.review['scenes']['001']['clip_sha256']=sha256_file(alt)
        self._save_review()
        return binding

    def test_explicit_binding_uses_selected_source_and_keeps_reviews_required(self):
        self._accept_alternative()
        self.assertEqual(validate(self.ep),[])
        self.review['scenes']['001']['status']='PENDING';self._save_review()
        self.assertTrue(validate(self.ep))
        self.review['scenes']['001']['status']='PASS'
        self.review['scenes']['001'].pop('accepted_media');self._save_review()
        self.assertTrue(any('바인딩' in e for e in validate(self.ep)))

    def test_explicit_binding_rejects_wrong_episode_stale_and_unapproved(self):
        b=self._accept_alternative()
        for field,value in [('file','../EP17/repair.mp4'),('sha256','stale'),('selection_approved',False)]:
            altered=copy.deepcopy(b);altered[field]=value
            self.contract['scenes']['001']['accepted_media']=altered
            self.contract_path.write_text(json.dumps(self.contract),encoding='utf8')
            self.assertTrue(validate_contract(self.ep),field)

    def test_selected_draft_exact_range_and_legacy_no_substitution(self):
        b=self._accept_alternative()
        draft={'materials':{'videos':[{'id':'a','path':str(self.ep/b['file']),'type':'video'},
                 {'id':'b','path':str(self.ep/'clips/002.mp4'),'type':'video'}]},
               'tracks':[{'type':'video','flag':0,'segments':[
                   {'material_id':'a','source_timerange':copy.deepcopy(b['source_range']),'target_timerange':{'start':0}},
                   {'material_id':'b','target_timerange':{'start':2000000}}]}]}
        self.assertEqual(validate_draft_sources(self.ep,draft),[])
        draft['tracks'][0]['segments'][0]['source_timerange']['start']=1
        self.assertTrue(validate_draft_sources(self.ep,draft))
        self.contract['scenes']['001'].pop('accepted_media')
        self.contract_path.write_text(json.dumps(self.contract),encoding='utf8')
        self.assertTrue(validate_draft_sources(self.ep,draft))

    def test_photo_requires_composite_and_animation_not_veo_camera(self):
        b=self._accept_alternative()
        photo=self.ep/'official.jpg';photo.write_bytes(b'official')
        b.update(file='official.jpg',sha256=sha256_file(photo),type='photo',source_range=None)
        self.contract['scenes']['001']['evidence_assets']=[{'file':'official.jpg','sha256':sha256_file(photo),'role':'actual source'}]
        self.contract_path.write_text(json.dumps(self.contract),encoding='utf8')
        self.review['contract_sha256']=sha256_file(self.contract_path)
        obs=self.review['scenes']['001'];obs.update(accepted_media=copy.deepcopy(b),clip_sha256=sha256_file(photo))
        self._save_review();self.assertTrue(validate(self.ep))
        obs.update(camera_motion='NOT_APPLICABLE_PHOTO',photo_animation='ZOOM1_FULL_DURATION_VERIFIED',composite_playback_reviewed=True,
                   evidence_asset_checks=[{'file':'official.jpg','status':'PASS','observed':'photo legible','visible_at_s':1}])
        self._save_review();self.assertEqual(validate(self.ep),[])

    def test_prebuild_contract_does_not_require_final_render_review(self) -> None:
        self.review_path.unlink()
        self.assertEqual(validate_contract(self.ep), [])
        self.assertTrue(validate(self.ep))

    def test_blocks_missing_or_failed_review(self) -> None:
        self.review_path.unlink()
        self.assertTrue(any("필수 검수 파일 없음" in item for item in validate(self.ep)))
        self._save_review()
        self.review["scenes"]["001"]["status"] = "FAIL"
        self._save_review()
        self.assertTrue(any("001: 전체 재생" in item for item in validate(self.ep)))

    def test_blocks_source_or_contract_drift(self) -> None:
        (self.ep / "clips/001.mp4").write_bytes(b"different")
        self.assertTrue(any("001: clip_sha256" in item for item in validate(self.ep)))
        (self.ep / "clips/001.mp4").write_bytes(b"video1")
        (self.ep / "02v.001.txt").write_text("different prompt", encoding="utf-8")
        self.assertTrue(any("001: 선택 프롬프트" in item for item in validate(self.ep)))

    def test_blocks_missing_evidence_or_boundary(self) -> None:
        self.review["scenes"]["001"]["evidence_checks"] = []
        self.review["boundaries"][0]["status"] = "FAIL"
        self._save_review()
        failures = validate(self.ep)
        self.assertTrue(any("001: 필수 화면 증거" in item for item in failures))
        self.assertTrue(any("경계 001>002" in item for item in failures))

    def test_draft_source_gate_rejects_previous_episode_footage(self) -> None:
        draft = {
            "materials": {"videos": [
                {"id": "clip1", "path": str(self.ep / "clips/001.mp4")},
                {"id": "clip2", "path": str(self.ep / "clips/002.mp4")},
            ]},
            "tracks": [{"type": "video", "flag": 0, "segments": [
                {"material_id": "clip1", "target_timerange": {"start": 0}},
                {"material_id": "clip2", "target_timerange": {"start": 2_000_000}},
            ]}],
        }
        self.assertEqual(validate_draft_sources(self.ep, draft), [])
        draft["materials"]["videos"][1]["path"] = str(self.ep.parent / "EP17" / "002.mp4")
        self.assertTrue(any("002: CapCut 본영상이 승인 컷과 다름" in item
                            for item in validate_draft_sources(self.ep, draft)))

    def test_official_photo_must_be_hash_locked_in_overlay_and_final_review(self) -> None:
        (self.ep / "reference").mkdir()
        photo = self.ep / "reference/official.jpg"
        photo.write_bytes(b"official-photo")
        self.contract["scenes"]["001"]["evidence_assets"] = [{
            "file": "reference/official.jpg", "sha256": sha256_file(photo),
            "role": "실물 농경 음각",
        }]
        self.contract_path.write_text(json.dumps(self.contract), encoding="utf-8")
        self.review["contract_sha256"] = sha256_file(self.contract_path)
        master = self.ep / "corrected.mp4"
        master.write_bytes(b"master")
        self.review["final_master_sha256"] = sha256_file(master)
        self.review["full_master_playback_reviewed"] = True
        self.review["scenes"]["001"]["composite_playback_reviewed"] = True
        self.review["scenes"]["001"]["evidence_asset_checks"] = [{
            "file": "reference/official.jpg", "status": "PASS",
            "observed": "실물 사진 확인", "visible_at_s": 1.2,
        }]
        self._save_review()
        self.assertEqual(validate(self.ep, master), [])

        draft = {
            "materials": {"videos": [
                {"id": "clip1", "path": str(self.ep / "clips/001.mp4")},
                {"id": "clip2", "path": str(self.ep / "clips/002.mp4")},
                {"id": "photo", "path": str(photo)},
            ]},
            "tracks": [
                {"type": "video", "flag": 0, "segments": [
                    {"material_id": "clip1", "target_timerange": {"start": 0}},
                    {"material_id": "clip2", "target_timerange": {"start": 2_000_000}},
                ]},
                {"type": "video", "flag": 1, "segments": [
                    {"material_id": "photo", "target_timerange": {"start": 0}},
                ]},
            ],
        }
        self.assertEqual(validate_draft_sources(self.ep, draft), [])
        draft["tracks"][1]["segments"].clear()
        self.assertTrue(any("공식 사진 증거 레이어 누락" in item
                            for item in validate_draft_sources(self.ep, draft)))
        photo.write_bytes(b"drift")
        self.assertTrue(any("증거 사진 해시 불일치" in item for item in validate_contract(self.ep)))


if __name__ == "__main__":
    unittest.main()
