from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "clients/browser-extension/common/icons"
STORE_DIR = ROOT / "store-assets/browser-extension"

BG = (246, 248, 247, 255)
TEAL = (15, 83, 74, 255)
TEAL_2 = (77, 137, 126, 255)
WHITE = (255, 255, 255, 255)
DARK = (24, 39, 36, 255)


def canvas(width: int, height: int, color=(0, 0, 0, 0)) -> bytearray:
    return bytearray(color * (width * height))


def set_px(buf: bytearray, width: int, x: int, y: int, color) -> None:
    if x < 0 or y < 0 or x >= width:
        return
    i = (y * width + x) * 4
    if i < 0 or i + 4 > len(buf):
        return
    buf[i : i + 4] = bytes(color)


def disk(buf: bytearray, width: int, height: int, cx: float, cy: float, r: float, color) -> None:
    x0, x1 = max(0, int(cx-r)), min(width-1, int(cx+r))
    y0, y1 = max(0, int(cy-r)), min(height-1, int(cy+r))
    rr = r * r
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if (x-cx) ** 2 + (y-cy) ** 2 <= rr:
                set_px(buf, width, x, y, color)


def line(buf: bytearray, width: int, height: int, x1: float, y1: float, x2: float, y2: float, thick: float, color) -> None:
    steps = max(1, int(max(abs(x2-x1), abs(y2-y1)) * 2))
    for n in range(steps + 1):
        t = n / steps
        disk(buf, width, height, x1+(x2-x1)*t, y1+(y2-y1)*t, thick/2, color)


def rect(buf: bytearray, width: int, height: int, x0: int, y0: int, x1: int, y1: int, color) -> None:
    for y in range(max(0, y0), min(height, y1)):
        for x in range(max(0, x0), min(width, x1)):
            set_px(buf, width, x, y, color)


def png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def save_png(path: Path, width: int, height: int, buf: bytearray) -> None:
    raw = b"".join(b"\x00" + bytes(buf[y*width*4:(y+1)*width*4]) for y in range(height))
    payload = (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + png_chunk(b"IDAT", zlib.compress(raw, 9))
        + png_chunk(b"IEND", b"")
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def draw_mark(buf: bytearray, width: int, height: int, cx: float, cy: float, diameter: float) -> None:
    r = diameter / 2
    disk(buf, width, height, cx, cy, r, TEAL)
    s = diameter
    thick = max(2, s * 0.075)
    pts = [(-0.23,-0.14),(-0.12,0.20),(0.0,-0.01),(0.12,0.20),(0.23,-0.14)]
    points = [(cx + x*s, cy + y*s) for x, y in pts]
    for (x1,y1),(x2,y2) in zip(points, points[1:]):
        line(buf, width, height, x1,y1,x2,y2,thick,WHITE)


FONT = {
    "A": ["01110","10001","10001","11111","10001","10001","10001"],
    "C": ["01111","10000","10000","10000","10000","10000","01111"],
    "E": ["11111","10000","10000","11110","10000","10000","11111"],
    "F": ["11111","10000","10000","11110","10000","10000","10000"],
    "I": ["11111","00100","00100","00100","00100","00100","11111"],
    "M": ["10001","11011","10101","10101","10001","10001","10001"],
    "N": ["10001","11001","10101","10011","10001","10001","10001"],
    "O": ["01110","10001","10001","10001","10001","10001","01110"],
    "R": ["11110","10001","10001","11110","10100","10010","10001"],
    "S": ["01111","10000","10000","01110","00001","00001","11110"],
    "T": ["11111","00100","00100","00100","00100","00100","00100"],
    "V": ["10001","10001","10001","10001","10001","01010","00100"],
    "W": ["10001","10001","10001","10101","10101","10101","01010"],
    "D": ["11110","10001","10001","10001","10001","10001","11110"],
}


def text5x7(buf: bytearray, width: int, height: int, text: str, x: int, y: int, scale: int, color) -> None:
    cursor = x
    for ch in text:
        if ch == " ":
            cursor += 4 * scale
            continue
        glyph = FONT[ch]
        for gy, row in enumerate(glyph):
            for gx, bit in enumerate(row):
                if bit == "1":
                    rect(buf, width, height,
                         cursor + gx*scale, y + gy*scale,
                         cursor + (gx+1)*scale, y + (gy+1)*scale, color)
        cursor += 6 * scale


def build() -> None:
    for size in (16, 32, 48, 128):
        buf = canvas(size, size)
        draw_mark(buf, size, size, size/2, size/2, size*0.75)
        save_png(ICON_DIR / f"wa-{size}.png", size, size, buf)

    logo_size = 300
    logo = canvas(logo_size, logo_size, BG)
    draw_mark(logo, logo_size, logo_size, logo_size/2, logo_size/2, logo_size*0.72)
    save_png(STORE_DIR / "logo-300x300.png", logo_size, logo_size, logo)

    w, h = 440, 280
    buf = canvas(w, h, BG)
    draw_mark(buf, w, h, 110, 140, 136)
    text5x7(buf, w, h, "WA COMMONS", 200, 88, 4, DARK)
    text5x7(buf, w, h, "EVIDENCE FIRST", 200, 142, 2, TEAL_2)
    rect(buf, w, h, 200, 185, 378, 190, TEAL)
    save_png(STORE_DIR / "small-promo-440x280.png", w, h, buf)


if __name__ == "__main__":
    build()
