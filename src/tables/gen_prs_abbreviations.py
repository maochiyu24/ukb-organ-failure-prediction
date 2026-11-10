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
gen_prs_table.py — Table S7: PRS 缩写对照 (39 个)
================================================
数据源: result/of903/01_prep/prs_prep.csv 列名中的
        'Standard_PRS_for_<label>__<ABBR>_' 解析得到源标签与缩写。
输出:   result908/tables/pro/TableS7_PRS_abbreviations.csv
        result908/tables/pro/prs_abbr_map.csv (供 organize_tables_final.py 重命名 S2d 用)
"""
import os
import re
import pandas as pd

PREP = _PROJECT + '/result/of903/01_prep/prs_prep.csv'
OUT = _PROJECT + '/result/result908/tables/pro'
os.makedirs(OUT, exist_ok=True)

# 表内显示缩写(与现有图表一致)
DISPLAY = {'HT': 'HTN', 'EBMDT': 'eBMD', 'HBA1C_DF': 'HbA1c', 'LDL_SF': 'LDL', 'HEIGHT': 'Height'}
# 发表用全称(英式拼写, 统一大小写与术语)
FULL = {
    'AAM': ("age at menopause", 'Reproductive ageing',
            'Source label reads "age at menopause"; most published PRS panels use AAM for age at menarche \u2014 verify which trait was scored.'),
    'AD': ("Alzheimer's disease", 'Neurological and psychiatric', ''),
    'AF': ('atrial fibrillation', 'Cardiometabolic', ''),
    'AMD': ('age-related macular degeneration', 'Musculoskeletal, ophthalmic and other', ''),
    'AST': ('asthma', 'Respiratory', ''),
    'BC': ('breast cancer', 'Cancer', ''),
    'BD': ('bipolar disorder', 'Neurological and psychiatric', ''),
    'BMI': ('body mass index', 'Cardiometabolic and anthropometric', ''),
    'CAD': ('coronary artery disease', 'Cardiometabolic', ''),
    'CD': ("Crohn's disease", 'Autoimmune and inflammatory', ''),
    'CED': ('coeliac disease', 'Autoimmune and inflammatory', ''),
    'CRC': ('colorectal cancer', 'Cancer', 'Source label reads "bowel cancer".'),
    'CVD': ('cardiovascular disease', 'Cardiometabolic', ''),
    'EOC': ('epithelial ovarian cancer', 'Cancer', ''),
    'EBMDT': ('estimated bone mineral density (T-score)', 'Musculoskeletal, ophthalmic and other', ''),
    'HBA1C_DF': ('glycated haemoglobin (HbA1c)', 'Cardiometabolic', ''),
    'HEIGHT': ('height', 'Cardiometabolic and anthropometric', ''),
    'HDL': ('high-density lipoprotein cholesterol', 'Cardiometabolic', ''),
    'HT': ('hypertension', 'Cardiometabolic', ''),
    'IOP': ('intraocular pressure', 'Musculoskeletal, ophthalmic and other', ''),
    'ISS': ('ischaemic stroke', 'Neurological and psychiatric', ''),
    'LDL_SF': ('low-density lipoprotein cholesterol', 'Cardiometabolic', ''),
    'MEL': ('melanoma', 'Cancer', ''),
    'MS': ('multiple sclerosis', 'Neurological and psychiatric', ''),
    'OP': ('osteoporosis', 'Musculoskeletal, ophthalmic and other', ''),
    'PC': ('prostate cancer', 'Cancer', ''),
    'PD': ("Parkinson's disease", 'Neurological and psychiatric', ''),
    'POAG': ('primary open-angle glaucoma', 'Musculoskeletal, ophthalmic and other', ''),
    'PSO': ('psoriasis', 'Autoimmune and inflammatory', ''),
    'RA': ('rheumatoid arthritis', 'Autoimmune and inflammatory', ''),
    'RHR': ('resting heart rate', 'Cardiometabolic', ''),
    'SCZ': ('schizophrenia', 'Neurological and psychiatric', ''),
    'SLE': ('systemic lupus erythematosus', 'Autoimmune and inflammatory', ''),
    'T1D': ('type 1 diabetes', 'Cardiometabolic', ''),
    'T2D': ('type 2 diabetes', 'Cardiometabolic', ''),
    'TCH': ('total cholesterol', 'Cardiometabolic', ''),
    'TTG': ('total triglyceride', 'Cardiometabolic', ''),
    'UC': ('ulcerative colitis', 'Autoimmune and inflammatory', ''),
    'VTE': ('venous thromboembolism', 'Cardiometabolic',
            'Source label reads "venous thromboembolic disease".'),
}

cols = pd.read_csv(PREP, nrows=0).columns.tolist()
rows = []
for c in cols:
    m = re.match(r'Standard_PRS_for_(.+)__([A-Za-z0-9_]+)_$', c)
    if not m:
        continue
    src_label, abbr = m.group(1).replace('_', ' ').strip(), m.group(2)
    disp = DISPLAY.get(abbr, abbr)
    full, cat, note = FULL.get(abbr, (src_label, 'Other', ''))
    rows.append(dict(**{'PRS abbreviation': f'PRS-{disp}', 'Full name': full,
                        'Category': cat, 'Source label in data': src_label,
                        'Notes': note}))
t = pd.DataFrame(rows).sort_values('PRS abbreviation').reset_index(drop=True)
assert len(t) == 39, f'expected 39 PRS, got {len(t)}'
t.to_csv(f'{OUT}/TableS7_PRS_abbreviations.csv', index=False, encoding='utf-8-sig')
t[['PRS abbreviation', 'Full name']].assign(Display=lambda d: d['Full name'] + ' (' + d['PRS abbreviation'] + ')') \
 .to_csv(f'{OUT}/prs_abbr_map.csv', index=False, encoding='utf-8-sig')
print(f'saved TableS7 ({len(t)} rows) + prs_abbr_map.csv')
print(t[['PRS abbreviation', 'Full name', 'Category']].to_string(index=False))
