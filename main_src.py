#!/usr/bin/env python3
"""One Day in the World - Friday, 27 November 2026.

Draws a newspaper front page summing up the day's world news and writes
it to /output/entry.png. Pure standard library: the PNG is encoded by hand
(zlib + struct) and the text is set with a built-in 5x7 bitmap font, so the
program is fully deterministic and needs no network.
Run main() to render the page; the PNG lands as entry.png inside the
directory named by MAKEFUN_OUTPUT_DIR, or /output when that is unset.
"""
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (247, 243, 232)
INK = (20, 20, 24)
NAVY = (20, 36, 62)
GOLD = (198, 158, 62)
RED = (178, 34, 34)
TEAL = (14, 110, 110)
ORANGE = (214, 106, 24)
GREY = (90, 90, 96)
LIGHT = (238, 232, 216)
WHITE = (255, 255, 255)
GREEN = (46, 160, 90)

# ---------------------------------------------------------------- font ----
# 5x7 bitmap font, each glyph is 7 rows of 5 bits ("1" = ink).
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10011", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10011", "10101", "11001", "10001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "00100", "00100", "00100"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "01100", "01000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "(": ("00011", "00100", "01000", "01000", "01000", "00100", "00011"),
    ")": ("11000", "00100", "00010", "00010", "00010", "00100", "11000"),
    "'": ("00100", "00100", "00100", "00000", "00000", "00000", "00000"),
    "&": ("01110", "10001", "10001", "01010", "10100", "10011", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
}

# ------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, c)

    def border(self, x, y, w, h, c, t=2):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def hline(self, x0, x1, y, c, t=1):
        for yy in range(y, y + t):
            for xx in range(x0, x1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        for xx in range(x, x + t):
            for yy in range(y0, y1):
                self.set(xx, yy, c)

    def circle(self, cx, cy, r, c):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, c)

    def ring(self, cx, cy, r, c, t=3):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d <= (r + t) ** 2:
                    self.set(xx, yy, c)

    def tri(self, ax, ay, bx, by, cx, cy, c):
        # Filled triangle via scanline fill, vertices sorted by y.
        pts = sorted([(ax, ay), (bx, by), (cx, cy)], key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        for y in range(y0, y2 + 1):
            if y <= y1:
                xa = x0 + (x1 - x0) * (y - y0) / max(1, y1 - y0)
            else:
                xa = x1 + (x2 - x1) * (y - y1) / max(1, y2 - y1)
            xb = x0 + (x2 - x0) * (y - y0) / max(1, y2 - y0)
            for x in range(int(min(xa, xb)), int(max(xa, xb)) + 1):
                self.set(x, y, c)

    def text(self, x, y, s, scale, c):
        s = s.upper()
        cx = x
        for ch in s:
            g = FONT.get(ch, FONT[" "])
            for r in range(7):
                row = g[r]
                for col in range(5):
                    if row[col] == "1":
                        self.rect(cx + col * scale, y + r * scale, scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale - scale

    def center(self, y, s, scale, c, x0=0, x1=None):
        x1 = x1 if x1 is not None else self.w
        w = self.text_w(s, scale)
        self.text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)

    def wrap(self, x, y, max_w, s, scale, c, lh=None):
        lh = lh if lh is not None else 9 * scale
        words = s.split(" ")
        lines, cur = [], ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if self.text_w(trial, scale) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
        for ln in lines:
            self.text(x, y, ln, scale, c)
            y += lh
        return y


def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


# -------------------------------------------------------------- icons -----
def icon_missile(cv, x, y, s):
    # a rocket climbing, with flame
    cv.tri(x + 55 * s // 10, y, x + 75 * s // 10, y + 20 * s // 10,
           x + 35 * s // 10, y + 20 * s // 10, RED)
    cv.rect(x + 35 * s // 10, y + 18 * s // 10, 40 * s // 10, 55 * s // 10, INK)
    cv.rect(x + 45 * s // 10, y + 30 * s // 10, 20 * s // 10, 12 * s // 10, WHITE)
    cv.tri(x + 35 * s // 10, y + 60 * s // 10, x + 20 * s // 10, y + 85 * s // 10,
           x + 35 * s // 10, y + 85 * s // 10, RED)
    cv.tri(x + 75 * s // 10, y + 60 * s // 10, x + 90 * s // 10, y + 85 * s // 10,
           x + 75 * s // 10, y + 85 * s // 10, RED)
    cv.tri(x + 45 * s // 10, y + 73 * s // 10, x + 55 * s // 10, y + 105 * s // 10,
           x + 65 * s // 10, y + 73 * s // 10, ORANGE)
    cv.tri(x + 50 * s // 10, y + 73 * s // 10, x + 55 * s // 10, y + 95 * s // 10,
           x + 60 * s // 10, y + 73 * s // 10, GOLD)


def icon_globe(cv, x, y, s):
    cx, cy, r = x + 50 * s // 10, y + 50 * s // 10, 42 * s // 10
    cv.circle(cx, cy, r, TEAL)
    cv.circle(cx - 12 * s // 10, cy - 10 * s // 10, 14 * s // 10, GREEN)
    cv.circle(cx + 14 * s // 10, cy + 12 * s // 10, 10 * s // 10, GREEN)
    cv.ring(cx, cy, r, NAVY, 3)
    cv.vline(cx, cy - r, cy + r, NAVY, 2)
    cv.hline(cx - r, cx + r, cy, NAVY, 2)


def icon_flame(cv, x, y, s):
    cv.tri(x + 50 * s // 10, y, x + 20 * s // 10, y + 55 * s // 10,
           x + 80 * s // 10, y + 55 * s // 10, ORANGE)
    cv.circle(x + 50 * s // 10, y + 55 * s // 10, 30 * s // 10, ORANGE)
    cv.tri(x + 50 * s // 10, y + 30 * s // 10, x + 35 * s // 10, y + 60 * s // 10,
           x + 65 * s // 10, y + 60 * s // 10, RED)
    cv.circle(x + 50 * s // 10, y + 60 * s // 10, 15 * s // 10, RED)
    cv.rect(x + 15 * s // 10, y + 88 * s // 10, 70 * s // 10, 6 * s // 10, INK)
    cv.rect(x + 25 * s // 10, y + 78 * s // 10, 50 * s // 10, 10 * s // 10, INK)


def icon_cloud(cv, x, y, s):
    # storm cloud with rain
    cv.circle(x + 35 * s // 10, y + 45 * s // 10, 22 * s // 10, NAVY)
    cv.circle(x + 60 * s // 10, y + 38 * s // 10, 26 * s // 10, NAVY)
    cv.circle(x + 78 * s // 10, y + 50 * s // 10, 18 * s // 10, NAVY)
    cv.rect(x + 15 * s // 10, y + 45 * s // 10, 80 * s // 10, 22 * s // 10, NAVY)
    for i in range(4):
        xx = x + (22 + i * 20) * s // 10
        cv.rect(xx, y + 75 * s // 10, 5 * s // 10, 16 * s // 10, TEAL)


def icon_star(cv, x, y, s):
    # four-point burst
    cx, cy = x + 50 * s // 10, y + 50 * s // 10
    cv.tri(cx, y, cx + 14 * s // 10, cy - 8 * s // 10,
           cx - 14 * s // 10, cy - 8 * s // 10, GOLD)
    cv.tri(cx, y + 100 * s // 10, cx + 14 * s // 10, cy + 8 * s // 10,
           cx - 14 * s // 10, cy + 8 * s // 10, GOLD)
    cv.tri(x, cy, cx - 8 * s // 10, cy - 14 * s // 10,
           cx - 8 * s // 10, cy + 14 * s // 10, GOLD)
    cv.tri(x + 100 * s // 10, cy, cx + 8 * s // 10, cy - 14 * s // 10,
           cx + 8 * s // 10, cy + 14 * s // 10, GOLD)
    cv.circle(cx, cy, 12 * s // 10, RED)


def icon_ship(cv, x, y, s):
    # cargo ship on waves
    cv.rect(x + 45 * s // 10, y + 8 * s // 10, 6 * s // 10, 34 * s // 10, INK)
    cv.tri(x + 51 * s // 10, y + 10 * s // 10, x + 78 * s // 10, y + 30 * s // 10,
           x + 51 * s // 10, y + 30 * s // 10, RED)
    cv.rect(x + 12 * s // 10, y + 42 * s // 10, 76 * s // 10, 26 * s // 10, NAVY)
    cv.rect(x + 30 * s // 10, y + 50 * s // 10, 10 * s // 10, 10 * s // 10, GOLD)
    cv.rect(x + 52 * s // 10, y + 50 * s // 10, 10 * s // 10, 10 * s // 10, GOLD)
    cv.tri(x + 8 * s // 10, y + 68 * s // 10, x + 92 * s // 10, y + 68 * s // 10,
           x + 50 * s // 10, y + 92 * s // 10, TEAL)
    cv.rect(x + 5 * s // 10, y + 96 * s // 10, 90 * s // 10, 4 * s // 10, TEAL)


def icon_tag(cv, x, y, s):
    # price tag
    cv.tri(x + 12 * s // 10, y + 12 * s // 10, x + 45 * s // 10, y + 12 * s // 10,
           x + 88 * s // 10, y + 55 * s // 10, ORANGE)
    cv.tri(x + 12 * s // 10, y + 12 * s // 10, x + 88 * s // 10, y + 55 * s // 10,
           x + 88 * s // 10, y + 88 * s // 10, ORANGE)
    cv.tri(x + 12 * s // 10, y + 12 * s // 10, x + 12 * s // 10, y + 45 * s // 10,
           x + 45 * s // 10, y + 88 * s // 10, ORANGE)
    cv.rect(x + 12 * s // 10, y + 45 * s // 10, 76 * s // 10, 43 * s // 10, ORANGE)
    cv.circle(x + 28 * s // 10, y + 28 * s // 10, 7 * s // 10, WHITE)
    cv.rect(x + 45 * s // 10, y + 55 * s // 10, 30 * s // 10, 6 * s // 10, WHITE)
    cv.rect(x + 45 * s // 10, y + 68 * s // 10, 20 * s // 10, 6 * s // 10, WHITE)


# -------------------------------------------------------------- page ------
def draw():
    cv = Canvas(W, H, PAPER)
    # masthead
    cv.rect(0, 0, W, 118, NAVY)
    cv.hline(0, W, 118, GOLD, 4)
    cv.center(14, "THE WORLD TODAY", 6, WHITE)
    cv.center(76, "FRIDAY 27 NOVEMBER 2026", 3, GOLD)
    cv.center(100, "VOL. I  -  NO. 331  -  PRICE FREE", 2, GOLD)
    # lead story
    cv.rect(24, 134, 976, 252, WHITE)
    cv.border(24, 134, 976, 252, INK, 3)
    cv.rect(24, 134, 976, 34, RED)
    cv.text(40, 143, "LEAD STORY  -  UKRAINE", 2, WHITE)
    cv.wrap(44, 188, 640, "ZELENSKYY WARNS OF NEW STRIKE ON POWER GRID", 4, INK, lh=40)
    cv.wrap(44, 292, 640,
            "Kyiv braces as Russia is poised to hit energy sites again; EU "
            "leaders split over a 45-billion-euro loan for Ukraine next year.",
            2, GREY, lh=20)
    icon_missile(cv, 760, 190, 10)
    # row 2
    row2(cv)
    # row 3
    row3(cv)
    # bottom strip
    cv.rect(24, 940, 976, 76, NAVY)
    cv.wrap(40, 948, 940,
            "ALSO TODAY:  TUBE STRIKES BEGIN IN LONDON  -  STEELERS CUT "
            "AARON RODGERS  -  HONG KONG TOWER FIRE: ONE YEAR ON  -  "
            "14 DEAD IN INDONESIA MINE FLOOD  -  EU LEADERS SEEK BUDGET "
            "DEAL  -  F-16 SALE TO UKRAINE OKAYED",
            2, WHITE, lh=20)
    # Gold frame around the whole front page, drawn last so it sits on top.
    cv.border(0, 0, W, H, GOLD, 4)
    return cv


def panel(cv, x, y, w, h, kicker, headline, body, icon):
    cv.rect(x, y, w, h, WHITE)
    cv.border(x, y, w, h, INK, 2)
    cv.rect(x, y, w, 30, NAVY)
    cv.text(x + 12, y + 8, kicker, 2, WHITE)
    yy = cv.wrap(x + 14, y + 44, w - 28, headline, 3, INK, lh=30)
    cv.wrap(x + 14, yy + 6, w - 28, body, 2, GREY, lh=19)
    icon(cv, x + w - 95, y + h - 82, 7)


def row2(cv):
    y, h, w, gap = 400, 256, 312, 20
    panel(cv, 24, y, w, h, "MIDDLE EAST",
          "ISRAELI STRIKES KILL 7 IN GAZA",
          "Deputy education minister among the dead.",
          icon_globe)
    panel(cv, 24 + w + gap, y, w, h, "EGYPT",
          "CAIRO TANKER FIRE KILLS 30",
          "Fuel truck overturns on a crowded highway.",
          icon_flame)
    panel(cv, 24 + 2 * (w + gap), y, w, h, "UNITED STATES",
          "THANKSGIVING STORM HITS US",
          "Parade postponed for the first time in a century.",
          icon_cloud)


def row3(cv):
    y, h, w, gap = 672, 260, 312, 20
    panel(cv, 24, y, w, h, "NORTH KOREA",
          "KIM VOWS MORE WARHEADS",
          "Pyongyang expands nuclear arsenal, state media says.",
          icon_star)
    panel(cv, 24 + w + gap, y, w, h, "GULF / RED SEA",
          "HOUTHIS HIT SAUDI REFINERY",
          "Rocket hits refinery; shipping on edge.",
          icon_ship)
    panel(cv, 24 + 2 * (w + gap), y, w, h, "TRADE",
          "VIETNAM RACES FOR US DEAL",
          "US tariffs of up to 35% loom over exports.",
          icon_tag)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
