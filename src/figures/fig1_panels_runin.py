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
fig1_panels_runin.py — Fig 1 四个子图(标签/run-in 口径, 与原 v906 拼图风格完全一致)
=================================================================================
口径(与 Table 1 一致):
  队列 = 502,131 排除 prevalent 或基线后首年事件(诊断矩阵值 2) → 492,904
  No event 440,621 | Any event 52,283;器官事件: heart 16,616 / lung 8,283 / liver 2,722 /
  kidney 24,800 / haematologic 5,690 / stroke 12,064
  事件年龄 = 基线年龄 + of905 器官事件时间(标签事件时间覆盖 100%)
风格: 逐行复刻 v906 四个脚本(figsize / 配色 #D62728 红, #4C72B0 蓝 / alpha 0.70 /
      hist+KDE / 横条 / 纵向 100% 堆叠 / seaborn split violin + Bonferroni 星号)
输出: result/all913/fig1_panels/
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from scipy import stats
import seaborn as sns

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
OUT = _PROJECT + '/result/all913/fig1_panels'
os.makedirs(OUT, exist_ok=True)
C_EVT, C_NOE, C_FEM, C_MAL = '#D62728', '#4C72B0', '#D62728', '#4C72B0'
SYS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
       ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]

# ---------------- 数据: 标签/run-in 口径 ----------------
M = _PROJECT + '/xm/ZS/8.7/data/all_icd_f_group_1000_25y_instance0.csv'
CODES = {'heart': ['I50'], 'lung': ['J96'], 'liver': ['K72', 'K74'],
         'renal': ['N17', 'N19'], 'hemat': ['D68', 'D69'],
         'brain': ['I60', 'I61', 'I62', 'I63', 'I64']}
need = ['Participant ID'] + sorted({c for v in CODES.values() for c in v})
lab = pd.read_csv(M, usecols=lambda c: c in need, dtype={'Participant ID': str})
val = {o: lab[cs].max(axis=1) for o, cs in CODES.items()}
excl = pd.concat([(v == 2) for v in val.values()], axis=1).any(axis=1)
cap = lab[~excl].copy()
for o in CODES:
    cap[f'g_{o}'] = (val[o] == 1) & (~excl)
cap['g_organ'] = cap[[f'g_{o}' for o in CODES]].any(axis=1)

bl = pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
                 usecols=['Participant ID', 'Age at recruitment', 'Sex'])
bl.columns = ['PID', 'Age', 'Sex']; bl['PID'] = bl['PID'].astype(str)
surv = pd.read_csv(_PROJECT + '/result/of905/05_survival/survival_matrix.csv',
                   dtype={'eid': str}, usecols=['eid'] + [f'{o}_time' for o in CODES])
d = (cap.rename(columns={'Participant ID': 'PID'}).merge(bl, on='PID', how='left')
       .merge(surv.rename(columns={'eid': 'PID'}), on='PID', how='left'))
d['Age'] = pd.to_numeric(d['Age'], errors='coerce')
d['Sex'] = d['Sex'].map({0: 'Female', 1: 'Male'})

# ---------------- Fig1A: 年龄分布(hist + KDE) ----------------
e0, e1 = d[d.g_organ == 0], d[d.g_organ == 1]
print(f'N = {len(d):,}  |  No event {len(e0):,}  |  Any event {len(e1):,}')
fig, ax = plt.subplots(figsize=(4.2, 3.5))
bins = np.arange(37, 74, 2)
for lab_, dfg, c, ls in [('No event', e0, C_NOE, '--'), ('Any event', e1, C_EVT, '-')]:
    v = dfg['Age'].dropna()
    ax.hist(v, bins=bins, density=True, alpha=0.35, color=c, edgecolor='white', linewidth=0.4)
    sns.kdeplot(v, ax=ax, color=c, linestyle=ls, linewidth=1.6, cut=0,
                label=f'{lab_} (n={len(v):,})')
ax.set_xlabel('Age at baseline (years)', fontweight='bold')
ax.set_ylabel('Density', fontweight='bold')
ax.set_xlim(38, 74)
ax.legend(frameon=True, fancybox=True, framealpha=0.9, fontsize=8, loc='upper left')
ax.grid(True, alpha=0.2, linewidth=0.3)
fig.savefig(f'{OUT}/Fig1A_age_distribution.pdf'); fig.savefig(f'{OUT}/Fig1A_age_distribution.png'); plt.close(fig)

# ---------------- Fig1B: 事件数(横条) ----------------
cnts = [int(d[f'g_{k}'].sum()) for k, _ in SYS]
fig, ax = plt.subplots(figsize=(4.4, 3.2))
y = np.arange(len(SYS))[::-1]
ax.barh(y, cnts, height=0.6, color=C_EVT, alpha=0.70, edgecolor='white', linewidth=0.5)
for yi, c in zip(y, cnts):
    ax.text(c + max(cnts) * 0.012, yi, f'{c:,}', va='center', fontsize=8, color='#333333')
ax.set_yticks(y); ax.set_yticklabels([lab_ for _, lab_ in SYS], fontsize=9)
ax.set_xlim(0, max(cnts) * 1.22)
ax.set_xlabel('Number of events', fontweight='bold')
ax.grid(True, axis='x', alpha=0.2, linewidth=0.3); ax.set_axisbelow(True)
fig.savefig(f'{OUT}/Fig1B_event_counts.pdf'); fig.savefig(f'{OUT}/Fig1B_event_counts.png'); plt.close(fig)

# ---------------- Fig1C: 性别构成(纵向 100% 堆叠) ----------------
cats = [('No event', d.g_organ == 0, True)] + [(lab_, d[f'g_{k}'] == 1, False) for k, lab_ in SYS]
fig, ax = plt.subplots(figsize=(4.6, 3.9))
x = np.arange(len(cats))
for xi, (lab_, mask, ref) in zip(x, cats):
    sub = d[mask]
    f = int((sub['Sex'] == 'Female').sum()); m = int((sub['Sex'] == 'Male').sum())
    pf, pm = f / (f + m) * 100, m / (f + m) * 100
    ax.bar(xi, pf, width=0.62, color=C_FEM, alpha=0.70, edgecolor='white', linewidth=0.5,
           label='Female' if xi == 0 else None)
    ax.bar(xi, pm, bottom=pf, width=0.62, color=C_MAL, alpha=0.70, edgecolor='white', linewidth=0.5,
           label='Male' if xi == 0 else None)
    ax.text(xi, pf / 2, f'{pf:.1f}%', ha='center', va='center', fontsize=7, color='white')
    ax.text(xi, pf + pm / 2, f'{pm:.1f}%', ha='center', va='center', fontsize=7, color='white')
ax.set_xticks(x)
ax.set_xticklabels([lab_ for lab_, _, _ in cats], rotation=32, ha='right',
                   fontsize=8.5, rotation_mode='anchor')
for tick, (lab_, _, ref) in zip(ax.get_xticklabels(), cats):
    if ref:
        tick.set_fontweight('bold')
ax.set_xlim(-0.6, len(cats) - 0.4); ax.set_ylim(0, 112)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel('Proportion within group (%)', fontweight='bold')
ax.legend(frameon=True, fancybox=True, framealpha=0.9, fontsize=8, ncol=2, loc='upper center')
ax.grid(True, axis='y', alpha=0.2, linewidth=0.3); ax.set_axisbelow(True)
fig.savefig(f'{OUT}/Fig1C_sex_composition.pdf'); fig.savefig(f'{OUT}/Fig1C_sex_composition.png'); plt.close(fig)

# ---------------- Fig1D: 事件年龄(seaborn split violin, 原风格) ----------------
data, pvals = {}, {}
for k, lab_ in SYS:
    sub = d[d[f'g_{k}']].copy()
    sub['age_ev'] = sub['Age'] + sub[f'{k}_time']
    sub = sub[sub['age_ev'].notna() & sub['age_ev'].between(18, 105)]
    data[lab_] = {s: sub.loc[sub['Sex'] == s, 'age_ev'].dropna().values for s in ['Female', 'Male']}
    f, ma = data[lab_]['Female'], data[lab_]['Male']
    pvals[lab_] = stats.mannwhitneyu(f, ma).pvalue if len(f) and len(ma) else np.nan
    print(f'{lab_:12s} n={len(f)+len(ma):6,}  F med {np.median(f):5.1f} | M med {np.median(ma):5.1f} | p={pvals[lab_]:.2e}')

CLIP_LO = 45.0      # 下尾截断阈值(仅可视化;检验用全数据)
rows = []
for _k, lab_ in SYS:
    for s in ['Female', 'Male']:
        v = data[lab_][s]
        rows.append(pd.DataFrame({'organ': lab_, 'Sex': s, 'age_ev': v[v >= CLIP_LO]}))
long = pd.concat(rows, ignore_index=True)

fig, ax = plt.subplots(figsize=(4.7, 4.5))
sns.violinplot(data=long, x='organ', y='age_ev', hue='Sex',
               hue_order=['Female', 'Male'], order=[lab_ for _, lab_ in SYS],
               split=True, inner='quartile', cut=0, alpha=0.70, linewidth=0.9,
               width=0.72, palette={'Female': C_FEM, 'Male': C_MAL}, ax=ax)
for coll in ax.collections:
    try:
        fc = coll.get_facecolor()
        if fc is not None and len(fc) and fc.ndim == 2 and fc.shape[0]:
            coll.set_edgecolor((fc[0, 0], fc[0, 1], fc[0, 2], 0.45))
    except Exception:
        pass
ax.set_xlabel('')
ax.set_ylabel('Age at event (years)', fontweight='bold')
ax.set_xticklabels([lab_ for _, lab_ in SYS], rotation=32, ha='right',
                   fontsize=8.5, rotation_mode='anchor')
ax.set_xlim(-0.65, len(SYS) - 0.35)
hi = max(np.nanmax(data[lab_][s]) for _, lab_ in SYS for s in ['Female', 'Male'])
star_y = hi + 1.8
for xi, (_k, lab_) in enumerate(SYS):
    p_adj = min(pvals[lab_] * len(SYS), 1.0)      # Bonferroni
    stars = '***' if p_adj < 0.001 else '**' if p_adj < 0.01 else '*' if p_adj < 0.05 else ''
    if stars:
        ax.text(xi, star_y, stars, ha='center', va='bottom', fontsize=11, color='#333333', zorder=5)
    print(f'{lab_:12s} p_adj={p_adj:.2e} -> {stars or "ns(不标)"}')
ax.set_ylim(40, 92.5); ax.set_yticks(np.arange(40, 91, 10))
ax.legend(loc='lower right', frameon=True, fancybox=True, framealpha=0.90,
          fontsize=8, handletextpad=0.4, borderpad=0.4)
ax.grid(True, axis='y', alpha=0.15, linewidth=0.3); ax.set_axisbelow(True)
fig.savefig(f'{OUT}/Fig1D_age_at_event.pdf', dpi=600); fig.savefig(f'{OUT}/Fig1D_age_at_event.png', dpi=600)
plt.close(fig)
print('saved all four panels to', OUT)
