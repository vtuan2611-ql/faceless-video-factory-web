\
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List

from gtts import gTTS


def list_voice_labels(lang: str = "vi") -> List[str]:
    """
    MVP: gTTS không có nhiều voice như Edge TTS.
    Trả về 1 lựa chọn để UI không bị trống.
    """
    if lang == "en":
        return ["en-Google-Standard"]
    return ["vi-Google-Standard"]


def tts_to_mp3(text: str, lang: str, out_mp3: Path) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(str(out_mp3))


def probe_audio_duration(audio_path: Path) -> float:
    """
    Dùng ffprobe để lấy độ dài (giây). Cần ffmpeg/ffprobe trên server.
    Nếu ffprobe không có, trả về 0 (caller sẽ tự xử lý).
    """
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return max(0.0, float(proc.stdout.strip()))
    except Exception:
        return 0.0
