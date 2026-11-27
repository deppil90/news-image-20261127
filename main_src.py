"""One Day in the World - Friday, 27 November 2026.

A program that draws a one-page newspaper front page summing up the
world news of 27 November 2026 and writes it to /output/entry.png.
Pure Python standard library, no network, no clock, no randomness:
every run writes the same bytes.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024
PAPER = (248, 246, 239)
INK = (17, 17, 17)
RED = (163, 18, 26)
GREY = (68, 68, 68)

# 5x7 bitmap font, written from scratch. Each glyph is 7 rows; each row
# is a 5-bit mask, bit 4 is the leftmost column. Only capitals, digits
# and punctuation are needed: all text is rendered in capitals.
FONT = {
    "A": (0x0E, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "B": (0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E),
    "C": (0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E),
    "D": (0x1E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1E),
    "E": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F),
    "F": (0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x10),
    "G": (0x0E, 0x11, 0x10, 0x17, 0x11, 0x11, 0x0F),
    "H": (0x11, 0x11, 0x11, 0x1F, 0x11, 0x11, 0x11),
    "I": (0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "J": (0x07, 0x02, 0x02, 0x02, 0x02, 0x12, 0x0C),
    "K": (0x11, 0x12, 0x14, 0x18, 0x14, 0x12, 0x11),
    "L": (0x10, 0x10, 0x10, 0x10, 0x10, 0x10, 0x1F),
    "M": (0x11, 0x1B, 0x15, 0x15, 0x11, 0x11, 0x11),
    "N": (0x11, 0x19, 0x15, 0x13, 0x11, 0x11, 0x11),
    "O": (0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "P": (0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10),
    "Q": (0x0E, 0x11, 0x11, 0x11, 0x15, 0x12, 0x0D),
    "R": (0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11),
    "S": (0x0F, 0x10, 0x10, 0x0E, 0x01, 0x01, 0x1E),
    "T": (0x1F, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04),
    "U": (0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E),
    "V": (0x11, 0x11, 0x11, 0x11, 0x11, 0x0A, 0x04),
    "W": (0x11, 0x11, 0x11, 0x15, 0x15, 0x15, 0x0A),
    "X": (0x11, 0x11, 0x0A, 0x04, 0x0A, 0x11, 0x11),
    "Y": (0x11, 0x11, 0x0A, 0x04, 0x04, 0x04, 0x04),
    "Z": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x10, 0x1F),
    "0": (0x0E, 0x11, 0x13, 0x15, 0x19, 0x11, 0x0E),
    "1": (0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E),
    "2": (0x0E, 0x11, 0x01, 0x06, 0x08, 0x10, 0x1F),
    "3": (0x1F, 0x02, 0x04, 0x02, 0x01, 0x11, 0x0E),
    "4": (0x02, 0x06, 0x0A, 0x12, 0x1F, 0x02, 0x02),
    "5": (0x1F, 0x10, 0x1E, 0x01, 0x01, 0x11, 0x0E),
    "6": (0x06, 0x08, 0x10, 0x1E, 0x11, 0x11, 0x0E),
    "7": (0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08),
    "8": (0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E),
    "9": (0x0E, 0x11, 0x11, 0x0F, 0x01, 0x02, 0x0C),
    " ": (0, 0, 0, 0, 0, 0, 0),
    ".": (0, 0, 0, 0, 0, 0x0C, 0x0C),
    ",": (0, 0, 0, 0, 0x0C, 0x04, 0x08),
    ";": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0x08),
    ":": (0, 0x0C, 0x0C, 0, 0x0C, 0x0C, 0),
    "!": (0x04, 0x04, 0x04, 0x04, 0x04, 0x00, 0x04),
    "?": (0x0E, 0x11, 0x01, 0x02, 0x04, 0x00, 0x04),
    "-": (0, 0, 0, 0x1F, 0, 0, 0),
    "'": (0x04, 0x04, 0x08, 0, 0, 0, 0),
    "/": (0x01, 0x01, 0x02, 0x04, 0x08, 0x10, 0x10),
    "(": (0x02, 0x04, 0x08, 0x08, 0x08, 0x04, 0x02),
    ")": (0x08, 0x04, 0x02, 0x02, 0x02, 0x04, 0x08),
    "&": (0x0C, 0x12, 0x14, 0x08, 0x15, 0x12, 0x0D),
    "%": (0x19, 0x19, 0x02, 0x04, 0x08, 0x13, 0x13),
    "$": (0x04, 0x0F, 0x14, 0x0E, 0x05, 0x1E, 0x04),
    "+": (0, 0x04, 0x04, 0x1F, 0x04, 0x04, 0),
    "=": (0, 0, 0x1F, 0, 0x1F, 0, 0),
    '"': (0x0A, 0x0A, 0x0A, 0, 0, 0, 0),
}


def glyph(ch):
    """Return the 7 row masks for a character, blank for anything unknown."""
    return FONT.get(ch, FONT[" "])


class Canvas:
    """A plain RGB canvas backed by one bytearray, with small drawing tools."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * w * h)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, rw, rh, c):
        for yy in range(y, y + rh):
            if 0 <= yy < self.h:
                lo = max(x, 0)
                hi = min(x + rw, self.w)
                for xx in range(lo, hi):
                    i = (yy * self.w + xx) * 3
                    self.px[i:i + 3] = bytes(c)

    def hline(self, x, y, length, c, t=1):
        self.rect(x, y, length, t, c)

    def vline(self, x, y, length, c, t=1):
        self.rect(x, y, t, length, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham line, one pixel wide."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def thick_line(self, x0, y0, x1, y1, c, t=3):
        """A line drawn with a square brush, for bold strokes."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = t // 2
        while True:
            self.rect(x0 - half, y0 - half, t, t, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def circle(self, cx, cy, r, c):
        """Midpoint circle outline."""
        x = 0
        y = r
        d = 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.set(px, py, c)
            x += 1
            if d < 0:
                d += 2 * x + 1
            else:
                y -= 1
                d += 2 * (x - y) + 1

    def fill_circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = math.isqrt(r * r - dy * dy)
            self.hline(cx - dx, cy + dy, 2 * dx + 1, c)

    def fill_triangle(self, p0, p1, p2, c):
        """Scanline-filled triangle from three (x, y) points."""
        pts = sorted((p0, p1, p2), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts
        if y0 == y2:
            return
        def edge_x(xa, ya, xb, yb, y):
            if yb == ya:
                return xa
            return xa + (xb - xa) * (y - ya) / (yb - ya)
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = edge_x(x0, y0, x1, y1, y)
                xb = edge_x(x0, y0, x2, y2, y)
            else:
                xa = edge_x(x1, y1, x2, y2, y)
                xb = edge_x(x0, y0, x2, y2, y)
            lo = int(min(xa, xb))
            hi = int(max(xa, xb))
            self.hline(lo, y, hi - lo + 1, c)

    def text(self, x, y, s, scale, c):
        """Draw text in capitals at scale; each glyph is 5x7, advance 6."""
        cx = x
        for ch in s.upper():
            rows = glyph(ch)
            for r in range(7):
                bits = rows[r]
                for col in range(5):
                    if (bits >> (4 - col)) & 1:
                        self.rect(cx + col * scale, y + r * scale,
                                  scale, scale, c)
            cx += 6 * scale
        return cx

    def text_w(self, s, scale):
        return len(s) * 6 * scale

    def center_text(self, y, s, scale, c):
        x = (self.w - self.text_w(s, scale)) // 2
        self.text(x, y, s, scale, c)

    def wrap(self, s, max_w, scale):
        """Greedy word wrap; returns a list of lines that fit max_w."""
        words = s.split(" ")
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if self.text_w(trial, scale) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
                while self.text_w(cur, scale) > max_w:
                    cut = max_w // (6 * scale)
                    lines.append(cur[:cut])
                    cur = cur[cut:]
        if cur:
            lines.append(cur)
        return lines


def _chunk(kind, data):
    return (struct.pack(">I", len(data)) + kind + data +
            struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF))


def save_png(cv, path):
    """Write the canvas as a deterministic RGB PNG (filter 0, level 6)."""
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw.extend(cv.px[y * cv.w * 3:(y + 1) * cv.w * 3])
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", ihdr) +
           _chunk(b"IDAT", zlib.compress(bytes(raw), 6)) +
           _chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


# ---- small drawn icons (each fits a ~44x44 box at the given corner) ----

def icon_flame(cv, x, y, s, c):
    cv.fill_triangle((x + 22 * s, y + 2 * s), (x + 2 * s, y + 40 * s),
                     (x + 42 * s, y + 40 * s), c)
    cv.fill_triangle((x + 22 * s, y + 18 * s), (x + 12 * s, y + 40 * s),
                     (x + 32 * s, y + 40 * s), PAPER)


def icon_derrick(cv, x, y, s, c):
    cv.line(x + 6 * s, y + 44 * s, x + 20 * s, y + 4 * s, c)
    cv.line(x + 38 * s, y + 44 * s, x + 24 * s, y + 4 * s, c)
    cv.line(x + 11 * s, y + 30 * s, x + 33 * s, y + 30 * s, c)
    cv.line(x + 15 * s, y + 16 * s, x + 29 * s, y + 16 * s, c)
    cv.rect(x + 18 * s, y + 2 * s, 8 * s, 4 * s, c)
    cv.hline(x, y + 44 * s, 44 * s, c)


def icon_cloud(cv, x, y, s, c):
    cv.fill_circle(x + 14 * s, y + 18 * s, 10 * s, c)
    cv.fill_circle(x + 26 * s, y + 14 * s, 12 * s, c)
    cv.fill_circle(x + 34 * s, y + 20 * s, 9 * s, c)
    cv.rect(x + 6 * s, y + 20 * s, 34 * s, 10 * s, c)
    for dx in (8, 20, 32):
        cv.line(x + dx * s, y + 34 * s, x + (dx - 2) * s, y + 42 * s, c)


def icon_atom(cv, x, y, s, c):
    cx, cy = x + 22 * s, y + 22 * s
    cv.circle(cx, cy, 16 * s, c)
    cv.line(cx - 16 * s, cy, cx + 16 * s, cy, c)
    cv.line(cx - 11 * s, cy - 11 * s, cx + 11 * s, cy + 11 * s, c)
    cv.line(cx + 11 * s, cy - 11 * s, cx - 11 * s, cy + 11 * s, c)
    cv.fill_circle(cx, cy, 3 * s, c)


def icon_train(cv, x, y, s, c):
    cv.rect(x + 2 * s, y + 6 * s, 40 * s, 24 * s, c)
    for wx in (6, 18, 30):
        cv.rect(x + wx * s, y + 12 * s, 8 * s, 8 * s, PAPER)
    cv.fill_circle(x + 12 * s, y + 34 * s, 4 * s, c)
    cv.fill_circle(x + 32 * s, y + 34 * s, 4 * s, c)
    cv.hline(x, y + 40 * s, 44 * s, c)


def icon_microbe(cv, x, y, s, c):
    cx, cy = x + 22 * s, y + 22 * s
    cv.circle(cx, cy, 12 * s, c)
    for k in range(8):
        a = k * math.pi / 4
        x0 = cx + int(12 * s * math.cos(a))
        y0 = cy + int(12 * s * math.sin(a))
        x1 = cx + int(19 * s * math.cos(a))
        y1 = cy + int(19 * s * math.sin(a))
        cv.line(x0, y0, x1, y1, c)
    cv.fill_circle(cx - 4 * s, cy - 3 * s, 2 * s, c)
    cv.fill_circle(cx + 5 * s, cy + 4 * s, 2 * s, c)


def draw_pylon(cv, x, y, w, h, c):
    """A power pylon: two legs, three cross-arms, a small top."""
    top_l = x + w // 2 - 6
    top_r = x + w // 2 + 6
    cv.line(x + 8, y + h, top_l, y, c)
    cv.line(x + w - 8, y + h, top_r, y, c)
    for f, span in ((0.30, 0.62), (0.55, 0.44), (0.80, 0.26)):
        yy = y + int(h * f)
        half = int(w * span / 2)
        cv.hline(x + w // 2 - half, yy, 2 * half, c)
    cv.rect(top_l - 2, y - 6, top_r - top_l + 4, 6, c)


def draw_bolt(cv, x, y, s, c):
    """A lightning bolt outline, drawn as a zigzag path."""
    pts = [(22, 0), (8, 20), (16, 20), (4, 44), (24, 16), (16, 16)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
        cv.thick_line(x + ax * s, y + ay * s, x + bx * s, y + by * s, c, 3)


def draw_skyline(cv, x, y, w, h, c):
    """A row of buildings with lit windows, sitting on the baseline y+h."""
    heights = [0.55, 0.80, 0.45, 0.70, 0.50]
    bw = w // len(heights)
    for i, f in enumerate(heights):
        bh = int(h * f)
        bx = x + i * bw
        cv.rect(bx + 2, y + h - bh, bw - 4, bh, c)
        for wy in range(y + h - bh + 8, y + h - 6, 14):
            for wx in range(bx + 6, bx + bw - 6, 10):
                cv.rect(wx, wy, 3, 4, PAPER)


# ---- the day's news, from live research on 27 November 2026 ----

MASTHEAD = "ONE DAY IN THE WORLD"
DATE_LINE = "FRIDAY, 27 NOVEMBER 2026"
DATE_RIGHT = "THE WORLD IN ONE PAGE"
FOOTER = "ONE DAY IN THE WORLD - FRIDAY, 27 NOVEMBER 2026"

LEAD_KICKER = "UKRAINE"
LEAD_HEAD = "ZELENSKYY WARNS OF NEW MASSIVE STRIKE ON POWER GRID"
LEAD_DECK = ("RUSSIA IS COMPLETING PREPARATIONS TO HIT ENERGY, LOGISTICS "
             "AND ESSENTIAL SERVICES, KYIV SAYS, AS WINTER NEARS. OVERNIGHT "
             "MISSILES AND 113 DRONES STRUCK KYIV, WOUNDING SEVEN; CREWS "
             "RACE TO RESTORE POWER IN SIX REGIONS. EU LEADERS FAIL TO "
             "AGREE A 45BN EURO LOAN FOR 2027.")
LEAD_STATS = ["113 DRONES AND MISSILES OVERNIGHT",
              "6 REGIONS WITHOUT POWER",
              "45BN EURO LOAN STALLED"]
LEAD_CAPTION = ("CREWS WORK TO RESTORE ELECTRICITY AFTER OVERNIGHT STRIKES "
                "ON SUBSTATIONS AND POWER LINES.")

PANELS = [
    ("GAZA", "ISRAELI STRIKES KILL 10 IN GAZA DESPITE CEASEFIRE",
     "AT LEAST 19 DEAD, 48 HURT IN LATEST STRIKES", "flame"),
    ("SAUDI ARABIA", "HOUTHI ATTACK HALTS JAZAN REFINERY; ONE WORKER KILLED",
     "OPERATIONS HALTED AFTER THE ATTACK", "derrick"),
    ("UNITED STATES", "STORM DELAYS THANKSGIVING PARADE; 900,000 LOSE POWER",
     "PARADE POSTPONED AS THE STORM HITS", "cloud"),
    ("NORTH KOREA", "KIM JONG UN VOWS TO EXPAND NUCLEAR ARSENAL",
     "MORE TACTICAL WEAPONS PROMISED", "atom"),
    ("LONDON", "24-HOUR TUBE STRIKE BRINGS THE CITY TO A STANDSTILL",
     "COMMUTERS FACE A DAY OF DISRUPTION", "train"),
    ("CONGO", "EBOLA OUTBREAK PASSES 12,000 CASES",
     "RESPONDERS EVACUATE AS CASES CLIMB", "microbe"),
]

BRIEFS = [
    "HONG KONG MARKS ONE YEAR SINCE THE FIRE THAT KILLED 168",
    "US APPROVES A $622M F-16 SUPPORT DEAL FOR UKRAINE",
    "EU BUDGET TALKS STALL; SERBIA SETS A 27 DECEMBER ELECTION",
]

ICONS = {"flame": icon_flame, "derrick": icon_derrick,
         "cloud": icon_cloud, "atom": icon_atom,
         "train": icon_train, "microbe": icon_microbe}


# ---- page layout ----

QUOTE = ("THE RUSSIANS KEEP TARGETING SUBSTATIONS, OVERHEAD POWER LINES, "
         "AND THE ENTIRE ELECTRICITY SUPPLY NETWORK.")
QUOTE_BY = "- VOLODYMYR ZELENSKYY, PRESIDENT OF UKRAINE"


def render(cv):
    # masthead
    cv.hline(36, 26, 952, INK, 2)
    cv.text(227, 40, MASTHEAD, 5, INK)
    cv.text(36, 88, DATE_LINE, 1, INK)
    cv.text(988 - cv.text_w(DATE_RIGHT, 1), 88, DATE_RIGHT, 1, GREY)
    cv.hline(36, 102, 952, INK, 4)
    cv.hline(36, 110, 952, INK, 2)

    # lead story, left column
    cv.rect(36, 128, 12, 12, RED)
    cv.text(56, 126, LEAD_KICKER, 2, RED)
    y = 150
    for line in cv.wrap(LEAD_HEAD, 560, 3):
        cv.text(36, y, line, 3, INK)
        y += 26
    y = 212
    for line in cv.wrap(LEAD_DECK, 560, 1):
        cv.text(36, y, line, 1, INK)
        y += 13
    # stat box
    cv.hline(36, 270, 560, INK, 2)
    cv.hline(36, 354, 560, INK, 2)
    cv.vline(36, 270, 84, INK, 2)
    cv.vline(596, 270, 84, INK, 2)
    sy = 282
    for stat in LEAD_STATS:
        cv.rect(52, sy, 8, 8, RED)
        cv.text(68, sy, stat, 1, INK)
        sy += 22
    # pull quote
    qy = 380
    for line in cv.wrap(QUOTE, 560, 1):
        cv.text(36, qy, line, 1, INK)
        qy += 13
    cv.text(36, qy + 6, QUOTE_BY, 1, GREY)

    # lead illustration, right column
    cv.hline(620, 150, 368, INK, 2)
    cv.hline(620, 440, 368, INK, 2)
    cv.vline(620, 150, 290, INK, 2)
    cv.vline(988, 150, 290, INK, 2)
    draw_pylon(cv, 640, 160, 120, 180, INK)
    draw_bolt(cv, 800, 170, 3, RED)
    draw_skyline(cv, 632, 340, 344, 100, INK)
    cy = 452
    for line in cv.wrap(LEAD_CAPTION, 368, 1):
        cv.text(620, cy, line, 1, GREY)
        cy += 13

    # divider
    cv.hline(36, 492, 952, INK, 2)

    # six story panels, two rows of three
    for i, (kicker, head, sub, icon) in enumerate(PANELS):
        px = 36 + (i % 3) * 325
        py = 508 + (i // 3) * 192
        cv.hline(px, py, 301, INK, 2)
        ICONS[icon](cv, px, py + 12, 1, INK)
        cv.text(px + 56, py + 16, kicker, 1, RED)
        hy = py + 66
        for line in cv.wrap(head, 301, 1):
            cv.text(px, hy, line, 1, INK)
            hy += 13
        cv.text(px, py + 118, sub, 1, GREY)

    # bottom strip: in brief
    cv.hline(36, 892, 952, INK, 2)
    cv.text(36, 904, "IN BRIEF", 2, RED)
    by = 930
    for brief in BRIEFS:
        cv.rect(36, by, 8, 8, RED)
        cv.text(52, by, brief, 1, INK)
        by += 18

    # footer
    cv.hline(36, 988, 952, INK, 1)
    cv.center_text(998, FOOTER, 1, GREY)


def main():
    os.makedirs("/output", exist_ok=True)
    cv = Canvas(W, H, PAPER)
    render(cv)
    save_png(cv, "/output/entry.png")


if __name__ == "__main__":
    main()
