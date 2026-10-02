"""Workspace-only CapCut correction after actual v9 export FAIL observations."""
from __future__ import annotations
import argparse,copy,json,shutil,uuid,re
from pathlib import Path
from ep18_integrated_diagnostic_v4 import EP,sha

def uid():return str(uuid.uuid4()).upper()

def prepare():
    src=EP/'qa/20261001_v9_GUI저장보존'
    d=json.loads((src/'draft_content.json').read_text(encoding='utf8'));old=copy.deepcopy(d)
    texttrack=next(t for t in d['tracks'] if t['type']=='text')
    for m in d['materials']['texts']:
        c=json.loads(m['content'])
        for st in c['styles']:st['size']=18
        m.update(content=json.dumps(c,ensure_ascii=False),font_size=18.,line_max_width=.95,force_apply_line_max_width=True)
    main=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==0)
    s=main['segments'][18];s['source_timerange']={'start':0,'duration':6000000}
    s['speed']=6000000/s['target_timerange']['duration']
    for m in d['materials']['speeds']:
        if m['id'] in s['extra_material_refs']:m['speed']=s['speed']
    # Raw frame3.5 has burial model dominant; raw5.3 has ritual model dominant.
    # At corrected rate these now match actual153.25s /155.48s narration.
    materials={m['id']:m for m in d['materials']['videos']}
    photo_track=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag') not in (0,2) and any(abs(x['target_timerange']['start']-156364000)<40000 for x in t.get('segments',[])))
    template=next(x for x in photo_track['segments'] if abs(x['target_timerange']['start']-156364000)<40000)
    new=copy.deepcopy(template);new['id']=uid();new['target_timerange']={'start':148980000,'duration':3157000}
    new['extra_material_refs']=[]
    for ref in template['extra_material_refs']:
        a=next((a for a in d['materials']['material_animations'] if a['id']==ref),None)
        if a:
            ac=copy.deepcopy(a);ac['id']=uid()
            for anim in ac['animations']:anim['start']=0;anim['duration']=3157000
            d['materials']['material_animations'].append(ac);new['extra_material_refs'].append(ac['id'])
    photo_track['segments'].append(new);photo_track['segments'].sort(key=lambda x:x['target_timerange']['start'])
    # Ordinary CapCut source attribution text, not local motion graphics.
    credit=copy.deepcopy(texttrack);credit.update(id=uid(),segments=[],name='공식사진 출처');credit['flag']=1
    base=next(m for m in d['materials']['texts'] if m['id']==texttrack['segments'][0]['material_id'])
    for begin,duration,text in [(47229000,1869000,'괴정동 방패형 청동기\n사진: 국립중앙박물관'),(49098000,9416000,'남성리 방패형 청동기\n사진: 국립중앙박물관')]:
        m=copy.deepcopy(base);m['id']=uid();c=json.loads(m['content']);c['text']=text
        for st in c['styles']:st['size']=10;st['range']=[0,len(text)]
        m.update(content=json.dumps(c,ensure_ascii=False),base_content=text,recognize_text=text,font_size=10.,line_max_width=.95,type='text')
        d['materials']['texts'].append(m)
        sg=copy.deepcopy(texttrack['segments'][0]);sg.update(id=uid(),material_id=m['id'],target_timerange={'start':begin,'duration':duration})
        sg['clip']['transform']={'x':0.,'y':.66};credit['segments'].append(sg)
    d['tracks'].insert(d['tracks'].index(texttrack),credit)
    for i,t in enumerate(d['tracks']):
        if t['type']!='audio':
            for x in t['segments']:x['track_render_index']=i
    assert len(texttrack['segments'])==154
    assert old['materials']['loudnesses']==d['materials']['loudnesses']
    for t in old['tracks']:
        nt=next(x for x in d['tracks'] if x['id']==t['id'])
        if t['type']=='audio':assert nt==t
        if t['type']=='text':assert [x['target_timerange'] for x in nt['segments']]==[x['target_timerange'] for x in t['segments']]
    return src,d,{'status':'ACTUAL_GUI_AND_MASTER_REVIEW_PENDING','parent_sha256':sha(src/'draft_content.json'),'caption_font':18,'caption_width':.95,'narration_caption_count':154,'narration_and_times_unchanged':True,'019_source_range':s['source_timerange'],'019_speed':s['speed'],'019_first_question_official_fracture':new['target_timerange'],'source_media_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');a=p.parse_args()
    if a.build:
        from diagnostic_draft_guard import block_retired_draft_builder
        block_retired_draft_builder()
    src,d,r=prepare();print(json.dumps(r,ensure_ascii=False,indent=2))
    if a.build:
        out=EP/'capcut_staging/EP18 농경문 청동기_교정_v10'
        if out.exists():raise RuntimeError('Preserve existing v10')
        out.mkdir();(out/'draft_content.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
        for name in ['draft_meta_info.json','draft_cover.jpg']:
            if (src/name).is_file():shutil.copy2(src/name,out/name)
        (out/'v10_change_report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(out)
if __name__=='__main__':main()
