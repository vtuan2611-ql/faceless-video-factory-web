\
from __future__ import annotations

import re
from typing import Tuple

def _first_sentence(text: str) -> str:
    text = text.strip()
    if not text:
        return "Video mới"
    # try split by punctuation
    m = re.split(r"[.!?…]\s+", text, maxsplit=1)
    return (m[0] if m else text)[:90].strip()

def make_title_and_description(script: str, style: str, keywords: str = "", shorts: bool = True) -> Tuple[str, str]:
    base = _first_sentence(script)
    # Basic hooks by style
    hook_map = {
        "Kể chuyện": "Câu chuyện ngắn",
        "Bí ẩn": "Bí mật bạn chưa biết",
        "Truyền cảm hứng": "Động lực mỗi ngày",
        "Facts": "Sự thật thú vị",
        "Review/Top list": "Top nhanh",
    }
    hook = hook_map.get(style, "Kể chuyện")
    title = base
    if len(title) < 25:
        title = f"{hook}: {title}"
    # keep it shortish
    title = title[:95].strip()

    # Description
    kw = [k.strip() for k in keywords.split(",") if k.strip()]
    tags = " ".join(f"#{re.sub(r'[^0-9A-Za-zÀ-ỹ_]+','',k).strip('_')}" for k in kw[:8])
    if shorts:
        tags = (tags + " #shorts").strip()
    desc = f"{script.strip()}\n\n{tags}".strip() + "\n"
    return title, desc
