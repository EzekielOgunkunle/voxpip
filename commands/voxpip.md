---
description: "Watch any video and get a transcript — even without an API key. Extends /watch with a local speech-to-text fallback."
argument-hint: <video-url-or-path> [question]
allowed-tools: [Bash, Read, AskUserQuestion]
---

Invoke the `voxpip` skill (defined in SKILL.md) with the user's arguments: $ARGUMENTS

Follow the skill's full pipeline: preflight setup check → download via yt-dlp → extract frames at auto-scaled fps → pull captions or Whisper transcript → Read each frame → answer the user grounded in frames and transcript. If the user provided no arguments, ask them for a video URL or local path before proceeding.
