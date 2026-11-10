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
"""pic904 统一绘图样式"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

FONT_DIR = _PROJECT + '/.cache/fonts'
for _f in ['LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf']:
    _p = os.path.join(FONT_DIR, _f)
    if os.path.exists(_p):
        font_manager.fontManager.addfont(_p)

plt.rcParams.update({
    'font.family': 'Liberation Sans',
    'font.size': 8,
    'axes.titlesize': 9.5,
    'axes.titleweight': 'bold',
    'axes.labelsize': 8.5,
    'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5,
    'legend.fontsize': 7.5,
    'axes.linewidth': 0.7,
    'xtick.major.width': 0.6,
    'ytick.major.width': 0.6,
    'figure.dpi': 300,
    'savefig.dpi': 600,
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.linestyle': ':',
    'grid.linewidth': 0.6,
})

from naming import ORG_CN, ORGANS, MOD_LABEL  # 统一正式命名

# 模态配色 (贯穿全文)
COLORS = {
    'proteome': '#C00000', 'metabolome': '#4472C4', 'blood': '#70AD47',
    'lifestyle': '#ED7D31', 'psych': '#A23B72', 'prs': '#7F7F7F',
    'history': '#BFBFBF', 'brain': '#00A2E8', 'merge': '#7030A0',
}

OUT_MAIN = _PROJECT + '/result/result905/figures_main'
OUT_SUPP = _PROJECT + '/result/result905/figures_supp'
OUT_COMB = _PROJECT + '/result/result905/figures_combined'
OUT_REV = _PROJECT + '/result/result905/figures_review'
for _d in (OUT_MAIN, OUT_SUPP, OUT_COMB, OUT_REV):
    import os as _os
    _os.makedirs(_d, exist_ok=True)


def save(fig, name, dpi_pdf=600, dpi_png=300, outdir=None):
    outdir = outdir or OUT_MAIN
    fig.savefig(f'{outdir}/{name}.pdf', dpi=dpi_pdf, bbox_inches='tight')
    fig.savefig(f'{outdir}/{name}.png', dpi=dpi_png, bbox_inches='tight')
    plt.close(fig)
    print(f'OK {name}')
