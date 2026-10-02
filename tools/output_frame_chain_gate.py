"""Strict output-frame chain branch. Recorded proofs never replace actual QA."""
import json
from pathlib import Path
from semantic_video_gate import sha256_file, effective_media

MODE='T2V_OUTPUT_FRAME_CHAIN_LOCKED'

def validate_output_chain(ep, phase, mode, contract):
    errors=[]
    def fail(s): errors.append('OUTPUT_CHAIN: '+s)
    def proof(item,label):
        if not isinstance(item,dict):fail(label+' missing');return None
        name=item.get('file','');p=(ep/str(name)).resolve()
        if not name or Path(name).is_absolute() or not p.is_relative_to(ep) or not p.is_file():fail(label+' path');return None
        if item.get('sha256')!=sha256_file(p):fail(label+' hash')
        return p
    count=mode.get('scene_count')
    if type(count) is not int or count<2:return ['OUTPUT_CHAIN: invalid scene count']
    if contract.get('mode')!=MODE or contract.get('scene_count')!=count:fail('mode/count mismatch')
    if mode.get('script_sha256')!=sha256_file(ep/'01.대본.txt'):fail('mode script hash stale')
    rows=contract.get('scenes',[]);links=contract.get('boundaries',[])
    if not isinstance(rows,list) or [r.get('n') for r in rows if isinstance(r,dict)]!=list(range(1,count+1)):return errors+['OUTPUT_CHAIN: scenes 1..N required']
    if not isinstance(links,list) or [r.get('after') for r in links if isinstance(r,dict)]!=list(range(1,count)):return errors+['OUTPUT_CHAIN: N-1 boundaries required']
    try:targets=json.loads((ep/'02P.대본화면계약.json').read_text(encoding='utf8'))['scenes']
    except (OSError,ValueError,KeyError):return errors+['OUTPUT_CHAIN: semantic source contract missing']
    for r in rows:
        sid=f"{r['n']:03d}";target=targets.get(sid,{})
        path,kind,binding=effective_media(ep,sid,target,errors)
        actual=proof(r.get('source'),sid+' source')
        if actual!=path.resolve():fail(sid+' not selected source')
        if r.get('source_type')!=kind:fail(sid+' type mismatch')
        if binding and r.get('source_range')!=binding.get('source_range'):fail(sid+' range mismatch')
        if kind=='photo':
            if not binding:fail(sid+' photo selection binding missing')
            if r.get('provenance_kind')!='OFFICIAL_PHOTO_EDIT':fail(sid+' photo must not claim Flow')
            if r.get('flow_result_id') or r.get('continuous_capture') is not False:fail(sid+' photo falsely claims camera chain')
        else:
            if r.get('provenance_kind') not in ('FLOW_T2V','FLOW_I2V','FLOW_OMNI_EDIT'):fail(sid+' Flow kind')
            if not str(r.get('flow_result_id','')).strip():fail(sid+' result ID missing')
            receipt=proof(r.get('submission_receipt'),sid+' submission receipt')
            if receipt:
                try:
                    data=json.loads(receipt.read_text(encoding='utf8'))
                    if data.get('flow_result_id')!=r.get('flow_result_id') or data.get('video_sha256')!=r.get('source',{}).get('sha256'):fail(sid+' receipt result/video mismatch')
                except (ValueError,OSError):fail(sid+' receipt malformed')
            end=r.get('actual_end');proof(end,sid+' actual decoded end')
            if not isinstance(end,dict) or end.get('source_video_sha256')!=r.get('source',{}).get('sha256') or end.get('last_decoded_frame_verified') is not True:fail(sid+' end not verified from selected original')
        if phase=='release':
            if r.get('status')!='PASS' or r.get('full_selected_playback_reviewed') is not True or not str(r.get('observed','')).strip():fail(sid+' playback pending')
            if kind=='photo' and (r.get('composite_playback_reviewed') is not True or r.get('zoom1_full_duration_reviewed') is not True):fail(sid+' photo composite/Zoom1 pending')
    for link,left,right in zip(links,rows,rows[1:]):
        label=f"{left['n']}>{right['n']}"
        photo='photo' in (left.get('source_type'),right.get('source_type'))
        if photo:
            if link.get('type')!='APPROVED_PHOTO_EDIT' or link.get('continuous_capture') is not False or not str(link.get('authorization_basis','')).strip():fail(label+' photo edit exception missing/false continuity')
        else:
            if link.get('type')!='OUTPUT_END_TO_START':fail(label+' output/start type')
            end=left.get('actual_end',{});start=link.get('uploaded_start',{})
            proof(start,label+' uploaded start')
            if start.get('file')!=end.get('file') or start.get('sha256')!=end.get('sha256'):fail(label+' actual output end differs from uploaded start')
            if not str(start.get('flow_asset_id','')).strip():fail(label+' uploaded asset missing')
            receipt=proof(link.get('attachment_receipt'),label+' attachment receipt')
            if receipt:
                try:
                    data=json.loads(receipt.read_text(encoding='utf8'))
                    if (data.get('flow_result_id')!=right.get('flow_result_id') or data.get('start_asset_id')!=start.get('flow_asset_id') or data.get('start_sha256')!=start.get('sha256') or data.get('chip_verified') is not True):fail(label+' attachment evidence mismatch')
                except (ValueError,OSError):fail(label+' attachment receipt malformed')
        if phase=='release' and (link.get('status')!='PASS' or link.get('last_first_second_played') is not True or not str(link.get('observed','')).strip()):fail(label+' boundary playback pending')
    return errors
