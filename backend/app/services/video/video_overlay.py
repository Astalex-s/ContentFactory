"""Append QR code end card to video for product link."""

from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from io import BytesIO

import qrcode
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger(__name__)

# End card dimensions (9:16 for Shorts)
ENDCARD_WIDTH = 1080
ENDCARD_HEIGHT = 1920
QR_SIZE = 400
ENDCARD_DURATION_SEC = 2.5


def _ensure_https(url: str) -> str:
    """Ensure URL has https://."""
    url = url.strip()
    if url.startswith("http://"):
        return "https://" + url[7:]
    if not url.startswith("https://"):
        return "https://" + url
    return url


def _create_endcard_image(url: str, width: int, height: int) -> bytes:
    """Create end card image with QR code and text. Returns PNG bytes."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))

    # QR size scales with video height
    qr_size = min(QR_SIZE, height // 2, width - 80)
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    qr_pil: Image.Image = qr.make_image(  # type: ignore[assignment]
        fill_color="black", back_color="white"
    )
    qr_img = qr_pil.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    qr_x = (width - qr_size) // 2
    qr_y = (height - qr_size) // 2 - 60
    img.paste(qr_img, (qr_x, qr_y))

    draw = ImageDraw.Draw(img)
    font_size = max(24, min(52, height // 35))
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    text = "Купить по ссылке"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    tx = (width - tw) // 2
    ty = qr_y + qr_size + 30
    draw.text((tx, ty), text, fill=(0, 0, 0), font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _get_video_dimensions(video_path: str) -> tuple[int, int]:
    """Get video width and height via ffprobe."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            video_path,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        return ENDCARD_WIDTH, ENDCARD_HEIGHT
    parts = result.stdout.strip().split(",")
    if len(parts) != 2:
        return ENDCARD_WIDTH, ENDCARD_HEIGHT
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return ENDCARD_WIDTH, ENDCARD_HEIGHT


def append_qr_endcard(video_bytes: bytes, marketplace_url: str | None) -> bytes:
    """
    Append 2.5 sec end card with QR code to video. Returns new video bytes.
    If marketplace_url is None/empty, returns original video unchanged.
    """
    if not marketplace_url or not marketplace_url.strip():
        return video_bytes

    url = _ensure_https(marketplace_url.strip())

    with tempfile.TemporaryDirectory() as tmp:
        video_path = os.path.join(tmp, "input.mp4")
        endcard_path = os.path.join(tmp, "endcard.png")
        endcard_video_path = os.path.join(tmp, "endcard.mp4")
        output_path = os.path.join(tmp, "output.mp4")

        with open(video_path, "wb") as f:
            f.write(video_bytes)

        width, height = _get_video_dimensions(video_path)
        endcard_img = _create_endcard_image(url, width, height)
        with open(endcard_path, "wb") as f:
            f.write(endcard_img)

        try:
            # Create 2.5 sec video from end card (match input dimensions)
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    endcard_path,
                    "-c:v",
                    "libx264",
                    "-t",
                    str(ENDCARD_DURATION_SEC),
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    "24",
                    "-vf",
                    f"scale={width}:{height}",
                    endcard_video_path,
                ],
                check=True,
                capture_output=True,
                timeout=30,
            )

            # Concat original + end card
            list_path = os.path.join(tmp, "list.txt")
            with open(list_path, "w") as f:
                f.write(f"file '{video_path}'\n")
                f.write(f"file '{endcard_video_path}'\n")

            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-f",
                    "concat",
                    "-safe",
                    "0",
                    "-i",
                    list_path,
                    "-c:v",
                    "libx264",
                    "-pix_fmt",
                    "yuv420p",
                    output_path,
                ],
                check=True,
                capture_output=True,
                timeout=60,
            )

            with open(output_path, "rb") as f:
                return f.read()

        except subprocess.CalledProcessError as e:
            log.warning("FFmpeg overlay failed: %s %s", e.stderr[:200] if e.stderr else "", e)
            return video_bytes
        except (FileNotFoundError, OSError) as e:
            log.warning("FFmpeg not available or failed: %s", e)
            return video_bytes
