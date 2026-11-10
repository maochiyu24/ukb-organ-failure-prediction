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
gen_table1_v4.py — 主表 1 (诊断标签文件口径: 1-year run-in; 全体人群分组)
=========================================================================
队列: 502,131 - 排除 9,227(prevalent 7,797 + 基线后 1 年内事件 1,436) = 492,904
分组: 诊断标签矩阵 all_icd_f_group_1000_25y_instance0.csv
      值2 = prevalent 或 1 年内事件(排除); 值1 = run-in 后新发事件
      血液学 = D68+D69(矩阵无 D65 列, 用户确认不影响)
行: 参与者 n(%) / 基线特征(9) / Events n(%) / Follow-up median(IQR)
注: 标签文件无事件日期, 故本表不列 incidence / age at event / time to event
    (该三项属日期判定口径, 待 survival 扫描修复后另表给出)
输出: result906/tables/pro/Table1_main.csv / .xlsx
"""
import os
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, _PROJECT + '/code/pic904')
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment

R = _PROJECT + '/result/of905'
OUT = _PROJECT + '/result/result908/tables/pro'
M = _PROJECT + '/xm/ZS/8.7/data/all_icd_f_group_1000_25y_instance0.csv'
CODES = {'heart': ['I50'], 'lung': ['J96'], 'liver': ['K72', 'K74'],
         'renal': ['N17', 'N19'], 'hemat': ['D68', 'D69'],
         'brain': ['I60', 'I61', 'I62', 'I63', 'I64']}
DISP = {'heart': 'Heart failure', 'lung': 'Respiratory failure',
        'liver': 'Liver failure/cirrhosis', 'renal': 'Kidney failure',
        'hemat': 'Haematological failure', 'brain': 'Stroke'}

# ---------- 标签矩阵 ----------
need = ['Participant ID'] + sorted({c for v in CODES.values() for c in v})
lab = pd.read_csv(M, usecols=lambda c: c in need, dtype={'Participant ID': str})
val = {o: lab[cs].max(axis=1) for o, cs in CODES.items()}
excl = pd.concat([(v == 2) for v in val.values()], axis=1).any(axis=1)
lab['excluded'] = excl
for o in CODES:
    lab[f'grp_{o}'] = (val[o] == 1) & (~excl)
lab['grp_organ'] = lab[[f'grp_{o}' for o in CODES]].any(axis=1)
lab['grp_none'] = ~lab['excluded'] & ~lab['grp_organ']
cap = lab[~lab.excluded].copy()
print('分析队列(run-in):', len(cap))

# ---------- 基线/随访 ----------
bl = pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
                 usecols=['Participant ID', 'Age at recruitment', 'Sex',
                          'Townsend deprivation index at recruitment',
                          'Education score (England)', 'Income score (England)'])
bl.columns = ['eid', 'Age', 'Sex', 'Townsend', 'Edu', 'Inc']; bl['eid'] = bl['eid'].astype(str)
li = pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/Lifestyle_Instance0.csv',
                 usecols=['Participant ID', 'Pack years of smoking', 'Sleep duration'])
li = li.rename(columns={'Participant ID': 'eid', 'Pack years of smoking': 'PackYrs',
                        'Sleep duration': 'Sleep'}); li['eid'] = li['eid'].astype(str)
fv = pd.read_csv(f'{R}/05_survival/survival_matrix.csv', dtype={'eid': str},
                 usecols=['eid', 'follow_time'])
d = (cap.merge(bl, left_on='Participant ID', right_on='eid', how='left')
        .merge(li, on='eid', how='left').merge(fv, on='eid', how='left'))
for c in ['PackYrs', 'Sleep']:
    d[c] = pd.to_numeric(d[c], errors='coerce')
d.loc[d.PackYrs < 0, 'PackYrs'] = np.nan
d.loc[(d.Sleep < 0) | (d.Sleep > 16), 'Sleep'] = np.nan
d['Female'] = d.Sex == 0
N = len(d)

GROUPS = [('grp_none', 'No organ failure')] + [(f'grp_{o}', DISP[o]) for o in CODES] + \
         [('grp_organ', 'Any organ failure')]


def med_iqr(s):
    return f"{np.nanmedian(s):.2f} ({np.nanpercentile(s, 25):.2f}-{np.nanpercentile(s, 75):.2f})"


rows = []
def add(label, fn):
    rows.append(dict(Characteristic=label, **{disp: fn(d[d[key]]) for key, disp in GROUPS}))

add('Participants', lambda s: f"{len(s):,} ({len(s)/N*100:.1f}%)")
add('Age at recruitment (years)', lambda s: f"{s.Age.mean():.1f} \u00b1 {s.Age.std():.1f}")
add('Female', lambda s: f"{int(s.Female.sum()):,} ({s.Female.mean()*100:.1f}%)")
add('Townsend deprivation index', lambda s: med_iqr(s.Townsend))
add('Education score (IMD)', lambda s: med_iqr(s.Edu))
add('Income score (IMD)', lambda s: med_iqr(s.Inc))
add('Ever smokers', lambda s: f"{int(s.PackYrs.notna().sum()):,} ({s.PackYrs.notna().mean()*100:.1f}%)")
add('Pack years of smoking, ever smokers',
    lambda s: med_iqr(s.loc[s.PackYrs.notna(), 'PackYrs']))
add('Sleep duration (h)', lambda s: med_iqr(s.Sleep))
add('Follow-up (years)', lambda s: med_iqr(s.follow_time))

t1 = pd.DataFrame(rows)[['Characteristic'] + [disp for _, disp in GROUPS]]
t1.to_csv(f'{OUT}/Table1_main.csv', index=False, encoding='utf-8-sig')
with pd.ExcelWriter(f'{OUT}/Table1_main.xlsx') as w:
    t1.to_excel(w, sheet_name='Table1', index=False)
    ws = w.sheets['Table1']
    for j in range(1, len(t1.columns) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 34 if j == 1 else 17
    for c in ws[1]:
        c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True, vertical='center')
    ws.freeze_panes = 'B2'
    r = len(t1) + 3
    notes = [
        'Note. Data are n (%) for categorical variables, mean \u00b1 SD for age at recruitment, and median (IQR) '
        'for all other continuous variables.',
        'Percentages are column-wise (within each outcome group). Participants may contribute to more than one '
        'organ-failure group, so organ-specific groups are not mutually exclusive and do not sum to the composite.',
        'Follow-up was censored at death, loss to follow-up or 31 October 2022; events in the first year after '
        'baseline were not counted (lag period).',
    ]
    for i, nt in enumerate(notes):
        c = ws.cell(row=r + i, column=1, value=nt)
        c.alignment = Alignment(wrap_text=False)
        c.font = Font(size=9)
print('saved Table1_main.csv/.xlsx (标签文件/run-in 口径, 表注已合并)')
print(t1.to_string(index=False))
