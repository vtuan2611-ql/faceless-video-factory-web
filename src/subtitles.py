\
from __future__ import annotations

import re
from typing import List, Tuple

_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")

def split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = [p.strip() for p in _SENT_SPLIT.split(text) if p.strip()]
    # Nếu quá dài mà không có dấu câu, chia theo độ dài
    out: List[str] = []
    for p in parts:
        if len(p) <= 160:
            out.append(p)
        else:
            # chunk ~120 chars
            for i in range(0, len(p), 120):
                chunk = p[i:i+120].strip()
                if chunk:
                    out.append(chunk)
    return out or [text]

def _sec_to_ts_vtt(sec: float) -> str:
    if sec < 0: sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", "," if False else ".")

def _sec_to_ts_srt(sec: float) -> str:
    if sec < 0: sec = 0.0
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    # SRT dùng dấu phẩy cho milliseconds
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

def make_vtt(segments: List[str], total_seconds: float) -> str:
    if not segments:
        segments = [""]
    if total_seconds <= 0:
        total_seconds = max(5.0, len(" ".join(segments).split()) / 2.2)

    weights = [max(1, len(seg.split())) for seg in segments]
    total_w = sum(weights) or 1
    times: List[Tuple[float, float]] = []
    cur = 0.0
    for w in weights:
        dur = total_seconds * (w / total_w)
        start, end = cur, min(total_seconds, cur + dur)
        times.append((start, end))
        cur = end

    # ensure last ends at total_seconds
    if times:
        s, _ = times[-1]
        times[-1] = (s, total_seconds)

    lines = ["WEBVTT", ""]
    for (start, end), text in zip(times, segments):
        lines.append(f"{_sec_to_ts_vtt(start)} --> {_sec_to_ts_vtt(end)}")
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"

def make_srt(segments: List[str], total_seconds: float) -> str:
    if not segments:
        segments = [""]
    if total_seconds <= 0:
        total_seconds = max(5.0, len(" ".join(segments).split()) / 2.2)

    weights = [max(1, len(seg.split())) for seg in segments]
    total_w = sum(weights) or 1
    times: List[Tuple[float, float]] = []
    cur = 0.0
    for w in weights:
        dur = total_seconds * (w / total_w)
        start, end = cur, min(total_seconds, cur + dur)
        times.append((start, end))
        cur = end
    if times:
        s, _ = times[-1]
        times[-1] = (s, total_seconds)

    out_lines = []
    for idx, ((start, end), text) in enumerate(zip(times, segments), start=1):
        out_lines.append(str(idx))
        out_lines.append(f"{_sec_to_ts_srt(start)} --> {_sec_to_ts_srt(end)}")
        out_lines.append(text)
        out_lines.append("")
    return "\n".join(out_lines).strip() + "\n"

def trim_to_target_seconds(text: str, target_seconds: int, words_per_sec: float = 2.2) -> str:
    """
    Cắt kịch bản theo độ dài mong muốn bằng ước lượng tốc độ đọc.
    """
    words = text.split()
    max_words = int(max(20, target_seconds * words_per_sec))
    if len(words) <= max_words:
        return text.strip()
    trimmed = " ".join(words[:max_words]).strip()
    # kết thúc đẹp
    if not re.search(r"[.!?…]$", trimmed):
        trimmed += "..."
    return trimmed
