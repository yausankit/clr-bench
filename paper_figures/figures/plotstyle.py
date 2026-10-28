"""Shared look for the result figures: white background, thin axes, the paper's Libertine font, a bold panel letter
before each title, and bars with value labels."""
import glob
import matplotlib
matplotlib.use("Agg")
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

for _f in glob.glob("/usr/local/texlive/*/texmf-dist/fonts/opentype/public/libertine/LinLibertine_R*.otf"):
    fm.fontManager.addfont(_f)
INK, SUB, GRID, BG = "#222222", "#555555", "#ececec", "#ffffff"
BLUE, LBLUE, GREEN, RED, AMBER, GRAY, PURPLE = "#1f4e8c", "#a8bbdb", "#2f7d4f", "#b5473a", "#c8902e", "#9a9a9a", "#7b5ea7"


def apply():
    plt.rcParams.update({
        "font.family": "Linux Libertine O", "font.size": 8, "axes.facecolor": BG, "axes.edgecolor": "#333333",
        "axes.linewidth": 0.6, "axes.labelcolor": INK, "axes.labelsize": 8, "axes.grid": False,
        "axes.spines.top": False, "axes.spines.right": False, "axes.axisbelow": True,
        "xtick.color": "#333333", "ytick.color": "#333333", "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "legend.frameon": False, "legend.fontsize": 7, "pdf.fonttype": 42, "mathtext.fontset": "custom",
        "mathtext.rm": "Linux Libertine O", "mathtext.it": "Linux Libertine O:italic"})


def title(ax, tag, text, x=0.0, y=1.06):
    """bold panel letter followed by the title, left-aligned above the axes"""
    ax.text(x, y, f"({tag})", transform=ax.transAxes, fontsize=8.5, fontweight="bold", color=INK, va="bottom", ha="left")
    ax.annotate(text, xy=(x, y), xycoords="axes fraction", xytext=(len(tag) * 4.6 + 12, 0), textcoords="offset points",
                fontsize=8, color=INK, va="bottom", ha="left")


def bar(ax, x, h, w, color, label=None, fmt="{:.0f}", fs=6.5, r=0.0, ymax=100):
    """vertical bar with rounded top corners and its value above it"""
    rad = min(r * w, h / 2 if h > 0 else 0)
    ax.add_patch(FancyBboxPatch((x - w / 2, 0), w, max(h, 1e-6), boxstyle=f"round,pad=0,rounding_size={rad}",
                                mutation_aspect=ymax / 6, fc=color, ec="none", zorder=3))
    if label is not False:
        ax.text(x, h + ymax * 0.015, fmt.format(h), ha="center", va="bottom", fontsize=fs, color=INK, zorder=4)


def key(ax, items, x=0.0, y=1.0, dx=None, marker="s", size=4.5, xs=None):
    """one-row legend of coloured squares or dots placed just above the axes"""
    handles = [plt.Line2D([], [], marker=marker, ls="none", ms=size, color=col, mec="white", mew=0.4, label=lab)
               for lab, col in items]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(x - 0.02, y - 0.01), ncol=len(items), fontsize=7,
              handletextpad=0.15, columnspacing=0.8, borderaxespad=0, borderpad=0)
