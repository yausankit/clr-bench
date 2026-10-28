"""Three candidate designs for the difficulty part of Figure 1, panel (b). Writes figures/difficulty_options.html;
render with: zsh figures/make_main_figure.sh is not used here, see the command in the module docstring of
build_main_figure.py. Run: python figures/build_difficulty_options.py"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INK, SUB, LINE = "#1e293b", "#64748b", "#475569"
BLUE, GREEN, RED = "#2f5fb3", "#2e7d4f", "#b8433a"
W, H = 1400, 300

el = []
add = el.append


def text(x, y, s, cls="n", anchor="start", fill=None):
    f = f' style="fill:{fill}"' if fill else ""
    add(f'<text x="{x}" y="{y}" class="{cls}" text-anchor="{anchor}"{f}>{s}</text>')


def rect(x, y, w, h, extra, rx=3):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" {extra}/>')


def icon(name, x, y, s=18, color=LINE, sw=None):
    style = f"color:{color}" + (f";stroke-width:{sw}" if sw else "")
    add(f'<use href="#i-{name}" x="{x}" y="{y}" width="{s}" height="{s}" style="{style}"/>')


NEW = f'fill="#edf2fb" stroke="{BLUE}" stroke-width="1.2"'
OLD = 'fill="#fff" stroke="#dbe0e7" stroke-width="1"'
CLEAN = 'fill="#a9bde3" stroke="#8fa8d6" stroke-width="1"'
SINGLE = 'fill="#fff" stroke="#9aa3b2" stroke-width="1.2" stroke-dasharray="3 2"'

# ---------------------------------------------------------------- option A: level x test-input matrix
ox = 20
rect(ox - 10, 10, 440, 270, 'fill="#f7f8fa"', 6)
text(ox, 36, "A. Level × test inputs", "t")
text(ox + 70, 66, "rules", "n")
text(ox + 268, 66, "test inputs", "n", "middle")
text(ox + 388, 66, "frozen", "n", "middle")
for k in range(1, 5):
    y = 78 + (k - 1) * 46
    text(ox, y + 24, f"Level {k}", "h")
    for r in range(1, k + 1):
        rect(ox + 70 + (r - 1) * 34, y + 8, 30, 22, NEW if r == k else OLD, 3)
        text(ox + 85 + (r - 1) * 34, y + 24, f"R{r}", "v", "middle", BLUE if r == k else SUB)
    for c in range(5):
        x = ox + 216 + c * 22
        rect(x, y + 6, 18, 26, CLEAN if c < 5 - k else SINGLE, 3)
        if c >= 5 - k:
            icon("help-circle", x + 2, y + 12, 14, "#9aa3b2", 2)
    text(ox + 388, y + 24, f".{10 - 2 * k}", "h", "middle")
rect(ox + 70, 268, 14, 10, CLEAN, 2); text(ox + 90, 277, "clean (example only)", "n")
rect(ox + 250, 268, 14, 10, SINGLE, 2); text(ox + 270, 277, "single (unseen values)", "n")

# ---------------------------------------------------------------- option B: rising stairs
ox = 480
rect(ox - 10, 10, 440, 270, 'fill="#f7f8fa"', 6)
text(ox, 36, "B. Rising stairs", "t")
base = 226
for k in range(1, 5):
    x = ox + 20 + (k - 1) * 98
    top = base - 36 * k
    rect(x, top, 92, base - top, 'fill="#fff" stroke="#cbd2dc" stroke-width="1"', 2)
    for r in range(1, k + 1):
        yy = base - 26 - (r - 1) * 26
        rect(x + 12, yy, 68, 20, NEW if r == k else OLD, 3)
        text(x + 46, yy + 14.5, f"rule {r}", "v", "middle", BLUE if r == k else SUB)
    text(x + 46, top - 8, f"Level {k}", "h", "middle") if k > 1 else text(x + 46, top - 60, f"Level {k}", "h", "middle")
    text(x + 46, base + 20, f".{10 - 2 * k}", "h", "middle")
icon("bot", ox + 52, base - 36 - 52, 22, SUB)
text(ox + 2, base + 20, "frozen", "n")
add(f'<path d="M {ox + 40} {base + 34} L {ox + 400} {base + 34}" fill="none" stroke="{LINE}" stroke-width="1.2" marker-end="url(#ah)"/>')
text(ox + 400, base + 50, "harder", "n", "end")

# ---------------------------------------------------------------- option C: filter funnel
ox = 940
rect(ox - 10, 10, 450, 270, 'fill="#f7f8fa"', 6)
text(ox, 36, "C. Stacked hidden filters", "t")
for k in range(1, 5):
    y = 62 + (k - 1) * 52
    text(ox, y + 22, f"L{k}", "h")
    icon("table-2", ox + 30, y + 6, 22, LINE)
    add(f'<path d="M {ox + 56} {y + 17} L {ox + 74} {y + 17}" fill="none" stroke="{LINE}" stroke-width="1.2" marker-end="url(#ah)"/>')
    for r in range(1, k + 1):
        x = ox + 78 + (r - 1) * 50
        add(f'<path d="M {x} {y} L {x + 40} {y} L {x + 28} {y + 34} L {x + 12} {y + 34} z" '
            + ('fill="#edf2fb" stroke="%s" stroke-width="1.2"' % BLUE if r == k else 'fill="#fff" stroke="#b7bec9" stroke-width="1"') + '/>')
        text(x + 20, y + 17, f"R{r}", "v", "middle", BLUE if r == k else SUB)
    xe = ox + 78 + k * 50
    add(f'<path d="M {xe - 6} {y + 17} L {xe + 14} {y + 17}" fill="none" stroke="{LINE}" stroke-width="1.2" marker-end="url(#ah)"/>')
    text(xe + 18, y + 22, "count", "n")
    text(ox + 420, y + 22, f".{10 - 2 * k}", "h", "end")
text(ox + 420, 56, "frozen", "n", "end")

css = f"""
  @page {{ size: {W}px {H}px; margin: 0; }}
  html, body {{ margin: 0; background: #fff; }}
  svg {{ display: block; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }}
  .t {{ font-size: 17px; font-weight: 700; fill: {INK}; }}
  .h {{ font-size: 14.5px; font-weight: 700; fill: {INK}; }}
  .v {{ font-size: 13.5px; font-weight: 600; }}
  .n {{ font-size: 13.5px; fill: {SUB}; }}
"""
syms = (ROOT / "lucide_symbols.txt").read_text()
help_icon = ('<symbol id="i-help-circle" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
             'stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/>'
             '<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></symbol>')
html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Difficulty options</title><style>{css}</style></head><body>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg"><defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0.5 L10,5 L0,9.5 z" fill="{LINE}"/></marker>
{syms}
{help_icon}
</defs>
{chr(10).join(el)}
</svg></body></html>"""
(ROOT / "difficulty_options.html").write_text(html)
print("wrote figures/difficulty_options.html")
