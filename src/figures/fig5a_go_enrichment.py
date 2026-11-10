# -*- coding: utf-8 -*-
# --- GitHub-release path bootstrap (auto-generated) ---
import os as _os, sys as _sys
_SRC = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
if not _os.path.exists(_os.path.join(_SRC, 'config.py')):
    _SRC = _os.path.dirname(_os.path.abspath(__file__))
if _SRC not in _sys.path:
    _sys.path.insert(0, _SRC)
_PROJECT = _os.environ.get('UKB_PROJECT_ROOT', _os.path.dirname(_SRC))
# ------------------------------------------------------
"""
Fig5 GO BP DotPlot — Stroke 版 (v906 v4, 基于 907 GO 结果)
===================================================
与 v3 相同的 "Organ (row block) x Organ (column)" GO:BP dotplot,
仅将 'Any organ failure'(all) 块/列替换为 Stroke(brain);
行块纵向顺序与 Fig2B 一致: Heart -> Lung -> Liver -> Kidney ->
Hematologic -> Stroke(上→下)。数据源 = input907_analysis_output(907 版,含 brain)。
输出: panels/Fig5_GO_dotplot_Stroke.pdf/.png (原 Fig5_GO_dotplot 不动)。
            GO labels are single-line where possible, so the panel fits
            approximately 12 x 12.5 cm.
  * NO left group-name column. Each organ name is a bold horizontal heading
            placed inside the vertical gap between its block and the block
            above, aligned to the left.
  * Columns = 6 organs; a cell is drawn when that GO term is also significant
            (p_adjust<0.05) in that organ column.

Encoding: dot size = Gene ratio (capped 20%); colour = -log10(FDR) 1.30..4.66
"""
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize, LinearSegmentedColormap
from pathlib import Path

# ----------------------------------------------------------------------
# Paths and font setup
# ----------------------------------------------------------------------
FD = Path(_PROJECT + '/.cache/fonts')
for fn in ('Arial.ttf', 'Arial-Bold.ttf'):
    p = FD / fn
    if p.exists():
        fm.fontManager.addfont(str(p))

plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 9.0,
    'mathtext.fontset': 'custom',
    'mathtext.rm': 'Arial',
    'mathtext.it': 'Arial',
    'mathtext.bf': 'Arial:bold',
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#444444',
    'figure.dpi': 600,
    'savefig.dpi': 600,
})

OUT  = Path(_PROJECT + '/result/result906/panels')
BASE = Path(_PROJECT + '/result/of903/input907_analysis_output/go_enrichment/top50')

# ----------------------------------------------------------------------
# Global style constants
# ----------------------------------------------------------------------
ORGS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
        ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]
COLS = [lab for _, lab in ORGS]
TOPN = 5
XLIM = (-0.50, len(ORGS) - 0.50)

FS_XTICK   = 12.0
FS_YTICK   = 11.0     # GO row labels (increased for readability)
FS_GROUP   = 12.0     # organ headings
FS_CBLABEL = 13.0
FS_CBTICK  = 11.0
FS_LEG     = 10.0

NEGLOG_MIN = 1.3010
NEGLOG_MAX = 4.75
# Enhanced colour palette – brighter and more saturated
CMAP = LinearSegmentedColormap.from_list('sig_red', [
    (0.00, '#FFEDA0'),   # light amber
    (0.25, '#FDBF6F'),   # orange
    (0.50, '#F07B3F'),   # deep orange
    (0.75, '#D6291C'),   # red
    (1.00, '#5E0008'),   # dark crimson
])
RATIO_CAP = 0.20

# ----------------------------------------------------------------------
# 1. Load + build structure
# ----------------------------------------------------------------------
allbp = []
for o, _ in ORGS:
    df = pd.read_csv(BASE / f'{o}_GO_enrichment.csv').assign(organ=o)
    allbp.append(df)
allbp = pd.concat(allbp, ignore_index=True)
allbp = allbp[(allbp['Namespace'] == 'biological_process') & (allbp['p_adjust'] < 0.05)]
signif = allbp.set_index(['GO_ID', 'organ'])

blocks = []
for o, lab in ORGS:
    sub = (allbp[allbp['organ'] == o]
           .sort_values('p_adjust')
           .drop_duplicates('GO_ID')
           .head(TOPN))
    blocks.append((lab, o, sub))

# ----------------------------------------------------------------------
# 2. Metrics: single-line label column width (measured at FS_YTICK)
# ----------------------------------------------------------------------
_probe = plt.figure(figsize=(14, 14), dpi=600)
_rend = _probe.canvas.get_renderer()

def _w(t, fp):
    return _probe.text(0, 0, t, fontsize=fp).get_window_extent(renderer=_rend).width / 600 * 2.54

row_meta, labels = [], []
for lab, o, sub in blocks:
    for _, row in sub.iterrows():
        row_meta.append((lab, o, row['GO_ID'], row['GO_Name']))
        labels.append(row['GO_Name'])

LBL_COL = max(_w(l, FS_YTICK) for l in labels) + 0.12
plt.close(_probe)

# ----------------------------------------------------------------------
# 3. Vertical layout (30 rows, 6 heading gaps) in "line units"
# ----------------------------------------------------------------------
ROW_UNIT  = 1.0
INTER_PAD = 0.14
GAP_UNIT  = 1.60      # gap between blocks -> hosts the heading
BAND_PAD  = 0.22

layout, ypos = {}, []
cur = 0.0
for bi, (lab, o, sub) in enumerate(blocks):
    heights = [ROW_UNIT] * TOPN
    total = sum(heights) + INTER_PAD * (TOPN - 1)
    ys = []
    acc = 0.0
    for h in heights:
        ys.append(cur + acc + h / 2.0)
        acc += h + INTER_PAD
    layout[bi] = {'lab': lab, 'o': o, 'top': cur, 'bottom': cur + total, 'ys': ys}
    ypos.extend(ys)
    cur += total + INTER_PAD + GAP_UNIT

# heading y = midline of the gap ABOVE each block (block0 uses the top headroom)
TOP_HEADROOM = 1.30
y_top = layout[0]['top'] - TOP_HEADROOM       # top boundary (inverted axis)
for bi in range(len(blocks)):
    if bi == 0:
        layout[bi]['head_y'] = (y_top + layout[0]['top']) / 2.0
    else:
        layout[bi]['head_y'] = (layout[bi-1]['bottom'] + layout[bi]['top']) / 2.0

n_rows = len(ypos)
y_bot = layout[len(blocks) - 1]['bottom'] + 0.30   # bottom padding
total_units = (y_bot - y_top)           # positive span (inverted axis: big-y at bottom)

# ----------------------------------------------------------------------
# 4. Figure geometry (explicit axes so nothing stretches)
# ----------------------------------------------------------------------
LINE_REQ = 0.350           # cm per row-unit (配合更大气泡)
PLOT_H   = total_units * LINE_REQ
XTICK_STRIP = 1.10
TOP_MARGIN  = 0.40

# width components (DOT_W increased for a larger bubble area)
DOT_W  = 5.20               # was 3.40/4.00, now enlarged
CB_W   = 0.32
CB_TICK_W = 0.52
CB_LABEL_W = 0.58
G_W    = 0.10
MARGIN = 0.06

FW = LBL_COL + G_W + DOT_W + G_W + CB_W + CB_TICK_W + CB_LABEL_W + MARGIN
FH = PLOT_H + XTICK_STRIP + TOP_MARGIN

fig = plt.figure(figsize=(FW / 2.54, FH / 2.54))
ax_l = LBL_COL / FW
ax_w = DOT_W / FW
ax_b = XTICK_STRIP / FH
ax_h = PLOT_H / FH
ax_d = fig.add_axes([ax_l, ax_b, ax_w, ax_h])
cax_l = (LBL_COL + G_W + DOT_W + G_W) / FW
cax_w = CB_W / FW
cax = fig.add_axes([cax_l, ax_b + ax_h * 0.04, cax_w, ax_h * 0.88])

# --- organ-block background bands ---
for bi, g in layout.items():
    top, bot = g['top'] - BAND_PAD, g['bottom'] + BAND_PAD
    ax_d.add_patch(Rectangle((XLIM[0], top), XLIM[1] - XLIM[0], bot - top,
                             facecolor='#F4F6F8', edgecolor='#D0D7DD',
                             linewidth=0.4, zorder=0))
for bi in range(1, len(blocks)):
    sep = (layout[bi-1]['bottom'] + layout[bi]['top']) / 2.0
    ax_d.axhline(sep, color='#D0D7DD', lw=0.6, zorder=1, clip_on=False)

# --- organ headings: LEFT aligned, reduced font, placed in the gaps ---
for bi, g in layout.items():
    ax_d.text(XLIM[0] + 0.05, g['head_y'], g['lab'],
              fontsize=FS_GROUP, fontweight='bold', color='#1F2933',
              ha='left', va='center', zorder=4)

# --- dots ---
DM_MAX = 0.36           # cm (increased for better visibility)
S_SCALE = np.pi * ((DM_MAX * 28.3465) / 2.0) ** 2 / RATIO_CAP
for (lab_, o, goid, goname), y in zip(row_meta, ypos):
    for xi, (co, clab) in enumerate(ORGS):
        key = (goid, co)
        if key not in signif.index:
            continue
        hit = signif.loc[key]
        if isinstance(hit, pd.DataFrame):
            hit = hit.sort_values('p_adjust').iloc[0]
        ratio = min(float(hit['Count_in_test']) / float(hit['Test_size']), RATIO_CAP)
        neg = -np.log10(float(hit['p_adjust']))
        ax_d.scatter(xi, y, s=ratio * S_SCALE, c=[neg], cmap=CMAP,
                     vmin=NEGLOG_MIN, vmax=NEGLOG_MAX,
                     edgecolor='#5A5A5A', linewidth=0.3, zorder=3)

# --- axes cosmetics ---
ax_d.set_xlim(XLIM)
ax_d.set_ylim(y_bot, y_top)
ax_d.set_xticks(range(len(ORGS)))
ax_d.set_xticklabels(COLS, rotation=45, ha='right', rotation_mode='anchor',
                     fontsize=FS_XTICK, color='#1F2933')
ax_d.set_yticks(ypos)
ax_d.set_yticklabels(labels, fontsize=FS_YTICK, color='#1F2933')
ax_d.tick_params(axis='x', length=3, width=0.8, pad=4)
ax_d.tick_params(axis='y', length=0, pad=2.5)
for s in ('top', 'right'):
    ax_d.spines[s].set_visible(False)

# --- colourbar ---
sm = ScalarMappable(norm=Normalize(vmin=NEGLOG_MIN, vmax=NEGLOG_MAX), cmap=CMAP)
sm.set_array([])
cb = fig.colorbar(sm, cax=cax)
cb.set_label('-log$_{10}$(FDR)', fontsize=FS_CBLABEL, color='#1F2933',
             fontweight='bold', labelpad=5)
cb.ax.tick_params(labelsize=FS_CBTICK, color='#444444', length=3)
cb.outline.set_linewidth(0.8)
cb.outline.set_edgecolor('#444444')
cb.ax.yaxis.set_major_locator(plt.MaxNLocator(6))  # more ticks for precision

# --- gene-ratio size legend (fixed at upper‑right, semi‑transparent) ---
def leg_ms(ratio):
    return 2.0 * np.sqrt(ratio * S_SCALE / np.pi)

leg_ratios = [0.05, 0.10, 0.20]
leg_handles = [Line2D([0], [0], marker='o', ls='', markerfacecolor='#AEB6BF',
                      markeredgecolor='#555555', markeredgewidth=0.4,
                      markersize=leg_ms(r)) for r in leg_ratios]

leg = ax_d.legend(leg_handles, [f'{r*100:.0f}%' for r in leg_ratios],
                  title='Gene ratio', title_fontsize=10.0, fontsize=9.0,
                  loc='upper right', bbox_to_anchor=(0.98, 0.98),
                  bbox_transform=ax_d.transAxes, frameon=True, fancybox=True,
                  framealpha=0.85, borderpad=0.45, labelspacing=0.48,
                  handletextpad=0.36, handlelength=0.8, columnspacing=0.0,
                  edgecolor='#B9C2CC', borderaxespad=0.0)
leg.set_zorder(6)
leg.get_title().set_color('#1F2933')
for t in leg.get_texts():
    t.set_color('#1F2933')

# ----------------------------------------------------------------------
# Save & report
# ----------------------------------------------------------------------
fig.savefig(OUT / 'Fig5_GO_dotplot_Stroke.pdf', dpi=600, bbox_inches='tight', pad_inches=0.03)
fig.savefig(OUT / 'Fig5_GO_dotplot_Stroke.png', dpi=600, bbox_inches='tight', pad_inches=0.03)
plt.close(fig)

from PIL import Image
im = Image.open(OUT / 'Fig5_GO_dotplot.png')
w_cm = im.size[0] / 600 * 2.54
h_cm = im.size[1] / 600 * 2.54
print(f'OK rows={n_rows} blocks={len(blocks)} cells={len(signif)}')
print(f'    LBL_COL={LBL_COL:.2f}cm  total_units={total_units:.1f}  S_SCALE={S_SCALE:.0f}')
print(f'    fig=(FW={FW:.2f} FH={FH:.2f})cm  size={w_cm:.2f} x {h_cm:.2f} cm')
