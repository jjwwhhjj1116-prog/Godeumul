"""Reviewed settings candidate. Default dry-run; --build writes workspace v9 only.

019 fit-to-width crop retains both model bases. Actual GUI validation pending.
No live files, media, caption times, spoken words or audio policy are changed.
"""
import argparse,copy,json,re,shutil
from pathlib import Path
from ep18_integrated_diagnostic_v4 import EP,sha

def wrap(text):
    words=text.split()
    def count(s):return len(re.findall('[가-힣]',s))
    # Prefer <=2 balanced lines, each at most7 Hangul; never split a word.
    if count(' '.join(words))<=7:return ' '.join(words)
    choices=[]
    for k in range(1,len(words)):
        a,b=' '.join(words[:k]),' '.join(words[k:])
        if max(count(a),count(b))<=7:choices.append((abs(count(a)-count(b)),a+'\n'+b))
    if choices:return min(choices,key=lambda v:v[0])[1]
    lines=[];line=[]
    for w in words:
        if line and count(' '.join(line+[w]))>7:lines.append(' '.join(line));line=[]
        line.append(w)
    if line:lines.append(' '.join(line))
    return '\n'.join(lines)

def prepare():
    src=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v8'
    d=json.loads((src/'draft_content.json').read_text(encoding='utf-8'));old=copy.deepcopy(d)
    main=next(t for t in d['tracks'] if t['type']=='video' and t.get('flag')==0)
    hashes={};changes=[]
    for number,start in [(8,2000000),(19,3000000)]:
        s=main['segments'][number-1];m=next(m for m in d['materials']['videos'] if m['id']==s['material_id'])
        hashes[m['path']]=sha(Path(m['path']))
        end=min(8000000,s['source_timerange']['start']+s['source_timerange']['duration'])
        s['source_timerange']={'start':start,'duration':end-start}
        s['speed']=(end-start)/s['target_timerange']['duration']
        for speed in d['materials']['speeds']:
            if speed['id'] in s['extra_material_refs']:speed['speed']=s['speed']
        if number==19:
            m['crop']={'upper_left_x':0.,'upper_left_y':.22,'upper_right_x':1.,'upper_right_y':.22,'lower_left_x':0.,'lower_left_y':.70,'lower_right_x':1.,'lower_right_y':.70}
            m['crop_ratio']='free';m['crop_scale']=1.
            cw,ch=m['width'],m['height']*.48
            canvas=d['canvas_config'];fit=min(canvas['width']/cw,canvas['height']/ch)
            scale=(canvas['width']/cw)/fit
            s['clip']['scale']={'x':scale,'y':scale}
            s['clip']['transform']={'x':0.,'y':0.}
        changes.append({'scene':number,'source_range':s['source_timerange'],'speed':s['speed'],'clip':s['clip']})
    captiontrack=next(t for t in d['tracks'] if t['type']=='text');overflow=[]
    for n,s in enumerate(captiontrack['segments'],1):
        m=next(m for m in d['materials']['texts'] if m['id']==s['material_id'])
        c=json.loads(m['content']);before=c['text'];c['text']=wrap(before)
        assert re.sub(r'\s','',before)==re.sub(r'\s','',c['text'])
        for style in c['styles']:style['size']=21;style['range']=[0,len(c['text'])]
        m['content']=json.dumps(c,ensure_ascii=False);m['base_content']=c['text'];m['recognize_text']=c['text'];m['font_size']=21.
        m['words']={'start_time':[],'end_time':[],'text':[]};m['current_words']={'start_time':[],'end_time':[],'text':[]}
        if c['text'].count('\n')>1 or any(len(re.findall('[가-힣]',line))>7 for line in c['text'].splitlines()):overflow.append({'cue':n,'text':c['text'],'reason':'No legal <=2line split without breaking word / >7 Hangul single word'})
    assert len(captiontrack['segments'])==154
    for t in old['tracks']:
        new=next(x for x in d['tracks'] if x['id']==t['id'])
        if t['type']=='audio':assert t==new
        assert [s['target_timerange'] for s in t['segments']]==[s['target_timerange'] for s in new['segments']]
    assert old['materials']['loudnesses']==d['materials']['loudnesses']
    assert hashes=={p:sha(Path(p)) for p in hashes}
    report={'status':'GUI_VALIDATION_PENDING_NOT_PASS','source_v8_sha256':sha(src/'draft_content.json'),'source_hashes':hashes,'changes':changes,'caption_count':154,'caption_overflow_unavoidable':overflow,'caption_text_identity_modulo_whitespace':True,'all_target_ranges_unchanged':True,'audio_policy_unchanged':True,'019_model_preservation':'Fit-to-width retains horizontal field; dark canvas outside crop. Existing caption y=-.442708 stays below central image band. Actual CapCut crop/letterboxing requires GUI review.','019_label_samples':'3to7 sampled crop strip shows foreground labels removed; not whole-frame/full-playback QA','source_media_unchanged':True}
    return src,d,report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--build',action='store_true');args=parser.parse_args()
    if args.build:
        from diagnostic_draft_guard import block_retired_draft_builder
        block_retired_draft_builder()
    src,d,report=prepare()
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if args.build:
        out=EP/'capcut_staging/EP18 농경문 청동기_증거근접진단_v9'
        if out.exists():raise RuntimeError('Preserve existing v9')
        out.mkdir();(out/'draft_content.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
        (out/'v9_framing_caption_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        for name in ['draft_meta_info.json','draft_cover.jpg','draft_cover.png']:
            if (src/name).exists():shutil.copy2(src/name,out/name)
        print(out)
if __name__=='__main__':main()
