"""Read-only gate for the 2026-09-10 no-transition user policy."""
import json
import sys
from pathlib import Path


def check(draft):
    transition_ids = {
        item.get('id') for item in draft.get('materials', {}).get('transitions', [])
        if item.get('id')
    }
    failures = []
    for track in draft.get('tracks', []):
        for segment in track.get('segments', []):
            refs = set(segment.get('extra_material_refs') or [])
            attached = sorted(refs & transition_ids)
            # Inspect explicit transition fields too; unused library assets are harmless.
            explicit = {k: v for k, v in segment.items()
                        if 'transition' in k.lower() and v not in (None, '', [], {}, False, 0)}
            if attached or explicit:
                failures.append({'segment_id': segment.get('id'),
                                 'transition_refs': attached, 'transition_fields': explicit})
    return {'policy': 'ZOOM_1_ONLY_NO_TRANSITIONS',
            'gate': 'FAIL' if failures else 'PASS', 'failures': failures}


if __name__ == '__main__':
    result = check(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig')))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1 if result['failures'] else 0)
