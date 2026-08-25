# Remotion 모션그래픽 마스터

기존 `render_final.py`가 만든 자막·TTS·워터마크 포함 베이스 영상을 입력으로 받아,
장면별 치수선·하중 화살표·분해도·수은층·방어 레이어를 합성한다.

## 입력

- `public/base.mp4`: 기존 파이프라인의 완성본
- `public/fonts/GmarketSansBold.otf`
- `public/fonts/NotoSansKR-VF.ttf`

## 실행

```powershell
npm install
npm run studio
npm run render
```

출력: `render/EP01_motion_master.mp4` (1080×1920, 30fps, H.264 CRF 16)

EP01 타임라인은 TTS 실측 130.544초를 30fps 격자에 맞춘 것이다. 다음 회차는
`src/scene-data.ts`를 해당 회차의 `audio/durations.json`에서 다시 생성해야 한다.
