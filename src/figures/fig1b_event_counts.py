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
"""Fig1B (v906): 各系统远期严重事件数量 — 横向单色条 (v906 事件红, alpha 0.70)
- 与 Fig1C(纵向构成) 方向正交, 减弱重复感; 系统行序 Heart(顶)->Stroke(底) 与 C 同序
- 无标题无字母; Arial; 单一图片输出 result/result906/panels/Fig1B.pdf/.png
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
country = pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/participant_country_classification.csv')
country['Region'] = country['Country'].map({'England': 1, 'Scotland': 2, 'Wales': 3})
country['Participant ID'] = country['Participant ID'].astype(str)
d = surv.merge(country[['Participant ID', 'Region']], left_on='eid',
               right_on='Participant ID', how='left')
d = d[(d['Region'].isin([1, 2, 3])) & (d['organ_prevalent'] == 0)].copy()  # 全体(训练+测试)队列

SYS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
       ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]
C_EVT = '#D62728'                     # v906 事件红
cnts = [int(d[f'{k}_event'].sum()) for k, _ in SYS]

fig, ax = plt.subplots(figsize=(4.4, 3.2))
y = np.arange(len(SYS))[::-1]         # 顶 Heart -> 底 Stroke
ax.barh(y, cnts, height=0.6, color=C_EVT, alpha=0.70,
        edgecolor='white', linewidth=0.5)
for yi, c in zip(y, cnts):
    ax.text(c + max(cnts) * 0.012, yi, f'{c:,}', va='center', fontsize=8, color='#333333')
ax.set_yticks(y)
ax.set_yticklabels([lab for _, lab in SYS], fontsize=9)
ax.set_xlim(0, max(cnts) * 1.22)
ax.set_xlabel('Number of events', fontweight='bold')
ax.grid(True, axis='x', alpha=0.2, linewidth=0.3)
ax.set_axisbelow(True)

fig.savefig(f'{OUT}/Fig1B.pdf', dpi=600)
fig.savefig(f'{OUT}/Fig1B.png', dpi=600)
plt.close(fig)
from PIL import Image
im = Image.open(f'{OUT}/Fig1B.png')
print('saved Fig1B(horizontal)', im.size[0] / 600 * 2.54, 'x', im.size[1] / 600 * 2.54, 'cm')
