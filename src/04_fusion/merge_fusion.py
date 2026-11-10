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
04_fusion - 多模态融合（Result 4）
==================================
设计（用户确认）：
  - 人群: 7 模态交集 30,226 人（不含 brain；brain 时间点不一致，作为独立子分析）
  - 特征: 各模态 DeLong 显著面板（Delong1<0.05）合并，加模态前缀防重名
  - 每器官独立建模: Region==1 训练（GridSearchCV 调参）+ Region 2/3 外部验证
  - merge 模型 DeLong 排序: 合并特征按重要性排序做顺序前向选择
  - 预测每个疾病的人数相同（交集人群内标签全覆盖）

输出: result/of823/04_fusion/{organ}_merge/
  - merge_features.csv        各模态贡献特征清单
  - merge_Importance.csv      合并特征重要性
  - Top_90_InfoGain_features.csv
  - Delong_Selection_Results.csv   merge 前向选择排序
  - external_test_metrics.csv 外部验证指标（Bootstrap 95%CI）
  - {organ}_external_ROC.pdf
  - merge_summary.csv         6 器官汇总

用法: python 04_fusion/merge_fusion.py [--organ heart|all] [--tune]
"""
import os
import sys
import json
import time
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import roc_auc_score, roc_curve, average_precision_score
import lightgbm as lgb
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '02_ranking'))
import config
from feature_ranking import compute_importance, top90_features, forward_selection

MERGE_MODALITIES = ['proteome', 'metabolome', 'blood', 'prs', 'history', 'lifestyle', 'psych']
PREP_DIR = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'])


def load_delong_features(organ, modality):
    """读取该器官×模态的 DeLong 显著面板"""
    f = os.path.join(config.RESULT_DIR, config.SUBDIRS['ranking'],
                     f'{organ}_{modality}', 'Delong_Selection_Results.csv')
    if not os.path.exists(f):
        print(f'  ⚠️ 缺少 {f}')
        return []
    df = pd.read_csv(f)
    feats = df[df['Delong1'] < config.DELONG_P]['feature'].tolist()
    if not feats:
        feats = df['feature'].head(1).tolist()
    return feats


def get_intersection():
    """7 模态 Participant ID 交集"""
    ids = [set(pd.read_csv(os.path.join(PREP_DIR, f'{m}_prep.csv'),
                           usecols=['Participant ID'])['Participant ID'].astype(str))
           for m in MERGE_MODALITIES]
    return set.intersection(*ids)


def build_merge_matrix(organ, inter_ids):
    """合并各模态显著特征（加模态前缀）到交集人群"""
    base = pd.read_csv(os.path.join(PREP_DIR, 'proteome_prep.csv'))
    base = base[base['Participant ID'].astype(str).isin(inter_ids)]
    feat_origin = {}
    for m in MERGE_MODALITIES:
        feats = load_delong_features(organ, m)
        if not feats:
            continue
        prep = pd.read_csv(os.path.join(PREP_DIR, f'{m}_prep.csv'))
        prep = prep[prep['Participant ID'].astype(str).isin(inter_ids)]
        renamer = {f: f'{m}__{f}' for f in feats if f in prep.columns}
        if not renamer:
            continue
        sub = prep[['Participant ID'] + list(renamer)].rename(columns=renamer)
        base = base.merge(sub, on='Participant ID', how='left')
        for orig, new in renamer.items():
            feat_origin[new] = (m, orig)
    return base, feat_origin


def merge_fusion(organ_label, tune=True):
    organ = config.ORGAN_SHORT[organ_label]
    out_dir = os.path.join(config.RESULT_DIR, config.SUBDIRS['fusion'], f'{organ}_merge')
    os.makedirs(out_dir, exist_ok=True)

    print(f'\n{"="*70}\n[merge | {organ}] 多模态融合\n{"="*70}')
    inter_ids = get_intersection()
    print(f'  7 模态交集人群: {len(inter_ids):,}')

    base, feat_origin = build_merge_matrix(organ, inter_ids)
    base = base[base[organ_label].isin([0, 1])]
    feat_cols = list(feat_origin.keys())
    print(f'  合并特征数: {len(feat_cols)} (各模态: '
          + ', '.join(f'{m}={sum(1 for v in feat_origin.values() if v[0]==m)}' for m in MERGE_MODALITIES) + ')')

    # 保存特征清单
    pd.DataFrame([{'feature': f, 'modality': v[0], 'original': v[1]}
                  for f, v in feat_origin.items()]).to_csv(
        os.path.join(out_dir, 'merge_features.csv'), index=False)

    train = base[base['Region'].isin(config.REGION_TRAIN)]
    test = base[base['Region'].isin(config.REGION_TEST)]
    print(f'  训练(England): {len(train)} (阳性={train[organ_label].sum()}), '
          f'外部验证(Scot+Wal): {len(test)} (阳性={test[organ_label].sum()})')
    X_tr, y_tr = train[feat_cols], train[organ_label]
    X_te, y_te = test[feat_cols], test[organ_label]

    # ---- 调参训练（GridSearchCV, 与单模态一致的网格）----
    if tune:
        cv = StratifiedKFold(**config.MODEL_CV)
        grid = GridSearchCV(lgb.LGBMClassifier(objective='binary', random_state=42,
                                               n_jobs=config.N_JOBS_RANKING),
                            config.MODEL_PARAM_GRID, cv=cv, scoring='roc_auc', n_jobs=1)
        print('  GridSearchCV 调参中...')
        t0 = time.time()
        grid.fit(X_tr, y_tr)
        best = grid.best_estimator_
        print(f'  最优参数: {grid.best_params_} | 内部AUC: {grid.best_score_:.4f} | {time.time()-t0:.0f}s')
    else:
        best = lgb.LGBMClassifier(**config.LGB_PARAMS, objective='binary',
                                  random_state=42, n_jobs=config.N_JOBS_RANKING)
        best.fit(X_tr, y_tr)

    # ---- 外部验证 ----
    p_te = best.predict_proba(X_te)[:, 1]
    auc = roc_auc_score(y_te, p_te)
    pr_auc = average_precision_score(y_te, p_te)
    rng = np.random.default_rng(42)
    idx = np.arange(len(y_te))
    boot = [roc_auc_score(y_te.iloc[i], p_te[i]) for i in
            (rng.choice(idx, len(idx), replace=True) for _ in range(1000))
            if len(np.unique(y_te.iloc[i])) > 1]
    ci_lo, ci_hi = np.percentile(boot, 2.5), np.percentile(boot, 97.5)
    print(f'  外部验证 AUC={auc:.4f} (95%CI {ci_lo:.4f}-{ci_hi:.4f}), PR-AUC={pr_auc:.4f}')

    joblib.dump(best, os.path.join(out_dir, f'{organ}_merge_model.pkl'))
    with open(os.path.join(out_dir, 'model_params.json'), 'w') as f:
        json.dump(best.get_params(), f, indent=2, default=str)
    pd.DataFrame([{'organ': organ, 'n': len(X_te), 'n_pos': int(y_te.sum()),
                   'AUC': auc, 'AUC_95CI_low': ci_lo, 'AUC_95CI_high': ci_hi,
                   'PR_AUC': pr_auc, 'n_features': len(feat_cols)}]).to_csv(
        os.path.join(out_dir, 'external_test_metrics.csv'), index=False)

    # ---- ROC ----
    fpr, tpr, _ = roc_curve(y_te, p_te)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, lw=2, label=f'AUC={auc:.3f}')
    plt.plot([0, 1], [0, 1], 'k--', lw=1)
    plt.xlabel('FPR'); plt.ylabel('TPR')
    plt.title(f'{organ} failure - multimodal fusion (n={len(X_te)})')
    plt.legend(loc='lower right'); plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f'{organ}_external_ROC.pdf'), dpi=300)
    plt.close()

    # ---- merge 模型 DeLong 排序（顺序前向选择）----
    print('  merge 特征 DeLong 排序中...')
    my_imp = compute_importance(X_tr, y_tr, dict(config.LGB_PARAMS),
                                out_dir, organ, resume=False)
    top_feats = top90_features(my_imp, out_dir, organ, resume=False)
    delong_df = forward_selection(X_tr[top_feats], y_tr, dict(config.LGB_PARAMS),
                                  top_feats, out_dir, organ, resume=False)
    sig_feats = delong_df[delong_df['Delong1'] < config.DELONG_P]['feature'].tolist()
    print(f'  DeLong 排序完成: 显著特征 {len(sig_feats)} 个')
    pd.DataFrame({'significant_feature': sig_feats}).to_csv(
        os.path.join(out_dir, 'significant_features.csv'), index=False)

    # ---- 汇总行 ----
    return {'organ': organ, 'n_inter': len(inter_ids), 'n_features': len(feat_cols),
            'AUC': auc, 'AUC_low': ci_lo, 'AUC_high': ci_hi, 'PR_AUC': pr_auc,
            'n_sig_delong': len(sig_feats)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', default='all', help='heart/lung/liver/renal/hemat/organ 或 all')
    ap.add_argument('--no-tune', action='store_true', help='跳过调参（用默认参数）')
    args = ap.parse_args()
    organs = (list(config.LABEL_COLUMNS) if args.organ == 'all'
              else [f'{args.organ}_failure'])
    rows = []
    for lbl in organs:
        rows.append(merge_fusion(lbl, tune=not args.no_tune))
    if len(rows) > 1:
        summary = pd.DataFrame(rows)
        summary.to_csv(os.path.join(config.RESULT_DIR, config.SUBDIRS['fusion'],
                                    'merge_summary.csv'), index=False)
        print('\n===== merge 汇总 =====')
        print(summary.to_string(index=False))
