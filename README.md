\
# Faceless Video Factory (Web Tool - No install for user)

✅ Mục tiêu: Bạn **không cần cài Python / CMD / thư viện** trên máy người dùng.  
Bạn deploy tool này lên cloud (Render/Railway). Sau đó chỉ cần **mở link web** là dùng.

Tool MVP làm được:
- Dán **kịch bản** → tự **cắt theo độ dài** (Shorts 30–60s / video 2–5 phút / tuỳ chỉnh)
- Tạo **voice MP3** bằng Google TTS (gTTS)
- Tạo **subtitles** (VTT + SRT)
- Render **video MP4** bằng **FFmpeg** (nền đơn giản + ghép voice + nhạc nền tự sinh)
- Tự tạo **title + description** cơ bản

> Lưu ý: Đây là bản MVP “chạy ổn định, dễ deploy”. Video nền đang là nền tối đơn giản để đảm bảo render nhanh & ít lỗi.
> Bạn có thể nâng cấp: ảnh nền, avatar, B-roll, hiệu ứng, burn subtitle…

---

## 1) Deploy online (khuyên dùng): Render.com (Docker)

### A. Tạo repo GitHub
1. Vào GitHub → tạo repo mới (ví dụ: `faceless-video-factory-web`)
2. Upload toàn bộ file trong project này lên repo (kéo thả trên web GitHub cũng được)

### B. Deploy lên Render
1. Tạo tài khoản Render
2. Chọn **New** → **Blueprint** (hoặc Web Service)
3. Chọn repo GitHub bạn vừa tạo
4. Render sẽ đọc `render.yaml` + `Dockerfile` và tự build
5. Chờ build xong → Render sẽ cho bạn 1 URL dạng:
   - `https://xxxx.onrender.com`

✅ Từ giờ: chỉ cần mở link đó là dùng.

---

## 2) Cách dùng
1. Mở link web
2. Dán kịch bản
3. Chọn tỉ lệ (9:16 hoặc 16:9) + độ dài
4. Bấm **Generate video**
5. Tải về:
   - `video.mp4`
   - `voice.mp3`
   - `subtitles.vtt` / `subtitles.srt`
   - `title.txt` / `description.txt`

---

## 3) Chạy local (tuỳ chọn – không bắt buộc)
Nếu bạn muốn test tại nhà (có cài Docker):
```bash
docker build -t faceless-web .
docker run -p 8501:8501 faceless-web
```
Mở: http://localhost:8501

---

## 4) Nếu gặp lỗi FFmpeg
Render (Docker) đã có ffmpeg sẵn.  
Nếu bạn dùng môi trường khác mà thiếu ffmpeg, cần cài ffmpeg vào hệ thống.

---

Chúc bạn làm kênh faceless bền vững!
