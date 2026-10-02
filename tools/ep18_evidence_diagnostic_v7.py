"""Workspace diagnostic only: restore stable captions and exclude fabricated 007."""
import copy, json, os, shutil
from pathlib import Path
from ep18_integrated_diagnostic_v4 import EP, sha
from ep18_comparison_evidence_draft import photo_insert
from capcut_no_transition_gate import check

def main():
    from diagnostic_draft_guard import block_retired_draft_builder
    block_retired_draft_builder()
    source=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v6'
    out=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v7'
    if out.exists(): raise RuntimeError('Preserve existing v7')
    d=json.loads((source/'draft_content.json').read_text(encoding='utf-8'))
    old=copy.deepcopy(d)
    stable=Path(os.environ['LOCALAPPDATA'])/'CapCut/User Data/Projects/com.lveditor.draft/EP18 농경문 청동기_안정자막_20260930/draft_content.json'
    sd=json.loads(stable.read_text(encoding='utf-8'))
    st=next(t for t in sd['tracks'] if t['type']=='text')
    ss=st['segments'][0]
    sm=next(m for m in sd['materials']['texts'] if m['id']==ss['material_id'])
    track=next(t for t in d['tracks'] if t['type']=='text')
    assert len(track['segments'])==154
    for seg in track['segments']:
        mat=next(m for m in d['materials']['texts'] if m['id']==seg['material_id'])
        content=json.loads(mat['content'])
        for style in content['styles']:style['size']=json.loads(sm['content'])['styles'][0]['size']
        mat['content']=json.dumps(content,ensure_ascii=False)
        mat['font_size']=sm['font_size']
        seg['clip']=copy.deepcopy(ss['clip'])
        seg['extra_material_refs']=[]
    maintrack=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==0)
    prev=maintrack['segments'][6]
    oldmat=next(m for m in d['materials']['videos'] if m['id']==prev['material_id'])
    photo=EP/'reference/NMK_agriculture_bronze_side_A.jpg'
    template=next(m for m in d['materials']['videos'] if m.get('type')=='photo')
    zoom=next(m for m in d['materials']['material_animations'] if (m.get('animations') or [{}])[0].get('name')=='줌 1')
    tr=prev['target_timerange']
    new=photo_insert(d,photo=photo,start_us=tr['start'],duration_us=tr['duration'],photo_material=template,photo_segment=prev,zoom_template=zoom,max_width=d['canvas_config']['width'],max_height=d['canvas_config']['height'],y=0,render_index=0)
    new['render_index']=0
    mat=next(m for m in d['materials']['videos'] if m['id']==new['material_id'])
    mat['type']='photo'
    mat['crop']={'upper_left_x':0.,'upper_left_y':0.,'upper_right_x':1.,'upper_right_y':0.,'lower_left_x':0.,'lower_left_y':1.,'lower_right_x':1.,'lower_right_y':1.}
    mat['crop_ratio']='free';mat['crop_scale']=1.
    maintrack['segments'][6]=new
    # Retain the official comparison materials; extend to exact spoken evidence endpoints.
    adjusted=[]
    for t in d['tracks']:
        for s in t['segments']:
            m=next((m for m in d['materials']['videos'] if m['id']==s['material_id']),None)
            if not m or not any(x in m.get('path','') for x in ['NMK_Goejeongdong','NMK_Namsungri']):continue
            r=s['target_timerange'];end=r['start']+r['duration']
            if r['start']<49098000:r['start']=47229000;r['duration']=49098000-47229000
            elif r['start']>=52510000:r['duration']=58514000-r['start']
            for a in d['materials']['material_animations']:
                if a['id'] in s['extra_material_refs']:
                    for an in a['animations']:an['duration']=r['duration']
            adjusted.append({'path':m['path'],'range':r})
    assert len(maintrack['segments'])==21
    assert all(t==next(x for x in d['tracks'] if x['id']==t['id']) for t in old['tracks'] if t['type']=='audio')
    assert check(d)['gate']=='PASS'
    assert [s['target_timerange'] for s in track['segments']]==[s['target_timerange'] for s in next(t for t in old['tracks'] if t['type']=='text')['segments']]
    out.mkdir()
    (out/'draft_content.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ['draft_meta_info.json','draft_cover.jpg','draft_cover.png']:
        if (source/name).exists():shutil.copy2(source/name,out/name)
    report={'status':'DIAGNOSTIC_NOT_QA_PASS','excluded_007':oldmat['path'],'excluded_source_preserved':True,'replacement_photo':str(photo),'photo_sha256':sha(photo),'stable_caption_template':str(stable),'caption_changes':'size23 / y=-.442708 / animation refs removed; render cause not conclusively established','caption_count':154,'audio_count':21,'scene_count':21,'comparison_overlays':adjusted,'pending':['GUI caption rendering','007 original photo readability and timing','all candidate composite playback','20 boundaries'],'007_v4_not_linked':True}
    (out/'v7_diagnostic_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out)
    print('STRUCTURE CHECKS OK; actual visual QA pending')
if __name__=='__main__':main()
