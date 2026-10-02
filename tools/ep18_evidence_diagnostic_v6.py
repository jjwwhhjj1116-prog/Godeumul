"""Workspace-only evidence crop diagnostic; no image edits, renders, or QA PASS."""
import copy
import json
import shutil
from pathlib import Path
from PIL import Image
from ep18_comparison_evidence_draft import photo_insert, normalized_photo_scale, uid
from ep18_integrated_diagnostic_v4 import EP, probe, sha
from capcut_no_transition_gate import check

SOURCE=EP/'capcut_staging/EP18 농경문 청동기_통합진단_v5'
OUT=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v6'
CROPS={'wide':(.20,.27,.80,.745),'farmer':(.55,.36,.71,.68),
       'jar':(.32,.40,.48,.54),'holes':(.30,.27,.70,.36),
       'fracture':(.24,.48,.73,.74),'leftbird':(.32,.39,.49,.535),
       'rightbird':(.53,.365,.65,.50)}
# Inclusive cue indices within each scene: use the locked cue boundaries exactly.
PLAN=[(1,4,6,'A','farmer'),(2,0,1,'A','farmer'),
      (2,5,5,'B','leftbird'),(2,6,7,'B','rightbird'),
      (4,0,1,'A','wide'),(4,4,5,'A','jar'),
      (5,7,7,'A','holes'),(6,1,4,'A','holes'),
      (9,1,3,'A','fracture'),(10,5,6,'A','farmer'),
      (11,1,2,'A','farmer'),(12,1,1,'B','leftbird'),
      (12,2,3,'B','rightbird'),(13,4,4,'A','farmer'),
      (13,5,6,'A','jar'),(14,0,0,'B','leftbird'),
      (14,1,2,'B','rightbird'),(14,3,4,'A','holes'),
      (15,0,1,'A','wide'),(15,2,2,'B','wide'),
      (18,5,5,'A','fracture'),(20,0,0,'A','fracture')]

def main():
    from diagnostic_draft_guard import block_retired_draft_builder
    block_retired_draft_builder()
    if OUT.exists():raise RuntimeError('Preserve existing v6')
    original=json.loads((SOURCE/'draft_content.json').read_text(encoding='utf-8'))
    d=copy.deepcopy(original)
    cue_file=EP/'자막_싱크.json'
    cues=json.loads(cue_file.read_text(encoding='utf-8'))['cues']
    assert len(cues)==154
    maintrack=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==0)
    assert len(maintrack['segments'])==21
    assert sum(len(t['segments']) for t in d['tracks'] if t['type']=='audio')==21
    mats={m['id']:m for m in d['materials']['videos']}
    segment=maintrack['segments'][12]
    bridge=EP/'video/013_semantic_bridge_pilot_20260930.mp4'
    meta=probe(bridge)
    mat=mats[segment['material_id']]
    mat.update(path=bridge.as_posix(),material_name=bridge.name,duration=round(meta['duration_s']*1e6),width=meta['width'],height=meta['height'])
    segment['source_timerange']={'start':0,'duration':round(meta['duration_s']*1e6)}
    segment['speed']=segment['source_timerange']['duration']/segment['target_timerange']['duration']
    for speed in d['materials']['speeds']:
        if speed['id'] in segment['extra_material_refs']:speed['speed']=segment['speed']
    photo_template=next(m for m in d['materials']['videos'] if m.get('type')=='photo')
    watermark=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==2)
    zoom=next(m for m in d['materials']['material_animations'] if (m.get('animations') or [{}])[0].get('name')=='줌 1')
    overlay=copy.deepcopy(watermark)
    overlay.update(id=uid(),flag=4,segments=[])
    sources={face:EP/f'reference/NMK_agriculture_bronze_side_{face}.jpg' for face in ['A','B']}
    before_hash={face:sha(p) for face,p in sources.items()}
    rows=[]
    for n,first,last,face,detail in PLAN:
        group=[q for q in cues if q['scene']==n]
        selected=group[first:last+1]
        start,end=selected[0]['start'],selected[-1]['end']
        photo=sources[face]
        s=photo_insert(d,photo=photo,start_us=round(start*1e6),duration_us=round((end-start)*1e6),photo_material=photo_template,photo_segment=watermark['segments'][0],zoom_template=zoom,max_width=900,max_height=1000,y=.15,render_index=4)
        pmat=next(m for m in d['materials']['videos'] if m['id']==s['material_id'])
        x0,y0,x1,y1=CROPS[detail]
        pmat['crop']={'upper_left_x':x0,'upper_left_y':y0,'upper_right_x':x1,'upper_right_y':y0,'lower_left_x':x0,'lower_left_y':y1,'lower_right_x':x1,'lower_right_y':y1}
        pmat['crop_ratio']='free'
        pmat['crop_scale']=1.0
        w,h=Image.open(photo).size
        cw,ch=w*(x1-x0),h*(y1-y0)
        scale,rw,rh=normalized_photo_scale(cw,ch,d['canvas_config']['width'],d['canvas_config']['height'],900,1000)
        s['clip']['scale']={'x':scale,'y':scale}
        s['render_index']=100  # Original watermark=1; subtitles=14000.
        s['track_render_index']=4
        overlay['segments'].append(s)
        rows.append({'scene':n,'start_s':start,'end_s':end,'cue_text':[q['text'] for q in selected],'source':str(photo),'sha256':before_hash[face],'crop':CROPS[detail],'detail':detail,'cropped_pixels':[cw,ch],'normalized_scale':scale,'estimated_rendered_pixels':[rw,rh],'render_index':100,'status':'PENDING_GUI_CROP_AND_COMPOSITE_REVIEW'})
    d['tracks'].append(overlay)
    assert check(d)['gate']=='PASS'
    for track in original['tracks']:
        if track['id']!=maintrack['id']:
            assert track==next(t for t in d['tracks'] if t['id']==track['id'])
    oldmain=next(t for t in original['tracks'] if t['id']==maintrack['id'])
    for i,s in enumerate(maintrack['segments']):
        if i!=12:assert s==oldmain['segments'][i]
    for s in overlay['segments']:
        anim=next(m for m in d['materials']['material_animations'] if m['id'] in s['extra_material_refs'])['animations'][0]
        assert anim['name']=='줌 1' and anim['duration']==s['target_timerange']['duration']
    assert before_hash=={face:sha(p) for face,p in sources.items()}
    report={'status':'DIAGNOSTIC_NOT_RELEASE','source_v5_sha256':sha(SOURCE/'draft_content.json'),'cue_sha256':sha(cue_file),'new_photo_segment_count':len(rows),'original_photo_sha256':before_hash,'scene013':{'source':str(bridge),'sha256':sha(bridge),'speed':segment['speed'],'status':'CANDIDATE_FRONT_EVIDENCE_ADDED_NOT_PASS'},'unresolved':['007 failed comparison footage and previous overlays unchanged; unsafe background remains','Crop and render-order calculations require actual CapCut GUI validation','All scene semantics/composite and 20 boundaries require real playback','No full-picture cards replacing moving main footage; partial evidence may not cover wrong underlying artifact'],'render_order_numeric':{'watermark':1,'new_photos':100,'subtitles':14000},'source_tracks_audio_captions_unchanged':True,'transition_count':0,'photo_segments':rows}
    OUT.mkdir(parents=True)
    for name in ('draft_cover.jpg','draft_meta_info.json'):
        if (SOURCE/name).exists():shutil.copy2(SOURCE/name,OUT/name)
    (OUT/'draft_content.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    report['draft_sha256']=sha(OUT/'draft_content.json')
    (OUT/'evidence_crop_diagnostic.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# EP18 v6 사진 근접 진단 — 게시 금지','','007 미해결. 013 후보 연결, 앞면 증거 합성 미검. 원본 JPEG 불변, 새 래스터/MP4 없음.','', '| 컷 | 절대 TTS 구간 | 원본/부위 | 실제 큐 |','|---|---|---|---|']
    lines += [f"| {r['scene']:03d} | {r['start_s']:.3f}–{r['end_s']:.3f} | {Path(r['source']).name} / {r['detail']} | {' '.join(r['cue_text'])} |" for r in rows]
    lines += ['','계산상 워터마크1 < 사진100 < 자막14000. 실제 렌더 우선순위/크롭/줌1 종점은 GUI 검수 필요.','21 TTS·154 자막·나머지 본영상·v5 보존. release PASS 없음.']
    (OUT/'사진근접_구간표_미해결QA.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'output':str(OUT),'photos':len(rows),'schema_checks':'21 videos/21 audio/154 cues; preserved original tracks; full-duration Zoom1; transitions0; source hashes unchanged','release':'NOT_PASS'},ensure_ascii=False))

if __name__=='__main__':main()
