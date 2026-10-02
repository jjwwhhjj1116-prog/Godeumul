import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from output_frame_chain_gate import validate_output_chain,MODE
from semantic_video_gate import sha256_file
from artifact_form_gate import validate_artifact_release_gate

class OutputChainTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ep=Path(self.tmp.name)/'EP18_test';self.ep.mkdir();(self.ep/'clips').mkdir()
        (self.ep/'01.대본.txt').write_text('test')
        self.mode={'mode':MODE,'scene_count':2,'script_sha256':sha256_file(self.ep/'01.대본.txt')}
        self.c={'mode':MODE,'scene_count':2,'scenes':[],'boundaries':[]}
        for n in [1,2]:
            source=self.file(f'clips/{n:03d}.mp4',b'video'+bytes([n]))
            end=self.file(f'end{n}.png',b'end'+bytes([n]));end.update(source_video_sha256=source['sha256'],last_decoded_frame_verified=True)
            receipt=self.file(f'receipt{n}.json',json.dumps({'flow_result_id':f'id{n}','video_sha256':source['sha256']}).encode())
            self.c['scenes'].append({'n':n,'source':source,'source_type':'video','provenance_kind':'FLOW_T2V' if n==1 else 'FLOW_I2V','flow_result_id':f'id{n}','submission_receipt':receipt,'actual_end':end,'status':'PASS','full_selected_playback_reviewed':True,'observed':'watched'})
        start=dict(self.c['scenes'][0]['actual_end']);start['flow_asset_id']='asset'
        rec=self.file('attach.json',json.dumps({'flow_result_id':'id2','start_asset_id':'asset','start_sha256':start['sha256'],'chip_verified':True}).encode())
        self.c['boundaries']=[{'after':1,'type':'OUTPUT_END_TO_START','uploaded_start':start,'attachment_receipt':rec,'status':'PASS','last_first_second_played':True,'observed':'watched'}]
        (self.ep/'02P.대본화면계약.json').write_text(json.dumps({'scenes':{'001':{},'002':{}}}))
    def file(self,name,data):
        p=self.ep/name;p.write_bytes(data);return {'file':name,'sha256':sha256_file(p)}
    def check(self):return validate_output_chain(self.ep,'release',self.mode,self.c)
    def test_bound_fixture(self):self.assertEqual(self.check(),[])
    def test_pending_blocks(self):
        self.c['boundaries'][0]['status']='PENDING';self.assertTrue(self.check())
    def test_wrong_start_and_stale_source(self):
        self.c['boundaries'][0]['uploaded_start']['sha256']='stale';self.assertTrue(self.check())
    def test_false_photo_continuity_blocks(self):
        self.c['scenes'][0]['source_type']='photo';self.assertTrue(self.check())
    def test_outside_file_blocks(self):
        self.c['scenes'][0]['source']['file']='../other.mp4';self.assertTrue(self.check())
    def test_missing_form_routing_blocks(self):
        self.assertTrue(validate_artifact_release_gate(self.ep).failures)

if __name__=='__main__':unittest.main()
