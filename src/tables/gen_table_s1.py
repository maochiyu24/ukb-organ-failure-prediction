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
"""Table S1a/b: 各模态外部性能矩阵 (行=模态含merge; 列=器官含 All)
  TableS1a_Cindex.csv (C-index) 与 TableS1b_AUC.csv (AUC) 分开
  - C-index: 官方 survival_metrics_all.csv (Cindex_lgbm_te) 点值
             + 1000x bootstrap 95%CI (calc_cindex_ci2.py -> cindex_ci_all.csv)
  - AUC    : "直接01预测不分时间标准" -> 官方 03_model/04_fusion external_test_metrics.csv
             (AUC + 官方 1000x bootstrap CI)
  范围: 7 单模态 (brain 影像因随访时间基准不一致不展示) + merge; 6 系统 + All
"""
import os, glob
import numpy as np, pandas as pd
import sys
from naming import ORG_CN, MOD_LABEL

R = _PROJECT + '/result/of903'
CACHE = os.path.join(_PROJECT, 'cache')
OUT = _PROJECT + '/result/result906/tables'
ORG_ORDER = ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
SINGLE = ['proteome', 'metabolome', 'blood', 'prs', 'history', 'lifestyle', 'psych']
MOD_ORDER = SINGLE + ['merge']
MOD_DISP = {m: MOD_LABEL[m] for m in SINGLE + ['merge']}


def fmt(v, lo, hi, nd=3):
    if pd.isna(lo) or pd.isna(hi):
        return f'{v:.{nd}f}'
    return f'{v:.{nd}f} ({lo:.{nd}f}-{hi:.{nd}f})'


def main():
    # ---------- C-index CI 缓存 (优先直接读 cindex_ci_all.csv; 无则从 10 片合并) ----------
    cci = f'{CACHE}/cindex_ci_all.csv'
    if os.path.exists(cci):
        ci = pd.read_csv(cci)
    else:
        parts = [pd.read_csv(f'{CACHE}/cindex_slice_{k}.csv') for k in range(10)]
        ci = pd.concat(parts, ignore_index=True)
        ci = ci.drop_duplicates(['organ', 'modality'])
        ci.to_csv(cci, index=False)
    official = pd.read_csv(f'{R}/05_survival/survival_metrics_all.csv')
    official = official[official.modality != 'brain']
    want = set(zip(official.organ, official.modality))
    got = set(zip(ci.organ, ci.modality))
    miss = want - got
    assert not miss, f'missing CI combos: {miss}'
    print('cindex_ci_all.csv rows =', len(ci))

    # ---------- C-index 官方点值 ----------
    met = pd.read_csv(f'{R}/05_survival/survival_metrics_all.csv')

    def cell_cindex(o, m):
        v = float(met[(met.organ == o) & (met.modality == m)]['Cindex_lgbm_te'].iloc[0])
        r = ci[(ci.organ == o) & (ci.modality == m)].iloc[0]
        return fmt(v, r.C_lo, r.C_hi)

    # ---------- AUC (01 直接预测) 官方文件 ----------
    auc3 = {}
    for f in glob.glob(f'{R}/03_model/*_*/external_test_metrics.csv') + \
            glob.glob(f'{R}/04_fusion/*_merge/external_test_metrics.csv'):
        d = f.split('/')[-2]                     # {organ}_{modality}
        o, m = d.rsplit('_', 1)
        e = pd.read_csv(f).iloc[0]
        auc3[(o, m)] = (e['AUC'], e['AUC_95CI_low'], e['AUC_95CI_high'])

    def cell_auc(o, m):
        v, lo, hi = auc3[(o, m)]
        return fmt(float(v), float(lo), float(hi))

    rows = []
    for m in MOD_ORDER:
        rows.append(dict(Modality=MOD_DISP[m],
                         **{ORG_CN[o]: cell_cindex(o, m) for o in ORG_ORDER}))
    t = pd.DataFrame(rows)
    t.to_csv(f'{OUT}/TableS1a_Cindex.csv', index=False, encoding='utf-8-sig')
    print('saved TableS1a_Cindex', len(t))

    rows = []
    for m in MOD_ORDER:
        rows.append(dict(Modality=MOD_DISP[m],
                         **{ORG_CN[o]: cell_auc(o, m) for o in ORG_ORDER}))
    t = pd.DataFrame(rows)
    t.to_csv(f'{OUT}/TableS1b_AUC.csv', index=False, encoding='utf-8-sig')
    print('saved TableS1b_AUC', len(t))

    # ---------- 样本量矩阵 (n_te (n_event)) ----------
    nrows = []
    for m in MOD_ORDER:
        sub = official[official.modality == m]
        row = {}
        for o in ORG_ORDER:
            r = sub[sub.organ == o].iloc[0]
            row[ORG_CN[o]] = f'{int(r.n_te):,} ({int(r.n_event_te)})'
        nrows.append(dict(Modality=MOD_DISP[m], Metric='N (events)', **row))
    pd.DataFrame(nrows).to_csv(f'{OUT}/TableS1_sample_sizes.csv', index=False,
                               encoding='utf-8-sig')
    print('saved TableS1_sample_sizes')


if __name__ == '__main__':
    main()
