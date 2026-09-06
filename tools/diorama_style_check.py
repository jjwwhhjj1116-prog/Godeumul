"""Text-contract lint only; never claims rendered-media QA or submits generation."""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def declaration():
    return json.loads((ROOT / '채널설정.json').read_text(encoding='utf-8-sig'))['시각화']['공통스타일선언']

def style_errors(image, video):
    expected = declaration()
    return [f'{label}: 공통 스타일 선언 누락/변경' for label,text in [('image',image),('video',video)]
            if expected not in text]

def read_blocks(path):
    text = Path(path).read_text(encoding='utf-8-sig').replace('\r\n','\n').strip()
    if not text or '\n\n\n' in text:
        raise ValueError('빈 입력 또는 빈 줄이 2개 이상임')
    blocks = text.split('\n\n')
    if any('\n' in b or not b.isascii() or re.match(r'(?:Scene\s+\d|```|#)', b, re.I) for b in blocks):
        raise ValueError('영문 한 줄 블록/라벨 없음 규칙 위반')
    if len(set(blocks)) != len(blocks):
        raise ValueError('동일 프롬프트 중복')
    return blocks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('images',type=Path)
    parser.add_argument('videos',type=Path)
    parser.add_argument('--expected-count',required=True,type=int)
    args=parser.parse_args()
    try:
        images,videos=read_blocks(args.images),read_blocks(args.videos)
        if args.expected_count < 1 or len(images)!=len(videos) or len(images)!=args.expected_count:
            raise ValueError('승인 컷 수와 이미지/영상 블록 수가 다름')
        errors=[f'{i:03}: {e}' for i,(a,b) in enumerate(zip(images,videos),1) for e in style_errors(a,b)]
        if errors:
            raise ValueError('\n'.join(errors))
    except (ValueError,KeyError,OSError) as exc:
        print(f'FAIL: {exc}')
        return 1
    print(f'PASS: {len(images)} paired prompt blocks; rendered-media QA NOT performed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
