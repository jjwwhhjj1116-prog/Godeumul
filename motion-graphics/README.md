# Remotion 피사체 결합형 모션그래픽

기존 `render_final.py`가 만든 베이스 영상을 입력으로 받아, 장면 속 피사체를 추적하는
흐름·치수·지도 경로·증거 배지를 합성한다. 큰 제목판과 검은 카드가 화면 위에 떠 있는
HUD 방식은 사용하지 않는다.

기본 `npm run render`는 실제 영상에 들어갈 모션 언어를 확인하는 6초 미리보기를 만든다.
바람길 펄스가 통로를 따라 이동하고 전경 기둥 뒤로 가려지며, 마지막에 피사체를 추적하는
최소 치수선이 나타난다.

## 입력

- `src/components/IntegratedMotion.tsx`: 흐름 경로·추적 치수 재사용 컴포넌트
- `src/MotionLanguagePreview.tsx`: 6초 모션 언어 미리보기
- `public/base.mp4`: 구버전 EP01 베이스 영상(있을 때만 레거시 구성에서 사용)
- `public/fonts/GmarketSansBold.otf`
- `public/fonts/NotoSansKR-VF.ttf`

## 실행

```powershell
npm install
npm run studio
npm run render
```

출력: `render/motion-language-preview.mp4` (1080×1920, 30fps, H.264 CRF 16)

`LegacyEP01Blocked` 구성은 폐기된 자동 석궁 대본과 화면 고정 HUD를 보존한 감사용이다.
배포용으로 렌더하지 않는다. 새 회차는 `audio/durations.json`과 장면표의 모션 소유권,
추적 키프레임, 전경 마스크를 사용해 새 구성으로 만든다.

## 새 모션 원칙

- 바람·흙·물·빛처럼 공간과 반응하는 현상은 I2V `GENERATED_PHYSICS`
- 정확한 흐름선·스캔파·지도 경로는 Remotion `TRACKED_COMPOSITE`
- 문자·치수·증거 배지만 `INFO_OVERLAY`
- 흐름은 발생점→경로→가림→도착 반응을 가진다
- 치수선 양 끝은 화면이 아니라 피사체 좌표를 추적한다
- 큰 헤더·유리 카드·고정 HUD는 금지한다
