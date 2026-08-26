---
name: ancient-artifact-capcut-finish
description: Finish and verify 고대유물의 비밀 videos in CapCut while preserving the user's manual transitions and animations. Use for final CapCut polish, audio normalization, 4K export, or release-master locking for this channel.
---

# 고대유물의 비밀 CapCut 최종 마감

## 시작 전

1. `00.제작_시작_워크플로우.md`, `05.캡컷_편집지침.md`, `채널설정.json`을 읽는다.
2. 현재 에피소드와 CapCut 프로젝트 이름이 일치하는지 확인한다.
3. 사용자가 직접 편집 중이면 창을 닫거나 타임라인을 수정하지 않는다. 사용자가 완료했다고
   명시한 뒤에만 이어서 작업한다.
4. 드래프트 세 파일과 기존 내보내기를 먼저 백업한다.

## 편집 보존 규칙

- 사용자가 넣은 전환과 조합 애니메이션을 기준본으로 취급한다.
- 장면 연결이 어색한 경계에만 즐겨찾기 `왼쪽으로 밀기` 또는 `페이크 줌`을 쓴다.
- 이미 있는 `velocity blur`, `페이드 인`, `줌 1`, `반동 1`은 삭제하거나 일괄 교체하지 않는다.
- 별도 Remotion 모션그래픽은 추가하지 않는다. 공간·단면·분해·치수·흐름 그래픽은
  Flow/Veo 영상 자체에서 해결하고 CapCut은 전환과 순간 타격감만 맡는다.

## 오디오

- 모든 영상 원음과 TTS에 CapCut **음량 노멀라이제이션만** 적용한다. 목표 −23 LUFS.
- 음성 보정, 노이즈 제거, 보컬 분리, 오디오 효과는 OFF.
- 영상 원음 −15dB, TTS +5dB.
- `tools/capcut_audio_guard.py <draft_content.json>`가 PASS여야 한다.
- 오디오 교정 전후 `transitions`와 `material_animations`의 ID·이름·개수가 같아야 한다.

## 내보내기와 잠금

1. 전체 재생으로 검은 프레임, 무음, 조기 종료 자막, 누락 클립을 확인한다.
2. 2160×3840, 9:16, H.264 MP4, 30fps로 에피소드 산출물 폴더에 내보낸다.
3. ffprobe로 해상도·코덱·프레임레이트·길이·오디오 스트림을 확인한다.
4. 대표 프레임과 전환 경계를 추출해 화면을 확인한다.
5. `tools/capcut_final_lock.py`를 `--audio-policy-verified`와 실제 GUI 확인 플래그로 실행한다.
6. 최종 보고에는 영상 절대경로, 크기, 길이, 해시 잠금, 썸네일 절대경로를 적는다.
