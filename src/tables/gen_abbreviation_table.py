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
"""生成 特征原始名 <-> 图内显示名(缩写) 对照表
来源: of903 全部 ranking (02_ranking/{organ}_{modal}/Top_90*) 与 04_fusion merge_features
输出: result/result906/figures_supp/feature_name_mapping.{csv,xlsx}
"""
import os, sys, glob
import pandas as pd
from naming import full_feature_name

R903 = _PROJECT + '/result/of903'
rows = []
seen = set()
for f in glob.glob(f'{R903}/02_ranking/*/Top_90_InfoGain_features.csv'):
    organ = f.split('/')[-2].split('_')[0]
    modal = f.split('/')[-2].split('_', 1)[1]
    df = pd.read_csv(f)
    for x in df['feature']:
        key = (modal, x)
        if key in seen:
            continue
        seen.add(key)
        disp = full_feature_name(f'{modal}__{x}')   # ranking 特征无模态前缀, 一律补前缀
        rows.append({'modality': modal, 'raw_feature': x, 'display_name': disp,
                     'shortened': disp != ' '.join(w.capitalize() for w in x.replace('_', ' ').split()) and disp != x})
for f in glob.glob(f'{R903}/04_fusion/*/merge_features.csv'):
    organ = f.split('/')[-2].replace('_merge', '')
    df = pd.read_csv(f)
    for x in df['feature']:
        key = ('merge', x)
        if key in seen:
            continue
        seen.add(key)
        disp = full_feature_name(x)
        rows.append({'modality': 'merge', 'raw_feature': x, 'display_name': disp,
                     'shortened': disp != ' '.join(w.capitalize() for w in x.replace('_', ' ').split()) and disp != x})

out = pd.DataFrame(rows).drop_duplicates(['modality', 'raw_feature'])
out = out.sort_values(['modality', 'raw_feature'])
# 缩略判定: 与简单 title 化不同或含官方缩写后缀等
out['note'] = ''
out.loc[out['raw_feature'].str.contains('Standard_PRS_for'), 'note'] = 'UKB 官方 PRS 后缀缩写'
# brain 影像特征仅做去下划线展示, 不算缩写
out.loc[out['modality'] == 'brain', 'note'] = ''
out.loc[(out['note'] == '') &
        (out['display_name'].str.len() <= out['raw_feature'].str.len() - 4), 'note'] = '映射缩写'

dest = _PROJECT + '/result/result906/figures_supp/feature_name_mapping.csv'
out.to_csv(dest, index=False, encoding='utf-8-sig')
try:
    out.to_excel(dest.replace('.csv', '.xlsx'), index=False)
    print('xlsx OK')
except Exception as e:
    print('xlsx fail:', e)
print(f'saved {dest}  | 总特征 {len(out)} (含 merge), 其中缩略 {int((out.note!="").sum())} 条')
print(out[out['note'] != ''].groupby('modality').size().to_dict())
