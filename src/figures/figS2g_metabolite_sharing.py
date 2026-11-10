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
"""FigS2G: Cross-system presence matrix of top-15 metabolome proteins.

六系统 (Heart, Lung, Liver, Kidney, Hematologic, Stroke) 各自 metabolome top-15
(按 Ensemble_cv 降序) 中出现于 >=2 个系统的蛋白 (16 个) 构成 6 行 x 16 列存在矩阵。

风格与 Fig2A-F 和谐: 白底, viridis 系数据色, 浅灰网格, Arial, 无 A-F 字母,
简洁标题, savefig tight, 600 dpi。输出 FigS2G.pdf / FigS2G.png。

Run: python src/figures/figS2g_metabolite_sharing.py
"""
import os
import sys
import textwrap
from collections import Counter

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap
from matplotlib.patches import Rectangle
from naming import metab_name

# ---- 字体 (Arial) ----
_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 8, 'axes.labelsize': 9,
    'axes.titlesize': 10, 'legend.fontsize': 8, 'xtick.labelsize': 8,
    'ytick.labelsize': 8.5, 'figure.dpi': 600, 'savefig.dpi': 600,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6, 'grid.linewidth': 0.4, 'axes.grid': False,
})

OUT = _PROJECT + '/result/result906/figures_supp'
R903 = _PROJECT + '/result/of903/02_ranking'
os.makedirs(OUT, exist_ok=True)

# 六系统 (organ code, 显示名);  显示顺序由上而下 = Stroke..Heart (Heart 在图底部)
SYS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
       ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]
SYS_TOP = SYS                 # 行显示顺序: Heart(顶) -> Stroke(底), 与 Fig1B 一致
MIN_SYSTEMS = 2              # 蛋白须出现于 >=2 系统

# 配色: 和谐于 viridis (Fig2A-F). 出现 = viridis 系深青绿, 未出现 = 极浅灰白
COL_PRESENT = '#21918c'      # viridis mid-high teal-green
COL_ABSENT = '#f2f2f2'       # 极浅灰
GRID = '#e3e3e3'
TITLE = 'Cross-system overlap of top-15 metabolome biomarkers'
FILE = 'FigS2G'


def load_top15(key):
    df = pd.read_csv(f'{R903}/{key}_metabolome/Top_90_InfoGain_features.csv')
    df = df.sort_values('Ensemble_cv', ascending=False).reset_index(drop=True)
    return [metab_name(f) for f in df.head(15)['feature']]


def build():
    top = {lab: load_top15(k) for k, lab in SYS}
    cnt = Counter()
    for names in top.values():
        cnt.update(set(names))
    shared = sorted([n for n, c in cnt.items() if c >= MIN_SYSTEMS],
                    key=lambda n: (-cnt[n], n))   # 次数降序, 同名按首字排序
    mat = np.array([[1 if p in top[lab] else 0 for p in shared]
                    for _, lab in SYS_TOP])       # 行 = SYS_TOP
    return [lab for _, lab in SYS_TOP], shared, mat, cnt


def draw(rows, cols, mat, cnt):
    nrow, ncol = mat.shape
    fig, ax = plt.subplots(figsize=(7.5, 2.6))   # 更宽更扁 (2x3 + 1x3 底行横条比例)

    cmap = ListedColormap([COL_ABSENT, COL_PRESENT])
    ax.imshow(mat, cmap=cmap, aspect='auto', interpolation='nearest')

    # 单元格刻度
    ax.set_xticks(np.arange(ncol))
    ax.set_yticks(np.arange(nrow))
    ax.set_xticklabels(['\n'.join(textwrap.wrap(c, 24)) if len(c) > 24 else c
                        for c in cols], rotation=45, ha='right', fontsize=6.8,
                       rotation_mode='anchor')
    ax.set_yticklabels(rows)

    # 浅灰网格 (cell 边界, 克制)
    ax.set_xticks(np.arange(-0.5, ncol, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nrow, 1), minor=True)
    ax.grid(which='minor', color=GRID, linewidth=0.5, linestyle='-')
    ax.tick_params(which='minor', length=0)

    # 去多余装饰
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)
    for s in ('left', 'bottom'):
        ax.spines[s].set_color('#888888')

    # 出现于全部 6 系统的列 (代谢组: Albumin/Glutamine/GlycA) subtle 强调
    for j, c in enumerate(cols):
        if cnt[c] == len(rows):
            ax.get_xticklabels()[j].set_fontweight('bold')
            ax.add_patch(Rectangle((j - 0.5, -0.5), 1, nrow,
                                   fill=False, edgecolor='#8c8c8c',
                                   linewidth=1.0, zorder=4))

    ax.set_title(TITLE, fontsize=10, fontweight='bold', pad=8)

    fig.savefig(f'{OUT}/{FILE}.pdf', dpi=600)
    fig.savefig(f'{OUT}/{FILE}.png', dpi=600)
    plt.close(fig)

    from PIL import Image
    im = Image.open(f'{OUT}/{FILE}.png')
    w_cm, h_cm = im.size[0] / 600 * 2.54, im.size[1] / 600 * 2.54
    print(f'OK {FILE}  matrix {nrow}x{ncol}  -> {w_cm:.2f} x {h_cm:.2f} cm '
          f'({im.size[0]}x{im.size[1]} px @600dpi)')
    return im.size


if __name__ == '__main__':
    rows, cols, mat, cnt = build()
    print('Rows (top->bottom):', rows)
    print('Cols:', cols)
    print('Counts:', {c: cnt[c] for c in cols})
    for r, mrow in zip(rows, mat):
        print(f'  {r:12s}', ''.join('X' if v else '.' for v in mrow))
    draw(rows, cols, mat, cnt)

    # 数据红线自检 (代谢组: 无蛋白名假设, 动态校验)
    assert len(cols) >= 8, len(cols)   # 此处为 20
    assert all(cnt[c] >= MIN_SYSTEMS for c in cols)
    print('data red-line checks passed')
