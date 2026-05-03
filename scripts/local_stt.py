#!/usr/bin/env python3
"""Local STT (speech-to-text) fallback tier for voxpip.

Detects an installed local engine (voxtype, whisper-cpp, mlx_whisper, or
openai-whisper CLI) and uses it to transcribe audio without any API key.
Returns segments in the same {start, end, text} format as whisper.py.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


VOXPIP_CONFIG_DIR = Path.home() / ".config" / "voxpip"
VOXPIP_CONFIG_FILE = VOXPIP_CONFIG_DIR / ".env"


def _read_voxpip_env_key(name: str) -> str | None:
    if not VOXPIP_CONFIG_FILE.exists():
        return None
    try:
        for line in VOXPIP_CONFIG_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, raw = line.partition("=")
            if key.strip() != name:
                continue
            raw = raw.strip()
            if len(raw) >= 2 and raw[0] in ('"', "'") and raw[-1] == raw[0]:
                raw = raw[1:-1]
            return raw or None
    except OSError:
        return None
    return None


def _write_voxpip_env_key(name: str, value: str) -> None:
    VOXPIP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    existing = VOXPIP_CONFIG_FILE.read_text() if VOXPIP_CONFIG_FILE.exists() else ""
    lines = existing.splitlines(keepends=True)
    new_lines = [ln for ln in lines if not ln.strip().startswith(f"{name}=")]
    if new_lines and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"
    new_lines.append(f"{name}={value}\n")
    VOXPIP_CONFIG_FILE.write_text("".join(new_lines))
    try:
        VOXPIP_CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def _detect_engine() -> str:
    """Detect installed local STT engine. Returns engine name or empty string."""
    if shutil.which("voxtype"):
        return "voxtype"
    if shutil.which("whisper-cpp"):
        return "whisper-cpp"
    try:
        result = subprocess.run(
            ["python3", "-m", "mlx_whisper", "--help"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "mlx_whisper"
    except (OSError, subprocess.TimeoutExpired):
        pass
    if shutil.which("whisper"):
        return "whisper"
    return ""


def _get_engine() -> str:
    """Return cached engine name, detecting and caching if absent. Empty string = none."""
    cached = _read_voxpip_env_key("LOCAL_STT_ENGINE")
    if cached is not None:
        return cached  # may be "" (written as empty) meaning previously detected none
    engine = _detect_engine()
    _write_voxpip_env_key("LOCAL_STT_ENGINE", engine)
    return engine


def _convert_to_wav(audio_mp3: Path, wav_path: Path) -> None:
    """Convert audio file to 16 kHz mono WAV via ffmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio_mp3),
        "-ar", "16000",
        "-ac", "1",
        str(wav_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg wav conversion failed: {result.stderr.strip()}")


def _run_engine(engine: str, wav_path: Path, tmp_dir: Path) -> str:
    """Invoke the engine and return the raw transcript text."""
    if engine == "voxtype":
        result = subprocess.run(
            ["voxtype", "transcribe", str(wav_path)],
            capture_output=True, text=True, timeout=600,
        )
        return result.stdout

    if engine == "whisper-cpp":
        result = subprocess.run(
            ["whisper-cpp", "-f", str(wav_path)],
            capture_output=True, text=True, timeout=600,
        )
        return result.stdout

    if engine == "mlx_whisper":
        result = subprocess.run(
            ["python3", "-m", "mlx_whisper", str(wav_path)],
            capture_output=True, text=True, timeout=600,
        )
        return result.stdout

    if engine == "whisper":
        subprocess.run(
            [
                "whisper", str(wav_path),
                "--model", "base",
                "--output_format", "txt",
                "--output_dir", str(tmp_dir),
            ],
            capture_output=True, text=True, timeout=600, check=True,
        )
        txt_path = tmp_dir / (wav_path.stem + ".txt")
        if txt_path.exists():
            return txt_path.read_text()
        return ""

    raise ValueError(f"Unknown engine: {engine}")


def _parse_segments(raw_text: str) -> list[dict]:
    """Parse raw engine output into {start, end, text} segments.

    If the text contains no timestamps, returns a single segment at 0.0.
    """
    text = raw_text.strip()
    if not text:
        return []
    return [{"start": 0.0, "end": 0.0, "text": text}]


def transcribe_local(video_path: Path, audio_out: Path) -> list[dict]:
    """Transcribe using a locally installed STT engine.

    Returns a list of {start, end, text} segment dicts — same shape as
    whisper.py's _segments_from_response(). Returns [] on any failure.
    """
    try:
        engine = _get_engine()
        if not engine:
            return []

        with tempfile.TemporaryDirectory(prefix="local-stt-") as tmp_str:
            tmp_dir = Path(tmp_str)
            wav_path = tmp_dir / "audio.wav"

            print(f"[watch] local STT: converting audio for {engine}...", file=sys.stderr)
            _convert_to_wav(audio_out, wav_path)

            print(f"[watch] local STT: running {engine}...", file=sys.stderr)
            raw = _run_engine(engine, wav_path, tmp_dir)
            segments = _parse_segments(raw)
            print(f"[watch] local STT: {len(segments)} segment(s) via {engine}", file=sys.stderr)
            return segments

    except Exception as exc:
        print(f"[watch] local STT warning: {exc}", file=sys.stderr)
        return []
