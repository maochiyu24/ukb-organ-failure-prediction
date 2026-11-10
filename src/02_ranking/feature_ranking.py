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
02_ranking - 特征选择（参照 ZS blood_ranking.ipynb 全流程）
============================================================
对指定 器官标签 × 模态 执行：
  1. 训练集(Region==1) 特征 Spearman 相关 -> 层次聚类(ward, 1-|rho|, 阈值0.5)
  2. 单特征 10 折 CV AUC（LightGBM, 参数见 config.LGB_PARAMS）
  3. 每簇保留 AUC 最高特征 -> best_features
  4. 10 折 CV 内 LightGBM TotalGain + SHAP 综合重要性 -> Ensemble_cv
  5. 累计增益前 90% 特征 -> Top_90_InfoGain_features.csv
  6. DeLong 顺序前向选择 -> Delong_Selection_Results.csv

输出目录: result/of823/02_ranking/{organ}/
用法:
  python 02_ranking/feature_ranking.py --organ heart --modality proteome
  python 02_ranking/feature_ranking.py --organ all --modality proteome [--resume]
"""
import os
import sys
import json
import time
import argparse
import numpy as np
import pandas as pd
from collections import Counter
from scipy.cluster import hierarchy
from scipy.spatial.distance import squareform
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from delong import delong_roc_test


def get_modality_params(modality):
    """读取模态级统一参数；未调参时回退 ZS 默认参数"""
    params_json = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'], f'{modality}_params.json')
    if os.path.exists(params_json):
        with open(params_json) as f:
            p = json.load(f)['params']
        print(f'  [参数] {modality} 模态统一参数: {p}')
        return dict(config.LGB_PARAMS, **p)  # 保证 verbosity 等基础字段
    print(f'  [参数] 未找到 {modality}_params.json，回退默认参数')
    return dict(config.LGB_PARAMS)


# ---------------- 阶段 1: 聚类去冗余 ----------------
def spearman_corr_fast(df):
    """快速 Spearman 相关矩阵：rank 后一次 BLAS 矩阵乘法。
    与 pandas .corr(method='spearman') 数值一致（数据无 NaN 时完全等价）"""
    ranks = df.rank(method='average').values.astype(np.float64)
    ranks = ranks - ranks.mean(axis=0)
    std = np.sqrt((ranks ** 2).sum(axis=0))
    corr = (ranks.T @ ranks) / np.outer(std, std)
    corr = np.clip(corr, -1.0, 1.0)
    return pd.DataFrame(corr, index=df.columns, columns=df.columns)


def spearman_cluster(df_feature, result_path, organ, resume):
    """Spearman 相关 + ward 层次聚类，阈值 0.5 切分"""
    out_cluster = os.path.join(result_path, f'{organ}_feature_clusters.csv')
    out_corr = os.path.join(result_path, f'{organ}_correlation_matrix.csv')
    if resume and os.path.exists(out_cluster):
        cluster_data = pd.read_csv(out_cluster)
        print(f'  [resume] 聚类结果已存在: {out_cluster}')
        return cluster_data
    print(f'  计算 Spearman 相关矩阵 ({df_feature.shape[1]} 特征)...')
    t0 = time.time()
    corr = spearman_corr_fast(df_feature)
    corr.to_csv(out_corr)
    dist = 1 - np.abs(corr.values)
    dist_array = squareform(dist, checks=False)
    linkage = hierarchy.linkage(dist_array, method='ward')
    cluster_ids = hierarchy.fcluster(linkage, config.CLUSTER_DISTANCE_THRESHOLD, criterion='distance')
    cluster_data = pd.DataFrame({'feature': df_feature.columns, 'ClusterID': cluster_ids})
    cluster_data.to_csv(out_cluster, index=False)
    print(f'  聚类完成: {cluster_data.ClusterID.nunique()} 簇, 耗时 {time.time()-t0:.0f}s')
    return cluster_data


# ---------------- 阶段 2: 单特征 AUC（特征级并行） ----------------
def _auc_one_feature(f, df_feature, df_group, cv, params):
    aucs = []
    for tr, te in cv.split(df_feature[[f]], df_group):
        m = lgb.LGBMClassifier(**params, objective='binary', random_state=42, n_jobs=1)
        m.fit(df_feature.iloc[tr][[f]], df_group.iloc[tr])
        aucs.append(roc_auc_score(df_group.iloc[te], m.predict_proba(df_feature.iloc[te][[f]])[:, 1]))
    return f, np.mean(aucs)


def single_feature_auc(df_feature, df_group, params, result_path, organ, resume):
    out_auc = os.path.join(result_path, f'{organ}_auc_scores.csv')
    if resume and os.path.exists(out_auc):
        auc_df = pd.read_csv(out_auc)
        print(f'  [resume] 单特征AUC已存在: {out_auc}')
        return auc_df
    cv = StratifiedKFold(**config.RANK_CV)
    print(f'  计算单特征 AUC ({df_feature.shape[1]} 特征 × {cv.n_splits} 折, '
          f'{config.N_JOBS_RANKING} 特征并行)...')
    t0 = time.time()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=config.N_JOBS_RANKING) as ex:
        results = list(ex.map(lambda f: _auc_one_feature(f, df_feature, df_group, cv, params),
                              df_feature.columns))
    auc_df = pd.DataFrame(results, columns=['feature', 'AUC'])
    auc_df.to_csv(out_auc, index=False)
    print(f'  单特征AUC完成 ({len(results)} 特征), 耗时 {time.time()-t0:.0f}s')
    return auc_df


# ---------------- 阶段 3: 综合重要性 (TotalGain + SHAP, 折间并行) ----------------
def _imp_one_fold(fold_info, df_feature, df_group, params):
    """单折: 返回 (fold_index, gain_series, shap_mean_series)"""
    import shap
    tr, te = fold_info
    X_tr, X_te = df_feature.iloc[tr], df_feature.iloc[te]
    y_tr, y_te = df_group.iloc[tr], df_group.iloc[te]
    m = lgb.LGBMClassifier(**params, objective='binary', random_state=42, n_jobs=1)
    m.fit(X_tr, y_tr)
    gain = m.feature_importances_.astype(float)
    if gain.sum() > 0:
        gain = gain / gain.sum()
    explainer = shap.TreeExplainer(m)
    sv = explainer.shap_values(X_te)
    sv_mean = np.mean(np.abs(sv), axis=0)
    if sv_mean.sum() > 0:
        sv_mean = sv_mean / sv_mean.sum()
    return gain, sv_mean


def compute_importance(df_feature, df_group, params, result_path, organ, resume):
    out_imp = os.path.join(result_path, f'{organ}_Importance.csv')
    if resume and os.path.exists(out_imp):
        my_imp_df = pd.read_csv(out_imp)
        print(f'  [resume] 重要性已存在: {out_imp}')
        return my_imp_df
    cv = StratifiedKFold(**config.RANK_CV)
    print(f'  计算 TotalGain + SHAP 重要性 ({cv.n_splits} 折并行, 全特征模型)...')
    t0 = time.time()
    from concurrent.futures import ThreadPoolExecutor
    folds = list(cv.split(df_feature, df_group))
    with ThreadPoolExecutor(max_workers=cv.n_splits) as ex:
        results = list(ex.map(lambda fi: _imp_one_fold(fi, df_feature, df_group, params), folds))
    tg_imp_cv = Counter()
    shap_imp_cv = np.zeros(df_feature.shape[1])
    for gain, sv_mean in results:
        tg_imp_cv += Counter(dict(zip(df_feature.columns, gain)))
        shap_imp_cv += sv_mean
    shap_imp_df = pd.DataFrame({'feature': df_feature.columns,
                                'ShapValues_cv': shap_imp_cv / cv.n_splits})
    tg_norm = {k: v / sum(tg_imp_cv.values()) for k, v in tg_imp_cv.items()}
    tg_imp_df = pd.DataFrame({'feature': list(tg_norm.keys()),
                              'TotalGain_cv': list(tg_norm.values())})
    my_imp_df = pd.merge(shap_imp_df, tg_imp_df, on='feature', how='left')
    my_imp_df['Ensemble_cv'] = (my_imp_df['ShapValues_cv'] + my_imp_df['TotalGain_cv']) / 2
    # 排序依据：OF 原代码按 Ensemble_cv（ZS 用 TotalGain_cv，OF 已改进）
    my_imp_df.sort_values('Ensemble_cv', ascending=False, inplace=True)
    my_imp_df.to_csv(out_imp, index=False)
    print(f'  重要性完成, 耗时 {time.time()-t0:.0f}s')
    return my_imp_df


# ---------------- 阶段 4: top90% 累计增益 ----------------
def top90_features(my_imp_df, result_path, organ, resume):
    out_top = os.path.join(result_path, f'Top_90_InfoGain_features.csv')
    if resume and os.path.exists(out_top):
        top_features = pd.read_csv(out_top)['feature'].tolist()
        print(f'  [resume] Top90 已存在: {len(top_features)} 特征')
        return top_features
    imp_score, it = 0, 0
    while imp_score < config.TOP_GAIN_PROP and it < len(my_imp_df):
        imp_score += my_imp_df['Ensemble_cv'].iloc[it]
        it += 1
    top_features = my_imp_df['feature'].iloc[:it].tolist()
    my_imp_df.iloc[:it].to_csv(out_top, index=False)
    print(f'  Top90% 特征数: {len(top_features)}')
    return top_features


# ---------------- 阶段 5: DeLong 顺序前向选择 ----------------
def forward_selection(df_feature, df_group, params, top_features, result_path, organ, resume):
    out_delong = os.path.join(result_path, 'Delong_Selection_Results.csv')
    if resume and os.path.exists(out_delong):
        print(f'  [resume] Delong 结果已存在: {out_delong}')
        return pd.read_csv(out_delong)
    cv = StratifiedKFold(**config.RANK_CV)
    y_pred_prev = [np.zeros(len(df_group)) for _ in range(3)]
    tmp_f, rows, consec_ns = [], [], 0
    t0 = time.time()
    # 精简：候选截断 + 连续不显著提前终止（经验：~10 轮后不再显著）
    candidates = top_features[:config.FORWARD_SELECTION_MAX]
    print(f'  顺序前向选择: {len(top_features)} 候选 -> 截断为 {len(candidates)} 轮 '
          f'(至少跑 {config.FORWARD_SELECTION_MIN} 轮, 之后连续 {config.FORWARD_SELECTION_STOP} '
          f'个不显著提前终止, 折间并行)')
    from concurrent.futures import ThreadPoolExecutor

    def _sel_one_fold(tr, te, my_X):
        m = lgb.LGBMClassifier(**params, objective='binary', random_state=42, n_jobs=1)
        m.fit(my_X.iloc[tr], df_group.iloc[tr])
        p = m.predict_proba(my_X.iloc[te])[:, 1]
        return p, df_group.iloc[te].values

    for k, f in enumerate(top_features):
        tmp_f.append(f)
        my_X = df_feature[tmp_f]
        folds = list(cv.split(my_X, df_group))
        with ThreadPoolExecutor(max_workers=len(folds)) as ex:
            fold_res = list(ex.map(lambda ft: _sel_one_fold(ft[0], ft[1], my_X), folds))
        y_pred_lst, y_true_lst, auc_cv = [], [], []
        for p, yt in fold_res:
            auc_cv.append(roc_auc_score(yt, p))
            y_pred_lst += p.tolist()
            y_true_lst += yt.tolist()
        y_true = np.array(y_true_lst)
        y_pred = np.array(y_pred_lst)
        log10_p = [delong_roc_test(y_true, prev, y_pred) for prev in y_pred_prev]
        y_pred_prev = [y_pred] + y_pred_prev[:2]
        p1 = 10 ** log10_p[0][0][0]
        rows.append([f, np.mean(auc_cv), np.std(auc_cv),
                     p1, 10 ** log10_p[1][0][0], 10 ** log10_p[2][0][0],
                     roc_auc_score(y_true, y_pred)])
        if p1 >= config.DELONG_P:
            consec_ns += 1
            # 至少评估 MIN 轮后才允许提前终止
            if (k + 1) >= config.FORWARD_SELECTION_MIN and consec_ns >= config.FORWARD_SELECTION_STOP:
                print(f'    第 {k+1} 轮: 连续 {consec_ns} 个候选不显著 (p={p1:.4f}), 提前终止')
                break
        else:
            consec_ns = 0
        if (k + 1) % 20 == 0:
            print(f'    {k+1}/{len(candidates)} 特征, AUC={rows[-1][1]:.4f}, 耗时 {time.time()-t0:.0f}s')
    auc_df = pd.DataFrame(rows, columns=['feature', 'AUC_mean', 'AUC_std',
                                         'Delong1', 'Delong2', 'Delong3', 'AUC_all'])
    auc_df[['AUC_mean', 'AUC_std', 'AUC_all']] = np.round(auc_df[['AUC_mean', 'AUC_std', 'AUC_all']], 3)
    auc_df.to_csv(out_delong, index=False)
    print(f'  前向选择完成, 耗时 {time.time()-t0:.0f}s')
    return auc_df


def run_ranking(organ_label, modality='proteome', resume=False):
    """完整特征选择流程"""
    organ = config.ORGAN_SHORT[organ_label]
    prep_file = os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'], f'{modality}_prep.csv')
    if not os.path.exists(prep_file):
        raise FileNotFoundError(f'请先运行 01_prep: {prep_file}')
    result_path = os.path.join(config.RESULT_DIR, config.SUBDIRS['ranking'], f'{organ}_{modality}')
    os.makedirs(result_path, exist_ok=True)

    print(f'\n{"="*70}\n[{organ} | {modality}] 特征选择开始\n{"="*70}')
    df = pd.read_csv(prep_file)
    train = df[df['Region'].isin(config.REGION_TRAIN)].copy()
    train = train[train[organ_label].isin([0, 1])]
    df_group = train[organ_label]
    df_feature = train.drop(columns=['Participant ID', 'Region'] + config.LABEL_COLUMNS)
    # 验证模式：仅取前 N 个特征（环境变量 OF823_MAX_FEATURES）
    max_feat = int(os.environ.get('OF823_MAX_FEATURES', 0) or 0)
    if max_feat > 0:
        df_feature = df_feature.iloc[:, :max_feat]
        print(f'  [验证模式] 仅使用前 {max_feat} 个特征')
    print(f'  训练集: {len(train)} 样本 (阳性={df_group.sum()}), 特征: {df_feature.shape[1]}')

    params = get_modality_params(modality)

    # 阶段 1：高维组学模态（蛋白/代谢/Brain）聚类去冗余；
    #         低维模态（PRS/家族史/生活方式/心理）保留全部特征（每特征独立成簇）
    if modality in config.REDUNDANCY_MODALITIES:
        cluster_data = spearman_cluster(df_feature, result_path, organ, resume)
    else:
        cluster_data = pd.DataFrame({'feature': df_feature.columns,
                                     'ClusterID': range(1, len(df_feature.columns) + 1)})
        print(f'  [{modality}] 低维模态 ({len(df_feature.columns)} 特征)：跳过聚类去冗余，保留全部特征')
    auc_df = single_feature_auc(df_feature, df_group, params, result_path, organ, resume)

    # 每簇保留 AUC 最高特征（中间产物，与 ZS/OF 输出结构一致）
    out_best = os.path.join(result_path, f'{organ}_best_features.csv')
    if not (resume and os.path.exists(out_best)):
        feature_sel = pd.merge(auc_df, cluster_data, on='feature', how='left')
        best = feature_sel.loc[feature_sel.groupby('ClusterID')['AUC'].idxmax()]
        best.to_csv(out_best, index=False)
        print(f'  每簇最佳特征（去冗余后）: {len(best)} 个')

    # 阶段 3-4：重要性基于【去冗余后的每簇最佳特征】计算
    best_feats = pd.read_csv(out_best)['feature'].tolist()
    df_feature_sel = df_feature[best_feats]
    my_imp_df = compute_importance(df_feature_sel, df_group, params, result_path, organ, resume)
    top_features = top90_features(my_imp_df, result_path, organ, resume)

    # 阶段 5：前向选择在 top90% 特征上做
    df_feature_top = df_feature_sel[top_features]
    forward_selection(df_feature_top, df_group, params, top_features, result_path, organ, resume)
    print(f'[{organ} | {modality}] 特征选择完成 ✅')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', required=True,
                    help='器官: heart/lung/liver/renal/hemat/organ 或 all')
    ap.add_argument('--modality', default='proteome',
                    choices=list(config.MODALITY_FILES.keys()))
    ap.add_argument('--resume', action='store_true', help='跳过已完成的阶段')
    args = ap.parse_args()
    if args.organ == 'all':
        for lbl in config.LABEL_COLUMNS:
            run_ranking(lbl, args.modality, args.resume)
    else:
        label = {v: k for k, v in config.ORGAN_SHORT.items()}[args.organ]
        run_ranking(label, args.modality, args.resume)
