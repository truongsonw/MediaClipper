"""Script to download FFmpeg, FFprobe, and yt-dlp binaries for development."""

import urllib.request
import sys
import os
import stat
import zipfile
import tempfile
import shutil

# Where tools should be placed
TOOLS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tools", "windows")
os.makedirs(TOOLS_DIR, exist_ok=True)

YT_DLP_URL = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def download_file(url: str, dest: str, desc: str = "file"):
    """Download a file with progress."""
    print(f"Downloading {desc} from {url}")
    try:
        urllib.request.urlretrieve(url, dest)
        print(f"  -> {dest}")
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    return True


def main():
    # 1. Download yt-dlp
    ytdlp_path = os.path.join(TOOLS_DIR, "yt-dlp.exe")
    download_file(YT_DLP_URL, ytdlp_path, "yt-dlp")

    # 2. Download FFmpeg (essentials build)
    print(f"\nDownloading FFmpeg (this may take a while)...")
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_path = tmp.name

    success = download_file(FFMPEG_URL, tmp_path, "FFmpeg")
    if success:
        try:
            with zipfile.ZipFile(tmp_path, "r") as z:
                # Find ffmpeg.exe and ffprobe.exe in the archive
                names = z.namelist()
                for name in names:
                    if name.endswith("ffmpeg.exe"):
                        z.extract(name, TOOLS_DIR)
                        extracted = os.path.join(TOOLS_DIR, name)
                        final = os.path.join(TOOLS_DIR, "ffmpeg.exe")
                        if extracted != final:
                            shutil.move(extracted, final)
                        print(f"  -> {final}")
                    if name.endswith("ffprobe.exe"):
                        z.extract(name, TOOLS_DIR)
                        extracted = os.path.join(TOOLS_DIR, name)
                        final = os.path.join(TOOLS_DIR, "ffprobe.exe")
                        if extracted != final:
                            shutil.move(extracted, final)
                        print(f"  -> {final}")
        except Exception as e:
            print(f"  Failed to extract FFmpeg: {e}")
        finally:
            os.unlink(tmp_path)
    else:
        print("FFmpeg download failed. You may need to install it manually.")

    print("\nDone! Bundled tools are in:")
    for f in os.listdir(TOOLS_DIR):
        print(f"  {os.path.join(TOOLS_DIR, f)}")


if __name__ == "__main__":
    main()
