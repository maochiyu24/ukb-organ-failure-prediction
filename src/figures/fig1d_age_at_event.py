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
"""Fig1D (v906 美化版): 事件发生年龄 by 系统 — 男女 split 小提琴 (手绘, 图族语言)
- x = 六系统 (Heart..Stroke); y = Age at event (基线年龄+随访年数, event flag 过滤与 Fig1B 一致)
- Female 红 #D62728 / Male 蓝 #4C72B0 亮填 alpha=0.70 + 白色细描边 (与 Fig1A/B/C 同语言);
  中心白中位线分居左右 (Female 左半内、Male 右半内, 不退回中心贯穿线)
- Bonferroni 组内 Mann-Whitney 分级 ***/**/* (Kidney ns 不标); 星号单行平齐
- 无标题无字母; Arial; 600dpi tight; 单一输出 result/result906/panels/Fig1D.pdf/.png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from scipy import stats

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
SYS = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
       ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke')]
cols = ['eid', 'baseline_date', 'organ_prevalent']
cols += [c for k, _ in SYS for c in (f'{k}_date', f'{k}_event')]
surv = pd.read_csv(f'{R903}/05_survival/survival_matrix.csv', dtype={'eid': str}, usecols=cols)
bl = pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
                 usecols=['Participant ID', 'Age at recruitment', 'Sex'])
bl.columns = ['eid', 'Age', 'Sex']; bl['eid'] = bl['eid'].astype(str)
country = pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/participant_country_classification.csv')
country['Region'] = country['Country'].map({'England': 1, 'Scotland': 2, 'Wales': 3})
country['Participant ID'] = country['Participant ID'].astype(str)
d = surv.merge(bl, on='eid', how='left').merge(
    country[['Participant ID', 'Region']], left_on='eid', right_on='Participant ID', how='left')
d = d[(d['Region'].isin([1, 2, 3])) & (d['organ_prevalent'] == 0)].copy()  # 全体(训练+测试)队列
d['Age'] = pd.to_numeric(d['Age'], errors='coerce')
d['Sex'] = d['Sex'].map({0: 'Female', 1: 'Male'})
d['base'] = pd.to_datetime(d['baseline_date'], errors='coerce')

data = {}            # lab -> {'Female': ages, 'Male': ages}
pvals = {}
for k, lab in SYS:
    evd = pd.to_datetime(d[f'{k}_date'], errors='coerce')
    diff = (evd - d['base']).dt.days / 365.25
    age = d['Age'] + diff
    m = (d[f'{k}_event'] == 1) & diff.notna() & diff.ge(0) & age.ge(18) & age.le(105)
    sub = d.loc[m].copy(); sub['age_ev'] = age[m]
    data[lab] = {s: sub.loc[sub['Sex'] == s, 'age_ev'].dropna().values for s in ['Female', 'Male']}
    f, ma = data[lab]['Female'], data[lab]['Male']
    pvals[lab] = stats.mannwhitneyu(f, ma).pvalue if len(f) and len(ma) else np.nan
    print(f'{lab:12s} n={len(f)+len(ma):6,}  F med {np.median(f):5.1f} | M med {np.median(ma):5.1f} | p={pvals[lab]:.2e}')

# ---------- seaborn split violin (参考图风格) ----------
import seaborn as sns
C_FEM, C_MAL = '#D62728', '#4C72B0'      # v906 红蓝规范 (Female 红 / Male 蓝)

CLIP_LO = 45.0      # 下尾截断阈值 (仅可视化; Mann-Whitney/Bonferroni 仍用全数据)
rows = []
for _k, lab in SYS:
    for s in ['Female', 'Male']:
        v = data[lab][s]
        rows.append(pd.DataFrame({'organ': lab, 'Sex': s,
                                  'age_ev': v[v >= CLIP_LO]}))
long = pd.concat(rows, ignore_index=True)

fig, ax = plt.subplots(figsize=(4.7, 4.5))
sns.violinplot(data=long, x='organ', y='age_ev', hue='Sex',
               hue_order=['Female', 'Male'], order=[lab for _k, lab in SYS],
               split=True, inner='quartile', cut=0, alpha=0.70, linewidth=0.9,
               width=0.72, palette={'Female': C_FEM, 'Male': C_MAL}, ax=ax)
# 边框: 同色但透明度调高
for coll in ax.collections:
    try:
        fc = coll.get_facecolor()
        if fc is not None and len(fc) and fc.ndim == 2 and fc.shape[0]:
            coll.set_edgecolor((fc[0, 0], fc[0, 1], fc[0, 2], 0.45))
    except Exception:
        pass

ax.set_xlabel('')
ax.set_ylabel('Age at event (years)', fontweight='bold')
ax.set_xticklabels([lab for _k, lab in SYS], rotation=32, ha='right',
                   fontsize=8.5, rotation_mode='anchor')
ax.set_xlim(-0.65, len(SYS) - 0.35)

# y 轴固定范围 40-90 (顶部留白放星号)
hi = max(np.nanmax(data[lab][s]) for _k, lab in SYS for s in ['Female', 'Male'])
star_y = hi + 1.8
n_test = len(SYS)
for xi, (_k, lab) in enumerate(SYS):
    p_adj = min(pvals[lab] * n_test, 1.0)    # Bonferroni
    stars = '***' if p_adj < 0.001 else '**' if p_adj < 0.01 else '*' if p_adj < 0.05 else ''
    if stars:
        ax.text(xi, star_y, stars, ha='center', va='bottom', fontsize=11,
                color='#333333', zorder=5)
    print(f'{lab:12s} p_adj={p_adj:.2e} -> {stars or "ns"}')
ax.set_ylim(40, 92.5)
ax.set_yticks(np.arange(40, 91, 10))

# 图例: 右下角
ax.legend(loc='lower right', frameon=True, fancybox=True, framealpha=0.90,
          fontsize=8, handletextpad=0.4, borderpad=0.4)
ax.grid(True, axis='y', alpha=0.15, linewidth=0.3)
ax.set_axisbelow(True)

fig.savefig(f'{OUT}/Fig1D.pdf', dpi=600)
fig.savefig(f'{OUT}/Fig1D.png', dpi=600)
plt.close(fig)
from PIL import Image
im = Image.open(f'{OUT}/Fig1D.png')
print('saved Fig1D(seaborn violin)', im.size[0] / 600 * 2.54, 'x', im.size[1] / 600 * 2.54, 'cm')
