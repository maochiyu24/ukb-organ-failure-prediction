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
中介分析每器官数据集组装
=========================
人群: 全人群暴露矩阵 ∩ 组学测量者, Region==1
暴露: lifestyle_score, psych_score
中介: 组学面板（proteome+metabolome DeLong 显著）+ 血液面板（blood DeLong 显著）
协变量: Age, Sex, Townsend
结局: 各器官 incident 标签

输出: result/of825/06_mediation/data/{organ}_mediation.csv
"""
import os
import numpy as np
import pandas as pd

BASE = _PROJECT + ''
OUT = os.path.join(BASE, 'result', 'of825', '06_mediation', 'data')
PREP = os.path.join(BASE, 'result', 'of825', '01_prep')
RANK = os.path.join(BASE, 'result', 'of825', '02_ranking')
ORGANS = ['heart', 'lung', 'liver', 'renal', 'hemat', 'organ']
ORG_LABEL = {o: f'{o}_failure' if o != 'organ' else 'organ_failure' for o in ORGANS}


def delong_panel(organ, modality):
    f = os.path.join(RANK, f'{organ}_{modality}', 'Delong_Selection_Results.csv')
    if not os.path.exists(f):
        return []
    df = pd.read_csv(f)
    return df[df['Delong1'] < 0.05]['feature'].tolist()


def main():
    expos = pd.read_csv(os.path.join(OUT, 'ukb_full_exposure_matrix.csv'))
    expos['Participant ID'] = expos['Participant ID'].astype(str)
    print(f'全人群暴露矩阵: {len(expos):,}')

    for organ in ORGANS:
        label = ORG_LABEL[organ]
        # 基础表（proteome prep: Region + 标签）
        base = pd.read_csv(os.path.join(PREP, 'proteome_prep.csv'))
        base = base[base['Region'].isin([1])][['Participant ID', label]]
        base['Participant ID'] = base['Participant ID'].astype(str)

        df = expos.merge(base, on='Participant ID', how='inner')

        # 组学中介（proteome + metabolome 显著面板）
        omics_feats = []
        for mod in ['proteome', 'metabolome']:
            feats = delong_panel(organ, mod)
            prep = pd.read_csv(os.path.join(PREP, f'{mod}_prep.csv'))
            prep['Participant ID'] = prep['Participant ID'].astype(str)
            sub = prep[['Participant ID'] + feats]
            df = df.merge(sub, on='Participant ID', how='left')
            omics_feats += [f'{mod}__{f}' for f in feats]
            df = df.rename(columns={f: f'{mod}__{f}' for f in feats})

        # 血液中介
        blood_feats = delong_panel(organ, 'blood')
        if blood_feats:
            prep = pd.read_csv(os.path.join(PREP, 'blood_prep.csv'))
            prep['Participant ID'] = prep['Participant ID'].astype(str)
            sub = prep[['Participant ID'] + blood_feats]
            df = df.merge(sub, on='Participant ID', how='left')
            df = df.rename(columns={f: f'blood__{f}' for f in blood_feats})
            blood_feats = [f'blood__{f}' for f in blood_feats]

        # 中介测量过滤（至少有一个组学中介有值）
        med_cols = omics_feats + blood_feats
        df = df.dropna(subset=med_cols, how='all')

        # 标签转 int
        df[label] = df[label].astype(int)
        # 协变量
        cov = ['Age', 'Sex', 'Townsend deprivation index at recruitment']
        keep = ['Participant ID', 'lifestyle_score', 'psych_score'] + cov + [label] + med_cols
        out = df[keep]
        out.to_csv(os.path.join(OUT, f'{organ}_mediation.csv'), index=False)
        print(f'{organ:6s}: n={len(out):,} | 组学中介 {len(omics_feats)} + 血液中介 {len(blood_feats)} '
              f'| 阳性={out[label].sum():,} | lifestyle缺失={out["lifestyle_score"].isna().sum()} psych缺失={out["psych_score"].isna().sum()}')

    print(f'\n✅ 全部输出 -> {OUT}')


if __name__ == '__main__':
    main()
