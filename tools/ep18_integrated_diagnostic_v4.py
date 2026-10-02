"""Workspace-only diagnostic draft. Never promotes semantic QA or publishes."""
import copy
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EP = ROOT / '산출물/EP18_농경문청동기'
SOURCE = EP / 'capcut_staging/EP18 농경문 청동기_실물증거교정_007_v3'
OUT = EP / 'capcut_staging/EP18 농경문 청동기_통합진단_v4'
FFPROBE = Path('C:/Users/7500F/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe/ffmpeg-8.1.2-full_build/bin/ffprobe.exe')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def probe(p):
    r = subprocess.run([str(FFPROBE), '-v','error','-show_streams','-show_format','-of','json',str(p)], capture_output=True, text=True, check=True)
    d = json.loads(r.stdout)
    v = next(x for x in d['streams'] if x['codec_type']=='video')
    return {'duration_s':float(v.get('duration',d['format']['duration'])), 'width':v['width'],'height':v['height'],'fps':v['r_frame_rate']}

def main():
    from diagnostic_draft_guard import block_retired_draft_builder
    block_retired_draft_builder()
    global SOURCE, OUT
    parser = argparse.ArgumentParser()
    parser.add_argument('--v5', action='store_true', help='Extend preserved v4 with the downloaded 017 candidate only')
    args = parser.parse_args()
    if args.v5:
        SOURCE = EP / 'capcut_staging/EP18 농경문 청동기_통합진단_v4'
        OUT = EP / 'capcut_staging/EP18 농경문 청동기_통합진단_v5'
    if OUT.exists():
        raise RuntimeError('Preserve existing v4: output already exists')
    src = json.loads((SOURCE/'draft_content.json').read_text(encoding='utf-8'))
    d = copy.deepcopy(src)
    contract = json.loads((EP/'02P.대본화면계약.json').read_text(encoding='utf-8'))
    track = next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==0)
    segments = sorted(track['segments'],key=lambda s:s['target_timerange']['start'])
    assert len(segments)==21
    materials = {m['id']:m for m in d['materials']['videos']}
    speeds = {m['id']:m for m in d['materials']['speeds']}
    replacements = {3:'video/003_opposite_faces_v3_20261001.mp4',4:'video/004_farming_actions_v3_20261001.mp4'}
    if args.v5:
        replacements[17]='video/017_labor_harvest_v2_20261001.mp4'
    for n,rel in replacements.items():
        p = EP/rel
        meta = probe(p)
        s = segments[n-1]
        mat = materials[s['material_id']]
        duration_us = round(meta['duration_s']*1e6)
        mat.update(path=p.as_posix(), material_name=p.name, duration=duration_us, width=meta['width'],height=meta['height'])
        s['source_timerange']={'start':0,'duration':duration_us}
        # Keep the existing frame-quantized audio/caption timeline untouched.
        # Use exact retained slot duration, rather than an independently rounded speed.
        s['speed']=duration_us/s['target_timerange']['duration']
        refs=[speeds[k] for k in s['extra_material_refs'] if k in speeds]
        assert len(refs)==1
        refs[0]['speed']=s['speed']
    for t in src['tracks']:
        if t['id']!=track['id']:
            assert t==next(x for x in d['tracks'] if x['id']==t['id'])
    for n,s in enumerate(segments,1):
        if n not in replacements:
            assert s==src['tracks'][src['tracks'].index(next(t for t in src['tracks'] if t['id']==track['id']))]['segments'][n-1]
    from capcut_no_transition_gate import check
    assert check(d)['gate']=='PASS'
    rows=[]
    for n,s in enumerate(segments,1):
        target=contract['scenes'][f'{n:03d}']
        path=Path(materials[s['material_id']]['path'])
        meta=probe(path)
        rows.append({'scene':n,'file':str(path),'sha256':sha(path),'probe':meta,
            'draft_start_s':s['target_timerange']['start']/1e6,
            'draft_end_s':(s['target_timerange']['start']+s['target_timerange']['duration'])/1e6,
            'draft_duration_s':s['target_timerange']['duration']/1e6,
            'tts_duration_s':target['tts_duration_s'],'source_range':s['source_timerange'],'speed':s['speed'],
            'status':'DIAGNOSTIC_FAIL_UNSAFE_BACKGROUND' if n==7 else 'PENDING_FULL_COMPOSITE_PLAYBACK',
            'narration':target['narration'],'must_show':target['must_show'],
            'official_photo_assets':target['evidence_assets'],'exact_tts_cues':target['tts_cues']})
    bridge=EP/'video/013_semantic_bridge_pilot_20260930.mp4'
    report={'status':'DIAGNOSTIC_NOT_RELEASE','source_v3_sha256':sha(SOURCE/'draft_content.json'),
        'only_replaced_scenes':list(replacements),'audio_captions_overlays_unchanged':True,'transition_count':0,
        'scene007':'FAIL: photos remain over original fabricated comparison footage; GUI diagnosis only',
        'scene013_candidate':{'file':str(bridge),'sha256':sha(bridge),'selected':False,'status':'PENDING_NOT_PASS'},
        'timing_note':'Existing frame-quantized slots preserved. Exact TTS cue times listed separately; inspect millisecond slot/cue differences. No TTS edits.',
        'scenes':rows,'boundaries':[{'pair':f'{n:03d}>{n+1:03d}','status':'PENDING_END1S_START1S_PLAYBACK'} for n in range(1,21)]}
    OUT.mkdir(parents=True)
    for name in ('draft_cover.jpg','draft_meta_info.json'):
        p=SOURCE/name
        if p.exists():shutil.copy2(p,OUT/name)
    (OUT/'draft_content.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    report['draft_sha256']=sha(OUT/'draft_content.json')
    (OUT/'diagnostic_review_order.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=[f"# EP18 {'v5' if args.v5 else 'v4'} 진단 재생 순서 — 게시 금지",'', f"교체 후보 연결: {list(replacements)}. 007 FAIL 유지, 013 미채택. 기존 진단본 및 자막/TTS 보존.",'',
        '정확 TTS cue는 audio alignment 절대 시각이다. 아래 드래프트 슬롯은 프레임 양자화되어 약간 다르며 원래 편집 시간축을 보존했다.','']
    for r in rows:
        lines += [f"## {r['scene']:03d} | {r['draft_start_s']:.6f}–{r['draft_end_s']:.6f}초 | {r['speed']:.8f}배",'',f"소스: {r['file']}",f"상태: {r['status']}",'']
        lines += ['- '+x for x in r['must_show']]
        lines += ['', '공식 사진 근접/증거를 맞출 실제 TTS 구절:', '']
        lines += [f"- {q['start_s']:.3f}–{q['end_s']:.3f}초: {q['text']}" for q in r['exact_tts_cues']]
        lines += ['']
    (OUT/'실제재생_증거근접_구간표.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'output':str(OUT),'replacements':[{'scene':n,'speed':segments[n-1]['speed'],'target_us':segments[n-1]['target_timerange']['duration']} for n in replacements],'status':'DIAGNOSTIC_NOT_RELEASE'},ensure_ascii=False))

if __name__=='__main__':main()
