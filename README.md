# /voxpip

**Give Claude the ability to watch any video — even without an API key.**

Claude Code:
```
/plugin marketplace add EzekielOgunkunle/voxpip
/plugin install voxpip@voxpip
```

claude.ai (web): [download `voxpip.skill`](https://github.com/EzekielOgunkunle/voxpip/releases/latest) and drop it into Settings → Capabilities → Skills.

Codex / generic skills:
```bash
git clone https://github.com/EzekielOgunkunle/voxpip.git ~/.codex/skills/voxpip
```

Zero config to start — local STT detected automatically on first run.

> **Note:** voxpip is a Claude Code plugin, not a PyPI package. `pip install voxpip` will not work — use the install commands above.

---

I built this because I work with a lot of video content and I wanted a way to hand video to Claude without needing an API key just to get a transcript. Brad Bonanno's `/watch` plugin was the perfect foundation — solid pipeline, clean code. I added a local STT tier so the transcription fallback works even if you've never touched a Groq or OpenAI account.

## What it adds to /watch

This plugin forks [bradautomates/claude-video](https://github.com/bradautomates/claude-video). Brad's pipeline handles everything: download via yt-dlp, frame extraction via ffmpeg, native caption parsing, and cloud Whisper fallback (Groq/OpenAI). voxpip's single addition is a local STT tier that sits between caption parsing and the cloud APIs.

If a video has no native captions, voxpip tries your local STT engine before reaching for a cloud API. If local STT isn't installed either, it falls back to Groq or OpenAI exactly as the upstream does. You can also force the behavior with `--no-local-stt` or `--no-whisper`.

## How it works

1. **You paste a video and a question.** URL (anything yt-dlp supports — YouTube, Loom, TikTok, X, Instagram, plus hundreds more) or a local path (`.mp4`, `.mov`, `.mkv`, `.webm`).
2. **`yt-dlp` downloads it.** For URLs, into a temp working directory. For local files, no download — just probed in place.
3. **`ffmpeg` extracts frames at an auto-scaled rate.** Duration-aware budget: ≤30s gets ~30 frames, 30-60s gets ~40, 1-3min gets ~60, 3-10min gets ~80, longer gets 100 sparsely. Hard caps: 2 fps, 100 frames. JPEGs at 512px wide by default.
4. **The transcript comes from one of three places.** First: native captions from yt-dlp (free, instant). Second: local STT engine on your machine (free, offline). Third: Whisper API — Groq's `whisper-large-v3` (preferred) or OpenAI's `whisper-1`.
5. **Frames + transcript are handed to Claude.** The script prints frame paths with `t=MM:SS` markers and the transcript with timestamps. Claude `Read`s each frame in parallel — JPEGs render directly as images in its context.
6. **Claude answers grounded in what's actually on screen and in the audio.** Not "based on the description" or "according to the title." It saw the frames. It heard the transcript.
7. **Cleanup.** The script prints a working directory at the end. If you're not asking follow-ups, Claude removes it.

## Local STT engines

| Engine | Platform | Install |
|--------|----------|---------|
| voxtype | Linux (Arch) | `paru -S voxtype` or `yay -S voxtype` — non-Arch: see [voxtype.io](https://voxtype.io) |
| whisper.cpp | Linux/macOS/Windows | [github.com/ggerganov/whisper.cpp](https://github.com/ggerganov/whisper.cpp) — build or grab a release binary |
| mlx_whisper | macOS (Apple Silicon) | `pip install mlx-whisper` |
| whisper (openai-whisper) | Linux/macOS/Windows | `pip install openai-whisper` |

> **voxtype note:** voxtype is primarily a push-to-talk dictation tool. voxpip invokes it via `voxtype transcribe <file>` — voxtype must expose this CLI transcription mode to be usable here. See [voxtype.io/docs](https://voxtype.io/docs) to verify your version supports it.

`setup.py` detects whichever is on your PATH and caches the result in `~/.config/voxpip/.env` (key: `LOCAL_STT_ENGINE`). Re-detection only happens if the key is missing.

## Bring your own keys (optional)

| Capability | What you need | Cost |
|------------|---------------|------|
| Local STT (auto-detected) | voxtype / whisper.cpp / mlx_whisper / openai-whisper | none required |
| Download + native captions | `yt-dlp` + `ffmpeg` | Free |
| Whisper fallback (preferred) | [Groq API key](https://console.groq.com/keys) — `whisper-large-v3` | Cheap, fast |
| Whisper fallback (alt) | [OpenAI API key](https://platform.openai.com/api-keys) — `whisper-1` | Standard pricing |
| Disable Whisper entirely | `--no-whisper` | Free, frames-only when no captions |

## Install

| Surface | Install |
|---------|---------|
| **Claude Code** | `/plugin marketplace add EzekielOgunkunle/voxpip` then `/plugin install voxpip@voxpip` |
| **claude.ai** (web) | [Download `voxpip.skill`](https://github.com/EzekielOgunkunle/voxpip/releases/latest) → Settings → Capabilities → Skills → `+` |
| **Codex** | `git clone https://github.com/EzekielOgunkunle/voxpip.git ~/.codex/skills/voxpip` |
| **Manual / dev** | `git clone https://github.com/EzekielOgunkunle/voxpip.git ~/.claude/skills/voxpip` |

## Usage

```
/voxpip https://youtu.be/dQw4w9WgXcQ what happens at the 30 second mark?
/voxpip https://www.tiktok.com/@user/video/123 summarize this
/voxpip ~/Movies/screen-recording.mp4 when does the UI break?
/voxpip https://vimeo.com/123 what tools does she mention?
```

Focused on a specific section — denser frame budget, lower token cost:
```
/voxpip https://youtu.be/abc --start 2:15 --end 2:45
/voxpip video.mp4 --start 50 --end 60
/voxpip "$URL" --start 1:12:00            # from 1h12m to end
```

Other flags:
- `--no-local-stt` — skip local STT tier, go straight to API fallback.
- `--max-frames N` — lower the frame cap for a tighter token budget.
- `--resolution W` — bump frame width to 1024 px when Claude needs to read on-screen text.
- `--fps F` — override the auto-fps calculation (still capped at 2 fps).
- `--whisper groq|openai` — force a specific Whisper backend.
- `--no-whisper` — disable cloud transcription entirely.
- `--out-dir DIR` — keep working files somewhere specific.

## Structure

```
.
├── SKILL.md                 # skill contract — loaded by all three surfaces  [changed]
├── commands/
│   └── voxpip.md            # slash command shim                             [renamed from watch.md]
├── scripts/
│   ├── watch.py             # entry point — orchestrates download → frames → transcript
│   ├── download.py          # yt-dlp wrapper
│   ├── frames.py            # ffmpeg frame extraction + auto-fps logic
│   ├── transcribe.py        # VTT parsing + dedupe + Whisper orchestration
│   ├── whisper.py           # Groq / OpenAI clients (pure stdlib)
│   ├── setup.py             # preflight + installer  [changed: local STT detection]
│   └── build-skill.sh       # build dist/voxpip.skill for claude.ai upload
├── hooks/                   # SessionStart status hook (Claude Code only)
├── .claude-plugin/          # plugin.json + marketplace.json  [changed]
├── .codex-plugin/           # codex packaging
└── .github/workflows/       # release.yml — auto-builds voxpip.skill on tag push
```

## Credits

Built on [claude-video](https://github.com/bradautomates/claude-video) by @bradautomates (MIT).

---

[github.com/EzekielOgunkunle/voxpip](https://github.com/EzekielOgunkunle/voxpip) · [LICENSE](LICENSE)
