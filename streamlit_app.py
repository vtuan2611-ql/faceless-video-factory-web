\
import os
import re
import json
import uuid
import time
import shutil
import textwrap
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

import streamlit as st

from src.tts import tts_to_mp3, list_voice_labels, probe_audio_duration
from src.subtitles import make_vtt, make_srt, split_sentences, trim_to_target_seconds
from src.video_engine import render_video_with_ffmpeg
from src.meta import make_title_and_description

APP_NAME = "Faceless Video Factory (Web - no install on user machine)"

RUNS_DIR = Path("runs")
RUNS_DIR.mkdir(exist_ok=True)

@dataclass
class GenerateOptions:
    aspect: str          # "9:16" or "16:9"
    target_seconds: int  # desired length (seconds)
    add_music: bool
    music_level: float   # 0..1
    auto_trim: bool
    lang: str            # "vi" or "en"
    voice: str

def _safe_filename(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name).strip("_")
    return name[:80] or "output"

def _write_text(path: Path, content: str):
    path.write_text(content, encoding="utf-8")

def _run_id() -> str:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{uuid.uuid4().hex[:8]}"

def _ffmpeg_exists() -> bool:
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        return True
    except Exception:
        return False

def main():
    st.set_page_config(page_title=APP_NAME, layout="wide")
    st.title("🎬 Faceless Video Factory (Web Tool)")
    st.caption("Chạy online (deploy lên cloud) • Người dùng chỉ mở link là dùng • Render video bằng FFmpeg (server-side)")

    with st.sidebar:
        st.header("⚙️ Cấu hình video")
        aspect = st.selectbox("Tỉ lệ khung hình", ["9:16 (Shorts/Reels)", "16:9 (Video dài)"], index=0)
        aspect_key = "9:16" if aspect.startswith("9:16") else "16:9"

        preset = st.selectbox("Preset độ dài", ["Shorts (45s)", "Shorts (60s)", "Video dài (120s)", "Video dài (180s)", "Tuỳ chỉnh"], index=0)
        if preset == "Shorts (45s)":
            target_seconds = 45
        elif preset == "Shorts (60s)":
            target_seconds = 60
        elif preset == "Video dài (120s)":
            target_seconds = 120
        elif preset == "Video dài (180s)":
            target_seconds = 180
        else:
            target_seconds = st.slider("Độ dài (giây)", 15, 600, 60, 5)

        auto_trim = st.checkbox("Tự cắt kịch bản theo độ dài (khuyên dùng)", value=True)
        add_music = st.checkbox("Thêm nhạc nền gốc (không bản quyền)", value=True)
        music_level = st.slider("Âm lượng nhạc nền", 0.0, 1.0, 0.25, 0.05)

        st.divider()
        st.header("🗣️ Voice")
        lang = st.selectbox("Ngôn ngữ", ["vi (Tiếng Việt)", "en (English)"], index=0)
        lang_key = "vi" if lang.startswith("vi") else "en"
        voices = list_voice_labels(lang_key)
        voice = st.selectbox("Giọng (demo)", voices, index=0)

        st.divider()
        st.caption("✅ Tool này thiết kế để chạy trên cloud (Render/Railway). Trên Streamlit Cloud cần thêm ffmpeg.")
        if not _ffmpeg_exists():
            st.warning("Server hiện tại không thấy ffmpeg. Nếu bạn deploy bằng Docker (Render/Railway) thì ffmpeg sẽ có sẵn.")
        st.caption("Tip: Nếu bạn chỉ cần subtitle, có thể bỏ render video để nhanh hơn (bản MVP này luôn render).")

    col1, col2 = st.columns([1.1, 0.9], gap="large")

    with col1:
        st.subheader("1) Nhập kịch bản")
        script = st.text_area(
            "Dán kịch bản vào đây (mỗi đoạn 1-3 câu, càng rõ càng tốt)",
            height=260,
            placeholder="Ví dụ: Hôm nay mình kể bạn nghe về một bí mật nhỏ...\nCâu chuyện bắt đầu từ..."
        )

        st.subheader("2) Tuỳ chọn style kể chuyện (tạo tiêu đề/mô tả)")
        style = st.selectbox("Style", ["Kể chuyện", "Bí ẩn", "Truyền cảm hứng", "Facts", "Review/Top list"], index=0)
        keywords = st.text_input("Từ khoá (tuỳ chọn, cách nhau bằng dấu phẩy)", value="")

        st.subheader("3) Tạo video")
        generate_btn = st.button("🚀 Generate video", type="primary", use_container_width=True)

        if generate_btn:
            if not script.strip():
                st.error("Bạn chưa nhập kịch bản.")
                st.stop()

            opts = GenerateOptions(
                aspect=aspect_key,
                target_seconds=int(target_seconds),
                add_music=bool(add_music),
                music_level=float(music_level),
                auto_trim=bool(auto_trim),
                lang=lang_key,
                voice=voice,
            )

            run_id = _run_id()
            run_dir = RUNS_DIR / run_id
            run_dir.mkdir(parents=True, exist_ok=True)

            # 1) Trim script (optional)
            final_script = script.strip()
            if opts.auto_trim:
                final_script = trim_to_target_seconds(final_script, opts.target_seconds)

            _write_text(run_dir / "script.txt", final_script)

            # 2) Title + description
            title, description = make_title_and_description(final_script, style=style, keywords=keywords, shorts=(opts.aspect=="9:16"))
            _write_text(run_dir / "title.txt", title)
            _write_text(run_dir / "description.txt", description)

            # 3) TTS -> mp3
            st.info("Đang tạo voice (mp3)...")
            voice_mp3 = run_dir / "voice.mp3"
            try:
                tts_to_mp3(final_script, lang=opts.lang, out_mp3=voice_mp3)
            except Exception as e:
                st.error(f"Tạo voice thất bại: {e}")
                st.stop()

            # 4) Subtitles
            st.info("Đang tạo subtitle (vtt/srt)...")
            dur = probe_audio_duration(voice_mp3)
            segments = split_sentences(final_script)
            vtt = make_vtt(segments, total_seconds=dur)
            srt = make_srt(segments, total_seconds=dur)
            _write_text(run_dir / "subtitles.vtt", vtt)
            _write_text(run_dir / "subtitles.srt", srt)

            # 5) Render video
            st.info("Đang render video (ffmpeg)...")
            out_mp4 = run_dir / "video.mp4"
            try:
                render_video_with_ffmpeg(
                    out_mp4=out_mp4,
                    voice_mp3=voice_mp3,
                    total_seconds=dur,
                    aspect=opts.aspect,
                    add_music=opts.add_music,
                    music_level=opts.music_level,
                )
            except Exception as e:
                st.error(f"Render video thất bại: {e}")
                st.stop()

            # 6) Meta
            meta = {
                "run_id": run_id,
                "aspect": opts.aspect,
                "target_seconds": opts.target_seconds,
                "audio_seconds": dur,
                "style": style,
                "keywords": keywords,
                "lang": opts.lang,
                "voice": opts.voice,
                "files": {
                    "video": str(out_mp4),
                    "voice": str(voice_mp3),
                    "vtt": str(run_dir / "subtitles.vtt"),
                    "srt": str(run_dir / "subtitles.srt"),
                },
            }
            (run_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

            st.success("✅ Xong! Cuộn xuống để tải file.")
            st.session_state["last_run_dir"] = str(run_dir)

    with col2:
        st.subheader("Kết quả / tải xuống")
        last_run_dir = st.session_state.get("last_run_dir")
        if not last_run_dir:
            st.info("Chưa có lần generate nào.")
        else:
            run_dir = Path(last_run_dir)
            title = (run_dir / "title.txt").read_text(encoding="utf-8")
            description = (run_dir / "description.txt").read_text(encoding="utf-8")

            st.markdown("### 🧾 Tiêu đề")
            st.code(title, language="text")

            st.markdown("### 📝 Mô tả")
            st.text_area("Description", description, height=160)

            st.markdown("### 📥 Tải file")
            for label, filename in [
                ("🎥 video.mp4", "video.mp4"),
                ("🔊 voice.mp3", "voice.mp3"),
                ("🧷 subtitles.vtt", "subtitles.vtt"),
                ("🧷 subtitles.srt", "subtitles.srt"),
                ("🗂 meta.json", "meta.json"),
                ("📄 script.txt", "script.txt"),
            ]:
                path = run_dir / filename
                if path.exists():
                    with open(path, "rb") as f:
                        st.download_button(label, data=f, file_name=filename, use_container_width=True)
            st.caption(f"📁 Thư mục: {run_dir}")

    st.divider()
    st.subheader("Deploy online (gợi ý nhanh)")
    st.markdown(
        """
**Mục tiêu:** bạn *không cần cài gì trên máy*. Bạn deploy lên Render/Railway, rồi dùng bằng link.

- Render/Railway (Docker): dễ, có sẵn FFmpeg.
- Streamlit Cloud: được nhưng cần thêm `packages.txt` để cài `ffmpeg`.

Xem file `README.md` trong project để làm từng bước.
        """
    )

if __name__ == "__main__":
    main()
