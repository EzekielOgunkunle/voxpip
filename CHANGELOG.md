# Changelog

## v0.1.0 — 2026-05-02

Forked from [claude-video v0.1.2](https://github.com/bradautomates/claude-video) by @bradautomates (MIT).

### Added
- Local speech-to-text fallback (tier 2 in transcription pipeline) — no API key required
- Engine auto-detection: voxtype, whisper.cpp, mlx_whisper, openai-whisper
- `--no-local-stt` flag to skip local STT tier
- `local_stt_engine` field in `setup.py --json` output
- Cache detected engine in `~/.config/voxpip/.env`
