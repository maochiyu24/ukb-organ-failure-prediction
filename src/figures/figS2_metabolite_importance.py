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
"""Fig2 (v906 v1): 六系统 metabolome 特征重要性气泡 — 每个系统一张单图
- x = Gain importance (TotalGain_cv), y = SHAP importance, 点大小/颜色 = Ensemble importance (viridis)
- 顶 3 蛋白标注 (metab_name) + 回归线(R², 4位) + colorbar
- 无 A-F 字母; 标题=器官名; Arial; 正方比例; 输出 result/result906/figures_supp/Fig2_{Heart..Stroke}.pdf/.png
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from scipy import stats
from naming import metab_name

_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 9, 'axes.labelsize': 10,
    'axes.titlesize': 11, 'legend.fontsize': 8, 'xtick.labelsize': 9,
    'ytick.labelsize': 9, 'figure.dpi': 600, 'savefig.dpi': 600,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6, 'grid.linewidth': 0.4, 'axes.grid': False,
})
OUT = _PROJECT + '/result/result906/figures_supp'
os.makedirs(OUT, exist_ok=True)
R903 = _PROJECT + '/result/of903'

SYS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
       ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]

for k, lab in SYS:
    df = pd.read_csv(f'{R903}/02_ranking/{k}_metabolome/Top_90_InfoGain_features.csv')
    df = df.sort_values('Ensemble_cv', ascending=False).reset_index(drop=True)
    x = df['TotalGain_cv'].values
    y = df['ShapValues_cv'].values
    ens = df['Ensemble_cv'].values

    fig, ax = plt.subplots(figsize=(4.7, 3.9))
    sc = ax.scatter(x, y, c=ens, s=ens * 5200, cmap='viridis',
                    alpha=0.80, edgecolor='none', zorder=2)

    # 顶 3 蛋白标注 (白底, 偏移右上方, 避免与回归线/R2 重叠时手动微调)
    for _, r in df.head(3).iterrows():
        ax.annotate(metab_name(r['feature']), (r['TotalGain_cv'], r['ShapValues_cv']),
                    fontsize=8, fontweight='bold', xytext=(8, 7),
                    textcoords='offset points',
                    bbox=dict(fc='white', ec='#CCCCCC', alpha=0.85, pad=1.5),
                    zorder=5)

    # 回归线 + R2 (中性深灰, 4 位小数)
    slope, intercept, rval, _, _ = stats.linregress(x, y)
    xs = np.linspace(x.min(), x.max(), 60)
    ax.plot(xs, slope * xs + intercept, color='#555555', ls='--', lw=1.2, zorder=3)
    ax.text(0.04, 0.96, f'R\u00b2 = {rval ** 2:.4f}', transform=ax.transAxes,
            fontsize=9, color='#444444', fontweight='bold', va='top', zorder=4)

    ax.set_title(lab, fontsize=11, fontweight='bold', pad=6)   # 器官名标题
    ax.set_xlabel('Gain importance', fontweight='bold')
    ax.set_ylabel('SHAP importance', fontweight='bold')
    ax.grid(True, alpha=0.15, linewidth=0.3)
    ax.set_axisbelow(True)

    cb = fig.colorbar(sc, ax=ax, shrink=0.85, pad=0.03)
    cb.set_label('Ensemble importance', fontsize=8)
    cb.ax.tick_params(labelsize=7.5)

    fig.savefig(f'{OUT}/FigS2_{lab}.pdf', dpi=600)
    fig.savefig(f'{OUT}/FigS2_{lab}.png', dpi=600)
    plt.close(fig)
    from PIL import Image
    im = Image.open(f'{OUT}/FigS2_{lab}.png')
    print(f'{lab:12s} n={len(df):4d}  R2={rval**2:.4f}  -> {im.size[0]/600*2.54:.2f}x{im.size[1]/600*2.54:.2f} cm')
