#!/usr/bin/env node
/** ElevenLabs Scribe v2로 지정 MP3를 전사한다. API 키는 출력하지 않는다. */

import fs from "node:fs";
import path from "node:path";

function parseArgs(argv) {
  const files = [];
  let envFile = ".env";
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === "--env-file") {
      envFile = argv[++i];
    } else {
      files.push(argv[i]);
    }
  }
  if (!files.length) {
    throw new Error("사용법: tts_transcription_qa.mjs [--env-file PATH] AUDIO...");
  }
  return {files, envFile};
}

function readEnvValue(file, key) {
  if (!fs.existsSync(file)) return "";
  for (const raw of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const line = raw.trim();
    if (!line || line.startsWith("#")) continue;
    const equals = line.indexOf("=");
    if (equals < 1 || line.slice(0, equals).trim() !== key) continue;
    let value = line.slice(equals + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) ||
        (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    return value;
  }
  return "";
}

async function transcribe(file, apiKey) {
  const form = new FormData();
  form.append("file", new Blob([fs.readFileSync(file)], {type: "audio/mpeg"}), path.basename(file));
  form.append("model_id", "scribe_v2");
  form.append("language_code", "kor");
  const response = await fetch("https://api.elevenlabs.io/v1/speech-to-text", {
    method: "POST",
    headers: {"xi-api-key": apiKey},
    body: form,
  });
  const body = await response.text();
  if (!response.ok) {
    throw new Error(`${path.basename(file)} 전사 실패 HTTP ${response.status}: ${body.slice(0, 300)}`);
  }
  return JSON.parse(body).text || "";
}

const {files, envFile} = parseArgs(process.argv.slice(2));
const apiKey = process.env.ELEVENLABS_API_KEY || readEnvValue(envFile, "ELEVENLABS_API_KEY");
if (!apiKey) throw new Error("ELEVENLABS_API_KEY가 없습니다.");

for (const file of files) {
  const text = await transcribe(file, apiKey);
  process.stdout.write(`[${path.basename(file)}] ${text}\n`);
}
