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
中介森林图 (of903 终版)
======================
7 器官分面；每面板 |中介比例| 前 12 的显著中介
点=PM(%), 线=95%CI, 颜色=暴露(lifestyle_v2/psych_v2), 形状=中介集(omics/blood)
输出: result/of903/06_mediation_v2/forest_mediation.pdf/png
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

for _f in ['LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf']:
    _p = os.path.join(_PROJECT + '/.cache/fonts', _f)
    if os.path.exists(_p):
        font_manager.fontManager.addfont(_p)
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 8,
                     'savefig.dpi': 600, 'savefig.bbox': 'tight'})

OUT = _PROJECT + '/result/of903/06_mediation_v2'
res = pd.read_csv(os.path.join(OUT, 'mediation_results_all_all_all.csv'))

res = res[(res['ACME_p'] < 0.05) & res['Prop_mediated'].notna()]
res['PM_pct'] = res['Prop_mediated'] * 100
res['PM_lo_pct'] = res['PM_lo'] * 100
res['PM_hi_pct'] = res['PM_hi'] * 100
res['PM_lo_pct'] = res['PM_lo_pct'].clip(-200, 300)
res['PM_hi_pct'] = res['PM_hi_pct'].clip(-200, 300)

ORGANS = ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
ORG_CN = {'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver', 'renal': 'Renal',
          'hemat': 'Haematologic', 'brain': 'Stroke', 'organ': 'Any-system'}
COLORS = {'lifestyle_score_v2': '#2E86AB', 'psych_score_v2': '#A23B72'}
MARKERS = {'omics': 'o', 'blood': 'D'}
LABELS = {'lifestyle_score_v2': 'Lifestyle', 'psych_score_v2': 'Psychosocial'}

fig, axes = plt.subplots(3, 3, figsize=(14, 15))
axes_flat = axes.flat
for ax, organ in zip(axes_flat, ORGANS):
    sub = res[res['Organ'] == organ]
    if sub.empty:
        ax.set_visible(False)
        continue
    sub = sub.reindex(sub['PM_pct'].abs().sort_values(ascending=False).index).head(12)
    sub = sub.sort_values('PM_pct')
    y = np.arange(len(sub))
    for i, (_, r) in enumerate(sub.iterrows()):
        ax.errorbar(r['PM_pct'], i, xerr=[[r['PM_pct'] - r['PM_lo_pct']],
                                          [r['PM_hi_pct'] - r['PM_pct']]],
                    fmt=MARKERS[r['Set']], color=COLORS[r['Exposure']],
                    markersize=6, capsize=2, lw=1.2, alpha=0.85)
    ax.axvline(0, color='grey', lw=0.8, ls='--')
    ax.set_yticks(y)
    ax.set_yticklabels([m.split('__')[1] if '__' in m else m for m in sub['Mediator']],
                       fontsize=6.5)
    ax.set_xlim(-200, 320)
    ax.set_title(ORG_CN[organ], fontsize=10, fontweight='bold')
    ax.set_xlabel('Proportion mediated (%)', fontsize=8)
    ax.tick_params(axis='x', labelsize=7)
    ax.grid(axis='x', alpha=0.3, ls=':')
for ax in axes_flat[len(ORGANS):]:
    ax.set_visible(False)
handles = []
for e in ['lifestyle_score_v2', 'psych_score_v2']:
    handles.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=COLORS[e],
                              markersize=8, label=LABELS[e]))
for s in ['omics', 'blood']:
    handles.append(plt.Line2D([0], [0], marker=MARKERS[s], color='w', markerfacecolor='grey',
                              markersize=8, label=s.capitalize()))
fig.legend(handles=handles, loc='upper center', ncol=4, fontsize=9, frameon=False,
           bbox_to_anchor=(0.5, 1.0))
fig.suptitle('Mediation of lifestyle and psychosocial exposures on organ events\n'
             '(top 12 significant mediators per organ, quasi-Bayesian 95% CI, of903)',
             fontsize=11, fontweight='bold', y=1.03)
plt.tight_layout(rect=[0, 0, 1, 0.97])
fig.savefig(os.path.join(OUT, 'forest_mediation.pdf'))
fig.savefig(os.path.join(OUT, 'forest_mediation.png'), dpi=300)
plt.close()
print(f'✅ 森林图已生成: {OUT}/forest_mediation.pdf/png')
print(f'显著条数: {len(res)} | 每器官: ' +
      ', '.join(f'{ORG_CN[o]}={len(res[res["Organ"]==o])}' for o in ORGANS))
