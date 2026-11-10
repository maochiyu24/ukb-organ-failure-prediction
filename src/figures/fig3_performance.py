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
"""Fig3 C/D/E (v906 v2, 缓存加速): 性能图
C: best 单模态 vs merge C-index | D: 七系统 merge ROC | E: Heart merge KM 分层
输出: result906/panels/Fig3C/D/E.pdf/.png (与 Fig3A/B 同比例 ~12.96x7.1cm)
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
from sklearn.metrics import roc_curve, roc_auc_score
from lifelines import KaplanMeierFitter
from naming import ORG_CN

_FD = _PROJECT + '/.cache/fonts'
for _fn in ['Arial.ttf', 'Arial-Bold.ttf']:
    _p = os.path.join(_FD, _fn)
    if os.path.exists(_p):
        fm.fontManager.addfont(_p)
plt.rcParams.update({
    'font.family': 'Arial', 'font.size': 10, 'axes.labelsize': 11,
    'legend.fontsize': 9, 'xtick.labelsize': 9.5, 'ytick.labelsize': 9.5,
    'figure.dpi': 600, 'savefig.dpi': 600, 'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05, 'axes.linewidth': 0.6,
    'grid.linewidth': 0.4, 'axes.grid': False,
})
R903 = _PROJECT + '/result/of903'
OUT_M = _PROJECT + '/result/result906/panels'
FIG = (4.40, 3.90)   # 偏方比例 (与 Fig1/Fig2 一致)
CACHE = os.path.join(_PROJECT, 'cache')
os.makedirs(CACHE, exist_ok=True)

ORG7 = [('heart', 'Heart'), ('lung', 'Lung'), ('liver', 'Liver'),
        ('renal', 'Kidney'), ('hemat', 'Hematologic'), ('brain', 'Stroke'),
        ('organ', 'Any organ failure')]
MODALITIES = ['proteome', 'metabolome', 'blood', 'prs', 'history', 'lifestyle', 'psych']
PREP = f'{R903}/01_prep'
FUS = f'{R903}/04_fusion'
SURV = pd.read_csv(f'{R903}/05_survival/survival_matrix.csv', dtype={'eid': str})
C_RED, C_BLUE = '#D62728', '#4C72B0'


def te_ids():
    """Region 2/3 测试集 eid 集合 (从任一 prep 的 Region 列)"""
    p = f'{CACHE}/te_ids.npy'
    if os.path.exists(p):
        return set(np.load(p, allow_pickle=True))
    df = pd.read_csv(f'{PREP}/proteome_prep.csv', usecols=['Participant ID', 'Region'])
    ids = set(df.loc[df['Region'].isin([2, 3]), 'Participant ID'].astype(str))
    np.save(p, np.array(list(ids), dtype=object), allow_pickle=True)
    return ids


def te_modal_table(mod):
    """测试集人群的该模态特征表 (列=全部器官该模态 merge 特征并集)"""
    p = f'{CACHE}/{mod}_te.pkl'
    if os.path.exists(p):
        return pd.read_pickle(p)
    cols = set()
    for o, _ in ORG7:
        mf = pd.read_csv(f'{FUS}/{o}_merge/merge_features.csv')
        cols |= set(mf.loc[mf['modality'] == mod, 'original'])
    cols = sorted(cols)
    ids = te_ids()
    use = ['Participant ID'] + [c for c in cols if c != 'Participant ID']
    keep = []
    for chunk in pd.read_csv(f'{PREP}/{mod}_prep.csv', usecols=use,
                             chunksize=200000, dtype={'Participant ID': str}):
        c = chunk[chunk['Participant ID'].isin(ids)]
        if len(c):
            keep.append(c)
    out = pd.concat(keep, ignore_index=True) if keep else pd.DataFrame(columns=use)
    out.to_pickle(p)
    print(f'  cached {mod}: {len(out)} rows x {len(use)} cols')
    return out


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
    return p, test[f'{organ}_event'].astype(int).values, test[f'{organ}_time'].values, len(test)


# ================= Fig3C =================
met = pd.read_csv(f'{R903}/05_survival/survival_metrics_all.csv')
fig, ax = plt.subplots(figsize=FIG)
y = np.arange(len(ORG7))[::-1]
for yi, (o, lab) in zip(y, ORG7):
    s = met[met['organ'] == o]
    best = s[s['modality'] != 'merge']['Cindex_lgbm_te'].max()
    mg = s[s['modality'] == 'merge']['Cindex_lgbm_te'].iloc[0]
    ax.plot([best, mg], [yi, yi], color='#B9B9B9', lw=1.1, zorder=1)
    ax.plot(best, yi, 'o', ms=6, color=C_BLUE, mec='white', mew=0.5, zorder=3)
    ax.plot(mg, yi, 'o', ms=7, color=C_RED, mec='white', mew=0.6, zorder=4)
ax.axvline(0.5, color='#999999', ls=':', lw=0.8)
ax.set_yticks(y)
ax.set_yticklabels([ORG_CN[o] for o, _ in ORG7], fontsize=9.5)
ax.set_xlim(0.5, 0.95)
ax.set_xlabel('C-index (external test set)', fontweight='bold')
ax.grid(True, axis='x', alpha=0.15, linewidth=0.3)
ax.set_axisbelow(True)
ax.legend(handles=[Line2D([0], [0], marker='o', ls='', color=C_BLUE, ms=6,
                         label='Best modality'),
                   Line2D([0], [0], marker='o', ls='', color=C_RED, ms=7,
                         label='Fusion')],
          loc='upper left', frameon=True,
          fancybox=True, framealpha=0.92, fontsize=9)
fig.savefig(f'{OUT_M}/Fig3C.pdf', dpi=600)
fig.savefig(f'{OUT_M}/Fig3C.png', dpi=600)
plt.close(fig)
print('Fig3C done')

# ================= Fig3D: merge 外部 AUC 横向柱 + 1000x bootstrap 95%CI 误差棒 =================
SYS_COL = {'heart': '#C0504D', 'lung': '#4F81BD', 'liver': '#9BBB59',
           'kidney': '#8064A2', 'hemat': '#F79646', 'stroke': '#4BACC6',
           'organ': '#555555'}
fig, ax = plt.subplots(figsize=FIG)
y = np.arange(len(ORG7))[::-1]
for yi, (o, lab) in zip(y, ORG7):
    em = pd.read_csv(f'{FUS}/{o}_merge/external_test_metrics.csv').iloc[0]
    auc, lo, hi = em['AUC'], em['AUC_95CI_low'], em['AUC_95CI_high']
    key = 'kidney' if o == 'renal' else 'stroke' if o == 'brain' else o
    ax.barh(yi, auc, height=0.62, color=SYS_COL[key], alpha=0.88,
            edgecolor='white', linewidth=0.5)
    ax.errorbar(auc, yi, xerr=[[auc - lo], [hi - auc]], fmt='none',
                ecolor='#333333', lw=1.0, capsize=3, capthick=1.0)
    ax.text(hi + 0.008, yi, f'{auc:.3f}', va='center', fontsize=9, color='#333333')
    print(f'  {o}: auc={auc:.3f} ci=({lo:.3f}-{hi:.3f})')
ax.axvline(0.5, color='#999999', ls=':', lw=0.8)
ax.set_yticks(y)
ax.set_yticklabels([ORG_CN[o] for o, _ in ORG7], fontsize=9.5)
ax.set_xlim(0.5, 1.0)
ax.set_xlabel('External AUC', fontweight='bold')
ax.grid(True, axis='x', alpha=0.15, linewidth=0.3)
ax.set_axisbelow(True)
fig.savefig(f'{OUT_M}/Fig3D.pdf', dpi=600)
fig.savefig(f'{OUT_M}/Fig3D.png', dpi=600)
plt.close(fig)
print('Fig3D done')

# ================= Fig3E: Any organ failure merge KM (粗线 + CI 阴影) =================
def km_plot(organ, out, fname, title=None):
    p, ev, tm, n = get_test_probs(organ)
    mr = met[(met['organ'] == organ) & (met['modality'] == 'merge')].iloc[0]
    lo, hi = sorted([float(mr['t90sn']), float(mr['t90sp'])])
    inverted = float(mr['t90sn']) > float(mr['t90sp'])
    if inverted:
        G = np.where(p >= hi, 2, 0); order = [0, 2]
    else:
        G = np.where(p < lo, 0, np.where(p < hi, 1, 2)); order = [0, 1, 2]
    cols = {0: '#70AD47', 1: '#ED7D31', 2: '#D62728'}
    labs = ['Low risk', 'Mid risk', 'High risk']
    fig, ax = plt.subplots(figsize=FIG)
    for g in order:
        kmf = KaplanMeierFitter()
        kmf.fit(tm[G == g], ev[G == g].astype(bool))
        sf = kmf.survival_function_
        t = sf.index.values; s = sf.values.ravel()
        ci = kmf.confidence_interval_
        ax.fill_between(t, ci.iloc[:, 0].values, ci.iloc[:, 1].values, step='post',
                        color=cols[g], alpha=0.16, lw=0)
        ax.step(t, s, where='post', lw=2.2, color=cols[g],
                label=f'{labs[g]} (n={(G == g).sum():,})')
    ax.set_xlim(0, 16); ax.set_ylim(0.70, 1.0)
    ax.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax.set_xlabel('Years since baseline', fontweight='bold')
    ax.set_ylabel('Event-free probability', fontweight='bold')
    ax.grid(True, alpha=0.15, linewidth=0.3)
    ax.set_axisbelow(True)
    ax.legend(loc='lower left', frameon=True, fancybox=True, framealpha=0.92, fontsize=9)
    if title:
        ax.set_title(title, fontsize=12, fontweight='bold', pad=5)
    fig.savefig(f'{out}/{fname}.pdf', dpi=600)
    fig.savefig(f'{out}/{fname}.png', dpi=600)
    plt.close(fig)
    print(f'{fname} done (strata={order}, inverted={inverted})')


km_plot('organ', OUT_M, 'Fig3E', title='Any organ failure')

from PIL import Image
for f in ['Fig3C', 'Fig3D', 'Fig3E']:
    im = Image.open(f'{OUT_M}/{f}.png')
    print(f'{f}: {im.size[0]/600*2.54:.2f} x {im.size[1]/600*2.54:.2f} cm')
