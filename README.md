# MediaClipper Desktop

> Desktop app Python dùng để tải video/audio từ link được phép, cắt nhanh video/audio local, xuất file hoàn chỉnh rồi tự dọn file tạm.  
> Mục tiêu: người không biết lập trình vẫn cài và dùng được như phần mềm bình thường.

---

## 1. Tóm tắt dự án

**MediaClipper Desktop** là một ứng dụng desktop chạy trên máy cá nhân, phục vụ 2 nhóm công việc chính:

1. **Download video/audio từ link**
   - Hỗ trợ các link được `yt-dlp` hỗ trợ, ví dụ YouTube, TikTok, Facebook và nhiều nền tảng khác.
   - Chỉ phục vụ mục đích cá nhân/nội bộ và chỉ tải nội dung người dùng có quyền tải/sử dụng.
   - Không bypass DRM, CAPTCHA, paywall, cơ chế bảo vệ, hoặc nội dung không có quyền truy cập.

2. **Cắt/xuất video/audio nhanh**
   - Mở video/audio local hoặc file vừa download.
   - Chọn thời gian bắt đầu/kết thúc.
   - Xuất ra video MP4 hoặc audio MP3/M4A.
   - Không lưu lịch sử thao tác, không tạo thư viện video, không lưu database nặng.

Ứng dụng được thiết kế theo hướng:

```text
Mở app
→ dán link hoặc kéo file vào
→ tải/cắt/chuyển đổi
→ chọn nơi lưu file output
→ xuất xong
→ app tự xóa file tạm
```

---

## 2. Mục tiêu sản phẩm

### 2.1. Mục tiêu chính

- Tạo một desktop app đơn giản, dễ dùng, không yêu cầu người dùng cuối biết lập trình.
- Người dùng chỉ cần cài app bằng file installer, mở app và thao tác bằng giao diện.
- App phải tự bundle hoặc tự quản lý các công cụ cần thiết như `yt-dlp`, `ffmpeg`, `ffprobe`.
- Không yêu cầu người dùng cài Python, pip, FFmpeg, yt-dlp, database hoặc mở terminal.
- Tối ưu cho thao tác nhanh: tải nhanh, cắt nhanh, xuất file nhanh.
- Không lưu lịch sử để hạn chế tích lũy rác và tránh làm nặng máy.

### 2.2. Mục tiêu phụ

- Có giao diện tiếng Việt thân thiện.
- Có thông báo lỗi dễ hiểu.
- Có progress bar cho tác vụ dài.
- Có nút cancel khi đang download/export.
- Có cơ chế dọn file tạm tự động.
- Có log giới hạn dung lượng để hỗ trợ debug khi cần.

---

## 3. Đối tượng sử dụng

### 3.1. Người dùng chính

Người dùng phổ thông, không biết lập trình, muốn:

- Dán link để tải video/audio.
- Kéo thả file video/audio vào app.
- Cắt một đoạn ngắn.
- Xuất video/audio ra thư mục mong muốn.
- Mở file hoặc mở thư mục sau khi xuất xong.

### 3.2. Người phát triển/bảo trì

Người phát triển app cần:

- Build app bằng Python.
- Đóng gói thành installer Windows.
- Bundle các binary cần thiết.
- Debug lỗi thông qua log.
- Cập nhật `yt-dlp` khi các nền tảng thay đổi.

---

## 4. Nguyên tắc thiết kế sản phẩm

### 4.1. Đơn giản trước

Không biến app thành editor phức tạp kiểu CapCut. MVP chỉ tập trung vào:

```text
Download
+
Cut
+
Export
```

### 4.2. Không lưu lịch sử

Không lưu:

- Lịch sử link đã tải.
- Lịch sử file đã mở.
- Lịch sử clip đã xuất.
- Thumbnail cache dài hạn.
- Project timeline.
- Database video/clip.

Chỉ lưu tối thiểu:

- Cài đặt app.
- File output do người dùng chủ động xuất.
- File tạm trong lúc xử lý.
- Log ngắn để debug.

### 4.3. Không bắt người dùng setup kỹ thuật

Người dùng cuối không cần:

- Cài Python.
- Cài pip packages.
- Cài FFmpeg.
- Cài yt-dlp.
- Cài database.
- Chạy command line.
- Chỉnh PATH/system environment.

### 4.4. Không dùng từ kỹ thuật trong UI nếu không cần

Không nên hiện:

```text
transcode
mux
demux
codec
probe
subprocess
keyframe
```

Nên hiện:

```text
Tải video
Cắt nhanh
Cắt chính xác
Xuất MP4
Xuất audio
Mở thư mục
Thử lại
```

---

## 5. Phạm vi dự án

## 5.1. In scope

### Download

- Dán link video/audio.
- Lấy metadata cơ bản:
  - Tên video.
  - Thumbnail nếu có.
  - Thời lượng.
  - Nền tảng.
- Chọn tải:
  - Video MP4.
  - Audio MP3/M4A.
- Chọn chất lượng:
  - Best.
  - 1080p.
  - 720p.
  - Audio only.
- Hiển thị tiến độ tải.
- Cho phép hủy tải.
- Sau khi tải xong:
  - Mở file.
  - Mở thư mục.
  - Cắt tiếp file vừa tải.

### Cắt video/audio

- Kéo thả file local vào app.
- Chọn file bằng file picker.
- Preview video/audio.
- Chọn `start time`.
- Chọn `end time`.
- Có nút:
  - Đặt Start từ vị trí hiện tại.
  - Đặt End từ vị trí hiện tại.
- Chọn chế độ cắt:
  - Cắt nhanh.
  - Cắt chính xác hơn.
- Xuất ra:
  - MP4.
  - MP3.
  - M4A.
- Hiển thị tiến độ export.
- Cho phép hủy export.
- Sau khi export xong:
  - Mở file.
  - Mở thư mục.
  - Làm file khác.

### Settings

- Thư mục output mặc định.
- Định dạng video mặc định.
- Định dạng audio mặc định.
- Chất lượng tải mặc định.
- Bật/tắt tự dọn file tạm.
- Dọn file tạm ngay.
- Kiểm tra/cập nhật công cụ tải video nếu cần.
- Ngôn ngữ giao diện, mặc định Tiếng Việt.

### Packaging

- Build app thành installer Windows.
- Người dùng cuối cài như phần mềm bình thường.
- Tạo shortcut Desktop/Start Menu.
- Có uninstall entry.
- Bundle `ffmpeg`, `ffprobe`, `yt-dlp`.

---

## 5.2. Out of scope

MVP không làm:

- Web app.
- Mobile app.
- Cloud sync.
- Đăng nhập tài khoản.
- Multi-user.
- Lịch sử download.
- Lịch sử export.
- Thư viện video.
- Project editor.
- Timeline nhiều layer.
- Subtitle editor nâng cao.
- Batch download hàng trăm link.
- Auto-login social bằng username/password.
- Bypass DRM/CAPTCHA/paywall.
- Tải nội dung riêng tư nếu không có quyền hợp lệ.
- Xóa watermark như một tính năng mặc định.

---

## 6. Tech stack đề xuất

## 6.1. Stack chính

| Thành phần | Công nghệ | Lý do |
|---|---|---|
| Ngôn ngữ | Python 3.12+ | Phù hợp tool desktop/media automation, dễ gọi subprocess |
| GUI | PySide6 / Qt for Python | Framework desktop mạnh, cross-platform, UI chuyên nghiệp |
| Video/audio preview | QtMultimedia | Có API playback audio/video trong app |
| Download | yt-dlp binary | Công cụ download audio/video hỗ trợ nhiều website |
| Media processing | FFmpeg + FFprobe binary | Công cụ chuẩn để cut, convert, transcode, extract audio |
| Settings | QSettings hoặc config JSON | Lưu setting nhẹ, không cần database |
| Background task | QThread hoặc QProcess | Không làm đơ UI khi tải/xuất video |
| Logging | Python logging + RotatingFileHandler | Có log debug nhưng giới hạn dung lượng |
| Packaging | PyInstaller one-folder | Bundle app Python và dependency |
| Installer Windows | Inno Setup | Tạo file setup `.exe` cho người dùng phổ thông |

---

## 6.2. Không dùng database trong MVP

Vì app không lưu lịch sử, MVP **không cần SQLite/Postgres/MongoDB**.

Chỉ cần lưu setting rất nhẹ, ví dụ:

```json
{
  "default_output_dir": "C:/Users/User/Videos/MediaClipper",
  "default_video_format": "mp4",
  "default_audio_format": "m4a",
  "default_quality": "best",
  "auto_cleanup_temp": true,
  "language": "vi"
}
```

Có thể dùng:

- `QSettings`: hợp với app Qt desktop.
- `config.json`: dễ đọc/debug.
- `TOML/YAML`: nếu muốn config rõ ràng hơn.

Khuyến nghị MVP: **QSettings**.

---

## 6.3. Công cụ ngoài bundle kèm app

Trong bản Windows, app nên bundle:

```text
tools/windows/
├── ffmpeg.exe
├── ffprobe.exe
└── yt-dlp.exe
```

Người dùng cuối không cần cài các công cụ này.

---

## 7. Kiến trúc tổng thể

```text
MediaClipper Desktop
│
├── UI Layer
│   ├── MainWindow
│   ├── HomePage
│   ├── DownloadPanel
│   ├── CutterPanel
│   ├── ExportPanel
│   └── SettingsDialog
│
├── Application Services
│   ├── YtDlpService
│   ├── FfmpegService
│   ├── FfprobeService
│   ├── CleanupService
│   └── SettingsService
│
├── Worker Layer
│   ├── MetadataWorker
│   ├── DownloadWorker
│   └── ExportWorker
│
├── Infrastructure
│   ├── PathManager
│   ├── ToolLocator
│   ├── ProcessRunner
│   ├── Logger
│   └── TempManager
│
└── Bundled Tools
    ├── ffmpeg
    ├── ffprobe
    └── yt-dlp
```

---

## 8. Luồng nghiệp vụ tổng quát

## 8.1. Luồng tải video/audio từ link

```text
User mở app
→ Dán URL
→ Bấm "Lấy thông tin"
→ App gọi yt-dlp để lấy metadata
→ Hiển thị thumbnail/title/duration
→ User chọn Video hoặc Audio
→ User chọn chất lượng
→ User chọn thư mục output nếu muốn
→ Bấm "Tải"
→ App tạo temp working directory
→ DownloadWorker chạy yt-dlp
→ App cập nhật progress
→ Tải xong
→ Nếu cần, app dùng FFmpeg để merge/convert
→ Lưu file output vào thư mục user chọn
→ Xóa temp nếu bật auto-cleanup
→ Hiện "Mở file" / "Mở thư mục" / "Cắt tiếp"
```

---

## 8.2. Luồng cắt file local

```text
User mở app
→ Kéo thả video/audio vào app hoặc chọn file
→ App dùng ffprobe lấy metadata
→ App mở preview
→ User chọn start/end
→ User chọn output type: Video hoặc Audio
→ User chọn mode: Cắt nhanh hoặc Cắt chính xác
→ User chọn nơi lưu
→ Bấm "Xuất file"
→ ExportWorker chạy FFmpeg
→ App cập nhật progress
→ Xuất xong
→ Xóa temp nếu có
→ Hiện "Mở file" / "Mở thư mục" / "Làm file khác"
```

---

## 8.3. Luồng dọn file tạm

```text
App khởi động
→ Kiểm tra thư mục temp
→ Xóa file tạm cũ hơn 24 giờ nếu auto-cleanup bật
→ Trong quá trình dùng app, tạo temp folder theo từng task
→ Task thành công: xóa temp
→ Task bị cancel: xóa temp
→ Task bị lỗi: giữ log, xóa file tạm nếu an toàn
→ User có thể bấm "Dọn file tạm ngay"
```

---

## 8.4. Luồng lỗi

```text
Tác vụ lỗi
→ Worker trả error code + stderr
→ App map lỗi kỹ thuật thành thông báo dễ hiểu
→ UI hiển thị nguyên nhân có thể
→ User có các lựa chọn:
   - Thử lại
   - Đổi link/file
   - Cập nhật công cụ tải
   - Sao chép thông tin lỗi
   - Mở file log
```

Thông báo lỗi mẫu:

```text
Không thể tải video này.

Có thể do:
- Link không hợp lệ.
- Video riêng tư hoặc cần đăng nhập.
- Nền tảng vừa thay đổi cách tải.
- Kết nối mạng không ổn định.
- Video bị giới hạn khu vực.

Bạn có thể thử lại hoặc cập nhật công cụ tải video.
```

---

## 9. Yêu cầu nghiệp vụ chi tiết

## 9.1. Download URL

### Input

- URL do user nhập.
- Output type:
  - Video.
  - Audio.
- Quality:
  - Best.
  - 1080p.
  - 720p.
  - Audio only.
- Output folder.
- File name tùy chọn.

### Validation

- URL không được rỗng.
- URL phải có dạng hợp lệ.
- Không hỗ trợ URL local nguy hiểm như:
  - `file://`
  - `localhost`
  - IP private nếu không cần.
- Nếu link cần đăng nhập hoặc không được phép tải, app hiển thị lỗi rõ ràng.

### Output

- Video:
  - `.mp4`
- Audio:
  - `.m4a` hoặc `.mp3`

### Acceptance criteria

- Người dùng dán link và bấm tải được.
- App hiển thị tiến độ.
- Người dùng có thể hủy.
- File hoàn tất nằm đúng thư mục đã chọn.
- App không lưu link vào lịch sử.
- File tạm được dọn sau khi hoàn tất.

---

## 9.2. Cắt video

### Input

- File local hoặc file vừa download.
- Start time.
- End time.
- Output folder.
- Output format:
  - MP4.
  - M4A.
  - MP3.
- Cut mode:
  - Fast cut.
  - Exact cut.

### Validation

- File input phải tồn tại.
- Start time >= 0.
- End time > Start time.
- End time không vượt duration.
- Output path hợp lệ.
- Nếu file output trùng tên, hỏi ghi đè hoặc tự thêm suffix.

### Output

- Clip đã cắt.
- File nằm tại folder user chọn.

### Acceptance criteria

- User mở video và preview được.
- User đặt start/end dễ dàng.
- Export thành công.
- Không lưu lịch sử clip.
- Có thể mở file/thư mục sau khi export.

---

## 9.3. Cắt audio / xuất audio

### Input

- Video hoặc audio file.
- Start/end.
- Output audio format:
  - M4A.
  - MP3.

### Output

- Audio clip.

### Acceptance criteria

- Xuất audio từ video được.
- Xuất đoạn audio theo start/end được.
- Không lưu lịch sử.

---

## 9.4. Settings

### Các setting cần có

- Default output folder.
- Default video quality.
- Default video output format.
- Default audio output format.
- Auto-cleanup temp files.
- Language.
- Check/update yt-dlp.
- Log level nếu cần.

### Acceptance criteria

- Setting được lưu sau khi đóng app.
- Setting rất nhẹ, không sinh database.
- Reset setting về mặc định được.

---

## 10. Thiết kế UI/UX

## 10.1. Home screen

```text
------------------------------------------------
MediaClipper
------------------------------------------------

Bạn muốn làm gì?

[ Dán link để tải video/audio ]

URL: __________________________________ [Lấy thông tin]

hoặc

[ Kéo file video/audio vào đây để cắt ]

Thư mục lưu mặc định:
C:/Users/User/Videos/MediaClipper
[Đổi thư mục]

------------------------------------------------
```

---

## 10.2. Download panel

Sau khi lấy metadata:

```text
------------------------------------------------
Thumbnail

Tên video: ...
Thời lượng: ...

Tải dưới dạng:
(o) Video MP4
( ) Audio M4A
( ) Audio MP3

Chất lượng:
[Best] [1080p] [720p]

Tên file:
[ ten-video.mp4 ]

[ Tải ngay ]
------------------------------------------------
```

Khi đang tải:

```text
Đang tải video... 42%

[ Hủy ]
```

Sau khi tải xong:

```text
Hoàn tất

[ Mở file ]
[ Mở thư mục ]
[ Cắt tiếp video này ]
```

---

## 10.3. Cutter panel

```text
------------------------------------------------
Preview video/audio
------------------------------------------------

Start: [00:00:00.000] [Đặt từ vị trí hiện tại]
End:   [00:00:30.000] [Đặt từ vị trí hiện tại]

Chế độ cắt:
(o) Cắt nhanh
( ) Cắt chính xác hơn

Xuất ra:
(o) Video MP4
( ) Audio M4A
( ) Audio MP3

Tên file xuất:
[ my_clip.mp4 ]

[ Xuất file ]
------------------------------------------------
```

---

## 10.4. Settings dialog

```text
Settings

Thư mục lưu mặc định:
[ C:/Users/User/Videos/MediaClipper ] [Đổi]

Chất lượng tải mặc định:
[Best v]

Định dạng video mặc định:
[MP4 v]

Định dạng audio mặc định:
[M4A v]

[x] Tự xóa file tạm sau khi hoàn tất
[x] Tự xóa file tạm khi mở app

[ Dọn file tạm ngay ]
[ Cập nhật công cụ tải video ]

[ Lưu ]
```

---

## 11. Xử lý file và lưu trữ

## 11.1. Nguyên tắc

- Không lưu video trong thư mục cài app.
- Không ghi dữ liệu lớn vào `Program Files`.
- Output file do người dùng chọn nơi lưu.
- Temp file đặt trong thư mục user.
- Log được rotate để không phình to.

## 11.2. Đường dẫn gợi ý trên Windows

```text
C:\Users\<User>\Videos\MediaClipper\
├── Downloads\
└── Exports\

C:\Users\<User>\AppData\Local\MediaClipper\
├── temp\
├── logs\
└── config/
```

## 11.3. Chính sách temp

- Tạo folder riêng cho mỗi task.
- Xóa temp sau khi task thành công.
- Xóa temp sau khi user cancel.
- Khi mở app, xóa temp cũ hơn 24 giờ.
- Cho phép user bấm "Dọn file tạm ngay".

## 11.4. Chính sách log

- Dùng `RotatingFileHandler`.
- Giữ tối đa 3–5 file log.
- Mỗi file tối đa 1–5 MB.
- Không ghi thông tin nhạy cảm nếu không cần.
- Có nút "Sao chép thông tin lỗi" hoặc "Mở thư mục log".

---

## 12. Xử lý tiến trình nền

Download/export là tác vụ dài, không được chạy trực tiếp trên UI thread.

### Khuyến nghị

Dùng:

- `QThread` nếu muốn worker Python kiểm soát logic.
- `QProcess` nếu muốn chạy process ngoài và đọc stdout/stderr tốt hơn.

### Trạng thái task

MVP chỉ chạy 1 task tại một thời điểm.

```text
idle
fetching_metadata
downloading
processing
exporting
completed
failed
cancelled
```

Không cần queue nhiều job trong MVP.

---

## 13. Cắt nhanh vs cắt chính xác

## 13.1. Cắt nhanh

Mục tiêu:

- Xử lý nhanh.
- Không re-encode.
- Dung lượng/quality gần như giữ nguyên.

Ý tưởng FFmpeg:

```bash
ffmpeg -ss START -to END -i input.mp4 -c copy output.mp4
```

Lưu ý:

- Có thể lệch nhẹ theo keyframe.
- Phù hợp cắt nhanh, file dài.

UI nên ghi:

```text
Cắt nhanh: nhanh hơn, chất lượng giữ nguyên, có thể lệch nhẹ ở điểm cắt.
```

---

## 13.2. Cắt chính xác

Mục tiêu:

- Điểm cắt chính xác hơn.
- Có re-encode.

Ý tưởng FFmpeg:

```bash
ffmpeg -ss START -to END -i input.mp4 -c:v libx264 -c:a aac output.mp4
```

Lưu ý:

- Chậm hơn.
- Tốn CPU hơn.

UI nên ghi:

```text
Cắt chính xác: điểm cắt chuẩn hơn, nhưng xử lý lâu hơn.
```

---

## 14. Format output

## 14.1. Video

MVP chỉ cần:

```text
MP4 / H.264 / AAC
```

Lý do:

- Dễ mở trên Windows/macOS/mobile.
- Dễ upload lên các nền tảng phổ biến.
- Tương thích tốt với trình duyệt và app chat.

## 14.2. Audio

MVP hỗ trợ:

```text
M4A
MP3
```

Khuyến nghị mặc định:

```text
M4A
```

---

## 15. Yêu cầu phi chức năng

## 15.1. Performance

- App khởi động nhanh.
- Download/export không làm đơ UI.
- Có thể xử lý file video vài trăm MB đến vài GB tùy máy.
- Không tạo database lớn.
- Không tích lũy cache/history.

## 15.2. Usability

- Người không biết lập trình dùng được.
- Không cần terminal.
- Không cần setup môi trường.
- Lỗi phải dễ hiểu.
- Nút chức năng rõ ràng.
- Có tiếng Việt mặc định.

## 15.3. Reliability

- Nếu task fail, app không crash.
- Nếu cancel, process con phải được dừng.
- File tạm phải được dọn.
- Nếu output trùng tên, app phải hỏi hoặc tự đổi tên.
- Nếu thiếu FFmpeg/yt-dlp, app phải báo rõ hoặc tự sửa.

## 15.4. Security & Safety

- Không lưu token/cookie/password.
- Không tự động đăng nhập nền tảng social.
- Không bypass DRM/CAPTCHA/paywall.
- Không ghi log thông tin nhạy cảm.
- Validate URL trước khi gọi downloader.
- Chỉ tải nội dung người dùng có quyền tải/sử dụng.

## 15.5. Maintainability

- Tách UI, service, worker, infra.
- Không viết command FFmpeg/yt-dlp lẫn trong UI.
- Có class riêng để locate tools.
- Có class riêng để cleanup temp.
- Có logging chuẩn.
- Dễ cập nhật yt-dlp/ffmpeg.

---

## 16. Cấu trúc source code đề xuất

```text
mediaclipper/
├── pyproject.toml
├── README.md
├── src/
│   └── mediaclipper/
│       ├── __init__.py
│       ├── main.py
│       ├── app.py
│       │
│       ├── ui/
│       │   ├── main_window.py
│       │   ├── home_page.py
│       │   ├── download_panel.py
│       │   ├── cutter_panel.py
│       │   ├── export_panel.py
│       │   └── settings_dialog.py
│       │
│       ├── services/
│       │   ├── ytdlp_service.py
│       │   ├── ffmpeg_service.py
│       │   ├── ffprobe_service.py
│       │   ├── cleanup_service.py
│       │   └── settings_service.py
│       │
│       ├── workers/
│       │   ├── metadata_worker.py
│       │   ├── download_worker.py
│       │   └── export_worker.py
│       │
│       ├── infra/
│       │   ├── paths.py
│       │   ├── logger.py
│       │   ├── process_runner.py
│       │   ├── temp_manager.py
│       │   └── tool_locator.py
│       │
│       └── resources/
│           ├── icons/
│           ├── styles/
│           └── translations/
│
├── tools/
│   └── windows/
│       ├── ffmpeg.exe
│       ├── ffprobe.exe
│       └── yt-dlp.exe
│
├── packaging/
│   ├── pyinstaller/
│   │   └── mediaclipper.spec
│   └── inno/
│       └── installer.iss
│
└── tests/
    ├── test_paths.py
    ├── test_time_parser.py
    ├── test_output_naming.py
    └── test_cleanup.py
```

---

## 17. Packaging & release

## 17.1. Mục tiêu release Windows

Người dùng nhận file:

```text
MediaClipper_Setup_1.0.0.exe
```

Sau khi cài:

- Có icon Desktop.
- Có shortcut Start Menu.
- Có app trong Add/Remove Programs.
- Không cần cài thêm gì.

## 17.2. Build strategy

Khuyến nghị:

```text
PyInstaller one-folder
+
Inno Setup installer
```

Không ưu tiên `--onefile` trong MVP vì app có nhiều binary và Qt plugin.

## 17.3. Output build

```text
dist/
└── MediaClipper/
    ├── MediaClipper.exe
    ├── _internal/
    ├── tools/
    │   ├── ffmpeg.exe
    │   ├── ffprobe.exe
    │   └── yt-dlp.exe
    ├── assets/
    ├── licenses/
    └── README.txt
```

Sau đó Inno Setup đóng gói thành:

```text
MediaClipper_Setup_1.0.0.exe
```

---

## 18. Kiểm tra công cụ khi mở app

Khi app khởi động lần đầu:

```text
Đang kiểm tra công cụ xử lý video...
✓ FFmpeg sẵn sàng
✓ FFprobe sẵn sàng
✓ yt-dlp sẵn sàng
```

Nếu thiếu:

```text
Không tìm thấy công cụ xử lý video.

Bạn có thể:
[Khôi phục công cụ]
[Mở hướng dẫn]
[Thoát]
```

MVP nên bundle đủ công cụ để gần như không bao giờ gặp case này.

---

## 19. Legal / Policy boundary

App này chỉ dùng để tải/xử lý nội dung mà người dùng có quyền sử dụng.

Không hỗ trợ:

- Bypass DRM.
- Bypass CAPTCHA.
- Bypass paywall.
- Tải nội dung private trái phép.
- Tự động đăng nhập social bằng username/password.
- Thu thập cookie/token nhạy cảm.
- Xóa watermark như tính năng mặc định.

Thông báo trong app có thể ghi:

```text
Bạn chịu trách nhiệm đảm bảo mình có quyền tải và sử dụng nội dung.
Ứng dụng không hỗ trợ vượt cơ chế bảo vệ, DRM, CAPTCHA hoặc nội dung không có quyền truy cập.
```

---

## 20. Roadmap triển khai

## Phase 1 — App shell + local cutter

Mục tiêu: cắt file local ổn định trước.

Tasks:

- Tạo project Python.
- Cài PySide6.
- Tạo MainWindow.
- Tạo Home screen.
- Tạo drag-and-drop file.
- Dùng ffprobe lấy duration.
- Preview video/audio.
- Chọn start/end.
- Export MP4 bằng FFmpeg.
- Hiển thị progress.
- Cancel export.
- Dọn temp.

Deliverable:

```text
User có thể kéo video vào app, cắt đoạn, xuất MP4.
```

---

## Phase 2 — Download from URL

Mục tiêu: thêm tải video/audio.

Tasks:

- Bundle yt-dlp.
- Tạo DownloadPanel.
- Dán URL.
- Lấy metadata bằng yt-dlp.
- Hiển thị title/thumbnail/duration.
- Chọn video/audio.
- Chọn quality.
- Download file.
- Progress bar.
- Cancel download.
- Sau khi tải xong, cho phép cắt tiếp.

Deliverable:

```text
User có thể dán link, tải video/audio, rồi cắt tiếp nếu muốn.
```

---

## Phase 3 — Settings + cleanup

Mục tiêu: app nhẹ, không lưu lịch sử, không phình máy.

Tasks:

- QSettings/config.
- Default output folder.
- Auto-cleanup temp.
- Dọn temp khi mở app.
- Dọn temp bằng nút trong Settings.
- Logging rotate.
- Export log khi có lỗi.
- Reset settings.

Deliverable:

```text
App không lưu lịch sử và tự kiểm soát file tạm/log.
```

---

## Phase 4 — Packaging

Mục tiêu: người không biết lập trình cài được.

Tasks:

- PyInstaller spec.
- Bundle Qt plugins.
- Bundle tools.
- Bundle icons/assets.
- Thêm licenses.
- Tạo Inno Setup script.
- Tạo installer `.exe`.
- Test trên máy sạch không cài Python.
- Test uninstall.

Deliverable:

```text
MediaClipper_Setup_1.0.0.exe
```

---

## Phase 5 — Polish

Mục tiêu: nâng trải nghiệm người dùng.

Tasks:

- Giao diện đẹp hơn.
- Tiếng Việt hoàn chỉnh.
- Better error mapping.
- Nút cập nhật yt-dlp.
- Preset TikTok/Reels/Shorts 9:16 nếu cần.
- Export audio nhanh.
- Kiểm tra dung lượng ổ đĩa trước khi xử lý.
- Tùy chọn overwrite hoặc auto rename output.

Deliverable:

```text
App đủ thân thiện để gửi cho người dùng phổ thông.
```

---

## 21. Definition of Done cho MVP

MVP được xem là hoàn thành khi:

- App cài được bằng installer Windows.
- Máy không cài Python vẫn chạy được.
- App mở được video local.
- App preview được video/audio.
- App cắt được video local.
- App xuất được MP4.
- App dán link và lấy metadata được.
- App tải được video/audio từ link được hỗ trợ.
- App xuất được audio M4A/MP3.
- App có progress và cancel.
- App không lưu lịch sử link/file/clip.
- App tự dọn file tạm.
- App có setting output folder.
- App có log giới hạn dung lượng.
- App có thông báo lỗi dễ hiểu.
- App không crash khi link/file lỗi phổ biến.

---

## 22. Acceptance test checklist

### Local cutter

- [ ] Kéo file MP4 vào app.
- [ ] Preview chạy được.
- [ ] Set Start từ vị trí hiện tại.
- [ ] Set End từ vị trí hiện tại.
- [ ] Export MP4 thành công.
- [ ] Mở file output được.
- [ ] Output nằm đúng folder.
- [ ] Không có record history được tạo.

### Audio export

- [ ] Mở video MP4.
- [ ] Chọn xuất audio M4A.
- [ ] File audio tạo thành công.
- [ ] Chọn xuất audio MP3.
- [ ] File MP3 tạo thành công.

### Download

- [ ] Dán URL hợp lệ.
- [ ] Lấy metadata được.
- [ ] Tải video được.
- [ ] Tải audio được.
- [ ] Cancel khi đang tải hoạt động.
- [ ] Link lỗi hiển thị message dễ hiểu.

### Cleanup

- [ ] Temp được tạo khi xử lý.
- [ ] Temp được xóa sau khi thành công.
- [ ] Temp được xóa sau khi cancel.
- [ ] Temp cũ được xóa khi mở app.
- [ ] Log không vượt giới hạn dung lượng.

### Packaging

- [ ] Build bằng PyInstaller thành công.
- [ ] Installer Inno Setup chạy được.
- [ ] Cài trên máy sạch không có Python.
- [ ] App tìm được ffmpeg/ffprobe/yt-dlp.
- [ ] Uninstall sạch.

---

## 23. Rủi ro kỹ thuật

| Rủi ro | Mức độ | Cách xử lý |
|---|---:|---|
| Một số link không tải được | Cao | Báo lỗi rõ, cho cập nhật yt-dlp, chấp nhận best-effort |
| FFmpeg lỗi với file lạ | Trung bình | Dùng ffprobe trước, fallback exact cut |
| Video quá lớn làm đầy ổ | Cao | Kiểm tra dung lượng trước, temp cleanup |
| UI bị đơ khi xử lý | Cao | Luôn dùng worker/QProcess |
| Antivirus nghi ngờ file build | Trung bình | Build one-folder, tránh packer lạ, cân nhắc code signing sau |
| Qt plugin thiếu khi đóng gói | Trung bình | Test trên máy sạch, chỉnh PyInstaller spec |
| yt-dlp outdated | Cao | Nút update yt-dlp trong app |
| Người dùng không hiểu lỗi kỹ thuật | Cao | Map lỗi thành message tiếng Việt dễ hiểu |

---

## 24. Tên gọi command nội bộ

Các command này chỉ dùng trong code, không hiển thị cho user.

### Lấy metadata

```bash
yt-dlp --dump-json "<url>"
```

### Download video

```bash
yt-dlp -f "bestvideo+bestaudio/best" -o "<output_path>" "<url>"
```

### Download audio

```bash
yt-dlp -x --audio-format m4a -o "<output_path>" "<url>"
```

### Probe file

```bash
ffprobe -v error -show_format -show_streams -of json "<input_path>"
```

### Fast cut

```bash
ffmpeg -ss START -to END -i "<input_path>" -c copy "<output_path>"
```

### Exact cut

```bash
ffmpeg -ss START -to END -i "<input_path>" -c:v libx264 -c:a aac "<output_path>"
```

### Extract audio segment

```bash
ffmpeg -ss START -to END -i "<input_path>" -vn -c:a aac "<output_path>"
```

---

## 25. Ghi chú phát triển

### Ưu tiên triển khai

1. Làm local cutter trước.
2. Sau đó mới thêm downloader.
3. Sau đó mới polish UI.
4. Cuối cùng mới packaging installer.

### Không nên làm quá sớm

- Queue nhiều job.
- Timeline editor phức tạp.
- Cloud sync.
- Account/login.
- Lịch sử/library.
- Batch download lớn.

### Triết lý MVP

```text
Ít tính năng nhưng chạy chắc.
Dễ dùng hơn là nhiều option.
Không lưu lịch sử.
Không làm nặng máy.
Không bắt user setup kỹ thuật.
```

---

## 26. Tài liệu tham khảo

- PySide6 / Qt for Python: https://doc.qt.io/qtforpython-6/
- Qt Multimedia: https://doc.qt.io/qtforpython-6/PySide6/QtMultimedia/index.html
- QSettings: https://doc.qt.io/qtforpython-6.5/PySide6/QtCore/QSettings.html
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- FFmpeg documentation: https://ffmpeg.org/ffmpeg.html
- FFmpeg documentation index: https://ffmpeg.org/documentation.html
- PyInstaller: https://pyinstaller.org/
- Inno Setup: https://jrsoftware.org/ishelp/
- Python logging handlers: https://docs.python.org/3/library/logging.handlers.html

---

## 27. Chốt scope cuối cùng

**MediaClipper Desktop MVP** là:

```text
Desktop app Python
+
PySide6 UI
+
yt-dlp downloader
+
FFmpeg/FFprobe processor
+
QSettings/config nhẹ
+
không database
+
không lịch sử
+
auto-cleanup temp
+
PyInstaller + Inno Setup installer
```

Người dùng cuối chỉ cần:

```text
Cài app
→ mở app
→ dán link hoặc kéo file
→ tải/cắt/xuất
→ mở file kết quả
```

Đây là hướng phù hợp nhất cho một tool cá nhân/nội bộ: nhẹ, dễ dùng, dễ gửi cho người khác, không phụ thuộc cloud và không cần setup lập trình.
