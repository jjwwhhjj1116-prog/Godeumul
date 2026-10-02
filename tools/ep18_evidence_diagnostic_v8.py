"""Workspace-only layering correction; preserve v7 and all narration processing."""
import copy,json,shutil
from ep18_integrated_diagnostic_v4 import EP

def main():
    from diagnostic_draft_guard import block_retired_draft_builder
    block_retired_draft_builder()
    src=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v7'
    out=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v8'
    if out.exists():raise RuntimeError('Preserve existing v8')
    d=json.loads((src/'draft_content.json').read_text(encoding='utf-8'))
    original=copy.deepcopy(d)
    texts=[t for t in d['tracks'] if t['type']=='text']
    d['tracks']=[t for t in d['tracks'] if t['type']!='text']+texts
    # CapCut displays later visual tracks above earlier ones. Do not rely on render_index alone.
    for index,t in enumerate(d['tracks']):
        if t['type']!='audio':
            for s in t['segments']:s['track_render_index']=index
    loudids={m['id'] for m in d['materials']['loudnesses']}
    removed=[];eligible=[]
    maintrack=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==0)
    for n,s in enumerate(maintrack['segments'],1):
        m=next(m for m in d['materials']['videos'] if m['id']==s['material_id'])
        if s.get('volume')==0 or m.get('has_audio') is False or m.get('type')=='photo':
            eligible.append(n)
            refs=[r for r in s['extra_material_refs'] if r in loudids]
            s['extra_material_refs']=[r for r in s['extra_material_refs'] if r not in loudids]
            removed.extend(refs)
    # Delete only normalization records no longer referenced anywhere.
    used={r for t in d['tracks'] for s in t['segments'] for r in s.get('extra_material_refs',[])}
    d['materials']['loudnesses']=[m for m in d['materials']['loudnesses'] if m['id'] not in removed or m['id'] in used]
    for t in original['tracks']:
        if t['type']=='audio':assert t==next(x for x in d['tracks'] if x['id']==t['id'])
    oldl={m['id']:m for m in original['materials']['loudnesses']}
    for m in d['materials']['loudnesses']:assert m==oldl[m['id']]
    assert all(d['tracks'].index(t)>max(i for i,x in enumerate(d['tracks']) if x['type']=='video') for t in texts)
    out.mkdir()
    (out/'draft_content.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    for name in ['draft_meta_info.json','draft_cover.jpg','draft_cover.png']:
        if (src/name).exists():shutil.copy2(src/name,out/name)
    report={'status':'GUI_VALIDATION_PENDING_NOT_PASS','parent':'v7','cause_evidence':'Root GUI: caption at 19.467 visible without photo; at 6.033 opaque photo masks caption bounds. Layer ordering is a confirmed cause during crop intervals.','text_track_last_above_all_photo_tracks':True,'eligible_muted_or_noaudio_scenes':eligible,'removed_normalization_references':removed,'narration_tracks_and_normalization_unchanged':True,'remaining_warning_count_not_verified':True}
    (out/'v8_layering_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
