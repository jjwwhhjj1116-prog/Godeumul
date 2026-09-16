import copy
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
from exploration_motion_gate import CONTRACT, REVIEW, SCENES, FIELDS, digest, validate
from capcut_final_lock import validate_capcut_lock


class ExplorationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ep = Path(self.tmp.name) / 'EP14_test'
        self.ep.mkdir()
        (self.ep / '01.대본.txt').write_text('승인된 대본', encoding='utf-8')
        self.master = self.ep / 'master.mp4'
        self.master.write_bytes(b'test master, not actual media')
        spec = {key: f'observed/planned {key}' for key in FIELDS}
        spec.update(narration='승인된 대본', active_motion_ratio=.9, end_hold_seconds=.5)
        self.scene = dict(n=1, txt=spec['narration'], exploration=spec,
                          vid='Travel through the doorway toward the evidence for 8 seconds.',
                          camera_path=dict(single_axis='DOLLY', speed_profile='CONTINUOUS'),
                          i2v_binding='START_END_FRAME')
        for key, sha, name, data in [('image_file','image_sha256','a.png',b'opening'),
                                    ('end_image_file','end_image_sha256','b.png',b'ending')]:
            (self.ep / name).write_bytes(data)
            self.scene.update({key: name, sha: digest(self.ep / name)})
        self.contract = dict(version=1, script_sha256=digest(self.ep/'01.대본.txt'), scenes={'1': copy.deepcopy(spec)})
        self.save()

    def write(self, name, value):
        (self.ep/name).write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')

    def save(self):
        self.write(SCENES, [self.scene]); self.write(CONTRACT, self.contract)

    def review(self):
        (self.ep/'clip.mp4').write_bytes(b'fixture clip')
        r = {key: 'PASS' for key in ('camera_motion','explanation_action','artifact_form','narration_sync','final_speed_motion')}
        r.update(observed_path='Doorway passes foreground, table grows, rear wall shifts slowly',
                 observed_action='Existing inscription becomes visible', reviewed_at='2026-09-14T10:00:00+09:00',
                 full_clip_playback_reviewed=True, observed_motion_ratio=.9,
                 submitted_start_asset_id='asset-A', submitted_end_asset_id='asset-B',
                 video_file='clip.mp4', video_sha256=digest(self.ep/'clip.mp4'),
                 image_sha256=self.scene['image_sha256'], end_image_sha256=self.scene['end_image_sha256'])
        qa = dict(contract_sha256=digest(self.ep/CONTRACT), scene_manifest_sha256=digest(self.ep/SCENES),
                  master_sha256=digest(self.master), scenes={'1': r})
        self.write(REVIEW, qa)
        return qa

    def test_valid_design_video_and_release(self):
        self.assertEqual(validate(self.ep, 'image'), [])
        self.assertEqual(validate(self.ep), [])
        self.review()
        self.assertEqual(validate(self.ep, 'release', self.master), [])

    def test_image_stage_does_not_require_generated_frames(self):
        (self.ep/'a.png').unlink()
        self.assertEqual(validate(self.ep, 'image'), [])
        self.assertTrue(validate(self.ep, 'video'))

    def test_private_upload_does_not_bypass_missing_contract(self):
        self.write('07.업로드결과.json', {'status':'PASS'})
        (self.ep/CONTRACT).unlink()
        self.assertTrue(validate(self.ep))

    def test_static_prompts_rejected(self):
        for prompt in ['Camera locked off', 'no zoom, no pan', 'exact artifact pixels', 'almost imperceptible']:
            with self.subTest(prompt=prompt):
                self.scene['vid'] = prompt; self.save()
                self.assertTrue(any('STATIC_PROMPT' in x for x in validate(self.ep)))

    def test_locked_camera_and_light_only_review_rejected(self):
        self.scene['camera_path']['single_axis']='LOCKED'; self.save()
        self.assertTrue(any('STATIC_CAMERA' in x for x in validate(self.ep)))
        qa = self.review(); qa['scenes']['1']['camera_motion']='PASS_RAKING_LIGHT'
        self.write(REVIEW, qa)
        self.assertTrue(any('camera_motion' in x for x in validate(self.ep,'release',self.master)))

    def test_same_endpoints_rejected(self):
        self.scene['end_image_file']='a.png'
        self.scene['end_image_sha256']=self.scene['image_sha256']; self.save()
        self.assertTrue(any('IDENTICAL_ENDPOINTS' in x for x in validate(self.ep)))

    def test_repair_cannot_silently_replace_contract(self):
        self.scene['exploration']['visual_action']='Replace process with still life'; self.save()
        self.assertTrue(any('CONTRACT_DRIFT' in x for x in validate(self.ep)))

    def test_tampered_frame_rejected(self):
        (self.ep/'b.png').write_bytes(b'changed')
        self.assertTrue(validate(self.ep))

    def test_master_change_invalidates_review(self):
        self.review(); self.master.write_bytes(b'changed')
        self.assertTrue(any('MASTER_CHANGED' in x for x in validate(self.ep,'release',self.master)))

    def test_missing_full_playback_and_same_submitted_asset_rejected(self):
        qa=self.review(); r=qa['scenes']['1']
        r['full_clip_playback_reviewed']=False
        r['submitted_end_asset_id']=r['submitted_start_asset_id']; self.write(REVIEW,qa)
        self.assertGreaterEqual(len(validate(self.ep,'release',self.master)),2)

    def test_final_lock_cannot_skip_exploration(self):
        self.write('05.캡컷마감잠금.json', {'status':'PASS','editor':'CapCut','video':'master.mp4'})
        report=validate_capcut_lock(self.ep,self.master)
        self.assertFalse(report.passed)
        self.assertTrue(any('EXPLORATION_EVIDENCE_MISSING' in x for x in report.failures))

    def test_legacy_repair_scripts_stop_before_writes(self):
        for script in TOOLS.glob('ep14_repair_*_video.py'):
            with self.subTest(script=script.name):
                result=subprocess.run([sys.executable,str(script)],capture_output=True)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('02E',result.stderr.decode(errors='replace'))

    def test_old_episodes_remain_untouched(self):
        self.assertEqual(validate(Path(self.tmp.name)/'EP13_old'),[])

    def test_extension_batch_preserves_and_checks_both_endpoints(self):
        import build_flow_extension_batch as batcher
        plan=dict(i2v_count=1,t2v_count=0,mapping=[dict(scene=1,generation_mode='I2V_LOCKED')])
        self.write('04.하이브리드생성계획.json',plan)
        self.write('02e.FLOW유물참조잠금.json',dict(artifact_name_ko='artifact',flow_reference={}))
        for name,body in [('flow_i2v_images.txt','Opening image.'),('flow_i2v_videos.txt','Travel for 8 seconds.'),('flow_t2v_videos.txt','')]:
            (self.ep/name).write_text(body,encoding='utf-8')
        with patch.object(batcher,'verify_pack',return_value=plan):
            batch=batcher.build_batch(self.ep)
            self.assertEqual(batch['jobs'][1]['input_end_image'],'b.png')
            self.assertEqual(batcher.verify_batch(self.ep)['jobs'][1]['input_image'],'a.png')
            # Even if somebody refreshes the batch hash, dropping B must fail.
            del batch['jobs'][1]['input_end_image']
            self.write(batcher.BATCH_NAME,batch)
            state=json.loads((self.ep/batcher.STATE_NAME).read_text(encoding='utf-8'))
            state['source_batch_sha256']=digest(self.ep/batcher.BATCH_NAME).upper()
            self.write(batcher.STATE_NAME,state)
            with self.assertRaisesRegex(ValueError,'A/B'):
                batcher.verify_batch(self.ep)

    def test_prompt_cli_checks_before_old_release_exemption(self):
        self.write('07.업로드결과.json', {'status':'PASS'})
        (self.ep/CONTRACT).unlink()
        result=subprocess.run([sys.executable,str(TOOLS/'prompt_check.py'),str(self.ep)],capture_output=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn(b'EXPLORATION_EVIDENCE_MISSING',result.stderr)


if __name__ == '__main__':
    unittest.main()
