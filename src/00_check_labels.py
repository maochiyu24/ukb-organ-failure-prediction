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
00_check_labels.py - of902 六系统标签重建一致性检验 (Phase 0 检查点 1)
=======================================================================
对照: of825 旧五系统定义 (同诊断矩阵)
输出: result/of902/00_label_validation_report.txt
"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

RESULT = os.path.join(config.RESULT_DIR)
os.makedirs(RESULT, exist_ok=True)
MATRIX = config.DIAG_MATRIX

# of825 旧定义 (对照)
OLD_ICD = {
    'heart': ['I13', 'I50', 'I97'],
    'lung':  ['J96'],
    'liver': ['K70', 'K71', 'K72', 'K91'],
    'renal': ['N99', 'N17', 'N19'],
    'hemat': ['D65', 'D68'],
}


def build_labels(icd_def):
    """按 ICD 定义从诊断矩阵重建: 阳性(值1), 排除(值2), 返回 df[org]=0/1/2"""
    need = sorted({c for cs in icd_def.values() for c in cs})
    diag = pd.read_csv(MATRIX, usecols=lambda c: c in need or c == 'Participant ID')
    missing = [c for c in need if c not in diag.columns]
    out = pd.DataFrame({'Participant ID': diag['Participant ID']})
    for org, codes in icd_def.items():
        cols = [c for c in codes if c in diag.columns]
        vals = diag[cols]
        pos = vals.eq(1).any(axis=1)
        ex = vals.eq(2).any(axis=1)
        lab = np.zeros(len(diag), dtype=int)
        lab[pos] = 1
        lab[ex & ~pos] = 2
        out[org] = lab
    return out, missing


def main():
    new_df, miss_new = build_labels(config.ORGAN_ICD)
    old_df, miss_old = build_labels(OLD_ICD)
    L = []
    L.append('# of902 六系统标签重建一致性报告')
    L.append(f'人群: {len(new_df):,} (诊断矩阵)')
    L.append(f'缺失列 of902: {miss_new} | of825: {miss_old}')
    L.append('')
    L.append('== 每系统阳性(值1)/排除(值2) 全队列 ==')
    for org, codes in config.ORGAN_ICD.items():
        n1 = (new_df[org] == 1).sum()
        n2 = (new_df[org] == 2).sum()
        L.append(f'  [{org}] ICD={codes}: 阳性={n1:,} ({n1/len(new_df):.2%}) | '
                 f'prevalent排除={n2:,}')
    L.append('')
    L.append('== 新旧定义差异归因 (共同器官) ==')
    m = old_df.merge(new_df, on='Participant ID', suffixes=('_old', '_new'))
    for org in ['heart', 'lung', 'liver', 'renal', 'hemat']:
        a = (m[f'{org}_old'] == 1).values
        b = (m[f'{org}_new'] == 1).values
        only_old = int((a & ~b).sum())     # 旧有新增无 (被剔除码)
        only_new = int((b & ~a).sum())     # 新有旧无 (新增码如 K74)
        L.append(f'  [{org}] 旧定义阳性={a.sum():,} -> 新定义={b.sum():,} | '
                 f'仅旧(剔除码)={only_old:,} | 仅新(新增码)={only_new:,}')
    L.append('')
    L.append('== brain (新增) 构成: 缺血 vs 出血 ==')
    for c in ['I60', 'I61', 'I62', 'I63', 'I64']:
        col = pd.read_csv(MATRIX, usecols=[c])
        L.append(f'  {c}: 阳性={(col[c]==1).sum():,} 排除={(col[c]==2).sum():,}')
    # 全部六系统阳性数并入 organ (先构建)
    any6 = new_df[[o for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain']]]
    new_df['organ'] = (any6 == 1).any(axis=1).astype(int)
    # Region 分布 (England vs Scot+Wal) — 供功效评估
    country = pd.read_csv(config.COUNTRY_FILE)
    country['Region'] = country['Country'].map(config.COUNTRY_MAP)
    reg = country[['Participant ID', 'Region']]
    nw = new_df.merge(reg, on='Participant ID', how='left')
    # 全部六系统阳性数并入 organ (先构建)
    any6 = new_df[[o for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain']]]
    new_df['organ'] = (any6 == 1).any(axis=1).astype(int)
    L.append('')
    L.append('== 六系统 England (Region=1) 阳性 — 分析人群功效预估 ==')
    for org in list(config.ORGAN_ICD) + ['organ']:
        n1 = ((nw[org] == 1) & (nw['Region'] == 1)).sum()
        L.append(f'  [{org}] England 阳性={n1:,}')
    report = '\n'.join(L)
    with open(os.path.join(RESULT, '00_label_validation_report.txt'), 'w') as f:
        f.write(report)
    print(report)


if __name__ == '__main__':
    main()
