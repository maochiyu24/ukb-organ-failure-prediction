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
02b_merge_survival_metrics.py - 融合 (merge) 面板的时序性能 (双轨)
==================================================================
与 02 相同的 LGBM+Cox 双轨, 面板 = 04_fusion 的跨模态 Delong 特征 (84个),
人群 = 7 模态交集。输出追加到 survival_metrics_all.csv (modality='merge')。
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from sksurv.metrics import cumulative_dynamic_auc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                '04_fusion'))
import config
from merge_fusion import get_intersection, build_merge_matrix
from sksurv_load import load_survival

RESULT = os.path.join(config.RESULT_DIR, '05_survival')
AUC_TIMES = [3, 5, 10]
ORGAN_LABEL = {o: o + '_failure' if o != 'organ' else 'organ_failure'
               for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']}


def eval_merge(organ):
    label = ORGAN_LABEL[organ]
    out_dir = os.path.join(config.RESULT_DIR, '04_fusion', f'{organ}_merge')
    if not os.path.exists(os.path.join(out_dir, f'{organ}_merge_model.pkl')):
        print(f'[{organ}] 无 merge 模型, 跳过')
        return None
    inter = get_intersection()
    base, feat_origin = build_merge_matrix(organ, inter)
    base['Participant ID'] = base['Participant ID'].astype(str)
    surv = load_survival()
    m = base.merge(surv[['eid', f'{organ}_time', f'{organ}_event',
                         f'{organ}_prevalent']], left_on='Participant ID',
                   right_on='eid', how='inner')
    m = m[m[f'{organ}_prevalent'] == 0]
    m = m[m[f'{organ}_event'].notna()]
    feats = list(feat_origin.keys())
    t = m[f'{organ}_time'].values
    ev = m[f'{organ}_event'].values.astype(bool)
    region = m['Region'].values
    tr_mask = np.isin(region, list(config.REGION_TRAIN))
    X = m[feats]
    y = np.array([(e, float(ti)) for e, ti in zip(ev, t)],
                 dtype=[('event', 'bool'), ('time', 'float')])
    print(f'[{organ}/merge] n={len(X)} 事件={ev.sum()} 特征={len(feats)}', flush=True)
    if ev.sum() < 50:
        return None
    # 轨道1: LGBM merge pkl
    model = joblib.load(os.path.join(out_dir, f'{organ}_merge_model.pkl'))
    p = model.predict_proba(X)[:, 1]
    p_tr, p_te, y_tr, y_te = p[tr_mask], p[~tr_mask], y[tr_mask], y[~tr_mask]
    t_sn = np.percentile(p_tr[y_tr['event']], 10)
    t_sp = np.percentile(p_tr[~y_tr['event']], 90)
    row = {'organ': organ, 'modality': 'merge', 'n_tr': len(y_tr),
           'n_te': len(y_te), 'n_event_tr': int(y_tr['event'].sum()),
           'n_event_te': int(y_te['event'].sum()),
           'Cindex_lgbm_tr': concordance_index(y_tr['time'], -p_tr, y_tr['event']),
           'Cindex_lgbm_te': concordance_index(y_te['time'], -p_te, y_te['event']),
           't90sn': t_sn, 't90sp': t_sp}
    tmin = float(y['time'].min())
    times = [t for t in AUC_TIMES if tmin * 1.05 < t]
    try:
        a_tr, _ = cumulative_dynamic_auc(y_tr, y_tr, p_tr, times)
        a_te, _ = cumulative_dynamic_auc(y_te, y_te, p_te, times)
        for ti, x, z in zip(times, a_tr, a_te):
            row[f'AUC{ti}y_lgbm_tr'], row[f'AUC{ti}y_lgbm_te'] = x, z
    except Exception as e:
        print(f'  ⚠ tdAUC: {e}')
    # 轨道2: Cox
    Xc = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())
    df_all = pd.DataFrame(Xc.values, columns=feats)
    df_all['T'], df_all['E'] = y['time'], y['event'].astype(int)
    try:
        cph = CoxPHFitter(penalizer=0.05)
        cph.fit(df_all[tr_mask], duration_col='T', event_col='E',
                show_progress=False, fit_options={'step_size': 0.5})
        rk_tr = cph.predict_partial_hazard(df_all[tr_mask])
        rk_te = cph.predict_partial_hazard(df_all[~tr_mask])
        row['Cindex_cox_tr'] = concordance_index(y_tr['time'], -rk_tr.values,
                                                 y_tr['event'])
        row['Cindex_cox_te'] = concordance_index(y_te['time'], -rk_te.values,
                                                 y_te['event'])
    except Exception as e:
        print(f'  ⚠ Cox: {e}')
    pd.DataFrame([row]).to_csv(os.path.join(RESULT, 'metrics',
                                            f'merge_{organ}_survival_metrics.csv'),
                               index=False)
    return row


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', default=None)
    args = ap.parse_args()
    organs = [args.organ] if args.organ else \
        ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
    all_df = pd.read_csv(os.path.join(RESULT, 'survival_metrics_all.csv'))
    new = []
    for o in organs:
        r = eval_merge(o)
        if r:
            new.append(r)
    if new:
        all_df = pd.concat([all_df, pd.DataFrame(new)], ignore_index=True)
        all_df.to_csv(os.path.join(RESULT, 'survival_metrics_all.csv'), index=False)
        print(f'✅ 已追加 merge 时序指标 -> survival_metrics_all.csv '
              f'({len(all_df)} 行)')


if __name__ == '__main__':
    main()
