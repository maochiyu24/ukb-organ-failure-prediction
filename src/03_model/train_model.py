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
03_model - LightGBM 训练 + 区域外部验证（参照 ZS model.ipynb）
==============================================================
  - 训练: Region==1 (England)，特征取 ranking 选出的面板
  - 调参: GridSearchCV 3 折 (roc_auc)
  - 验证: Region in [2,3] (Scotland+Wales) 外部测试集
          + Region==1 内部 5 折 CV
  - 指标: AUC(ROC), PR-AUC, 准确率/敏感度/特异度/PPV/NPV/F1/MCC + Bootstrap 95%CI

用法:
  python 03_model/train_model.py --organ heart --modality proteome
      [--features top90|delong|all] [--cv-folds 5] [--bootstrap 1000]
"""
import os
import sys
import time
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import (roc_auc_score, roc_curve, precision_recall_curve,
                             average_precision_score, accuracy_score,
                             precision_score, recall_score, f1_score,
                             matthews_corrcoef, confusion_matrix)
import lightgbm as lgb
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def load_features(prep_file, organ_label, ranking_dir, feature_mode):
    """读取 prep 数据并按 ranking 结果筛选特征"""
    df = pd.read_csv(prep_file)
    if feature_mode == 'all':
        return df
    # 从 ranking 结果取特征面板
    if feature_mode == 'top90':
        feat_file = os.path.join(ranking_dir, 'Top_90_InfoGain_features.csv')
        feat_col = 'feature'
    elif feature_mode == 'delong':
        feat_file = os.path.join(ranking_dir, 'Delong_Selection_Results.csv')
        feat_col = 'feature'
    else:
        raise ValueError(feature_mode)
    if not os.path.exists(feat_file):
        raise FileNotFoundError(f'缺少 ranking 结果: {feat_file}')
    feats = pd.read_csv(feat_file)[feat_col].tolist()
    if feature_mode == 'delong':
        # 仅保留 DeLong 显著特征 (Delong1 < 0.05)
        sel = pd.read_csv(feat_file)
        feats = sel.loc[sel['Delong1'] < config.DELONG_P, 'feature'].tolist()
        if not feats:
            feats = sel['feature'].head(1).tolist()
    keep = ['Participant ID', 'Region', organ_label] + [c for c in feats if c in df.columns]
    print(f'  [features={feature_mode}] 面板特征数: {len(keep)-3}')
    return df[keep]


def calc_metrics(y_true, y_pred_prob):
    """全套分类指标"""
    fpr, tpr, _ = roc_curve(y_true, y_pred_prob)
    auc = roc_auc_score(y_true, y_pred_prob)
    pr_auc = average_precision_score(y_true, y_pred_prob)
    # 默认 0.5 阈值
    y_pred = (y_pred_prob >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    return {
        'AUC': auc, 'PR_AUC': pr_auc,
        'Accuracy': accuracy_score(y_true, y_pred),
        'Sensitivity': tp / (tp + fn) if (tp + fn) else np.nan,
        'Specificity': tn / (tn + fp) if (tn + fp) else np.nan,
        'PPV': tp / (tp + fp) if (tp + fp) else np.nan,
        'NPV': tn / (tn + fn) if (tn + fn) else np.nan,
        'F1': f1_score(y_true, y_pred),
        'MCC': matthews_corrcoef(y_true, y_pred),
        'n': len(y_true), 'n_pos': int(y_true.sum()),
    }


def bootstrap_ci(y_true, y_pred_prob, n_boot=1000, seed=42):
    """Bootstrap 95% CI for AUC"""
    rng = np.random.default_rng(seed)
    aucs = []
    idx = np.arange(len(y_true))
    for _ in range(n_boot):
        i = rng.choice(idx, size=len(idx), replace=True)
        if len(np.unique(y_true[i])) < 2:
            continue
        aucs.append(roc_auc_score(y_true[i], y_pred_prob[i]))
    if not aucs:
        return np.nan, np.nan
    return np.percentile(aucs, 2.5), np.percentile(aucs, 97.5)


def train_eval(organ_label, modality='proteome', feature_mode='top90',
               cv_folds=5, n_boot=1000, resume=False):
    organ = config.ORGAN_SHORT[organ_label]
    prep_file = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'], f'{modality}_prep.csv')
    ranking_dir = os.path.join(config.RESULT_DIR, config.SUBDIRS['ranking'], f'{organ}_{modality}')
    out_dir = os.path.join(config.RESULT_DIR, config.SUBDIRS['model'], f'{organ}_{modality}')
    os.makedirs(out_dir, exist_ok=True)

    print(f'\n{"="*70}\n[{organ} | {modality} | {feature_mode}] 模型训练\n{"="*70}')
    df = load_features(prep_file, organ_label, ranking_dir, feature_mode)
    df = df[df[organ_label].isin([0, 1])]

    train = df[df['Region'].isin(config.REGION_TRAIN)]
    test = df[df['Region'].isin(config.REGION_TEST)]
    print(f'  训练(England): {len(train)} (阳性={train[organ_label].sum()}), '
          f'外部验证(Scot+Wal): {len(test)} (阳性={test[organ_label].sum()})')

    feat_cols = [c for c in train.columns if c not in
                 ['Participant ID', 'Region'] + config.LABEL_COLUMNS]
    X_tr, y_tr = train[feat_cols], train[organ_label]
    X_te, y_te = test[feat_cols], test[organ_label]

    # ---- 训练：使用模态级统一参数（00_tune 确定，同一模态所有器官共享）----
    params_json = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'], f'{modality}_params.json')
    if os.path.exists(params_json):
        import json as _json
        with open(params_json) as f:
            params = dict(config.LGB_PARAMS, **_json.load(f)['params'])
        print(f'  使用模态统一参数: {params}')
    else:
        params = dict(config.LGB_PARAMS)
        print(f'  [警告] 未找到模态参数文件，回退默认参数')
    t0 = time.time()
    best = lgb.LGBMClassifier(**params, objective='binary', random_state=42, n_jobs=config.N_JOBS_RANKING)
    best.fit(X_tr, y_tr)
    print(f'  训练完成, 耗时 {time.time()-t0:.0f}s')

    # ---- 外部验证 ----
    p_te = best.predict_proba(X_te)[:, 1]
    m_te = calc_metrics(y_te, p_te)
    ci_lo, ci_hi = bootstrap_ci(y_te.values, p_te, n_boot)
    m_te['AUC_95CI_low'], m_te['AUC_95CI_high'] = ci_lo, ci_hi
    print(f'  外部验证 AUC={m_te["AUC"]:.4f} (95%CI {ci_lo:.4f}-{ci_hi:.4f}), PR-AUC={m_te["PR_AUC"]:.4f}')

    # ---- 训练集内部 5 折 CV ----
    cv5 = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
    cv_aucs = []
    for tr_i, va_i in cv5.split(X_tr, y_tr):
        m = lgb.LGBMClassifier(**best.get_params())
        m.fit(X_tr.iloc[tr_i], y_tr.iloc[tr_i])
        cv_aucs.append(roc_auc_score(y_tr.iloc[va_i], m.predict_proba(X_tr.iloc[va_i])[:, 1]))
    print(f'  训练集 {cv_folds} 折 CV AUC: {np.mean(cv_aucs):.4f} ± {np.std(cv_aucs):.4f}')

    # ---- 保存 ----
    joblib.dump(best, os.path.join(out_dir, f'{organ}_LightGBM_model.pkl'))
    import json as _json
    with open(os.path.join(out_dir, 'model_params.json'), 'w') as f:
        _json.dump(best.get_params(), f, indent=2, default=str)
    pd.DataFrame([{'set': 'external_test', **m_te}]).to_csv(
        os.path.join(out_dir, 'external_test_metrics.csv'), index=False)
    pd.DataFrame({'cv_auc': cv_aucs}).to_csv(
        os.path.join(out_dir, 'train_cv_aucs.csv'), index=False)
    pd.DataFrame({'feature': feat_cols,
                  'importance': best.feature_importances_}).sort_values(
        'importance', ascending=False).to_csv(
        os.path.join(out_dir, 'feature_importance.csv'), index=False)

    # ---- ROC 图 ----
    fpr, tpr, _ = roc_curve(y_te, p_te)
    plt.figure(figsize=(5, 5))
    plt.plot(fpr, tpr, lw=2, label=f'AUC={m_te["AUC"]:.3f}')
    plt.plot([0, 1], [0, 1], 'k--', lw=1)
    plt.xlabel('False Positive Rate'); plt.ylabel('True Positive Rate')
    plt.title(f'{organ} failure - external validation')
    plt.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, f'{organ}_external_ROC.pdf'), dpi=300)
    plt.close()
    print(f'[{organ} | {modality}] 模型训练完成 ✅ -> {out_dir}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', required=True, help='heart/lung/liver/renal/hemat/organ')
    ap.add_argument('--modality', default='proteome', choices=list(config.MODALITY_FILES.keys()))
    ap.add_argument('--features', default='delong', choices=['top90', 'delong', 'all'],
                    help='delong=DeLong显著面板(默认,精简) top90=90%增益特征 all=全部')
    ap.add_argument('--cv-folds', type=int, default=5)
    ap.add_argument('--bootstrap', type=int, default=1000)
    args = ap.parse_args()
    label = {v: k for k, v in config.ORGAN_SHORT.items()}[args.organ]
    train_eval(label, args.modality, args.features, args.cv_folds, args.bootstrap)
