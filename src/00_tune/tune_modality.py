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
00_tune - 模态级统一调参
========================
对每个模态，用【全特征集】+ organ_failure（综合衰竭）标签在 Region==1 训练集上
GridSearchCV(3折, roc_auc) 确定该模态唯一超参数。

逻辑依据：
  - 超参数主要由数据形态（特征维度/样本量/信噪比）决定；
    同一模态 6 个器官共享相同特征空间与样本，故每模态一套参数，跨器官复用
  - 不沿用 ZS（抑郁任务）参数：器官衰竭任务需重新确定
  - 先确定参数 → 后续该模态所有步骤（去冗余/特征选择/建模）共用此参数

输出: result/of823/01_prep/{modality}_params.json
      {"params": {...}, "best_auc": x, "grid_size": n, "n_features": n, "n_samples": n, "date": ...}

用法: python 00_tune/tune_modality.py --modality proteome
"""
import os
import sys
import json
import time
import argparse
import pandas as pd
from sklearn.model_selection import GridSearchCV, StratifiedKFold
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '01_prep'))
import config


def tune_modality(modality):
    prep_file = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'], f'{modality}_prep.csv')
    if not os.path.exists(prep_file):
        raise FileNotFoundError(f'请先运行 01_prep: {prep_file}')
    out_json = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'], f'{modality}_params.json')
    if os.path.exists(out_json):
        print(f'[resume] 参数已存在: {out_json}')
        return json.load(open(out_json))

    df = pd.read_csv(prep_file)
    train = df[df['Region'].isin(config.REGION_TRAIN)].copy()
    train = train[train['organ_failure'].isin([0, 1])]
    y = train['organ_failure']
    X = train.drop(columns=['Participant ID', 'Region'] + config.LABEL_COLUMNS)
    # 特征名清洗（与 ranking 保持一致：取分号前部分等）
    from prep_data import clean_feature_names
    new_cols, _ = clean_feature_names(X.columns.tolist(), config.LABEL_COLUMNS)
    X.columns = new_cols

    print(f'\n{"="*66}\n[{modality}] 模态级调参（全特征 {X.shape[1]} × 训练集 {len(X)}，'
          f'organ_failure 阳性={y.sum()}）\n{"="*66}')
    cv = StratifiedKFold(**config.MODEL_CV)
    grid = GridSearchCV(
        lgb.LGBMClassifier(objective='binary', random_state=42, n_jobs=config.N_JOBS_RANKING),
        config.MODEL_PARAM_GRID, cv=cv, scoring='roc_auc',
        n_jobs=1, verbose=1)
    t0 = time.time()
    grid.fit(X, y)
    elapsed = time.time() - t0

    # 仅整数型参数转 int（n_estimators/num_leaves/min_child_samples），浮点参数保留
    int_params = {'n_estimators', 'num_leaves', 'min_child_samples', 'max_depth', 'subsample_for_bin'}
    params = {k: (int(v) if k in int_params else v) for k, v in grid.best_params_.items()}
    result = {
        'modality': modality,
        'params': params,
        'best_auc': float(grid.best_score_),
        'grid_size': len(config.MODEL_PARAM_GRID['n_estimators'])
                     * len(config.MODEL_PARAM_GRID['learning_rate'])
                     * len(config.MODEL_PARAM_GRID['num_leaves'])
                     * len(config.MODEL_PARAM_GRID.get('min_child_samples', [1]))
                     * len(config.MODEL_PARAM_GRID['class_weight']),
        'n_features': int(X.shape[1]),
        'n_samples': int(len(X)),
        'elapsed_min': round(elapsed / 60, 1),
    }
    with open(out_json, 'w') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f'✅ [{modality}] 最优参数: {params}')
    print(f'   内部 AUC: {grid.best_score_:.4f} | 耗时 {elapsed/60:.1f} 分钟')
    print(f'   已保存: {out_json}')
    return result


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--modality', required=True, choices=list(config.MODALITY_FILES.keys()))
    args = ap.parse_args()
    tune_modality(args.modality)
