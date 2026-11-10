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
"""Fig3 配套附图 (v906): 输出 result906/figures_supp/
FigS3_AUC_contrast: 全随访 01 AUC 哑铃对比 (best 单模态 vs merge, 7 系统; 与 TableS1b AUC* 同源)
FigS3_tdAUC_merge  : merge 模型 3/5/10y 时间依赖 AUC (7 系统折线)
FigS3_KM_{...}     : 其余 6 系统+All 的 merge 风险分层 KM (Heart 已在正文 Fig3E; 保持原状不动)
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.lines import Line2D
from lifelines import KaplanMeierFitter
from naming import ORG_CN

_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
_NEW_RC = {
    'font.family': 'Arial', 'font.size': 10, 'axes.labelsize': 11,
    'legend.fontsize': 9, 'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5,
    'figure.dpi': 600, 'savefig.dpi': 600, 'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05, 'axes.linewidth': 0.6,
    'grid.linewidth': 0.4, 'axes.grid': False,
}
# KM 附图保持现状 (原字号), 不随全局放大; 仅正文 tdAUC 与新 AUC10y 对比图用新字号
_KM_RC = dict(_NEW_RC)
_KM_RC.update({'font.size': 9, 'axes.labelsize': 9, 'legend.fontsize': 6.8,
               'xtick.labelsize': 7, 'ytick.labelsize': 7.5})
plt.rcParams.update(_NEW_RC)
R903 = _PROJECT + '/result/of903'
OUT_S = _PROJECT + '/result/result906/figures_supp'
CACHE = os.path.join(_PROJECT, 'cache')
FIG = (4.40, 3.90)   # 偏方比例 (与 Fig1/Fig2 一致)

ORG7 = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
        ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke'),
        ('organ', 'Any organ failure')]
MODALITIES = ['proteome', 'metabolome', 'blood', 'prs', 'history', 'lifestyle', 'psych']
PREP = f'{R903}/01_prep'
FUS = f'{R903}/04_fusion'
SURV = pd.read_csv(f'{R903}/05_survival/survival_matrix.csv', dtype={'eid': str})
met = pd.read_csv(f'{R903}/05_survival/survival_metrics_all.csv')
C_RED, C_BLUE = '#D62728', '#4C72B0'
SYS_COL = {'heart': '#C0504D', 'lung': '#4F81BD', 'liver': '#9BBB59',
           'kidney': '#8064A2', 'hemat': '#F79646', 'stroke': '#4BACC6',
           'organ': '#555555'}


def te_modal_table(mod):
    return pd.read_pickle(f'{CACHE}/{mod}_te.pkl')


def merge_test_matrix(organ):
    mf = pd.read_csv(f'{FUS}/{organ}_merge/merge_features.csv')
    feat_cols = list(mf['feature'])
    base = None
    for mod in MODALITIES:
        sel = mf[mf['modality'] == mod]
        if sel.empty:
            continue
        tab = te_modal_table(mod)
        ren = {orig: f'{mod}__{orig}' for orig in sel['original'] if orig in tab.columns}
        if not ren:
            continue
        sub = tab[['Participant ID'] + list(ren)].rename(columns=ren)
        base = sub if base is None else base.merge(sub, on='Participant ID', how='inner')
    test = base.merge(SURV[['eid', f'{organ}_time', f'{organ}_event']],
                      left_on='Participant ID', right_on='eid', how='inner')
    test = test[test[f'{organ}_event'].notna()].reset_index(drop=True)
    return test, feat_cols


def get_test_probs(organ):
    test, feat_cols = merge_test_matrix(organ)
    X_te = test[feat_cols]   # 保留 NaN (LGBM 原生处理, 与 04_fusion 一致)
    model = joblib.load(f'{FUS}/{organ}_merge/{organ}_merge_model.pkl')
    p = model.predict_proba(X_te)[:, 1]
    return p, test[f'{organ}_event'].astype(int).values, test[f'{organ}_time'].values


def km_strata(organ):
    p, ev, tm = get_test_probs(organ)
    r = met[(met['organ'] == organ) & (met['modality'] == 'merge')].iloc[0]
    lo, hi = sorted([float(r['t90sn']), float(r['t90sp'])])
    inverted = float(r['t90sn']) > float(r['t90sp'])
    # 正常: Low<p<lo, Mid lo..hi, High>=hi; 反转: 两层 (Low 含中间)
    if inverted:
        G = np.where(p >= hi, 2, 0)
        order = [0, 2]
    else:
        G = np.where(p < lo, 0, np.where(p < hi, 1, 2))
        order = [0, 1, 2]
    return p, ev, tm, G, order, inverted


# ================= FigS3: tdAUC merge 折线 =================
fig, ax = plt.subplots(figsize=FIG)
ts = [3, 5, 10]
for o, lab in ORG7:
    r = met[(met['organ'] == o) & (met['modality'] == 'merge')].iloc[0]
    vals = [r['AUC3y_lgbm_te'], r['AUC5y_lgbm_te'], r['AUC10y_lgbm_te']]
    key = 'kidney' if o == 'renal' else 'stroke' if o == 'brain' else o
    ax.plot(ts, vals, '-o', ms=4, lw=1.3, color=SYS_COL[key], label=ORG_CN[o])
ax.axhline(0.5, color='#999999', ls=':', lw=0.8)
ax.set_xticks(ts)
ax.set_xlabel('Year', fontweight='bold')
ax.set_ylabel('Time-dependent AUC (external)', fontweight='bold')
ax.set_ylim(0.5, 1.05)
ax.grid(True, alpha=0.15, linewidth=0.3)
ax.set_axisbelow(True)
ax.legend(frameon=True, fancybox=True, framealpha=0.92, fontsize=9,
          ncol=2, loc='lower right')
fig.savefig(f'{OUT_S}/FigS3_tdAUC_merge.pdf', dpi=600)
fig.savefig(f'{OUT_S}/FigS3_tdAUC_merge.png', dpi=600)
plt.close(fig)
print('FigS3_tdAUC_merge done')

# ================= FigS3: 全随访 AUC 对比 (best 单模态 vs merge 哑铃, 样式/字号与 Fig3C 一致) =================
# 口径 = 全随访 01 AUC (external_test_metrics.csv, 与 TableS1b AUC* 同源); 已去掉 10y tdAUC 版本
def full_auc(o, m):
    if m == 'merge':
        e = pd.read_csv(f'{R903}/04_fusion/{o}_merge/external_test_metrics.csv').iloc[0]
    else:
        e = pd.read_csv(f'{R903}/03_model/{o}_{m}/external_test_metrics.csv').iloc[0]
    return float(e['AUC'])
SINGLE7 = ['proteome', 'metabolome', 'blood', 'prs', 'history', 'lifestyle', 'psych']
fig, ax = plt.subplots(figsize=FIG)
y = np.arange(len(ORG7))[::-1]
for yi, (o, lab) in zip(y, ORG7):
    best = max(full_auc(o, m) for m in SINGLE7)
    mg = full_auc(o, 'merge')
    ax.plot([best, mg], [yi, yi], color='#B9B9B9', lw=1.1, zorder=1)
    ax.plot(best, yi, 'o', ms=6, color=C_BLUE, mec='white', mew=0.5, zorder=3)
    ax.plot(mg, yi, 'o', ms=7, color=C_RED, mec='white', mew=0.6, zorder=4)
ax.axvline(0.5, color='#999999', ls=':', lw=0.8)
ax.set_yticks(y)
ax.set_yticklabels([ORG_CN[o] for o, _ in ORG7], fontsize=9.5)
ax.set_xlim(0.5, 0.95)
ax.set_xlabel('AUC (full follow-up, external test set)', fontweight='bold')
ax.grid(True, axis='x', alpha=0.15, linewidth=0.3)
ax.set_axisbelow(True)
ax.legend(handles=[Line2D([0], [0], marker='o', ls='', color=C_BLUE, ms=6,
                         label='Best modality'),
                   Line2D([0], [0], marker='o', ls='', color=C_RED, ms=7,
                         label='Fusion')],
          loc='upper left', frameon=True,
          fancybox=True, framealpha=0.92, fontsize=9)
fig.savefig(f'{OUT_S}/FigS3_AUC_contrast.pdf', dpi=600)
fig.savefig(f'{OUT_S}/FigS3_AUC_contrast.png', dpi=600)
plt.close(fig)
print('FigS3_AUC_contrast done')

# ================= FigS3: KM 分层 (Heart..Stroke 六系统; Any organ failure 在正文 Fig3E) =================
plt.rcParams.update(_KM_RC)   # KM 附图保持原字号 (现状不动)
KM_COL = {0: '#70AD47', 1: '#ED7D31', 2: '#D62728'}
KM_LAB = {0: 'Low risk', 1: 'Mid risk', 2: 'High risk'}
for o, lab in ORG7[:6]:
    p, ev, tm, G, order, inverted = km_strata(o)
    fig, ax = plt.subplots(figsize=FIG)
    for g in order:
        kmf = KaplanMeierFitter()
        kmf.fit(tm[G == g], ev[G == g].astype(bool))
        sf = kmf.survival_function_
        t = sf.index.values
        ci = kmf.confidence_interval_
        ax.fill_between(t, ci.iloc[:, 0].values, ci.iloc[:, 1].values, step='post',
                        color=KM_COL[g], alpha=0.16, lw=0)
        ax.step(t, sf.values.ravel(), where='post', lw=2.2, color=KM_COL[g],
                label=f'{KM_LAB[g]} (n={(G == g).sum():,})')
    ax.set_xlim(0, 16)
    ax.set_ylim(0.70, 1.0)
    ax.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax.set_xlabel('Years since baseline', fontweight='bold')
    ax.set_ylabel('Event-free probability', fontweight='bold')
    ax.grid(True, alpha=0.15, linewidth=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc='lower left', frameon=True, fancybox=True, framealpha=0.92, fontsize=6.5)
    ax.set_title(lab, fontsize=10.5, fontweight='bold', pad=5)
    fname = 'FigS3_KM_' + lab.replace(' ', '')
    fig.savefig(f'{OUT_S}/{fname}.pdf', dpi=600)
    fig.savefig(f'{OUT_S}/{fname}.png', dpi=600)
    plt.close(fig)
    print(f'{fname} done  (strata={order}, inverted={inverted})')

from PIL import Image
for f in ['FigS3_tdAUC_merge', 'FigS3_AUC_contrast']:
    im = Image.open(f'{OUT_S}/{f}.png')
    print(f'{f}: {im.size[0]/600*2.54:.2f} x {im.size[1]/600*2.54:.2f} cm')
