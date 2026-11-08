#!/usr/bin/env python3
"""
Pixel-art header for the Nazzioo GitHub profile.

Draws a 240x80 pixel scene at dusk (sakura tree, Mount Fuji, a torii in the
lake, a stone lantern, "Welcome to my design world :))") and writes it as an
animated SVG: falling petals, twinkling stars and water sparkles. Everything is plain rects/paths, so GitHub renders it crisp at any width.

    python3 tools/build_header.py
"""
import math
import random
from pathlib import Path

W, H = 240, 80
HZ = 62  # horizon row (first water row)
OUT = Path(__file__).resolve().parent.parent / "assets" / "sakura-header.svg"

rng = random.Random(20261108)
px = [[None] * W for _ in range(H)]


def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        px[y][x] = c


BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def thr(x, y):
    return (BAYER[y % 4][x % 4] + 0.5) / 16


def h01(x, y, s=0):
    n = (x * 374761393 + y * 668265263 + s * 974711) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65536


def ramp(colors, f, x, y, sharp=2.2):
    """Dithered pick along a palette; f in [0, 1]."""
    n = len(colors) - 1
    f = max(0.0, min(1.0, f)) * n
    i = min(int(f), n - 1)
    k = max(0.0, min(1.0, (f - i - 0.5) * sharp + 0.5))
    return colors[i + 1] if k > thr(x, y) else colors[i]


# ---------------------------------------------------------------- sky
SKY = ["#120e30", "#1a1444", "#251a58", "#34206a", "#4a277b", "#653089",
       "#853a92", "#a94595", "#cb5394", "#e5668f", "#f5818b", "#fc9f8b", "#ffbf92"]


def sky():
    for y in range(HZ):
        for x in range(W):
            put(x, y, ramp(SKY, y / (HZ - 1), x, y))


def stars():
    for _ in range(60):
        x = rng.randrange(W)
        y = int(rng.random() ** 1.7 * 28)
        put(x, y, "#fff3d6" if rng.random() < 0.3 else "#a996e8")


# ---------------------------------------------------------------- sun
SX, SY, SR = 228, 40, 10
SUN = ["#fff2cf", "#ffd59c", "#ffab88"]


def sun():
    for y in range(SY - SR - 3, SY + SR + 4):
        for x in range(SX - SR - 3, SX + SR + 4):
            d = math.hypot(x - SX, y - SY)
            if d <= SR:
                put(x, y, ramp(SUN, (y - SY + SR) / (2 * SR), x, y, 1.6))
            elif d <= SR + 1.6 and thr(x, y) < 0.55:
                put(x, y, "#ffb48f")
            elif d <= SR + 3.2 and thr(x, y) < 0.2:
                put(x, y, "#f7978d")


# ---------------------------------------------------------------- fuji
FX, FY = 205, 33
fuji_mask = set()


def fuji_hw(d):
    return 2.5 + 1.05 * d + 0.043 * d * d


def fuji():
    for y in range(FY, HZ):
        d = y - FY
        hw = fuji_hw(d)
        for x in range(int(FX - hw), int(FX + hw) + 1):
            if not 0 <= x < W:
                continue
            fuji_mask.add((x, y))
            dx = x - FX
            snow = 6 + (3 if (dx // 2) % 3 == 0 else 0) + int(h01(x, 1, 3) * 2.5) + max(0, 3 - abs(dx) // 4)
            right = dx > d * 0.18 + (1 if thr(x, y) < 0.5 else 0)
            if d < snow:
                c = "#f4ecff" if right else "#c3b3ea"
            else:
                c = "#5a3f92" if right else "#4a3482"
            put(x, y, c)
        # rim light on the sunny edge
        put(int(FX + hw), y, "#f4ecff" if d < 7 else "#8a5fae")


def hills():
    for x in range(W):
        h1 = 5 + 2.2 * math.sin(x / 9.0) + 1.4 * math.sin(x / 4.1 + 1.3) + 1.2 * math.sin(x / 17 + 0.5)
        top = int(HZ - h1)
        for y in range(top, HZ):
            put(x, y, "#4b2f7f" if y > top else "#6a3f92")
        h2 = 2.2 + 1.3 * math.sin(x / 6.3 + 2.0) + 0.8 * math.sin(x / 2.9)
        top2 = int(HZ - h2)
        for y in range(top2, HZ):
            put(x, y, "#33215f" if y > top2 else "#432a72")


# ---------------------------------------------------------------- water
WATER = ["#7a3f8e", "#5c3083", "#452872", "#332062", "#271a52", "#1e1645"]


def water():
    for y in range(HZ, H):
        for x in range(W):
            put(x, y, ramp(WATER, (y - HZ) / (H - 1 - HZ), x, y))
    # fuji reflection, broken into wavy lines
    for y in range(HZ, H):
        row = y - HZ
        if row % 3 == 2:
            continue
        my = HZ - 1 - row
        wob = int(round(math.sin(y * 1.7) * 1.2))
        for x in range(W):
            if (x + wob, my) in fuji_mask:
                put(x, y, "#3b2a6c" if row < 6 else "#2e2160")
    # sun reflection
    for y in range(HZ + 1, H):
        row = y - HZ
        if row % 2 == 0:
            continue
        hw = 8 - row * 0.32
        for x in range(int(SX - hw - 3), int(SX + hw + 4)):
            dx = abs(x - SX)
            n = h01(x, y, 9)
            if dx < hw * 0.55 and n > 0.15:
                put(x, y, "#ffb98f")
            elif dx < hw and n > 0.35:
                put(x, y, "#e57d8e")
    # shimmer lines
    for _ in range(26):
        y = rng.randrange(HZ + 1, H)
        x = rng.randrange(80, W)
        ln = rng.randrange(2, 7)
        c = "#9a559f" if y < HZ + 6 else "#45307c"
        for i in range(ln):
            put(x + i, y, c)


# ---------------------------------------------------------------- torii
TX, TY = 194, 48  # top-left of the torii sprite
TORII = [
    "K.....................K",
    "KKKKKKKKKKKKKKKKKKKKKKK",
    ".kkkkkkkkkkkkkkkkkkkkk.",
    "..rrrrrrrrrrrrrrrrrrr..",
    ".....rR....p....rR.....",
    ".....rR...ppp...rR.....",
    "..rrrrrrrrrrrrrrrrrrr..",
    "..ddddddddddddddddddd..",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....rR.........rR.....",
    ".....dR.........dR.....",
    ".....dd.........dd.....",
]
TORII_C = {"K": "#24152f", "k": "#3a2440", "r": "#e2383a", "R": "#ff6a55",
           "d": "#a3243c", "p": "#2b1830"}
TORII_REF = {"K": "#1d1540", "k": "#1d1540", "r": "#86305a", "R": "#a2405e",
             "d": "#6c2650", "p": "#1d1540"}


def torii():
    for j, row in enumerate(TORII):
        for i, ch in enumerate(row):
            if ch != ".":
                put(TX + i, TY + j, TORII_C[ch])
    base = TY + len(TORII)
    for j in range(H - base):
        if j % 3 == 2:
            continue
        src = TORII[len(TORII) - 1 - j] if j < len(TORII) else None
        if src is None:
            break
        wob = 1 if (j // 2) % 2 else 0
        for i, ch in enumerate(src):
            if ch != ".":
                put(TX + i + wob, base + j, TORII_REF[ch])
    for x in (TX + 3, TX + 4, TX + 7, TX + 8, TX + 15, TX + 16, TX + 19, TX + 20):
        put(x, base - 1, "#9a6ab4")


# ---------------------------------------------------------------- shore + lantern
def bank_top(x):
    bump = math.sin(x / 5.0) * 0.8 + math.sin(x / 2.3 + 1) * 0.5
    return int(59 + (max(0, x - 8) / 62) ** 2 * 11 + bump)


ROCKS = [(70, 3, 2), (77, 2, 1), (84, 2, 1)]  # (x, width radius, height) at the waterline


def shore():
    for x in range(W):
        top = bank_top(x)
        if top >= H:
            break
        # foam where the bank meets the water
        if top > HZ:
            put(x + 1, top, "#6d4a9a")
        for y in range(top, H):
            if y == top:
                c = "#4a3a78"
            elif y == top + 1:
                c = "#352a62"
            else:
                c = "#231b45" if h01(x, y, 4) > 0.12 else "#2d2354"
            put(x, y, c)
        if h01(x, 0, 5) > 0.5:
            put(x, top - 1, "#4a3a78")
            if h01(x, 0, 8) > 0.75:
                put(x, top - 2, "#3b2d68")
        if h01(x, 0, 6) > 0.6:
            put(x, top + rng.randrange(0, 3), rng.choice(["#f59cbf", "#ffc4da", "#e17aa6"]))
    for (rx, rw, rh) in ROCKS:
        ry = bank_top(rx) + 1
        for y in range(ry - rh, ry + 1):
            for x in range(rx - rw, rx + rw + 1):
                if ((x - rx) / (rw + 0.5)) ** 2 + ((y - ry) / (rh + 0.5)) ** 2 <= 1:
                    put(x, y, "#4d3d7a" if y == ry - rh or x == rx + rw else "#30265a")
        put(rx - rw - 1, ry + 1, "#6d4a9a")
        put(rx + rw + 1, ry + 1, "#6d4a9a")


LANTERN = [
    "....a....",
    "...aah...",
    ".aaaaaah.",
    "aaaaaaaah",
    "..bbbbg..",
    "..bLLLg..",
    "..bLLLg..",
    "..bLLLg..",
    "..bbbbg..",
    "...bbg...",
    "....b....",
    "....g....",
    "...bbg...",
    "..bbbbg..",
]
LANTERN_C = {"a": "#3d2e63", "h": "#5a4888", "b": "#2c2250", "g": "#43356f", "L": "#ffd27a"}
LX = 56


def lantern():
    base = bank_top(LX + 4) + 1
    top = base - len(LANTERN)
    for j, row in enumerate(LANTERN):
        for i, ch in enumerate(row):
            if ch != ".":
                put(LX + i, top + j, LANTERN_C[ch])
    return LX + 4, top + 6  # window centre


# ---------------------------------------------------------------- sakura tree
tree_mask = set()


def limb(x0, y0, x1, y1, t0, t1):
    n = int(math.hypot(x1 - x0, y1 - y0) * 4) + 1
    for k in range(n + 1):
        t = k / n
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        r = (t0 + (t1 - t0) * t) / 2
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r + 0.15:
                    tree_mask.add((x, y))


BRANCHES = [
    (24, 62, 26, 50, 8, 6),
    (26, 50, 30, 40, 6, 5),
    (30, 40, 35, 31, 5, 4),
    (29, 42, 17, 31, 3.2, 2.2),
    (17, 31, 7, 24, 2.2, 1.4),
    (17, 31, 14, 21, 1.8, 1.2),
    (33, 34, 49, 25, 3.6, 2.6),
    (49, 25, 65, 19, 2.6, 2.0),
    (65, 19, 84, 13, 2.0, 1.1),
    (35, 31, 38, 18, 3.0, 2.0),
    (38, 18, 30, 9, 2.0, 1.1),
    (49, 25, 55, 14, 2.0, 1.1),
    (19, 63, 24, 59, 2, 2),
    (31, 63, 27, 59, 2, 2),
]


def trunk():
    for b in BRANCHES:
        limb(*b)
    for (x, y) in tree_mask:
        if (x + 1, y) not in tree_mask:
            c = "#6b3f5e"
        elif (x - 1, y) not in tree_mask:
            c = "#1f1026"
        elif h01(x, y, 7) > 0.8:
            c = "#3c2440"
        else:
            c = "#2d1932"
        put(x, y, c)


FRONT = ["#a24a83", "#d0679d", "#f592ba", "#ffbcd5", "#ffe3ee"]
BACK = ["#6e356d", "#934580", "#bf5e98", "#e486b2", "#f7b2cf"]
LIGHT = (0.55, -0.83)


def blossom(cx, cy, r, pal, seed):
    rr = random.Random(seed)
    subs = []
    for _ in range(int(r * r / 4.5) + 4):
        a = rr.random() * math.tau
        d = math.sqrt(rr.random()) * r * 0.82
        subs.append((cx + math.cos(a) * d, cy + math.sin(a) * d, 2.4 + rr.random() * 1.8))
    for y in range(int(cy - r - 5), int(cy + r + 6)):
        for x in range(int(cx - r - 5), int(cx + r + 6)):
            best = None
            for (sx, sy, sr) in subs:
                q = math.hypot(x + 0.5 - sx, y + 0.5 - sy) / sr
                if best is None or q < best[0]:
                    best = (q, sx, sy, sr)
            q, sx, sy, sr = best
            if q > 1 + (h01(x, y, seed) - 0.5) * 0.35:
                continue
            s_sub = ((x + 0.5 - sx) * LIGHT[0] + (y + 0.5 - sy) * LIGHT[1]) / sr
            s_cl = ((x - cx) * LIGHT[0] + (y - cy) * LIGHT[1]) / r
            s = 0.55 * s_sub + 0.55 * s_cl + (h01(x, y, seed + 1) - 0.5) * 0.35
            if s > 0.62:
                c = pal[4]
            elif s > 0.18:
                c = pal[3]
            elif s > -0.28:
                c = pal[2]
            elif s > -0.7:
                c = pal[1]
            else:
                c = pal[0]
            if c == pal[4] and h01(x, y, seed + 2) > 0.9:
                c = "#fff7fb"
            put(x, y, c)


CANOPY_BACK = [(5, 19, 9), (29, 5, 10), (58, 9, 9), (79, 7, 7), (44, 17, 8), (18, 2, 8)]
CANOPY_FRONT = [(13, 12, 10), (23, 23, 7), (38, 9, 10), (52, 18, 8), (68, 15, 7),
                (85, 11, 5), (2, 30, 5), (41, 26, 6), (8, 25, 5), (61, 24, 4)]


def canopy():
    for i, (x, y, r) in enumerate(CANOPY_BACK):
        blossom(x, y, r, BACK, 100 + i)
    for i, (x, y, r) in enumerate(CANOPY_FRONT):
        blossom(x, y, r, FRONT, 200 + i)
    # a few loose blossoms hanging under the canopy
    for _ in range(18):
        x = rng.randrange(0, 88)
        y = rng.randrange(26, 36)
        if px[y - 1][x] in FRONT or px[y - 1][x] in BACK:
            put(x, y, rng.choice(["#f592ba", "#ffbcd5"]))


# ---------------------------------------------------------------- text
FONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "C": [".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "G": [".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".###."],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "'": ["#", "#", ".", ".", ".", ".", "."],
    ":": [".", ".", "#", ".", ".", "#", "."],
    ")": ["#..", ".#.", "..#", "..#", "..#", ".#.", "#.."],
    " ": ["...", "...", "...", "...", "...", "...", "..."],
}


def text_width(s, scale=1, gap=1):
    return sum((len(FONT[ch][0]) + gap) * scale for ch in s) - gap * scale


def text(s, x0, y0, scale, rows, shadow, gap=1):
    lit = {}
    x = x0
    for ch in s:
        g = FONT[ch]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "#":
                    for sy in range(scale):
                        for sx in range(scale):
                            lit[(x + i * scale + sx, y0 + j * scale + sy)] = rows[j]
        x += (len(g[0]) + gap) * scale
    for (ox, oy, c) in shadow:
        for (lx, ly) in lit:
            if (lx + ox, ly + oy) not in lit:
                put(lx + ox, ly + oy, c)
    for (lx, ly), c in lit.items():
        put(lx, ly, c)
    return x - gap * scale


TXL = 98
BIG_ROWS = ["#fff8ef", "#fff8ef", "#fff1f2", "#ffe4ee", "#ffd6e6", "#ffc3da", "#ffc3da"]
SMALL_ROWS = ["#ffb3cf"] * 7
SHADOW = [(1, 1, "#24123f"), (2, 2, "#170b2c")]


def title():
    text("WELCOME TO", TXL, 9, 1, SMALL_ROWS, [(1, 1, "#24123f")], gap=2)
    text("MY DESIGN", TXL, 20, 2, BIG_ROWS, SHADOW)
    text("WORLD :))", TXL, 38, 2, BIG_ROWS, SHADOW)


# ---------------------------------------------------------------- corners
def corners():
    for (x, y) in [(0, 0), (1, 0), (0, 1)]:
        for (fx, fy) in [(x, y), (W - 1 - x, y), (x, H - 1 - y), (W - 1 - x, H - 1 - y)]:
            px[fy][fx] = None


# ---------------------------------------------------------------- animated layer
def rect(x, y, w, h, c, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{c}"{extra}/>'


def twinkles():
    spots = [(112, 4), (147, 7), (189, 3), (230, 11), (168, 16), (131, 15), (214, 22), (98, 1)]
    out = []
    for i, (x, y) in enumerate(spots):
        delay = -rng.random() * 4
        dur = 2.6 + rng.random() * 2.4
        out.append(
            f'<g class="tw" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
            + rect(x, y, 1, 1, "#fff8e7")
            + rect(x - 1, y, 1, 1, "#b9a6f2") + rect(x + 1, y, 1, 1, "#b9a6f2")
            + rect(x, y - 1, 1, 1, "#b9a6f2") + rect(x, y + 1, 1, 1, "#b9a6f2")
            + "</g>")
    return "".join(out)


def sparkles():
    out = []
    for _ in range(7):
        x = SX + rng.randrange(-7, 8)
        y = HZ + 1 + rng.randrange(0, 12)
        delay = -rng.random() * 3
        out.append(f'<g class="sp" style="animation-delay:{delay:.1f}s">'
                   + rect(x, y, 2, 1, "#fff2d8") + "</g>")
    return "".join(out)


PETAL_COLORS = [("#ffc6db", "#f08cb5"), ("#ffd9e7", "#f7a3c4"), ("#ffb0cd", "#e0709f")]


def petals():
    out = []
    for i in range(18):
        kind = "pa pb pc".split()[i % 3]
        if i < 12:
            x, y = rng.randrange(4, 92), rng.randrange(6, 38)
        else:
            x, y = rng.randrange(90, 170), rng.randrange(-6, 4)
        dur = 9 + rng.random() * 8
        delay = -rng.random() * dur
        flut = 0.9 + rng.random() * 1.2
        c1, c2 = rng.choice(PETAL_COLORS)
        out.append(
            f'<g class="{kind}" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">'
            f'<g transform="translate({x} {y})">'
            f'<g class="fl" style="animation-duration:{flut:.1f}s">'
            + rect(0, 0, 2, 1, c1) + rect(1, 1, 1, 1, c2)
            + "</g></g></g>")
    return "".join(out)


STYLE = """
.tw{animation:tw 4s ease-in-out infinite}
@keyframes tw{0%,100%{opacity:.15}50%{opacity:1}}
.sp{animation:sp 2.6s steps(1) infinite}
@keyframes sp{0%,55%{opacity:0}60%,80%{opacity:1}85%,100%{opacity:0}}
.glow{animation:glow 3.2s ease-in-out infinite}
@keyframes glow{0%,100%{opacity:.55}45%{opacity:1}70%{opacity:.75}}
.pa,.pb,.pc{animation-timing-function:linear;animation-iteration-count:infinite}
.pa{animation-name:fa}.pb{animation-name:fb}.pc{animation-name:fc}
@keyframes fa{0%{transform:translate(0,0);opacity:0}8%{opacity:1}30%{transform:translate(16px,14px)}
55%{transform:translate(26px,30px)}85%{opacity:1}100%{transform:translate(58px,58px);opacity:0}}
@keyframes fb{0%{transform:translate(0,0);opacity:0}8%{opacity:1}25%{transform:translate(30px,10px)}
50%{transform:translate(55px,24px)}75%{transform:translate(86px,34px)}85%{opacity:1}100%{transform:translate(118px,50px);opacity:0}}
@keyframes fc{0%{transform:translate(0,0);opacity:0}8%{opacity:1}30%{transform:translate(10px,16px)}
50%{transform:translate(4px,28px)}75%{transform:translate(18px,42px)}85%{opacity:1}100%{transform:translate(30px,58px);opacity:0}}
.fl{transform-box:fill-box;transform-origin:center;animation:fl 1.4s ease-in-out infinite alternate}
@keyframes fl{0%{transform:scale(1,1)}50%{transform:scale(.4,1.2)}100%{transform:scale(1,.6)}}
@media (prefers-reduced-motion:reduce){*{animation:none!important}}
"""


def to_svg(glow):
    by_color = {}
    for y in range(H):
        x = 0
        while x < W:
            c = px[y][x]
            if c is None:
                x += 1
                continue
            x0 = x
            while x < W and px[y][x] == c:
                x += 1
            by_color.setdefault(c, []).append(f"M{x0} {y}h{x - x0}v1h-{x - x0}z")
    paths = "".join(f'<path fill="{c}" d="{"".join(d)}"/>' for c, d in by_color.items())

    gx, gy = glow
    glow_px = []
    for y in range(gy - 3, gy + 4):
        for x in range(gx - 3, gx + 4):
            d = math.hypot(x - gx, y - gy)
            if 1.5 < d <= 3.3 and thr(x, y) < (0.5 if d < 2.5 else 0.22) and px[y][x] not in (None,):
                glow_px.append(rect(x, y, 1, 1, "#ffcf7a", ' opacity=".55"'))
    glow_g = '<g class="glow">' + "".join(glow_px) + "</g>"

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W * 4}" height="{H * 4}" '
        'shape-rendering="crispEdges" role="img" aria-labelledby="t">'
        "<title id=\"t\">Welcome to my design world: pixel-art sakura tree, Mount Fuji and a torii at dusk</title>"
        f"<style>{STYLE.strip()}</style>"
        f"<g>{paths}</g>{twinkles()}{sparkles()}{glow_g}{petals()}</svg>\n"
    )


def main():
    sky()
    stars()
    sun()
    fuji()
    hills()
    water()
    torii()
    shore()
    glow = lantern()
    trunk()
    canopy()
    title()
    corners()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(to_svg(glow))
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
