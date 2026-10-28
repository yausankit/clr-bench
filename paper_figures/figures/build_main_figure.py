"""Build figures/main_figure.html (Figure 1): hand-drawn style with OpenMoji icons (CC BY-SA 4.0, figures/assets_openmoji)
and the Comic Neue font (OFL, figures/assets_font), both inlined. Then render with figures/make_main_figure.sh.
Run from the repository root: python figures/build_main_figure.py && zsh figures/make_main_figure.sh"""
import base64
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
W, H = 1400, 384
PH = 372  # height of the three upper panels
INK, SUB = "#1f2430", "#5b6272"
BLUE, GREEN, RED, PURPLE, SALMON = "#2f5fb3", "#2f8a4c", "#c4473c", "#9b7be0", "#ea6a52"
PANEL, INNER = "#f3f4f8", "#e8ebf4"

font = lambda f: base64.b64encode((ROOT / "assets_font" / f).read_bytes()).decode()
css = f"""
  @font-face {{ font-family: "CN"; font-weight: 400; src: url(data:font/woff2;base64,{font("ComicNeue-Regular.woff2")}) format("woff2"); }}
  @font-face {{ font-family: "CN"; font-weight: 700; src: url(data:font/woff2;base64,{font("ComicNeue-Bold.woff2")}) format("woff2"); }}
  @page {{ size: {W}px {H}px; margin: 0; }}
  html, body {{ margin: 0; padding: 0; background: #fff; }}
  svg {{ display: block; font-family: "CN", "Comic Sans MS", sans-serif; }}
  .t  {{ font-size: 26px; font-weight: 700; fill: {INK}; }}
  .h  {{ font-size: 20px; font-weight: 700; fill: {INK}; }}
  .b  {{ font-size: 18px; font-weight: 700; fill: {INK}; }}
  .n  {{ font-size: 17px; fill: {SUB}; font-weight: 700; }}
  .c  {{ font-size: 17px; font-weight: 700; }}
  .s  {{ font-size: 15px; fill: {SUB}; font-weight: 700; }}
  .xs {{ font-size: 14px; fill: {SUB}; font-weight: 700; }}
  .rl {{ font-size: 15px; font-weight: 700; }}
  .num {{ font-size: 14px; font-weight: 700; fill: #fff; }}
  .dash {{ fill: #fff; stroke: {INK}; stroke-width: 1.6; stroke-dasharray: 6 4; }}
  .ln  {{ fill: none; stroke: {INK}; stroke-width: 1.8; }}
"""

# OpenMoji icons as <symbol>s (ids inside each file are dropped so they do not collide)
EMO = {"plane": "2708", "q": "2753", "globe": "1F310", "yes": "2705", "no": "274C", "test": "1F9EA",
       "robot": "1F916", "memo": "1F4DD", "chat": "1F4AC", "note": "1F4D2", "files": "1F5C2", "abc": "1F524",
       "puzzle": "1F9E9", "search": "1F50D", "monkey": "1F648", "bulb": "1F4A1", "books": "1F4DA", "box": "1F4E6",
       "ladder": "1FA9C", "chains": "1F517", "lists": "1F4DA", "travel": "2708", "pharmacy": "1F48A",
       "security": "1F6E1", "logs": "1F5A5", "sport": "26BD", "chem": "2697", "raw": "26CF", "port": "1F6A2",
       "scholar": "1F393", "grant": "1F4B6", "map": "1F5FA", "climber": "1F9D7",
       "flag": "1F6A9", "brain": "1F9E0"}
symbols = []
for name, code in EMO.items():
    svg = (ROOT / "assets_openmoji" / f"{code}.svg").read_text()
    inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S)
    inner = re.sub(r'\sid="[^"]*"', "", inner)
    symbols.append(f'<symbol id="e-{name}" viewBox="0 0 72 72">{inner}</symbol>')
defs = "\n".join(symbols) + f"""
<marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0.5 L10,5 L0,9.5 z" fill="{INK}"/></marker>
<marker id="ahr" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0,0.5 L10,5 L0,9.5 z" fill="{RED}"/></marker>
<marker id="ahp" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0,0.5 L10,5 L0,9.5 z" fill="{PURPLE}"/></marker>
"""

el = []
add = el.append


def emo(name, x, y, s=40):
    add(f'<use href="#e-{name}" x="{x}" y="{y}" width="{s}" height="{s}"/>')


def text(x, y, s, cls="b", anchor="start", fill=None):
    f = f' style="fill:{fill}"' if fill else ""
    add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}" dominant-baseline="central"{f}>{s}</text>')


def sub(base, idx):
    return f'{base}<tspan baseline-shift="sub" font-size="12">{idx}</tspan>'


def chip(x, cy, w, label, color, fill="#fff", dashed=False, pill=True, h=28):
    dash = ' stroke-dasharray="5 3.5"' if dashed else ""
    add(f'<rect x="{x}" y="{cy - h / 2}" width="{w}" height="{h}" rx="{h / 2 if pill else 6}" fill="{fill}" '
        f'stroke="{color}" stroke-width="1.7"{dash}/>')
    text(x + w / 2, cy + 1, label, "c", "middle", color)


def big_arrow(x1, y1, x2, y2, color, w=11):
    """thick straight arrow with a broad head"""
    a = math.atan2(y2 - y1, x2 - x1)
    hl, hw = w * 1.7, w * 1.45
    bx, by = x2 - hl * math.cos(a), y2 - hl * math.sin(a)
    px, py = -math.sin(a), math.cos(a)
    pts = [(x1 + px * w / 2, y1 + py * w / 2), (bx + px * w / 2, by + py * w / 2), (bx + px * hw, by + py * hw), (x2, y2),
           (bx - px * hw, by - py * hw), (bx - px * w / 2, by - py * w / 2), (x1 - px * w / 2, y1 - py * w / 2)]
    add(f'<polygon points="{" ".join(f"{u:.1f},{v:.1f}" for u, v in pts)}" fill="{color}" stroke="{INK}" '
        f'stroke-width="1.2" stroke-linejoin="round"/>')


def panel(x, w, title):
    add(f'<rect x="{x}" y="6" width="{w}" height="{PH}" rx="16" fill="{PANEL}"/>')
    text(x + w / 2, 34, title, "t", "middle")


# ================================================================== (a)
panel(6, 446, "(a) A level hides a rule")
add('<rect x="22" y="56" width="414" height="76" rx="12" class="dash"/>')
emo("plane", 30, 60, 36)
text(74, 79, "Count reimbursable flight segments", "b")
text(74, 112, "exclude", "b")
chip(146, 112, 158, "review queue B8", BLUE, "#eaf0fb", pill=False)
text(314, 112, "e.g.", "n")
text(350, 112, "Lufthansa", "b")

emo("chat", 22, 140, 30)
text(58, 156, "practice feedback", "n")
emo("yes", 24, 176, 26)
chip(54, 189, 148, "Thai Airways", GREEN, "#e7f4ea")
emo("no", 24, 210, 26)
chip(54, 223, 148, "ITA Airways", RED, "#fbeae7", pill=False)
add('<path d="M 208 189 C 232 189, 230 206, 252 206" class="ln"/>')
add('<path d="M 208 223 C 232 223, 230 206, 252 206" class="ln" marker-end="url(#ah)"/>')
add('<rect x="262" y="146" width="174" height="104" rx="12" class="dash" style="fill:#fafafa"/>')
emo("q", 326, 150, 42)
text(349, 208, "hidden class", "h", "middle")
emo("globe", 404, 152, 24)
text(349, 234, "Star Alliance founders", "s", "middle")

add('<rect x="22" y="262" width="414" height="108" rx="12" class="dash"/>')
emo("test", 28, 266, 32)
text(64, 283, "Test on unseen values", "b")
text(34, 318, "exclude", "b")
chip(110, 318, 150, "United Airlines", GREEN, dashed=True)
chip(268, 318, 118, "Air Canada", GREEN, dashed=True)
text(34, 352, "keep", "b")
chip(110, 352, 176, "Norse Atlantic UK", RED, dashed=True, pill=False)
chip(294, 352, 134, "Air Tahiti Nui", RED, dashed=True, pill=False)

# ================================================================== (b)
panel(460, 482, "(b) Curriculum chain and protocol")
# rising mountains: level k is k strata high, one stratum per rule; the top stratum is the rule added at level k
B, BAND, TOPW, SLOPE = 196, 26, 24, 0.58
centers = {1: 566, 2: 640, 3: 732, 4: 842}
STRATA = ["#f3ece0", "#e9dfcd"]
add(f'<path d="M 478 {B} L 928 {B}" stroke="{INK}" stroke-width="1.6"/>')
for k in (4, 3, 2, 1):
    cx, hk = centers[k], BAND * k
    top = B - hk
    half = TOPW + hk * SLOPE
    shape = (f"M {cx - half:.1f} {B} L {cx - TOPW:.1f} {top + 4} Q {cx} {top - 5} {cx + TOPW:.1f} {top + 4} "
             f"L {cx + half:.1f} {B} Z")
    defs += f'<clipPath id="mt{k}"><path d="{shape}"/></clipPath>'
    for r in range(1, k + 1):
        y1 = B - BAND * r
        new = r == k
        add(f'<rect x="{cx - half - 2:.1f}" y="{y1 - (8 if new else 0)}" width="{2 * half + 4:.1f}" '
            f'height="{BAND + (8 if new else 0)}" fill="{"#d7e5f8" if new else STRATA[r % 2]}" clip-path="url(#mt{k})"/>')
        if r > 1:
            add(f'<line x1="{cx - half:.1f}" y1="{y1 + BAND}" x2="{cx + half:.1f}" y2="{y1 + BAND}" stroke="#b9ad97" '
                f'stroke-width="1" stroke-dasharray="3 3" clip-path="url(#mt{k})"/>')
        text(cx, y1 + BAND / 2 + 1, f"rule {r}", "rl", "middle", BLUE if new else "#7a6a52")
    add(f'<path d="{shape}" fill="none" stroke="{INK}" stroke-width="1.7" stroke-linejoin="round"/>')
    add(f'<circle cx="{cx}" cy="{top - 18}" r="11" fill="{INK}"/>')
    text(cx, top - 17, str(k), "num", "middle")
emo("climber", 478, 150, 42)
emo("flag", centers[4] + 12, B - 4 * BAND - 44, 30)
text(500, 88, "harder", "n", "middle")
text(500, 108, "levels", "n", "middle")

add(f'<rect x="474" y="200" width="454" height="170" rx="14" fill="{INNER}"/>')
emo("robot", 480, 220, 38)
text(499, 266, "agent", "n", "middle")
add('<path d="M 520 236 L 544 236" class="ln" marker-end="url(#ah)"/>')
steps = [(572, "memo", "Practice", "with feedback"), (714, "brain", "Learn", None), (866, "test", "Test", "unseen values")]
for i, (cx, ic, lab, note) in enumerate(steps, start=1):
    emo(ic, cx - 23, 212, 46)
    add(f'<circle cx="{cx - 30}" cy="282" r="11" fill="{INK}"/>')
    text(cx - 30, 283, str(i), "num", "middle")
    text(cx - 14, 283, lab, "h")
    if note:
        text(cx, 306, note, "n", "middle")
# the learning loop between practice and learn: feedback goes up, a retry comes back
add('<path d="M 600 226 C 624 206, 662 206, 686 226" class="ln" marker-end="url(#ah)"/>')
add('<path d="M 688 252 C 664 282, 622 282, 598 252" class="ln" marker-end="url(#ah)"/>')
emo("yes", 616, 233, 18)
emo("yes", 634, 233, 18)
emo("no", 652, 233, 18)
# what learning should produce: a hypothesis about the hidden class
add(f'<rect x="632" y="295" width="176" height="23" rx="11.5" fill="#fff" stroke="{BLUE}" stroke-width="1.5"/>')
emo("bulb", 636, 297.5, 17)
add(f'<text x="727" y="307" text-anchor="middle" dominant-baseline="central" style="font-size:12.5px;font-weight:700;fill:{BLUE}">B8 = Star Alliance founders</text>')
add('<path d="M 742 236 L 838 236" class="ln" marker-end="url(#ah)"/>')
text(790, 222, "learned rule", "xs", "middle")
add(f'<path d="M 866 322 C 866 358, 572 358, 572 322" fill="none" stroke="{PURPLE}" stroke-width="3" '
    f'marker-end="url(#ahp)"/>')
text(719, 360, "next level, same state", "n", "middle", PURPLE)

# ================================================================== (c)
panel(950, 444, "(c) Automated synthesis pipeline")
for cx, ic, lab in ((1040, "files", "records"), (1172, "abc", "described values"), (1304, "globe", "named Web lists")):
    emo(ic, cx - 18, 50, 36)
    text(cx, 98, lab, "s", "middle")
big_arrow(1172, 110, 1172, 134, SALMON)
# a candidate slot: each chip with a one-word role underneath
x = 966
for w, lab, color, fill, dashed, pill, role in [
        (66, "class C", INK, "#f1f1f1", True, False, "hidden"), (44, "A", INK, "#fff", False, False, "example"),
        (52, sub("m", "0"), GREEN, "#e7f4ea", False, True, "revealed"),
        (62, sub("m", "1") + ", " + sub("m", "2"), GREEN, "#fff", True, True, "unseen"),
        (44, sub("n", "p"), RED, "#fbeae7", False, False, "rejected"), (44, sub("N", "t"), RED, "#fff", True, False, "test foils")]:
    chip(x, 154, w, lab, color, fill, dashed, pill)
    add(f'<text x="{x + w / 2}" y="{181}" text-anchor="middle" dominant-baseline="central" '
        f'style="font-size:12px;font-weight:700;fill:{SUB}">{role}</text>')
    x += w + 7
cand_end = x - 7
big_arrow(1172, 194, 1172, 216, SALMON)
# four probes, each with the requirement it checks
for i, (ic, lab, req) in enumerate((("books", "Known?", "lists it by name"), ("monkey", "Hidden?", "no blind guess"),
                                    ("search", "Learnable?", "feedback helps"), ("bulb", "Solvable?", "with the lesson"))):
    px = 962 + i * 100
    add(f'<rect x="{px}" y="222" width="94" height="86" rx="12" class="dash"/>')
    emo(ic, px + 31, 226, 32)
    text(px + 47, 271, lab, "b", "middle")
    add(f'<text x="{px + 47}" y="{292}" text-anchor="middle" dominant-baseline="central" '
        f'style="font-size:12px;font-weight:700;fill:{SUB}">{req}</text>')
# rejected candidates are redrawn: an orthogonal return path from the probes back to the candidate slot
RX = 1380
add(f'<path d="M 1356 265 L {RX} 265 L {RX} 154 L {cand_end + 8} 154" fill="none" stroke="{RED}" stroke-width="2" '
    f'stroke-dasharray="5 4" stroke-linejoin="round" marker-end="url(#ahr)"/>')
emo("no", RX - 10, 199, 20)
big_arrow(1172, 312, 1172, 336, "#6fbf73")
emo("box", 1060, 336, 34)
text(1100, 354, "certified chain (4 levels)", "b")

html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>CLR-Bench main figure</title>
<!-- Generated by figures/build_main_figure.py; render with figures/make_main_figure.sh.
     Icons: OpenMoji (CC BY-SA 4.0). Font: Comic Neue (SIL OFL). -->
<style>{css}</style>
</head>
<body>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg">
  <defs>{defs}
  </defs>
  {chr(10).join('  ' + e for e in el)}
</svg>
</body>
</html>
"""
(ROOT / "main_figure.html").write_text(html)
print("wrote figures/main_figure.html")
