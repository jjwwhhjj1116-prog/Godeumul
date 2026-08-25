# Remotion 감사용 프로토타입 — 배포 사용 금지

이 폴더는 과거 후합성 방식을 재현하고 비교하기 위한 감사용 프로토타입이다.
새 회차와 배포 영상에는 사용하지 않는다. 설명 그래픽은
`02V.VEO_통합3D_설명모션.md`에 따라 Flow/Veo/Omni 영상 안에 직접 생성한다.

`npm run render:prototype`는 과거 모션 언어를 확인하는 6초 미리보기를 만든다.
3D 바람길 튜브와 펄스가 통로의 깊이축을 따라 이동하고 실제 메시 뒤로 가려지며,
원근 카메라가 전진한 뒤 3D 치수선이 나타난다. 저음의 바람 SFX도 함께 렌더한다.

## 입력

- `src/components/IntegratedMotion.tsx`: 흐름 경로·추적 치수 재사용 컴포넌트
- `src/ThreeDMotionPreview.tsx`: Three.js 기반 6초 3D 모션 언어 미리보기
- `public/sfx/wind-bed.wav`: 프리뷰 바람 공간음
- `public/base.mp4`: 구버전 EP01 베이스 영상(있을 때만 레거시 구성에서 사용)
- `public/fonts/GmarketSansBold.otf`
- `public/fonts/NotoSansKR-VF.ttf`

## 실행

```powershell
npm install
npm run studio
npm run render:prototype
```

출력: `render/motion-language-preview.mp4` (1080×1920, 30fps, H.264 CRF 16)

`LegacyEP01Blocked`와 `Legacy3DPrototype` 모두 감사용이다. 배포용으로 렌더하지 않는다.

## 새 모션 원칙

- 바람·흙·물·빛처럼 공간과 반응하는 현상은 I2V `GENERATED_PHYSICS`
- 정확한 흐름선·스캔파·지도 경로는 Veo `VEO_INTEGRATED_3D`
- 문자·치수·증거 배지만 `INFO_OVERLAY`
- 흐름은 발생점→경로→가림→도착 반응을 가진다
- 치수선 양 끝은 화면이 아니라 피사체 좌표를 추적한다
- `WORLD_3D`는 원근 카메라·메시·조명·depth test를 쓰며 SVG/CSS 3D 흉내를 금지한다
- 정확한 글자만 2D이고, 위치는 3D 앵커를 화면에 투영해 정한다
- 큰 헤더·유리 카드·고정 HUD는 금지한다
