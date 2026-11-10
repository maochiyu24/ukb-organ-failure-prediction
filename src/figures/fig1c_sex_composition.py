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
"""Fig1C (v906): 各系统事件组性别构成 — 纵向 100% 堆叠柱 (横纵互换版)
- x = No event(参照) + Heart..Stroke (与 Fig1B 同序); 柱内 Female 粉/Male 蓝 + % 标注
- 无标题无字母; Arial; 单一图片输出 result/result906/panels/Fig1C.pdf/.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

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
OUT = _PROJECT + '/result/result906/panels'
os.makedirs(OUT, exist_ok=True)

R903 = _PROJECT + '/result/of903'
surv = pd.read_csv(f'{R903}/05_survival/survival_matrix.csv', dtype={'eid': str})
bl = pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
                 usecols=['Participant ID', 'Sex'])
bl.columns = ['eid', 'Sex']; bl['eid'] = bl['eid'].astype(str)
country = pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/participant_country_classification.csv')
country['Region'] = country['Country'].map({'England': 1, 'Scotland': 2, 'Wales': 3})
country['Participant ID'] = country['Participant ID'].astype(str)
d = surv.merge(bl, on='eid', how='left').merge(
    country[['Participant ID', 'Region']], left_on='eid', right_on='Participant ID', how='left')
d = d[(d['Region'].isin([1, 2, 3])) & (d['organ_prevalent'] == 0)].copy()  # 全体(训练+测试)队列
d['Sex'] = d['Sex'].map({0: 'Female', 1: 'Male'})

SYS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
       ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]
cats = [('No event', d['organ_event'] == 0, True)]
cats += [(lab, d[f'{k}_event'] == 1, False) for k, lab in SYS]

C_FEM, C_MAL = '#D62728', '#4C72B0'   # v906 红蓝规范 (与 Fig1A 同款, 弃粉色)
fig, ax = plt.subplots(figsize=(4.6, 3.9))
x = np.arange(len(cats))
for xi, (lab, mask, ref) in zip(x, cats):
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
ax.set_xticklabels([lab for lab, _, _ in cats], rotation=32, ha='right',
                   fontsize=8.5, rotation_mode='anchor')
for tick, (lab, _, ref) in zip(ax.get_xticklabels(), cats):
    if ref:
        tick.set_fontweight('bold')
ax.set_xlim(-0.6, len(cats) - 0.4)
ax.set_ylim(0, 112)
ax.set_yticks([0, 25, 50, 75, 100])
ax.set_ylabel('Proportion within group (%)', fontweight='bold')
ax.legend(frameon=True, fancybox=True, framealpha=0.9, fontsize=8,
          ncol=2, loc='upper center')
ax.grid(True, axis='y', alpha=0.2, linewidth=0.3)
ax.set_axisbelow(True)

fig.savefig(f'{OUT}/Fig1C.pdf', dpi=600)
fig.savefig(f'{OUT}/Fig1C.png', dpi=600)
plt.close(fig)
from PIL import Image
im = Image.open(f'{OUT}/Fig1C.png')
print('saved Fig1C(vertical)', im.size[0] / 600 * 2.54, 'x', im.size[1] / 600 * 2.54, 'cm')
