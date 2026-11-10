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
"""Fig1A 单图 (v906 迭代版) — Age distribution by event status
- 单一图片输出: result/result906/panels/Fig1A.pdf/.png
- 无标题、无面板字母; 压低高度、横向比例; 字体 Arial (Liberation Sans 兼容替身)
- 队列 = 全体(训练+测试, 无 prevalent, N=494,334); 与 Table1 Overall 一致
"""
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from scipy import stats
import seaborn as sns

# ---------- 字体: Arial (服务器无正版 Arial; 用度量兼容替身; 若放入正版同名文件则自动优先) ----------
_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)

# ---------- SCI 期刊风格 (参考已接收稿件代码) ----------
plt.rcParams.update({
    'font.family': 'Arial',
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'legend.fontsize': 8,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 600,
    'savefig.dpi': 600,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6,
    'grid.linewidth': 0.4,
    'axes.grid': False,
})

OUT = _PROJECT + '/result/result906/panels'
os.makedirs(OUT, exist_ok=True)

# ---------- 数据装载 (与 fig1_v4 相同队列定义) ----------
R903 = _PROJECT + '/result/of903'
surv = pd.read_csv(f'{R903}/05_survival/survival_matrix.csv', dtype={'eid': str})
bl = pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
                 usecols=['Participant ID', 'Age at recruitment', 'Sex'])
bl.columns = ['eid', 'Age', 'Sex']; bl['eid'] = bl['eid'].astype(str)
country = pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/participant_country_classification.csv')
country['Region'] = country['Country'].map({'England': 1, 'Scotland': 2, 'Wales': 3})
country['Participant ID'] = country['Participant ID'].astype(str)
d = (surv.merge(bl, on='eid', how='left')
        .merge(country[['Participant ID', 'Region']], left_on='eid',
               right_on='Participant ID', how='left'))
d = d[(d['Region'].isin([1, 2, 3])) & (d['organ_prevalent'] == 0)].copy()  # 全体(训练+测试)队列
d['ev'] = d['organ_event'].astype(int)
d['Age'] = pd.to_numeric(d['Age'], errors='coerce')
e0, e1 = d[d['ev'] == 0], d[d['ev'] == 1]
print(f'N = {len(d):,}  |  No event {len(e0):,}  |  Any event {len(e1):,}')

# ---------- 绘图: 直方图 + KDE, 无标题无字母 ----------
# v906 统一配色规范: 事件状态两组对比 = 对照组蓝 / 事件组红 (后续各图沿用)
C_NOE = '#4C72B0'          # No event 蓝 (对照组)
C_EVT = '#D62728'          # Any event 红 (事件组)
fig, ax = plt.subplots(figsize=(4.2, 3.5))   # 参考 (8,3.5) 双面板中的单面板比例 (~1.2:1, 偏方)

bins = np.arange(37, 74, 2)
for lab, dfg, c, ls in [('No event', e0, C_NOE, '--'),
                        ('Any event', e1, C_EVT, '-')]:
    v = dfg['Age'].dropna()
    ax.hist(v, bins=bins, density=True, alpha=0.35, color=c,
            edgecolor='white', linewidth=0.4)
    sns.kdeplot(v, ax=ax, color=c, linestyle=ls, linewidth=1.6, cut=0,
                label=f'{lab} (n={len(v):,})')

ax.set_xlabel('Age at baseline (years)', fontweight='bold')
ax.set_ylabel('Density', fontweight='bold')
ax.set_xlim(38, 74)
ax.legend(frameon=True, fancybox=True, framealpha=0.9, fontsize=8, loc='upper left')
ax.grid(True, alpha=0.2, linewidth=0.3)

fig.savefig(f'{OUT}/Fig1A.pdf', dpi=600)
fig.savefig(f'{OUT}/Fig1A.png', dpi=600)
plt.close(fig)

# 实测尺寸
from PIL import Image
im = Image.open(f'{OUT}/Fig1A.png')
print(f'saved Fig1A -> {OUT}/Fig1A.pdf/.png  ({im.size[0]/600*2.54:.2f} x {im.size[1]/600*2.54:.2f} cm)')
