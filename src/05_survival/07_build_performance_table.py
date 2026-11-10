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
07_build_performance_table.py - Table 2 自动生成 (防手抄)
==========================================================
从 survival_metrics_all.csv (C-index/tdAUC) + 03_model 外部 metrics (AUC)
生成 result902/table2_performance.csv + markdown 渲染版。
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

SURV = os.path.join(config.RESULT_DIR, '05_survival', 'survival_metrics_all.csv')
OUT_DIR = _PROJECT + '/result/result902'
os.makedirs(OUT_DIR, exist_ok=True)
ORG_CN = {'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver',
          'renal': 'Renal',
          'brain': 'Brain', 'hemat': 'Hematologic', 'organ': 'Any-organ'}
MODS = ['proteome', 'metabolome', 'blood', 'lifestyle', 'merge']
MOD_CN = {'proteome': 'Proteome', 'metabolome': 'Metabolome', 'blood': 'Biochemistry',
          'lifestyle': 'Lifestyle', 'merge': 'Multimodal fusion'}


def main():
    df = pd.read_csv(SURV)
    rows = []
    for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']:
        for m in MODS:
            r = df[(df['organ'] == o) & (df['modality'] == m)]
            if r.empty:
                continue
            r = r.iloc[0]
            # 二分类 AUC (外部): 03_model 或 04_fusion
            if m == 'merge':
                f = os.path.join(config.RESULT_DIR, '04_fusion', f'{o}_merge',
                                 'external_test_metrics.csv')
            else:
                f = os.path.join(config.RESULT_DIR, '03_model', f'{o}_{m}',
                                 'external_test_metrics.csv')
            auc_ext = np.nan
            if os.path.exists(f):
                auc_ext = round(pd.read_csv(f)['AUC'].iloc[0], 3)
            rows.append({
                'Organ': ORG_CN[o], 'Modality': MOD_CN[m],
                'n_features': int(r.get('n_event_tr', 0) + r.get('n_event_te', 0)
                                  ) if False else '',
                'External_AUC': auc_ext,
                'Cindex_int_LGBM': round(r['Cindex_lgbm_tr'], 3),
                'Cindex_ext_LGBM': round(r['Cindex_lgbm_te'], 3),
                'Cindex_ext_Cox': round(r['Cindex_cox_te'], 3)
                if pd.notna(r.get('Cindex_cox_te')) else np.nan,
                'tdAUC3y_ext': round(r['AUC3y_lgbm_te'], 3)
                if pd.notna(r.get('AUC3y_lgbm_te')) else '',
                'tdAUC5y_ext': round(r['AUC5y_lgbm_te'], 3)
                if pd.notna(r.get('AUC5y_lgbm_te')) else '',
                'tdAUC10y_ext': round(r['AUC10y_lgbm_te'], 3)
                if pd.notna(r.get('AUC10y_lgbm_te')) else '',
            })
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(OUT_DIR, 'table2_performance.csv'), index=False)
    # markdown 渲染
    md = t.to_markdown(index=False)
    with open(os.path.join(OUT_DIR, 'table2_performance.md'), 'w') as f:
        f.write('# Table 2. Discrimination of single-modality and fusion panels\n\n')
        f.write('External = Scotland+Wales (models trained in England).\n\n')
        f.write(md + '\n')
    print(f'✅ Table 2 -> {OUT_DIR}/table2_performance.csv (+ .md)')
    print(t.to_string(index=False))


if __name__ == '__main__':
    main()
