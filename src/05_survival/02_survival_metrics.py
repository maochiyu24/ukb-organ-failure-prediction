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
02_survival_metrics.py - 时序性能评估 (双轨, of825)
====================================================
轨道1 (判别/分层): 现有 LGBM pkl 预测概率作风险分数
  - Harrell C-index (England 内部 / Scot+Wal 外部)
  - time-dependent AUC at 1/3/5/10 年 (sksurv cumulative_dynamic_auc)
  - 90%Sn / 90%Sp 阈值 (England 训练集确定, 应用于外部)
轨道2 (Cox PH): 同面板 lifelines CoxPHFitter (England 拟合)
  - Harrell C-index (内/外) + top HR 表

用法:
  python 02_survival_metrics.py                       # 全部
  python 02_survival_metrics.py --organ heart --modality proteome   # 单点冒烟
  python 02_survival_metrics.py --organ heart          # 单器官全部模态
输出: result/of825/05_survival/metrics/{organ}_{modality}_survival_metrics.csv
      result/of825/05_survival/metrics/hr_{organ}_{modality}.csv
"""
import os
import sys
import json
import argparse
import numpy as np
import pandas as pd
import joblib
from concurrent.futures import ProcessPoolExecutor
from lifelines import CoxPHFitter
from lifelines.utils import concordance_index
from sksurv.metrics import cumulative_dynamic_auc

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

RESULT = os.path.join(config.RESULT_DIR, '05_survival')
METRICS_DIR = os.path.join(RESULT, 'metrics')
os.makedirs(METRICS_DIR, exist_ok=True)
# tdAUC 时间点: 事件定义含 1 年 run-in (基线后满 1 年才算事件, 用户确认),
# 故 1y 无事件、2y 外部事件过少, 评估 3/5/10 年。
AUC_TIMES = [3, 5, 10]

# 模态 -> prep 文件与 ranking 目录 (与 03_model 一致)
MODALITIES = ['proteome', 'metabolome', 'prs', 'lifestyle', 'psych',
              'blood', 'brain', 'history']
# organ -> 标签列全名
ORGAN_LABEL = {o: o + '_failure' if o != 'organ' else 'organ_failure'
               for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']}

_surv_df = None


def load_survival():
    global _surv_df
    if _surv_df is None:
        _surv_df = pd.read_csv(os.path.join(RESULT, 'survival_matrix.csv'),
                               dtype={'eid': str})
    return _surv_df


def load_organ_data(organ, modality):
    """载入 prep 特征 + survival, 返回 England/外部 (X, y_surv) 与面板"""
    label = ORGAN_LABEL[organ]
    surv = load_survival()
    # ranking 面板 (Delong 显著, 同 03_model)
    rank_dir = os.path.join(config.RESULT_DIR, '02_ranking', f'{organ}_{modality}')
    sel = pd.read_csv(os.path.join(rank_dir, 'Delong_Selection_Results.csv'))
    feats = sel[sel['Delong1'] < config.DELONG_P]['feature'].tolist()
    if not feats:
        feats = sel['feature'].head(1).tolist()
    # prep 特征
    prep = pd.read_csv(os.path.join(config.RESULT_DIR, '01_prep',
                                    f'{modality}_prep.csv'),
                       usecols=['Participant ID', 'Region', label] + feats)
    prep['Participant ID'] = prep['Participant ID'].astype(str)
    # 融合: 按 eid 对齐 survival 与 prep
    m = prep.merge(surv[['eid', f'{organ}_time', f'{organ}_event',
                         f'{organ}_prevalent']], left_on='Participant ID',
                   right_on='eid', how='inner')
    m = m[m[f'{organ}_prevalent'] == 0]      # 排除基线前已有
    m = m[m[f'{organ}_event'].notna()]
    # 事件时间最小 0.01 年
    t = m[f'{organ}_time'].values
    ev = m[f'{organ}_event'].values.astype(bool)
    region = m['Region'].values
    tr_mask = region == config.REGION_TRAIN[0] if hasattr(config, 'REGION_TRAIN') \
        else region == 1
    X = m[feats]
    y = np.array([(e, float(ti)) for e, ti in zip(ev, t)],
                 dtype=[('event', 'bool'), ('time', 'float')])
    return feats, X, y, tr_mask


def thresh_90(y_tr, p_tr):
    """England 训练集上确定 90%Sn 与 90%Sp 风险分数阈值"""
    ev = y_tr['event']
    p_pos = p_tr[ev]
    p_neg = p_tr[~ev]
    # 90% 敏感度: 90% 的事件者分数 >= t_sn
    t_sn = np.percentile(p_pos, 10) if len(p_pos) else np.nan
    # 90% 特异度: 90% 的非事件者分数 < t_sp
    t_sp = np.percentile(p_neg, 90) if len(p_neg) else np.nan
    return t_sn, t_sp


def eval_one(organ, modality, pkl_path, fit_cox=True):
    feats, X, y, tr_mask = load_organ_data(organ, modality)
    print(f'[{organ}/{modality}] n={len(X)} 事件={y["event"].sum()} 特征={len(feats)}',
          flush=True)
    if y['event'].sum() < 50 or len(X) < 500:
        return None
    # ---- 轨道1: LGBM 概率 ----
    model = joblib.load(pkl_path)
    p = model.predict_proba(X)[:, 1]
    p_tr, p_te = p[tr_mask], p[~tr_mask]
    y_tr, y_te = y[tr_mask], y[~tr_mask]
    t_sn, t_sp = thresh_90(y_tr, p_tr)
    ci_tr = concordance_index(y_tr['time'], -p_tr, y_tr['event'])
    ci_te = concordance_index(y_te['time'], -p_te, y_te['event'])
    # time-dependent AUC (England 内 / Scot+Wal 外)
    # 时间点必须落在随访范围内 (brain 等晚基线模态最短随访 >1y)
    tmin, tmax = float(y['time'].min()), float(y['time'].max())
    times = [t for t in AUC_TIMES if tmin * 1.05 < t < tmax]
    row = {'organ': organ, 'modality': modality, 'n_tr': len(y_tr),
           'n_te': len(y_te), 'n_event_tr': int(y_tr['event'].sum()),
           'n_event_te': int(y_te['event'].sum()),
           'followup_min': round(tmin, 2), 'followup_max': round(tmax, 2),
           'Cindex_lgbm_tr': ci_tr, 'Cindex_lgbm_te': ci_te,
           't90sn': t_sn, 't90sp': t_sp}
    if len(times):
        try:
            auc_tr, _ = cumulative_dynamic_auc(y_tr, y_tr, p_tr, times)
            auc_te, _ = cumulative_dynamic_auc(y_te, y_te, p_te, times)
            for ti, a_tr, a_te in zip(times, auc_tr, auc_te):
                row[f'AUC{ti}y_lgbm_tr'] = a_tr
                row[f'AUC{ti}y_lgbm_te'] = a_te
        except Exception as e:
            print(f'  ⚠ tdAUC 失败: {e}')
    # ---- 轨道2: Cox PH (England 拟合) ----
    if fit_cox:
        Xc = X.copy()
        Xc = Xc.replace([np.inf, -np.inf], np.nan)
        Xc = Xc.fillna(Xc.median())
        cph = CoxPHFitter(penalizer=0.05)
        df_tr = pd.DataFrame(Xc.values, columns=feats)
        df_tr['T'] = y['time']
        df_tr['E'] = y['event'].astype(int)
        df_tr = df_tr[tr_mask]
        try:
            cph.fit(df_tr, duration_col='T', event_col='E',
                    show_progress=False, fit_options={'step_size': 0.5})
            df_te = pd.DataFrame(Xc.values, columns=feats)[~tr_mask]
            risk_te = cph.predict_partial_hazard(df_te)
            risk_tr = cph.predict_partial_hazard(df_tr)
            row['Cindex_cox_tr'] = concordance_index(
                y_tr['time'], -risk_tr.values, y_tr['event'])
            row['Cindex_cox_te'] = concordance_index(
                y_te['time'], -risk_te.values, y_te['event'])
            hr = cph.summary[['coef', 'exp(coef)', 'exp(coef) lower 95%',
                              'exp(coef) upper 95%', 'p']].copy()
            hr.index.name = 'feature'
            hr.to_csv(os.path.join(METRICS_DIR,
                                   f'hr_{organ}_{modality}.csv'))
        except Exception as e:
            print(f'  ⚠ Cox 失败: {e}')
    pd.DataFrame([row]).to_csv(os.path.join(
        METRICS_DIR, f'{organ}_{modality}_survival_metrics.csv'), index=False)
    return row


def pkl_path(organ, modality):
    d = os.path.join(config.RESULT_DIR, '03_model', f'{organ}_{modality}')
    return os.path.join(d, f'{organ}_LightGBM_model.pkl')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', default=None)
    ap.add_argument('--modality', default=None)
    ap.add_argument('--workers', type=int, default=1)   # 沙箱限制: 串行
    args = ap.parse_args()
    organs = [args.organ] if args.organ else \
        ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
    mods = [args.modality] if args.modality else MODALITIES
    rows = []
    for o in organs:
        for m in mods:
            pk = pkl_path(o, m)
            if not os.path.exists(pk):
                continue
            try:
                r = eval_one(o, m, pk)
                if r:
                    rows.append(r)
            except Exception as e:
                print(f'  ✗ {o}/{m}: {e}')
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(os.path.join(RESULT, 'survival_metrics_all.csv'), index=False)
        print(f'\n✅ 汇总: {os.path.join(RESULT, "survival_metrics_all.csv")} '
              f'({len(df)} 行)')


if __name__ == '__main__':
    main()
