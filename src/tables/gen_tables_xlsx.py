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
"""Tables_summary.xlsx: 把 result906/tables 现行主表+附表汇总为单文件多 sheet"""
import glob
import pandas as pd

OUT = _PROJECT + '/result/result906/tables'
files = ['pro/Table1_main.csv',
         'TableS1a_Cindex.csv', 'TableS1b_AUC.csv', 'TableS1_sample_sizes.csv'] + \
        sorted(glob.glob(f'{OUT}/TableS2?_*.csv')) + \
        ['TableS3_mediation_all.csv', 'TableS4_GO_enrichment_all.csv',
         'TableS5_metabolite_mapping.csv']
with pd.ExcelWriter(f'{OUT}/Tables_summary.xlsx') as w:
    for f in files:
        name = ('Table1' if f.endswith('Table1_main.csv') else f.split('/')[-1][:-4])
        path = f if f.startswith('/') else f'{OUT}/{f}'
        pd.read_csv(path).to_excel(w, sheet_name=name[:31], index=False)
print('xlsx ok:', len(files), 'sheets')
