"""Retired EP18 draft writers are not an alternative production pipeline."""


def block_retired_draft_builder() -> None:
    raise RuntimeError(
        "EP18 진단 드래프트 생성 경로 폐기: 실패 컷·구형 소스·사진 대체를 복제하지 않습니다. "
        "원본 복구와 전체 QA 후 tools/capcut_build.py의 정식 경로를 사용하세요. "
        "기존 파일은 보존되며 새 드래프트를 쓰지 않습니다."
    )
