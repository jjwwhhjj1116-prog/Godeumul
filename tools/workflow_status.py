"""Read-only resume snapshot, not a production executor or QA approval."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

FILES = {
    "mode": "02d.영상생성모드.json", "script": "01.대본.txt",
    "script_review": "01.문맥검수.json", "audio": "audio/durations.json",
    "contract": "02P.대본화면계약.json", "review": "04Q.대본영상의미검수.json",
    "chain": "02G.연속탐방계약.json", "lock": "05.캡컷마감잠금.json",
    "upload": "07.업로드결과.json",
}
LIMIT = 2 * 1024 * 1024


def read_small(path, text=False):
    if not path.is_file():
        return {"state": "MISSING", "path": str(path)}, None
    try:
        if path.stat().st_size > LIMIT:
            raise ValueError("snapshot size limit exceeded")
        raw = path.read_text(encoding="utf-8-sig")
        data = raw if text else json.loads(raw)
        if not text and not isinstance(data, dict):
            raise ValueError("JSON object required")
        return {"state": "PRESENT_UNVERIFIED", "path": str(path)}, data
    except (OSError, ValueError) as exc:
        return {"state": "READ_ERROR", "path": str(path), "error": str(exc)}, None


def snapshot(episode):
    ep = Path(episode).resolve()
    records, data = {}, {}
    for key, name in FILES.items():
        records[key], data[key] = read_small(ep / name, key == "script")
    mode = data["mode"] or {}
    # Only explicit QA references in this episode's current progress note.
    # Never infer a failure from a globally hard-coded scene number or scan archives.
    refs = re.findall(r"qa/[\w./-]+\.json", str(mode.get("progress_note", "")))
    findings = []
    for name in dict.fromkeys(refs):
        path = (ep / name).resolve()
        if not path.is_relative_to(ep):
            findings.append({"path": name, "status": "INVALID_REFERENCE"})
            continue
        rec, item = read_small(path)
        records[name] = rec
        if item:
            status = str(item.get("status", ""))
            if "FAIL" in status.upper() or item.get("retry_authorized") is False:
                findings.append({"path": str(path), "status": status,
                    "retry_authorized": item.get("retry_authorized"),
                    "retry_authorization_state": item.get("retry_authorization_state"),
                    "video_file": item.get("video_file")})
    bad = next((k for k, r in records.items() if r["state"] == "READ_ERROR"), None)
    missing = next((k for k in FILES if records[k]["state"] == "MISSING"), None)
    if findings:
        action = "현재 명시 QA 실패/재시도 권한을 확인. 후속 생성·편집으로 승격하지 않음."
        blocker = "RECORDED_FAILURE_OR_AUTHORIZATION_PENDING"
    elif bad:
        blocker, action = "UNREADABLE_RECORD", f"{bad} 기록 오류 확인"
    elif missing:
        blocker, action = "MISSING_EVIDENCE", f"{missing} 근거를 확인하고 해당 선행 단계부터 재개"
    else:
        blocker, action = "NOT_VALIDATED", "필요한 --check 실행 및 실제 QA/원격 게시 상태 확인"
    return {"episode": str(ep), "kind": "READ_ONLY_SNAPSHOT", "verified": False,
            "completion": "NOT_ESTABLISHED", "mode": mode.get("mode", "UNDECLARED"),
            "recorded_status": mode.get("status"), "blocker": blocker,
            "next_action": action, "findings": findings, "records": records,
            "checks": "NOT_RUN", "note": "파일 존재·기록상 PASS는 현재 검증 또는 제작 완료가 아님"}


def check_command(episode, check):
    ep = Path(episode).resolve()
    tools = Path(__file__).resolve().parent
    scripts = {"script": ["script_context_gate.py", str(ep / FILES["script"]),
                          "--review", str(ep / FILES["script_review"])],
               "sources": ["semantic_video_gate.py", str(ep)],
               "continuity": ["continuity_provenance_gate.py", str(ep), "--phase", "release"]}
    args = scripts[check]
    return [sys.executable, "-B", "-X", "utf8", str(tools / args[0]), *args[1:]]


def run_check(episode, check):
    command = check_command(episode, check)
    try:
        result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=90, check=False)
        output = result.stdout + result.stderr
        return {"name": check, "status": "PASS" if result.returncode == 0 else "FAIL",
                "exit_code": result.returncode, "command": command,
                "output": output[:6000], "output_truncated": len(output) > 6000,
                "scope": "선택한 기존 게이트만 검증; 실제 영상 QA나 전체 완료를 대체하지 않음"}
    except subprocess.TimeoutExpired:
        return {"name": check, "status": "TIMEOUT", "timeout_seconds": 90, "command": command}
    except OSError as exc:
        return {"name": check, "status": "EXECUTION_ERROR", "error": str(exc), "command": command}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode", type=Path)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--check", choices=("script", "sources", "continuity"))
    args = parser.parse_args()
    report = snapshot(args.episode)
    if args.check:
        report["checks"] = run_check(args.episode, args.check)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"{args.episode.name}: {report['recorded_status'] or report['blocker']}")
        print(f"모드: {report['mode']} | 제작 완료 미확정 | 기본 조회는 검문 미실행")
        print("다음: " + report["next_action"])
        for item in report["findings"]:
            print(f"근거: {item['path']} ({item['status']})")
        if args.check:
            print(f"검문 {args.check}: {report['checks']['status']}")
            print(report["checks"].get("output", ""))
    return 1 if args.check and report["checks"]["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
