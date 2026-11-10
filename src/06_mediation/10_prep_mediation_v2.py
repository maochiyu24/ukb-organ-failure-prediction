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
10_prep_mediation_v2.py - v2 中介数据组装 (不覆盖 v1)
======================================================
同 v1 逻辑 (England Region1 基础 + proteome/metabolome/blood Delong 面板),
但 exposure = lifestyle_score_v2 / psych_score_v2 (v2 矩阵)。
输出: result/of903/06_mediation_v2/data/{organ}_mediation_v2.csv
"""
import os
import sys
import pandas as pd

BASE = _PROJECT + ''
PREP = os.path.join(BASE, 'result', 'of903', '01_prep')
RANK = os.path.join(BASE, 'result', 'of903', '02_ranking')
OUT = os.path.join(BASE, 'result', 'of903', '06_mediation_v2', 'data')
os.makedirs(OUT, exist_ok=True)
ORGANS = ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
ORG_LABEL = {o: f'{o}_failure' if o != 'organ' else 'organ_failure' for o in ORGANS}
EXPOSURES = ['lifestyle_score_v2', 'psych_score_v2']


def delong_panel(organ, modality):
    f = os.path.join(RANK, f'{organ}_{modality}', 'Delong_Selection_Results.csv')
    if not os.path.exists(f):
        return []
    df = pd.read_csv(f)
    return df[df['Delong1'] < 0.05]['feature'].tolist()


def main():
    expos = pd.read_csv(os.path.join(OUT, 'ukb_full_exposure_matrix_v2.csv'))
    expos['Participant ID'] = expos['Participant ID'].astype(str)
    print(f'v2 暴露矩阵: {len(expos):,} 人')

    for organ in ORGANS:
        label = ORG_LABEL[organ]
        base = pd.read_csv(os.path.join(PREP, 'proteome_prep.csv'))
        base = base[base['Region'].isin([1])][['Participant ID', label]]
        base['Participant ID'] = base['Participant ID'].astype(str)
        df = expos.merge(base, on='Participant ID', how='inner')
        omics_feats = []
        for mod in ['proteome', 'metabolome']:
            feats = delong_panel(organ, mod)
            prep = pd.read_csv(os.path.join(PREP, f'{mod}_prep.csv'))
            prep['Participant ID'] = prep['Participant ID'].astype(str)
            sub = prep[['Participant ID'] + feats]
            df = df.merge(sub, on='Participant ID', how='left')
            df = df.rename(columns={f: f'{mod}__{f}' for f in feats})
            omics_feats += [f'{mod}__{f}' for f in feats]
        blood_feats = delong_panel(organ, 'blood')
        if blood_feats:
            prep = pd.read_csv(os.path.join(PREP, 'blood_prep.csv'))
            prep['Participant ID'] = prep['Participant ID'].astype(str)
            sub = prep[['Participant ID'] + blood_feats]
            df = df.merge(sub, on='Participant ID', how='left')
            df = df.rename(columns={f: f'blood__{f}' for f in blood_feats})
            blood_feats = [f'blood__{f}' for f in blood_feats]
        med_cols = omics_feats + blood_feats
        df = df.dropna(subset=med_cols, how='all')
        keep = (['Participant ID'] + EXPOSURES + ['Age', 'Sex',
                'Townsend deprivation index at recruitment', label] + med_cols)
        out = df[[c for c in keep if c in df.columns]]
        out.to_csv(os.path.join(OUT, f'{organ}_mediation_v2.csv'), index=False)
        print(f'[{organ}] {len(out):,} 人 | 阳性={out[label].sum():,} | '
              f'mediators={len(med_cols)} | lifestyle缺失={out["lifestyle_score_v2"].isna().sum():,} '
              f'psych缺失={out["psych_score_v2"].isna().sum():,}')
    print(f'✅ v2 中介数据 -> {OUT}/')


if __name__ == '__main__':
    main()
