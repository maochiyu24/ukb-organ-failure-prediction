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
01_prep - 数据准备
==================
为每个模态构建模型输入矩阵：
  - 蛋白组(OF/data/organ_failure.csv) 已含 Region 列
  - 其余模态(metabolome/prs/brain/history/lifestyle/psych) 无 Region，
    按 Participant ID 从 UKB 评估中心映射合并 Region (England=1, Scotland=2, Wales=3)
  - 特征名清洗：蛋白名取分号前部分，非法字符 -> '_'，重复列名加后缀
  - 输出: result/of823/01_prep/{modality}_prep.csv
         每文件列 = Participant ID, Region, <特征...>, <标签列...>

用法:
  python 01_prep/prep_data.py [--modality proteome] [--quick N]
"""
import os
import re
import sys
import argparse
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def clean_feature_names(columns, labels, id_col='Participant ID', region_col='Region'):
    """参照 ZS model.ipynb 的 clean_feature_names + OF 的蛋白名简化。
    返回 (清洗后列名列表, 特征列索引列表)"""
    new_cols, feature_idx = [], []
    seen = {}
    for col in columns:
        if col == id_col or col in labels or col == region_col:
            new_cols.append(col)
            continue
        feature_idx.append(len(new_cols))
        # 蛋白名取分号前部分；其余保留
        clean = col.split(';')[0] if ';' in col else col
        clean = re.sub(r'[^a-zA-Z0-9_]', '_', str(clean))
        clean = f'f_{clean}' if clean and clean[0].isdigit() else clean
        # 空名兜底
        if not clean:
            clean = 'feature'
        # 重复列名加后缀
        if clean in seen:
            seen[clean] += 1
            clean = f'{clean}_{seen[clean]}'
        else:
            seen[clean] = 1
        new_cols.append(clean)
    return new_cols, feature_idx


def load_modality(modality):
    path = config.MODALITY_FILES[modality]
    df = pd.read_csv(path)
    print(f'[{modality}] 读取 {path}')
    if modality == 'blood' and not config.INCIDENT_ONLY:
        # ZS 血生化: 无器官衰竭标签/Region。
        # 单模态建模用 blood 全部样本(490k)，标签从 OF 全人群诊断标签文件(his 502k)合并
        df = df.drop(columns=[c for c in ['F32', 'Region'] if c in df.columns])
        labels = pd.read_csv(config.MODALITY_FILES['history'],
                             usecols=['Participant ID'] + config.LABEL_COLUMNS)
        df = df.merge(labels, on='Participant ID', how='left')
        miss = df[config.LABEL_COLUMNS[0]].isna().sum()
        print(f'  [blood] 全人群标签合并: {df.shape[0]} 样本, 标签缺失: {miss}')
    elif modality == 'blood':
        # incident-only 模式: 标签由诊断矩阵重建，这里只保留特征
        df = df.drop(columns=[c for c in ['F32', 'Region'] if c in df.columns])
        print(f'  [blood] incident-only 模式: 标签将由诊断矩阵重建')
    print(f'  原始形状: {df.shape}')
    return df


def attach_region(df):
    """若数据无 Region 列，从 country classification 合并"""
    if 'Region' in df.columns:
        print('  已含 Region 列，无需合并')
        return df
    country = pd.read_csv(config.COUNTRY_FILE, usecols=['Participant ID', 'Country'])
    country['Region'] = country['Country'].map(config.COUNTRY_MAP)
    n_before = len(df)
    df = df.merge(country[['Participant ID', 'Region']], on='Participant ID', how='left')
    miss = df['Region'].isna().sum()
    print(f'  合并 Region: {n_before} -> {len(df)} (缺失 Region: {miss})')
    return df


def rebuild_labels_incident_only(df, id_col='Participant ID'):
    """incident-only 标签重建（OF_INCIDENT_ONLY=1 时启用）：
    从诊断矩阵按器官 ICD 定义重建 6 个标签：
      值1(基线后新发) -> 阳性 1
      值2(基线前/基线期 prevalent) -> 该样本从分析中【排除】
      值0(无诊断) -> 阴性 0
    返回 (新df, 排除样本数)"""
    code_def = config.ORGAN_ICD
    need = [id_col] + [c for codes in code_def.values() for c in codes]
    diag = pd.read_csv(config.DIAG_MATRIX, usecols=lambda c: c in need)
    # 只保留矩阵中存在的 ICD 列
    exist = {c for c in diag.columns if c != id_col}
    df = df.merge(diag, on=id_col, how='left')
    exclude = pd.Series(False, index=df.index)
    for organ, codes in code_def.items():
        present = [c for c in codes if c in exist]
        if not present:
            df[f'{organ}_failure'] = 0
            continue
        vals = df[present].fillna(0)
        df[f'{organ}_failure'] = vals.eq(1).any(axis=1).astype(int)
        exclude |= vals.eq(2).any(axis=1)
    df['organ_failure'] = df[['liver_failure', 'lung_failure', 'heart_failure',
                              'renal_failure', 'hemat_failure',
                              'brain_failure']].any(axis=1).astype(int)
    n_excl = int(exclude.sum())
    df = df[~exclude].reset_index(drop=True)
    # 删除诊断矩阵 ICD 列（防止被当作特征参与建模 -> 标签泄漏）
    icd_cols = [c for c in df.columns if c != id_col and c not in config.LABEL_COLUMNS
                and c in {c for codes in code_def.values() for c in codes}]
    if icd_cols:
        df = df.drop(columns=icd_cols)
    return df, n_excl


def prep_modality(modality, quick=None, out_dir=None):
    df = load_modality(modality)
    df = attach_region(df)

    # 标签列检查
    missing_labels = [c for c in config.LABEL_COLUMNS if c not in df.columns]
    if missing_labels and not config.INCIDENT_ONLY:
        raise ValueError(f'[{modality}] 缺少标签列: {missing_labels}')

    if config.INCIDENT_ONLY:
        # incident-only: 从诊断矩阵重建标签（值1=阳性，值2=排除，值0=阴性）
        df, n_excl = rebuild_labels_incident_only(df)
        print(f'  [incident-only] 标签重建完成，排除 prevalent(值2)样本: {n_excl}')
        # 去掉模态自带标签列（避免混淆）
        df = df.drop(columns=[c for c in config.LABEL_COLUMNS if c in df.columns and
                              c not in ['liver_failure', 'lung_failure', 'heart_failure',
                                        'renal_failure', 'hemat_failure', 'brain_failure',
                                        'organ_failure']]
                     , errors='ignore')
    else:
        missing_labels = [c for c in config.LABEL_COLUMNS if c not in df.columns]
        if missing_labels:
            raise ValueError(f'[{modality}] 缺少标签列: {missing_labels}')

    # 特征名清洗
    new_cols, _ = clean_feature_names(df.columns.tolist(), config.LABEL_COLUMNS)
    df.columns = new_cols

    # 缺失处理（ZS 标准）：特征缺失率>30% 剔除；
    # 插补方法按模态缺失机制区分（参数仅在训练集 Region==1 内计算，防泄漏）：
    #   metabolome: NMR 左删失（低于检测限）-> 每列最小值的一半 (half-min)
    #   prs:        标准化评分缺失 -> 中位数（人群平均遗传风险）
    #   其他模态:   中位数（无缺失时不影响）
    feat_cols = [c for c in df.columns
                 if c not in ['Participant ID', 'Region'] + config.LABEL_COLUMNS]
    if feat_cols:
        train_mask = df['Region'].isin(config.REGION_TRAIN)
        miss = df.loc[train_mask, feat_cols].isna().mean()
        drop_cols = miss[miss > 0.3].index.tolist()
        if drop_cols:
            print(f'  剔除缺失率>30%的特征: {len(drop_cols)} 个')
            df = df.drop(columns=drop_cols)
            feat_cols = [c for c in feat_cols if c not in drop_cols]
        n_miss = int(df.loc[train_mask, feat_cols].isna().sum().sum())
        if n_miss > 0:
            if modality == 'metabolome':
                # 左删失：每列最小值的一半（训练集内计算）
                fill_vals = df.loc[train_mask, feat_cols].min() / 2
                method = 'half-min（低于检测限）'
            else:
                fill_vals = df.loc[train_mask, feat_cols].median()
                method = '中位数'
            df[feat_cols] = df[feat_cols].fillna(fill_vals)
            print(f'  {method} 插补 {n_miss} 个缺失值（参数来自训练集）')

    # 仅保留 Region 有效的样本（训练+测试区域）
    df = df[df['Region'].isin(config.REGION_TRAIN + config.REGION_TEST)]
    print(f'  区域过滤后: {df.shape} (Region1={len(df[df.Region==1])}, 2/3={len(df[df.Region.isin([2,3])])})')

    # 标签转 int
    for c in config.LABEL_COLUMNS:
        df[c] = df[c].astype(int)

    if quick:
        # quick 模式：每区域按 organ_failure 标签比例分层抽样（保证两类都有）
        parts = []
        for r in sorted(df['Region'].unique()):
            sub = df[df['Region'] == r]
            pos, neg = sub[sub['organ_failure'] == 1], sub[sub['organ_failure'] == 0]
            ratio = len(pos) / len(sub) if len(sub) else 0.5
            n_pos = max(1, min(quick - 1, int(quick * ratio)))
            n_neg = min(quick - n_pos, len(neg))
            n_pos = min(n_pos, quick - n_neg)
            parts.append(pd.concat([pos.sample(n_pos, random_state=42),
                                    neg.sample(n_neg, random_state=42)]))
        df = pd.concat(parts).sort_values('Region').reset_index(drop=True)
        print(f'  [quick={quick}] 比例分层抽样后: {df.shape} '
              f'(阳性={df["organ_failure"].sum()})')

    out_dir = out_dir or os.path.join(config.RESULT_DIR, config.SUBDIRS['prep'])
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'{modality}_prep.csv')
    df.to_csv(out_path, index=False)
    print(f'  ✅ 已保存: {out_path} ({df.shape[0]} 行 × {df.shape[1]} 列)')
    return out_path


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--modality', default='proteome',
                    choices=list(config.MODALITY_FILES.keys()))
    ap.add_argument('--quick', type=int, default=None,
                    help='每区域抽样 N 行（流程验证用）')
    args = ap.parse_args()
    prep_modality(args.modality, quick=args.quick)
