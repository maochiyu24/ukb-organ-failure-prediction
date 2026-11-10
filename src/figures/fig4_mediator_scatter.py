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
"""Fig4C/D (v906): J44 式 |beta_a| x |beta_b| 双轴散点 (独立两图)
Fig4C = Lifestyle, Fig4D = Psychosocial (Any organ failure 层面, 显著通路)
颜色=3类中介; 形状=方向(o 正向 / v 逆-保护); 气泡大小=|a*b|; 每类 top1 标注
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from naming import mediator_name

_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 10, 'axes.labelsize': 11,
    'axes.titlesize': 12, 'legend.fontsize': 8.5, 'xtick.labelsize': 9,
    'ytick.labelsize': 9, 'figure.dpi': 600, 'savefig.dpi': 600,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.8, 'grid.linewidth': 0.4, 'axes.grid': False,
})
OUT = _PROJECT + '/result/result906/panels'
AB = os.path.join(_PROJECT, 'cache', 'ab_paths_organ.csv')
R = _PROJECT + '/result/of903'
res = pd.read_csv(f'{R}/06_mediation_v2/mediation_results_all_all_all.csv')

df = pd.read_csv(AB)
df['mcat'] = df['Mediator'].str.split('__').str[0]
df['nm'] = df['Mediator'].apply(mediator_name)
df['abs_a'] = df['a'].abs()
df['abs_b'] = df['b'].abs()
df['ab'] = (df['a'] * df['b']).abs()
df['pos'] = (df['a'] * df['b']) > 0

CATS = ['proteome', 'metabolome', 'blood']
CAT_LABEL = {'proteome': 'Proteomics', 'metabolome': 'Metabolomics',
             'blood': 'Biochemical measures'}
COLORS = {'proteome': '#C00000', 'metabolome': '#4472C4', 'blood': '#70AD47'}
EXP = {'lifestyle_score_v2': 'Healthy behaviour', 'psych_score_v2': 'Psychological distress'}
SHAPE = {True: 'o', False: 'v'}
SHAPE_L = {True: 'positive (a·b > 0)', False: 'inverse (a·b < 0)'}

VMAX = df['ab'].max()


def ms(v, smin=16, smax=190):
    val = max(v, 1.2e-4)
    f = (np.log10(val) - np.log10(1.2e-4)) / (np.log10(VMAX) - np.log10(1.2e-4))
    return smin + (smax - smin) * f


def draw_one(exp, fname):
    sub = df[df['Exposure'] == exp].copy()
    # 只保留 ACME 显著通路 (与 ab 缓存对齐)
    sig_med = set(res[(res['Organ'] == 'organ') & (res['Exposure'] == exp)
                      & (res['ACME_p'] < 0.05)]['Mediator'])
    sub = sub[sub['Mediator'].isin(sig_med)]

    fig, ax = plt.subplots(figsize=(4.5, 4.0))
    for mc in CATS:
        g = sub[sub['mcat'] == mc]
        for _, r in g.iterrows():
            ax.scatter(r['abs_a'], r['abs_b'], s=ms(r['ab']),
                       marker=SHAPE[r['pos']], facecolor=COLORS[mc],
                       edgecolor='white', linewidths=0.6, alpha=0.90, zorder=3)
    # 每类 top1 (按 |a*b|) 标注
    for mc in CATS:
        g = sub[sub['mcat'] == mc]
        if g.empty:
            continue
        r = g.sort_values('ab', ascending=False).iloc[0]
        ax.annotate(r['nm'], (r['abs_a'], r['abs_b']), fontsize=8,
                    fontweight='bold', color='#222222', xytext=(7, 6),
                    textcoords='offset points',
                    bbox=dict(fc='white', ec='#BBBBBB', alpha=0.90,
                              boxstyle='round,pad=0.18', lw=0.7), zorder=5)
    ax.set_xscale('log'); ax.set_yscale('log')
    xlo, xhi = sub['abs_a'].min() / 1.4, sub['abs_a'].max() * 2.2
    ylo, yhi = sub['abs_b'].min() / 1.6, sub['abs_b'].max() * 1.5
    ax.set_xlim(xlo, xhi); ax.set_ylim(ylo, yhi)
    ax.set_xlabel('|βa|  exposure → mediator', fontweight='bold')
    ax.set_ylabel('|βb|  mediator → outcome (logOR)', fontweight='bold')
    ax.grid(True, which='major', alpha=0.16, ls=':', lw=0.5)
    # 两个图例: 类别+方向 -> 左下角; 气泡大小 -> 右上角
    h1 = [Line2D([0], [0], marker='o', ls='', markerfacecolor=COLORS[c],
                 markeredgecolor='white', ms=8, label=CAT_LABEL[c]) for c in CATS]
    h2 = [Line2D([0], [0], marker=SHAPE[k], ls='', markerfacecolor='#777777',
                 markeredgecolor='white', ms=7, label=SHAPE_L[k])
          for k in (True, False)]
    leg1 = ax.legend(handles=h1 + h2, loc='lower left', frameon=True,
                     fancybox=True, framealpha=0.92, fontsize=7.8,
                     handlelength=1.1, labelspacing=0.35, borderpad=0.35)
    leg1.get_frame().set_linewidth(0.6); leg1.get_frame().set_edgecolor('#BBBBBB')
    ax.add_artist(leg1)
    handles = [Line2D([0], [0], marker='o', ls='', markerfacecolor='#BFBFBF',
                      markeredgecolor='#666666', ms=np.sqrt(ms(v)) / 2.4,
                      label=f'{v:g}') for v in (1e-3, 1e-2, 5e-2)]
    leg2 = ax.legend(handles=handles, title='|a·b|', loc='upper right',
                     frameon=True, fancybox=True, framealpha=0.92, fontsize=7.6,
                     title_fontsize=7.8, handletextpad=0.4, borderpad=0.3,
                     labelspacing=0.5)
    leg2.get_frame().set_linewidth(0.6); leg2.get_frame().set_edgecolor('#BBBBBB')
    ax.set_title(EXP[exp], fontsize=12, fontweight='bold', pad=7)
    fig.savefig(f'{OUT}/{fname}.pdf', dpi=600)
    fig.savefig(f'{OUT}/{fname}.png', dpi=600)
    plt.close(fig)
    from PIL import Image
    im = Image.open(f'{OUT}/{fname}.png')
    print(f'{fname} n={len(sub)} -> {im.size[0]/600*2.54:.2f}x{im.size[1]/600*2.54:.2f} cm')


draw_one('lifestyle_score_v2', 'Fig4C')
draw_one('psych_score_v2', 'Fig4D')
