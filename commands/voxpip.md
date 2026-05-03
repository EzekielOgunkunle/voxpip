---
description: "Watch any video and get a transcript — even without an API key. Extends /watch with a local speech-to-text fallback."
argument-hint: <video-url-or-path> [question]
allowed-tools: [Bash, Read, AskUserQuestion]
---

Extract the video URL or path from: $ARGUMENTS

If no video was provided, use AskUserQuestion to ask for one before doing anything else.

Run this exact command. Do NOT run yt-dlp, ffmpeg, ffprobe, or whisper yourself — the script handles everything:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/watch.py" "<video-url-or-path>"
```

Wait for the script to finish. It will download the video, extract frames, and attempt transcription in this order: native captions → local STT (voxtype/whisper.cpp/mlx_whisper/openai-whisper) → Groq API → OpenAI API. Read every frame path the script prints. Answer the user using the frames and transcript. Separate any question the user asked from the video URL and answer it directly.
