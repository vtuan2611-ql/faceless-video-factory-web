\
from __future__ import annotations

import subprocess
from pathlib import Path

def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "FFmpeg failed:\n"
            + "CMD: " + " ".join(cmd) + "\n\n"
            + "STDOUT:\n" + (proc.stdout or "") + "\n"
            + "STDERR:\n" + (proc.stderr or "")
        )

def render_video_with_ffmpeg(
    out_mp4: Path,
    voice_mp3: Path,
    total_seconds: float,
    aspect: str = "9:16",
    add_music: bool = True,
    music_level: float = 0.25,
) -> None:
    """
    Tạo video nền đơn giản + ghép voice + nhạc nền (tự sinh).
    - aspect: "9:16" or "16:9"
    - total_seconds: độ dài theo voice (giây)
    """
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    # Resolution
    if aspect == "16:9":
        size = "1920x1080"
    else:
        size = "1080x1920"

    dur = max(1.0, float(total_seconds))

    # 1) Create background (solid color)
    bg = out_mp4.parent / "bg.mp4"
    _run([
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=#0b0b0b:s={size}:d={dur}:r=30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(bg),
    ])

    # 2) Generate simple "original" background music via sine chord (royalty-free)
    music = out_mp4.parent / "music.wav"
    if add_music and music_level > 0:
        # Major chord: 220Hz, 277Hz, 330Hz
        _run([
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"sine=frequency=220:duration={dur}",
            "-f", "lavfi", "-i", f"sine=frequency=277:duration={dur}",
            "-f", "lavfi", "-i", f"sine=frequency=330:duration={dur}",
            "-filter_complex", f"[0:a][1:a][2:a]amix=inputs=3:duration=longest,volume={max(0.0, float(music_level))}",
            str(music),
        ])
    else:
        music = None

    # 3) Merge bg video + voice + (optional) music
    if music and music.exists():
        _run([
            "ffmpeg", "-y",
            "-i", str(bg),
            "-i", str(voice_mp3),
            "-i", str(music),
            "-filter_complex",
            # mix voice + music (music quieter)
            "[2:a]volume=1.0[m];[1:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]",
            "-map", "0:v:0",
            "-map", "[a]",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_mp4),
        ])
    else:
        _run([
            "ffmpeg", "-y",
            "-i", str(bg),
            "-i", str(voice_mp3),
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(out_mp4),
        ])
