# EP04 산싱두이 — Flow 직접 생성 이미지 QA

- 프로젝트: `EP04 산싱두이 청동 가면`
- Flow: https://labs.google/fx/ko/tools/flow/project/ae109fb5-267c-4b4a-ad73-33dfa55b564e
- 생성 방식: Chrome Flow UI, Nano Banana 2, 9:16, x1
- 검수일: 2026-08-27
- 원칙: 확장 프로그램 산출물은 채택하지 않으며, 아래 직접 생성·수정본만 I2V 시작 이미지로 사용한다.

| 장면 | 채택 Flow 자산/스택 | 검수 결과 |
|---:|---|---|
| 001 | `Sanxingdui bronze mask 3D diorama` | 실물 레퍼런스 기반 넓은 귀·돌출 눈·토층 단면 통과 |
| 002 | `Bronze mask macro 3D diorama` | 돌출 눈 끝–날개형 귀 3/4 매크로 통과 |
| 003 | `Bronze mask 3D diorama scale` | 실물 가면과 작은 점토 인두의 착용 불가 규모 비교 통과 |
| 004 | `Farmer digging up jade object` | 1929년 중국 농부·관개수로·옥 발견 통과 |
| 005 | `Laborers uncovering Sanxingdui…` | 1986년 벽돌공장 작업·두 직사각형 갱·유물군 통과 |
| 006 | `Archaeological 3D diorama of bronze…` | 돌출 눈 정체성·가면 옆면·사각 결합구멍 통과 |
| 007 | `Bronze mask mounting hypothesis…` | 인체·뿔·완성 신전 없이 목재 기둥 장착 가설 통과 |
| 008 | `Sanxingdui archaeological diorama…` 스택 최종본 | 네 증거 구역 분리, 청동대립인 손의 별도 고리 제거 통과 |
| 009 | `Archaeological diorama of Sanxingdui…` | 사람축·신수축·가면/금면축 분리 통과 |
| 010 | `Archaeological diorama of sacrificial…` | 하부 파손 청동–상아–재층 단일 갱 단면 통과 |
| 011 | `Excavating Sanxingdui bronze mask…` 스택 최종 자연 적층본 | 얼굴 없는 청동 역면·10점 이상 상아의 자연스러운 겹침 통과 |
| 012 | 같은 스택의 직전 정돈 적층본 | 청동 역면·반복 호형 적층으로 의도성 질문컷 통과 |
| 013 | `Conservator analyzes soil sample…` | 시료·박편·열변색 없는 갱벽 비교, 가짜 데이터 없음 |
| 014 | `Archaeological diorama showing a…` | 외부 재더미–바구니–파손 유물층, 갱 내부 불길 없음 |
| 015 | `Forensic archaeological 3D diorama` | 파손 유물–재/흙–밀봉토 3층과 불탄 흔적 없는 갱벽 통과 |
| 016 | `Archaeological hypothesis diorama…` | 세 가설 동일 면적·동일 채도, 정답 표시 없음 |
| 017 | `Sanxingdui archaeological evidence…` 스택 최종본 | 유물대/빈 기록대 대비, 숫자·표찰 제거 통과 |
| 018 | `Bronze mask archaeological 3D diorama…` | 실물 레퍼런스 기반 정면 유물, 괴물/외계인화 없음 |
| 019 | `Archaeological diorama showing b…` | 상부 제작 유물군과 하부 파손 매납 상태 분리 통과 |
| 020 | `Conservators holding matching bronze…` | 미결합 파편 간 틈과 미조사 발굴 그리드 통과 |
| 021 | `Archaeological diorama of Sanxingdui…` 최신 엔딩컷 | 현재 유적·발굴구역·정착 흔적·불투명 지하 통과 |

## 폐기/교정 기록

- 장면 001 최초 무참조 생성: 실제 산싱두이 돌출안면 가면이 아닌 작은 웃는 얼굴로 변형되어 폐기.
- 장면 008 최초본: 청동대립인의 손에 별도 고리 생성. 두 차례 수정 후 손가락 사이 빈 공간만 남긴 최종본 채택.
- 장면 011 최초본: 가면 정면이 노출되어 폐기. 역면 주조판을 고정한 뒤 상아를 자연 적층한 최종본 채택.
- 장면 017 최초본: 트레이 숫자 표지가 생겨 폐기. 모든 숫자·표찰을 제거한 수정본 채택.

## I2V 잠금

- `flow_videos_ep04_ui.txt`는 위 채택 이미지 기준으로 재검수·수정한다.
- 시작 이미지에 없는 물체를 카메라 종료점으로 삼지 않는다.
- 얼굴·유물 형상·유물 수량·시대·재질을 변형하지 않는다.
- 장면 011은 스택 최종 자연 적층본, 장면 012는 바로 직전 정돈 적층본을 각각 선택한다.
