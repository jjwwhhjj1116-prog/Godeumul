from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import capcut_build as builder  # noqa: E402


def template_documents():
    def segment(material, text=False):
        result = {"id": material + "-segment", "material_id": material,
                  "extra_material_refs": []}
        if text:
            result["clip"] = {"transform": {"x": 0, "y": -0.206}}
        return result

    return {
        "materials": {
            "videos": [{"id": "video", "type": "video"}, {"id": "watermark", "type": "photo"}],
            "audios": [{"id": "audio"}],
            "texts": [{"id": "text", "content": json.dumps({"text": "old", "styles": [{}]})}],
        },
        "tracks": [
            {"type": "video", "flag": 0, "segments": [segment("video")]},
            {"type": "audio", "segments": [segment("audio")]},
            {"type": "text", "segments": [segment("text", True)]},
            {"type": "video", "flag": 2, "segments": [segment("watermark")]},
        ],
    }, {"draft_materials": [{"type": 0, "value": []}]}


class TemplateStagingTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.template = self.base / "template"
        self.template.mkdir()
        self.root = self.base / "drafts"
        self.content, self.meta = template_documents()
        self.save_template()
        self.source = self.base / "source.mp4"
        self.source.write_bytes(b"mocked media")

    def save_template(self):
        (self.template / "draft_content.json").write_text(json.dumps(self.content), encoding="utf-8")
        (self.template / "draft_meta_info.json").write_text(json.dumps(self.meta), encoding="utf-8")

    def save(self):
        return builder.save_complete_draft(self.root, "test draft", self.content, self.meta, self.source)

    def fake_cover(self, source, output):
        self.assertEqual(source, self.source)
        self.assertFalse((self.root / "test draft").exists())
        self.assertTrue((output.parent / "draft_content.json").is_file())
        self.assertTrue((output.parent / "draft_meta_info.json").is_file())
        output.write_bytes(b"JPEG fixture")

    def test_template_reads_each_document_once_and_returns_validated_data(self):
        original = Path.read_text
        reads = []

        def read(path, *args, **kwargs):
            reads.append(path.name)
            return original(path, *args, **kwargs)

        with patch.object(Path, "read_text", read):
            content, meta = builder.load_validated_template(self.template)
        self.assertEqual(content, self.content)
        self.assertEqual(meta, self.meta)
        self.assertEqual(reads, ["draft_content.json", "draft_meta_info.json"])

    def test_missing_or_malformed_template_metadata_is_a_preflight_failure(self):
        metadata = self.template / "draft_meta_info.json"
        metadata.unlink()
        with self.assertRaisesRegex(ValueError, "draft_meta_info.json"):
            builder.load_validated_template(self.template)
        metadata.write_text("{broken", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "draft_meta_info.json"):
            builder.load_validated_template(self.template)
        self.assertFalse(self.root.exists())

    def test_non_object_template_documents_fail(self):
        for name in ("draft_content.json", "draft_meta_info.json"):
            with self.subTest(name=name):
                self.save_template()
                (self.template / name).write_text("[]", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "JSON 객체"):
                    builder.load_validated_template(self.template)

    def test_missing_tracks_materials_references_and_caption_structure_fail(self):
        cases = ("watermark", "audio", "text", "empty", "material", "reference", "clip", "content", "registry")
        for case in cases:
            with self.subTest(case=case):
                self.content, self.meta = template_documents()
                if case == "watermark":
                    self.content["tracks"].pop()
                elif case == "audio":
                    self.content["materials"]["audios"] = []
                elif case == "text":
                    self.content["materials"]["texts"] = []
                elif case == "empty":
                    self.content["tracks"][0]["segments"] = []
                elif case == "material":
                    self.content["tracks"][0]["segments"][0]["material_id"] = "missing"
                elif case == "reference":
                    self.content["tracks"][0]["segments"][0]["extra_material_refs"] = ["missing"]
                elif case == "clip":
                    self.content["tracks"][2]["segments"][0]["clip"] = None
                elif case == "content":
                    self.content["materials"]["texts"][0]["content"] = "[]"
                else:
                    self.meta["draft_materials"] = []
                self.save_template()
                with self.assertRaises(ValueError):
                    builder.load_validated_template(self.template)

    def test_complete_folder_is_renamed_only_after_both_json_and_cover_exist(self):
        with patch.object(builder, "extract_draft_cover", side_effect=self.fake_cover):
            dest = self.save()
        self.assertEqual(dest, self.root / "test draft")
        self.assertEqual(sorted(path.name for path in dest.iterdir()),
                         ["draft_content.json", "draft_cover.jpg", "draft_meta_info.json"])
        self.assertEqual(json.loads((dest / "draft_meta_info.json").read_text()), self.meta)
        self.assertEqual(list(self.root.glob(".capcut-build-*")), [])

    def test_cover_failure_preserves_staging_and_allows_retry_same_final_name(self):
        with patch.object(builder, "extract_draft_cover", side_effect=ValueError("decoder error")):
            with self.assertRaisesRegex(RuntimeError, "decoder error.*임시 폴더 보존"):
                self.save()
        self.assertFalse((self.root / "test draft").exists())
        staging = list(self.root.glob(".capcut-build-*"))
        self.assertEqual(len(staging), 1)
        self.assertTrue((staging[0] / "draft_content.json").is_file())
        with patch.object(builder, "extract_draft_cover", side_effect=self.fake_cover):
            self.save()
        self.assertTrue((self.root / "test draft").is_dir())
        self.assertTrue(staging[0].is_dir())

    def test_second_json_write_failure_never_leaves_final_destination(self):
        original = Path.open

        def open_file(path, *args, **kwargs):
            if path.name == "draft_meta_info.json" and path.parent.name.startswith(".capcut-build-"):
                raise OSError("disk full")
            return original(path, *args, **kwargs)

        with patch.object(Path, "open", open_file), patch.object(builder, "extract_draft_cover") as cover:
            with self.assertRaisesRegex(RuntimeError, "disk full"):
                self.save()
        self.assertFalse((self.root / "test draft").exists())
        cover.assert_not_called()

    def test_existing_project_is_preserved_without_staging_or_cover(self):
        dest = self.root / "test draft"
        dest.mkdir(parents=True)
        marker = dest / "user-edit.txt"
        marker.write_text("user's edit", encoding="utf-8")
        with patch.object(builder, "extract_draft_cover") as cover:
            with self.assertRaises(FileExistsError):
                self.save()
        self.assertEqual(marker.read_text(encoding="utf-8"), "user's edit")
        self.assertEqual(list(self.root.glob(".capcut-build-*")), [])
        cover.assert_not_called()

    def test_concurrent_target_is_preserved(self):
        def cover(source, output):
            self.fake_cover(source, output)
            target = self.root / "test draft"
            target.mkdir()
            (target / "user-edit.txt").write_text("concurrent edit", encoding="utf-8")

        with patch.object(builder, "extract_draft_cover", side_effect=cover):
            with self.assertRaisesRegex(RuntimeError, "덮어쓰지"):
                self.save()
        self.assertEqual((self.root / "test draft/user-edit.txt").read_text(), "concurrent edit")
        self.assertEqual(len(list(self.root.glob(".capcut-build-*"))), 1)

    def test_windows_rename_refuses_target_created_after_last_check(self):
        original = builder.os.rename

        def race(source, target):
            target.mkdir()
            original(source, target)

        with patch.object(builder, "extract_draft_cover", side_effect=self.fake_cover), \
             patch.object(builder.os, "rename", side_effect=race):
            with self.assertRaises(RuntimeError):
                self.save()
        self.assertEqual(list((self.root / "test draft").iterdir()), [])
        self.assertEqual(len(list(self.root.glob(".capcut-build-*"))), 1)

    def test_rename_failure_preserves_prepared_staging(self):
        with patch.object(builder, "extract_draft_cover", side_effect=self.fake_cover), \
             patch.object(builder.os, "rename", side_effect=PermissionError("rename blocked")):
            with self.assertRaisesRegex(RuntimeError, "rename blocked"):
                self.save()
        self.assertFalse((self.root / "test draft").exists())
        staging = next(self.root.glob(".capcut-build-*"))
        self.assertTrue((staging / "draft_cover.jpg").is_file())

    def test_invalid_windows_project_names_fail_before_any_write(self):
        for name in ("", ".", "..", "../outside", "outside/name", "C:\\escape", "NUL", "COM1.txt", "trailing.", "trailing "):
            with self.subTest(name=name), self.assertRaises(ValueError):
                builder.draft_destination(self.root, name)
        self.assertFalse(self.root.exists())

    def test_non_windows_save_fails_before_any_write(self):
        with patch.object(sys, "platform", "linux"):
            with self.assertRaisesRegex(RuntimeError, "Windows"):
                self.save()
        self.assertFalse(self.root.exists())

    def test_cover_timeout_exit_error_missing_binary_or_empty_output_are_reported(self):
        output = self.base / "cover.jpg"
        failures = [
            (subprocess.TimeoutExpired("ffmpeg", 30), "시간 초과"),
            (subprocess.CalledProcessError(1, "ffmpeg", stderr="bad decoder"), "exit 1.*bad decoder"),
            (FileNotFoundError("ffmpeg absent"), "실행 불가"),
        ]
        for failure, message in failures:
            with self.subTest(failure=failure), patch.object(builder.subprocess, "run", side_effect=failure) as run:
                with self.assertRaisesRegex(ValueError, message):
                    builder.extract_draft_cover(self.source, output)
                self.assertEqual(run.call_args.kwargs["timeout"], 30)
        with patch.object(builder.subprocess, "run", return_value=subprocess.CompletedProcess([], 0)):
            with self.assertRaisesRegex(ValueError, "출력이 없거나 비어"):
                builder.extract_draft_cover(self.source, output)

    def test_cover_success_uses_bounded_noninteractive_nonoverwriting_call(self):
        output = self.base / "cover.jpg"

        def run(command, **kwargs):
            output.write_bytes(b"JPEG fixture")
            self.assertIn("-nostdin", command)
            self.assertIn("-n", command)
            self.assertNotIn("-y", command)
            self.assertEqual(kwargs["timeout"], builder.FFMPEG_COVER_TIMEOUT_SECONDS)
            return subprocess.CompletedProcess(command, 0)

        with patch.object(builder.subprocess, "run", side_effect=run):
            builder.extract_draft_cover(self.source, output)

    def test_template_transition_is_never_cloned(self):
        self.content["materials"]["transitions"] = [{"id": "old-transition"}]
        segment = self.content["tracks"][0]["segments"][0]
        segment["extra_material_refs"] = ["old-transition"]
        cloner = builder.Cloner(self.content)
        self.assertEqual(cloner.clone_extras(segment), [])
        self.assertEqual(cloner.out["transitions"], [])


class BuilderPreflightIntegrationTests(unittest.TestCase):
    setUp = TemplateStagingTests.setUp
    save_template = TemplateStagingTests.save_template

    def run_builder(self, *, check=False, after_load=None):
        ep = self.base / "EP01_test"
        ep.mkdir(exist_ok=True)
        (ep / "audio").mkdir(exist_ok=True)
        (ep / "clips").mkdir(exist_ok=True)
        (ep / "audio/001.mp3").write_bytes(b"audio")
        (ep / "clips/001.mp4").write_bytes(b"video")
        (ep / "audio/durations.json").write_text(json.dumps({"scenes": {"1": {"duration": 1.0, "text": "hello"}}}))
        cue = {"n": 1, "scene": 1, "start": 0.0, "end": 1.0, "text": "hello"}
        (ep / "자막.json").write_text(json.dumps({"cues": [cue]}), encoding="utf-8")
        (ep / "자막_싱크.json").write_text(json.dumps({
            "source": "elevenlabs-forced-alignment", "count": 1, "cues": [cue],
        }), encoding="utf-8")
        watermark = self.base / "watermark.png"
        watermark.write_bytes(b"watermark")
        args = ["capcut_build.py", str(ep), "--template", str(self.template),
                "--draft-root", str(self.root), "--name", "test draft"] + (["--check"] if check else [])
        original_load = builder.load_validated_template

        def load(folder):
            result = original_load(folder)
            if after_load:
                after_load()
            return result

        with ExitStack() as stack:
            stack.enter_context(redirect_stdout(io.StringIO()))
            stack.enter_context(patch.object(sys, "argv", args))
            stack.enter_context(patch.object(builder, "WATERMARK", watermark))
            stack.enter_context(patch.object(builder, "validate_context_review", return_value=SimpleNamespace(
                failures=[], passed=True, paragraphs=1, sentences=1)))
            stack.enter_context(patch.object(builder, "validate_semantic_prebuild", return_value=[]))
            stack.enter_context(patch.object(builder, "validate_draft_sources", return_value=[]))
            stack.enter_context(patch.object(builder, "probe_video_metadata", return_value={"duration": 1.0, "has_audio": False}))
            stack.enter_context(patch.object(builder, "load_validated_template", side_effect=load))
            save = stack.enter_context(patch.object(builder, "save_complete_draft", return_value=self.root / "test draft"))
            result = builder.main()
        return result, save

    def test_check_rejects_missing_meta_before_assembly_or_destination_creation(self):
        (self.template / "draft_meta_info.json").unlink()
        result, save = self.run_builder(check=True)
        self.assertEqual(result, 1)
        save.assert_not_called()
        self.assertFalse(self.root.exists())

    def test_build_uses_validated_in_memory_template_after_both_source_files_disappear(self):
        def remove_after_validation():
            (self.template / "draft_content.json").unlink()
            (self.template / "draft_meta_info.json").unlink()

        result, save = self.run_builder(after_load=remove_after_validation)
        self.assertEqual(result, 0)
        save.assert_called_once()
        self.assertEqual(save.call_args.args[3]["draft_name"], "test draft")
        self.assertTrue(save.call_args.args[3]["draft_materials"][0]["value"])
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
