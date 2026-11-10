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
gen_history_table.py — Table S8: 家族史变量对照 (UKB 字段/条件编码/全称)
=====================================================================
依据 UK Biobank Showcase 家族史三字段(20107 父亲 / 20110 母亲 / 20111 兄弟姐妹)
及其共用条件编码 (Data-Coding 1010, "Illnesses, touchscreen self-entry")。
编码→疾病对应经以下公开来源核对(Showcase 页面为 JS 渲染, 其数组标签由以下镜像复现):
  - h2atlas phenotype 索引 (20107_1 heart disease; 20107_3 lung cancer; 20107_6 chronic bronchitis/
    emphysema; 20110_8 high blood pressure; 20111_9 diabetes; 20111_12 severe depression; 20111_100 none)
  - PheWeb UKB-Neale: 20107_4 bowel cancer; 20107_7 不存在(非表型); 20107_10 Alzheimer's disease/dementia;
    20107_11 Parkinson's disease; 20107_13 prostate cancer; 20110_5 breast cancer
  - TSEADB(Neale 标签镜像): 20107_2 stroke; 20110_3 lung cancer; 20111_8 high blood pressure;
    20111_13 prostate cancer; 20110_11 Parkinson's disease
输出: result908/tables/pro/TableS8_family_history_abbreviations.csv
      result908/tables/pro/history_name_map.csv (供 organize_tables_final.py 改名 S2e)
"""
import os
import re
import pandas as pd

OUT = _PROJECT + '/result/result908/tables/pro'
os.makedirs(OUT, exist_ok=True)
S2E = _PROJECT + '/result/result908/tables/TableS2e_Family_history.csv'

FIELD = {'father': ('20107', 'Father'), 'mother': ('20110', 'Mother'),
         'siblings': ('20111', 'Sibling')}
CODE = {  # UKB Data-Coding 1010
    '1': 'heart disease', '2': 'stroke', '3': 'lung cancer', '4': 'bowel cancer',
    '5': 'breast cancer', '6': 'chronic bronchitis/emphysema', '8': 'high blood pressure',
    '9': 'diabetes', '10': "Alzheimer's disease/dementia", '11': "Parkinson's disease",
    '12': 'severe depression', '13': 'prostate cancer',
}
PLAIN = {
    'Father s age at death': "Father's age at death",
    'Mother still alive': 'Mother alive at baseline',
    'Father still alive': 'Father alive at baseline',
    'Number of full brothers': 'Number of full brothers',
    'Number of full sisters': 'Number of full sisters',
    'Breastfed as a baby': 'Breastfed as a baby',
    'Comparative body size at age 10': 'Comparative body size at age 10',
    'Comparative height size at age 10': 'Comparative height size at age 10',
    'Handedness chirality laterality': 'Handedness (chirality/laterality)',
    'Country of birth UK elsewhere': 'Country of birth (UK/elsewhere)',
    'Maternal smoking around birth': 'Maternal smoking around birth',
    'Part of a multiple birth': 'Part of a multiple birth',
    'Adopted as a child': 'Adopted as a child',
}
NOTE = {
    '5': 'Breast cancer was not asked about the father (code absent for field 20107).',
    '13': 'Prostate cancer was not asked about the mother (code absent for field 20110).',
}

rows = []
for feat in sorted(pd.read_csv(S2E).Feature.unique()):
    m = re.match(r'Illnesses of (father|mother|siblings) (\d+)$', feat)
    if m:
        rel, code = m.group(1), m.group(2)
        fid, rel_disp = FIELD[rel]
        disease = CODE.get(code, f'condition code {code}')
        disp = f'{rel_disp}: {disease}'
        rows.append({'Feature in data': feat, 'Display name': disp, 'Relative': rel_disp,
                     'UK Biobank field': fid, 'Condition code (coding 1010)': code,
                     'Full name': disease, 'Source': 'UK Biobank Showcase / Neale-label mirrors',
                     'Notes': NOTE.get(code, '')})
    else:
        rows.append({'Feature in data': feat, 'Display name': PLAIN.get(feat, feat),
                     'Relative': '', 'UK Biobank field': '', 'Condition code (coding 1010)': '',
                     'Full name': PLAIN.get(feat, feat), 'Source': 'UK Biobank Showcase',
                     'Notes': ''})
t = pd.DataFrame(rows)
t.to_csv(f'{OUT}/TableS8_family_history_abbreviations.csv', index=False, encoding='utf-8-sig')
t[['Feature in data', 'Display name']].to_csv(f'{OUT}/history_name_map.csv', index=False,
                                              encoding='utf-8-sig')
print(f'saved TableS8 ({len(t)} rows) + history_name_map.csv')
print(t[['Feature in data', 'Display name', 'UK Biobank field', 'Condition code (coding 1010)']]
      .to_string(index=False))
