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
"""Fig3 (v906 v2 restyle): merge 模型前向选择排序 — 双轴图 (参考 Delong 选择图)
- 左轴: 各特征 Ensemble 重要性条形, 按模态着色 (展示 merge 中各模态排序)
- 右轴: 前向选择累积 AUC (AUC_mean ± AUC_std 带); 连续显著段(nb_f)前红、之后深灰; nb_f 竖参考线
- 正文: Fig3A=Heart, Fig3B=Kidney, Fig3C=Any organ failure (result906/panels)
   版式: 将来 1x2 一行两张 -> 单张横长条 (宽扁)
- 附图: FigS3_Lung/Liver/Hematologic/Stroke (result906/figures_supp)
   版式: 3x2 附图网格单格 -> 小尺寸, K 下调以保持可读 (nb_f 完整可见)
- 无 A/B 字母; 标题=器官名; Arial; 600dpi; 数值/统计/命名 100% 不动
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import matplotlib.ticker
from naming import full_feature_name, MOD_LABEL

# ---- 字体 (Arial) ----
_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
# 文字色: 避免纯黑, 用 #333-#555 更柔和
TXT = '#333333'
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 9, 'axes.labelsize': 9,
    'axes.titlesize': 10.5, 'legend.fontsize': 6.8, 'xtick.labelsize': 7,
    'ytick.labelsize': 7, 'figure.dpi': 600, 'savefig.dpi': 600,
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.04,
    'axes.linewidth': 0.6, 'grid.linewidth': 0.35, 'axes.grid': False,
    'text.color': TXT, 'axes.edgecolor': TXT, 'axes.labelcolor': TXT,
    'xtick.color': TXT, 'ytick.color': TXT,
})
R903 = _PROJECT + '/result/of903'
OUT_M = _PROJECT + '/result/result906/panels'
OUT_S = _PROJECT + '/result/result906/figures_supp'
os.makedirs(OUT_M, exist_ok=True); os.makedirs(OUT_S, exist_ok=True)

# ---- 基色 (保守鲜艳) 后统一 lighten 降对比; 图例色块同步 ----
BASE = {'proteome': '#C00000', 'metabolome': '#4472C4', 'blood': '#70AD47',
        'lifestyle': '#ED7D31', 'psych': '#A23B72', 'prs': '#8C8C8C',
        'history': '#B8B8B8'}
BAR_ALPHA = 0.96     # 更接近不透明, 以厚重色调消除填充带透底; 靠 lighten 更多降对比
LIGHTEN = 0.42       # 基础色向白混入比例 -> 更浅更淡 (柔和 pastel)


def _hex(c):
    c = c.lstrip('#')
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _lighten(c, t=LIGHTEN):
    r, g, b = _hex(c)
    return (r + (1 - r) * t, g + (1 - g) * t, b + (1 - b) * t)


COLORS = {k: _lighten(v) for k, v in BASE.items()}
# AUC: 红=显著段 (稍柔), 灰=其后; 填充带浅; 参考线灰
C_RED = '#CC4444'
C_GRAY = '#6E6E6E'
FILL = '#E8C4C0'
REF_LINE = '#A6A6A6'
GRID_ALPHA = 0.12


def nb_forward(p):
    i = 0
    while i + 1 < len(p) and (p[i] < 0.05 or p[i + 1] < 0.05):
        i += 1
    return i + 1


def draw_one(o, title, out, fname, figsize, k, fs):
    """fs: dict of font sizes {title, axlab, tick, leg} for this panel size."""
    d = pd.read_csv(f'{R903}/04_fusion/{o}_merge/Delong_Selection_Results.csv')
    top = pd.read_csv(f'{R903}/04_fusion/{o}_merge/Top_90_InfoGain_features.csv')
    mf = pd.read_csv(f'{R903}/04_fusion/{o}_merge/merge_features.csv')
    mod = dict(zip(mf['feature'], mf['modality']))
    imp = dict(zip(top['feature'], top['Ensemble_cv']))
    d = d.head(k).reset_index(drop=True)
    feats = d['feature'].tolist()
    imp_v = [imp.get(f, 0.0) for f in feats]
    mods = [mod.get(f, 'proteome') for f in feats]
    auc = d['AUC_all'].values
    lo = np.clip(d['AUC_mean'].values - d['AUC_std'].values, 0.4, None)
    hi = np.clip(d['AUC_mean'].values + d['AUC_std'].values, None, 1.0)
    nb_f = min(nb_forward(d['Delong1'].values), k)   # Delong1: 与全链一致(选择/模型/表S2/正文均 Delong1<0.05)

    fig, ax = plt.subplots(figsize=figsize)
    x = np.arange(len(feats))
    for xi, (mv, f) in enumerate(zip(mods, feats)):
        ax.bar(xi, imp_v[xi], width=0.74, color=COLORS.get(mv, '#C8C8C8'),
               alpha=BAR_ALPHA, edgecolor='none', zorder=3)
    ax.set_xticks(x)
    ax.set_xticklabels([full_feature_name(f) for f in feats], rotation=45,
                       ha='right', fontsize=fs['tick'], rotation_mode='anchor')
    ax.set_xlim(-0.6, len(feats) - 0.4)
    ax.set_ylim(0, max(imp_v) * 1.12)
    ax.set_ylabel('Ensemble importance', fontweight='bold', fontsize=fs['axlab'])
    ax.grid(True, axis='y', alpha=GRID_ALPHA, linewidth=0.35, color='#808080')
    ax.set_axisbelow(True)

    # 独立 twinx: 填充带 (置于条形之后)
    axb = ax.twinx()
    axb.set_zorder(ax.get_zorder() - 1)
    ax.patch.set_visible(False)         # 让底层轴背景透明, 使 axb 内容先画
    axb.fill_between(x, lo, hi, color=FILL, alpha=0.38, zorder=1,
                     edgecolor='none')

    # 独立 twinx: AUC 折线 (置于条形之上), 负责右轴刻度/标签
    ax2 = ax.twinx()
    ax2.set_zorder(ax.get_zorder() + 1)
    ax2.plot(x[:nb_f], auc[:nb_f], color=C_RED, lw=1.4, marker='o', ms=2.6,
             zorder=6, label='Significant AUC')
    if nb_f < len(auc):
        ax2.plot(x[nb_f - 1:nb_f + 1], auc[nb_f - 1:nb_f + 1], color=C_RED,
                 lw=1.4, ms=2.6, zorder=6)
        # 灰段后画且 zorder>=红线: 交界点(灰色)盖在红色线段上方
        ax2.plot(x[nb_f:], auc[nb_f:], color=C_GRAY, lw=1.4, marker='o', ms=2.6,
                 zorder=7, label='Cumulative AUC')   # 后画覆盖交界红点, 点大小一致
    else:
        ax2.plot(x, auc, color=C_RED, lw=1.4, marker='o', ms=2.6, zorder=6)
        ax2.plot([], [], color=C_GRAY, lw=1.4, marker='o', ms=2.6, label='Cumulative AUC')
    ax2.set_ylabel('Cumulative AUC', fontweight='bold', fontsize=fs['axlab'])
    for a2 in (axb, ax2):
        a2.set_ylim(max(0.50, auc.min() - 0.05), min(1.0, auc.max() + 0.05))
        a2.set_yticks([])                # 用统一 twiny 的 ticks
    ax2.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(6))
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter('%.2f'))
    ax2.tick_params(labelsize=fs['tick'])
    if nb_f < len(feats):
        ax.axvline(nb_f - 0.5, color=REF_LINE, ls=':', lw=0.9, zorder=4)

    # 两个独立图例 (均挂顶层 ax2, 置顶避免线段穿框)
    seen = []
    for mv in mods:
        if mv not in seen:
            seen.append(mv)
    h_mod = [Rectangle((0, 0), 1, 1, facecolor=COLORS[mv], alpha=BAR_ALPHA,
                       edgecolor='none') for mv in seen]
    l_mod = [MOD_LABEL[mv] for mv in seen]          # 正式模态名 (Proteomics 等)
    h_auc = [Line2D([0], [0], color=C_RED, lw=1.4, marker='o', ms=2.6),
             Line2D([0], [0], color=C_GRAY, lw=1.4, marker='o', ms=2.6)]
    l_auc = ['Significant', 'Non-significant']
    leg_mod = ax2.legend(handles=h_mod, labels=l_mod, loc='lower right',
                         frameon=True, fancybox=True, framealpha=0.92,
                         fontsize=fs['leg'], handlelength=1.0, handletextpad=0.4,
                         borderpad=0.35, labelspacing=0.25, borderaxespad=0.2)
    ax2.add_artist(leg_mod)
    leg_auc = ax2.legend(handles=h_auc, labels=l_auc, loc='upper right',
                         frameon=True, fancybox=True, framealpha=0.92,
                         fontsize=fs['leg'], handlelength=1.4, handletextpad=0.5,
                         borderpad=0.35, labelspacing=0.3, borderaxespad=0.2)
    for _lg in (leg_mod, leg_auc):
        _lg.set_zorder(20)

    ax.set_title(title, fontsize=fs['title'], fontweight='bold', pad=5,
                 color='#1A1A1A')
    fig.savefig(f'{out}/{fname}.pdf', dpi=600)
    fig.savefig(f'{out}/{fname}.png', dpi=600)
    plt.close(fig)
    from PIL import Image
    im = Image.open(f'{out}/{fname}.png')
    print(f'{title:18s} K={k} nb_f={nb_f} 末AUC={auc[-1]:.3f} '
          f'-> {im.size[0]/600*2.54:.2f}x{im.size[1]/600*2.54:.2f} cm')


# ---- 正文 (1x2 一行两张 -> 横长条, 宽扁): ~17 x ~6.6cm ----
MAIN_FS = dict(title=10.5, axlab=9, tick=7, leg=6.8)
MAIN_FIG = (5.30, 2.30)  # -> tight 后 ~12.96 x 7.13 cm (用户选定比例, w/h=1.82)
draw_one('heart', 'Heart', OUT_M, 'Fig3A', MAIN_FIG, 20, MAIN_FS)
draw_one('renal', 'Kidney', OUT_M, 'Fig3B', MAIN_FIG, 20, MAIN_FS)
draw_one('organ', 'Any organ failure', OUT_S, 'FigS3_AnyOrganFailure', MAIN_FIG, 20, MAIN_FS)

# ---- 附图: 比例与主图保持一致 (同 figsize/字号/K) ----
for o, lab in [('lung', 'Lung'), ('liver', 'Liver'), ('hemat', 'Hematologic'),
               ('brain', 'Stroke')]:
    draw_one(o, lab, OUT_S, f'FigS3_{lab}', MAIN_FIG, 20, MAIN_FS)
