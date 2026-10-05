from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, call, patch


TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import youtube_upload as uploader  # noqa: E402


class FakeHttpError(Exception):
    def __init__(self, status: int):
        super().__init__(f"HTTP {status}")
        self.resp = types.SimpleNamespace(status=status)


class UploadResumeTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.ep = Path(temporary.name)
        self.video = self.ep / "final_capcut.mp4"
        self.video.write_bytes(b"locked video bytes")
        self.thumb = self.ep / "cover.jpg"
        self.thumb.write_bytes(b"locked cover bytes")
        self.path = self.ep / "youtube.upload.checkpoint.json"
        self.meta = {"제목": "유물의 비밀", "설명": "AI 재현물입니다.", "태그": ["유물"]}
        (self.ep / "06.메타.json").write_text(json.dumps(self.meta), encoding="utf-8")
        self.body = uploader.build_body(self.meta, "private", None)
        self.owner = "channel-owned"
        self.vid = "video-owned"
        self.identity = uploader.upload_identity(self.video, self.body, self.owner)
        self.yt = MagicMock()
        self.yt.channels.return_value.list.return_value.execute.return_value = {
            "items": [{"id": self.owner, "snippet": {"title": "test channel"}}],
        }
        self.remote = {
            "id": self.vid,
            "snippet": {
                **copy.deepcopy(self.body["snippet"]), "channelId": self.owner,
                "thumbnails": {"default": {"url": "https://example.invalid/thumb.jpg"}},
            },
            "status": {**self.body["status"], "uploadStatus": "processed"},
            "processingDetails": {"processingStatus": "succeeded"},
        }
        self.yt.videos.return_value.list.return_value.execute.return_value = {"items": [self.remote]}
        fake_google = types.ModuleType("googleapiclient")
        fake_errors = types.ModuleType("googleapiclient.errors")
        fake_errors.HttpError = FakeHttpError
        fake_http = types.ModuleType("googleapiclient.http")
        self.media = fake_http.MediaFileUpload = MagicMock()
        module_patch = patch.dict(sys.modules, {
            "googleapiclient": fake_google,
            "googleapiclient.errors": fake_errors,
            "googleapiclient.http": fake_http,
        })
        module_patch.start()
        self.addCleanup(module_patch.stop)
        output = redirect_stdout(io.StringIO())
        output.__enter__()
        self.addCleanup(output.__exit__, None, None, None)

    def checkpoint(self, state="PACKAGING_COMPLETE", *, thumb=False, **fields):
        payload = {
            "version": 2, "status": state, "video_id": self.vid,
            "identity": self.identity, "video": str(self.video),
            "thumbnail_sha256": uploader._sha256(self.thumb) if thumb else None,
            "thumbnail_result": {
                "applied": True, "verified": True,
                "remote_urls": {"default": "https://example.invalid/thumb.jpg"},
            } if thumb else None,
            "playlist": "",
            **fields,
        }
        self.path.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    def upload(self, *, thumb=False, body=None, owner=None):
        return uploader.upload(
            self.yt, self.video, body or self.body, self.thumb if thumb else None,
            self.path, channel_id=owner or self.owner,
        )

    def run_main(self, *, failures=()):
        with (
            patch.object(sys, "argv", ["youtube_upload.py", str(self.ep), "--run", "--공개", "비공개"]),
            patch.object(uploader, "service", return_value=self.yt) as service,
            patch.object(uploader, "validate_capcut_lock", return_value=types.SimpleNamespace(failures=failures)) as gate,
            patch.object(uploader, "CFG", {"업로드.채널명": "test channel", "업로드.합성콘텐츠고지": True}),
        ):
            result = uploader.main()
        return result, service, gate

    def test_completed_resume_only_reads_remote_and_preserves_checkpoint(self):
        self.checkpoint(thumb=True)
        before = self.path.read_bytes()
        with patch.object(uploader, "set_and_verify_thumbnail") as thumbnail:
            vid, result = self.upload(thumb=True)
        self.assertEqual(vid, self.vid)
        self.assertTrue(result["verified"])
        self.yt.videos.return_value.list.assert_called_once()
        self.yt.videos.return_value.insert.assert_not_called()
        thumbnail.assert_not_called()
        self.media.assert_not_called()
        self.assertEqual(before, self.path.read_bytes())

    def test_pending_thumbnail_uses_same_video_and_retains_identity(self):
        self.checkpoint("VIDEO_UPLOADED_THUMBNAIL_PENDING", thumb=True, thumbnail_result=None)
        with patch.object(uploader, "set_and_verify_thumbnail", return_value={
            "applied": True, "verified": True, "remote_urls": {"default": "url"},
        }) as thumbnail:
            self.assertEqual(self.upload(thumb=True)[0], self.vid)
        thumbnail.assert_called_once_with(self.yt, self.vid, self.thumb)
        self.yt.videos.return_value.insert.assert_not_called()
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["identity"], self.identity)
        self.assertEqual(saved["status"], "THUMBNAIL_APPLIED_VERIFIED")

    def test_changed_video_metadata_channel_or_cover_blocks_new_insert(self):
        cases = ("video", "metadata", "channel", "cover")
        for case in cases:
            with self.subTest(case=case):
                self.video.write_bytes(b"locked video bytes")
                self.thumb.write_bytes(b"locked cover bytes")
                self.checkpoint(thumb=True)
                body = copy.deepcopy(self.body)
                owner = self.owner
                if case == "video":
                    self.video.write_bytes(b"another video")
                elif case == "metadata":
                    body["snippet"]["title"] = "another title"
                elif case == "channel":
                    owner = "another-channel"
                else:
                    self.thumb.write_bytes(b"another cover")
                with self.assertRaises(uploader.UploadRecoveryError):
                    self.upload(thumb=True, body=body, owner=owner)
                self.yt.videos.return_value.insert.assert_not_called()

    def test_remote_missing_wrong_owner_metadata_or_rejected_blocks(self):
        self.checkpoint()
        for case in ("missing", "owner", "metadata", "rejected", "disclosure"):
            with self.subTest(case=case):
                remote = copy.deepcopy(self.remote)
                items = [remote]
                if case == "missing":
                    items = []
                elif case == "owner":
                    remote["snippet"]["channelId"] = "wrong-channel"
                elif case == "metadata":
                    remote["snippet"]["description"] = "changed remotely"
                elif case == "rejected":
                    remote["status"]["uploadStatus"] = "rejected"
                else:
                    remote["status"]["containsSyntheticMedia"] = False
                self.yt.videos.return_value.list.return_value.execute.return_value = {"items": items}
                with self.assertRaises(uploader.UploadRecoveryError):
                    self.upload()
                self.yt.videos.return_value.insert.assert_not_called()

    def test_remote_publication_change_is_read_only(self):
        self.checkpoint()
        self.remote["status"]["privacyStatus"] = "public"
        self.assertEqual(self.upload()[0], self.vid)
        self.yt.videos.return_value.update.assert_not_called()
        self.yt.videos.return_value.insert.assert_not_called()

    def test_unknown_legacy_malformed_or_incomplete_records_block_before_api(self):
        records = [
            {"version": 2, "status": "UPLOAD_OUTCOME_UNKNOWN", "identity": self.identity},
            {"status": "PACKAGING_COMPLETE", "video_id": self.vid},
            {"version": 2, "status": "PACKAGING_COMPLETE", "video_id": self.vid},
            ["not an object"],
        ]
        for record in records:
            with self.subTest(record=record):
                self.path.write_text(json.dumps(record), encoding="utf-8")
                with self.assertRaises(uploader.UploadRecoveryError):
                    self.upload()
        self.path.write_text("{partial", encoding="utf-8")
        with self.assertRaises(uploader.UploadRecoveryError):
            self.upload()
        self.yt.assert_not_called()
        self.yt.videos.assert_not_called()
        self.yt.channels.assert_not_called()

    def test_result_without_checkpoint_prevents_new_upload(self):
        (self.ep / "07.업로드결과.json").write_text('{"video_id":"existing"}', encoding="utf-8")
        with self.assertRaises(uploader.UploadRecoveryError):
            self.upload()
        self.yt.videos.assert_not_called()

    def test_complete_with_missing_thumbnail_proof_never_reapplies(self):
        self.checkpoint(thumb=True, thumbnail_result=None)
        with patch.object(uploader, "set_and_verify_thumbnail") as thumbnail:
            with self.assertRaises(uploader.UploadRecoveryError):
                self.upload(thumb=True)
        thumbnail.assert_not_called()
        self.yt.videos.assert_not_called()

    def test_new_upload_persists_intent_before_insert_and_id_before_thumbnail(self):
        request = MagicMock()
        request.next_chunk.return_value = (None, {"id": self.vid})

        def insert(**kwargs):
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "UPLOAD_OUTCOME_UNKNOWN")
            self.assertEqual(saved["identity"], self.identity)
            return request

        def thumbnail(*args):
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            self.assertEqual(saved["video_id"], self.vid)
            self.assertEqual(saved["status"], "VIDEO_UPLOADED_THUMBNAIL_PENDING")
            raise RuntimeError("thumbnail failed")

        self.yt.videos.return_value.insert.side_effect = insert
        with patch.object(uploader, "set_and_verify_thumbnail", side_effect=thumbnail):
            with self.assertRaisesRegex(RuntimeError, "thumbnail failed"):
                self.upload(thumb=True)
        self.yt.videos.return_value.insert.assert_called_once()
        self.assertEqual(uploader.read_upload_checkpoint(self.path)["video_id"], self.vid)

    def test_server_errors_stop_after_five_attempts_with_backoff_and_block_rerun(self):
        request = self.yt.videos.return_value.insert.return_value
        request.next_chunk.side_effect = FakeHttpError(503)
        with patch.object(uploader.time, "sleep") as sleep:
            with self.assertRaises(uploader.UploadRecoveryError):
                self.upload()
        self.assertEqual(request.next_chunk.call_count, 5)
        self.assertEqual(sleep.call_args_list, [call(1), call(2), call(4), call(8)])
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], "UPLOAD_OUTCOME_UNKNOWN")
        self.assertEqual(saved["retry_errors"], 5)
        self.assertEqual(saved["identity"], self.identity)
        with self.assertRaises(uploader.UploadRecoveryError):
            self.upload()
        self.yt.videos.return_value.insert.assert_called_once()

    def test_retry_budget_does_not_reset_after_chunk_progress(self):
        request = self.yt.videos.return_value.insert.return_value
        progress = types.SimpleNamespace(progress=lambda: 0.5)
        request.next_chunk.side_effect = [
            FakeHttpError(500), (progress, None), FakeHttpError(502),
            (progress, None), FakeHttpError(503), (progress, None),
            FakeHttpError(504), (progress, None), FakeHttpError(500),
        ]
        with patch.object(uploader.time, "sleep") as sleep:
            with self.assertRaises(uploader.UploadRecoveryError):
                self.upload()
        self.assertEqual(sleep.call_count, 4)
        self.assertEqual(request.next_chunk.call_count, 9)
        self.yt.videos.return_value.insert.assert_called_once()

    def test_transient_failure_reuses_request_and_finishes(self):
        request = self.yt.videos.return_value.insert.return_value
        request.next_chunk.side_effect = [FakeHttpError(503), (None, {"id": self.vid})]
        with patch.object(uploader.time, "sleep") as sleep:
            self.assertEqual(self.upload()[0], self.vid)
        sleep.assert_called_once_with(1)
        self.yt.videos.return_value.insert.assert_called_once()
        self.assertEqual(uploader.read_upload_checkpoint(self.path)["video_id"], self.vid)

    def test_non_retryable_response_interrupt_or_transport_failure_keeps_intent(self):
        for failure in (FakeHttpError(403), ConnectionError("lost response"), KeyboardInterrupt()):
            with self.subTest(failure=type(failure).__name__):
                self.path.unlink(missing_ok=True)
                request = self.yt.videos.return_value.insert.return_value
                request.next_chunk.side_effect = failure
                with patch.object(uploader.time, "sleep") as sleep:
                    with self.assertRaises(type(failure)):
                        self.upload()
                sleep.assert_not_called()
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                self.assertEqual(saved["status"], "UPLOAD_OUTCOME_UNKNOWN")
                with self.assertRaises(uploader.UploadRecoveryError):
                    self.upload()

    def test_atomic_checkpoint_failure_keeps_existing_id(self):
        self.checkpoint()
        before = self.path.read_bytes()
        with patch.object(uploader.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                uploader._write_upload_checkpoint(self.path, status="new")
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(list(self.ep.glob("*.tmp")), [])

    def test_exclusive_checkpoint_claim_never_overwrites_existing_record(self):
        self.checkpoint()
        before = self.path.read_bytes()
        with self.assertRaises(FileExistsError):
            uploader._write_upload_checkpoint(self.path, exclusive=True, status="new")
        self.assertEqual(before, self.path.read_bytes())

    def test_main_completed_resume_is_read_only_and_still_runs_capcut_gate(self):
        self.checkpoint()
        before = self.path.read_bytes()
        result, service, gate = self.run_main()
        self.assertEqual(result, 0)
        service.assert_called_once()
        gate.assert_called_once_with(self.ep, self.video)
        self.yt.videos.return_value.insert.assert_not_called()
        self.yt.playlistItems.assert_not_called()
        self.assertEqual(before, self.path.read_bytes())
        self.assertFalse((self.ep / "07.업로드결과.json").exists())

    def test_main_resume_cannot_bypass_release_or_capcut_gate(self):
        self.checkpoint()
        result, service, _ = self.run_main(failures=["video hash mismatch"])
        self.assertEqual(result, 1)
        service.assert_not_called()
        (self.ep / "00.진행상황.md").write_text("배포 차단", encoding="utf-8")
        result, service, _ = self.run_main()
        self.assertEqual(result, 1)
        service.assert_not_called()

    def test_main_unknown_checkpoint_blocks_before_credentials(self):
        self.checkpoint("UPLOAD_OUTCOME_UNKNOWN", video_id=None)
        result, service, _ = self.run_main()
        self.assertEqual(result, 1)
        service.assert_not_called()

    def test_main_new_upload_completes_with_identity_and_rerun_reuses_id(self):
        self.yt.videos.return_value.insert.return_value.next_chunk.return_value = (
            None, {"id": self.vid},
        )
        result, _, _ = self.run_main()
        self.assertEqual(result, 0)
        saved = uploader.read_upload_checkpoint(self.path)
        self.assertEqual(saved["identity"], self.identity)
        self.assertEqual(saved["status"], "PACKAGING_COMPLETE")
        receipt = self.ep / "07.업로드결과.json"
        before = receipt.read_bytes()
        self.assertEqual(self.run_main()[0], 0)
        self.yt.videos.return_value.insert.assert_called_once()
        self.assertEqual(before, receipt.read_bytes())

    def test_main_pending_upload_finishes_packaging_without_insert(self):
        self.checkpoint("VIDEO_UPLOADED_THUMBNAIL_PENDING")
        self.assertEqual(self.run_main()[0], 0)
        saved = uploader.read_upload_checkpoint(self.path)
        self.assertEqual(saved["identity"], self.identity)
        self.assertEqual(saved["video_id"], self.vid)
        self.assertEqual(saved["status"], "PACKAGING_COMPLETE")
        self.yt.videos.return_value.insert.assert_not_called()

    def test_playlist_retry_checks_existing_membership_before_insert(self):
        self.yt.playlistItems.return_value.list.return_value.execute.return_value = {
            "items": [{"id": "already-added"}],
        }
        with patch.object(uploader, "find_playlist", return_value="playlist-id"):
            uploader.add_to_playlist(self.yt, self.vid, "playlist")
        self.yt.playlistItems.return_value.insert.assert_not_called()

    def test_missing_playlist_fails_without_claiming_packaging_complete(self):
        with patch.object(uploader, "find_playlist", return_value=None):
            with self.assertRaises(uploader.UploadRecoveryError):
                uploader.add_to_playlist(self.yt, self.vid, "missing")
        self.yt.playlistItems.return_value.insert.assert_not_called()


if __name__ == "__main__":
    unittest.main()
