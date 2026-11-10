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
01_build_survival_data.py - 生存数据重建 (of825 时序框架地基)
==============================================================
输入:
  - xm/UKB/diagnoses1.csv                     全队列诊断 + 精确日期 (ICD$YYYY-MM-DD, 259 槽位)
  - xm/UKB/Assessment_centre/2Recruitment.csv 基线日期 (Instance 0)
  - xm/UKB/Assessment_centre/7Death_register_death.csv       死亡日期
  - xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv 失访日期
输出 (result/of825/05_survival/):
  - survival_matrix.csv    生存矩阵 (基线/首诊/死亡/失访/时间/事件)
  - validation_report.txt  与现有标签的一致性验证报告
设计:
  - 事件: 各器官首次诊断 (ORGAN_ICD 前缀匹配, 与现有标签定义一致)
  - prevalent (基线前诊断) 排除; 与管理性删失 CENSOR_DATE 比较
  - 随访截止默认 2022-10-31 (诊断数据提取日, 待用户确认)
"""
import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

# ---------------- 参数 ----------------
UKB = os.path.join(config.XM_DIR, 'UKB')
DIAG_FILE = os.path.join(UKB, 'diagnoses1.csv')
RECRUIT_FILE = os.path.join(UKB, 'Assessment_centre', '2Recruitment.csv')
DEATH_FILE = os.path.join(UKB, 'Assessment_centre', '7Death_register_death.csv')
LOST_FILE = os.path.join(UKB, 'Assessment_centre',
                         '1Baseline_characteristics_participant.csv')
CENSOR_DATE = '2022-10-31'          # ⚠ 诊断数据提取日, 待用户确认后更新
OUT_DIR = os.path.join(config.RESULT_DIR, '05_survival')
os.makedirs(OUT_DIR, exist_ok=True)

ORGAN_ICD = config.ORGAN_ICD        # {liver:[K70,K71,K72,K91], lung:[J96], ...}
# organ_failure = 5 器官任一 (与现有 LABEL_COLUMNS 一致)
FIVE = ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain']


def parse_date(s):
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d')
    except Exception:
        return None


def scan_diagnoses(cache_file=None):
    """分块扫描 diagnoses1.csv: 每器官最早的诊断日期 (全队列)
    ICD 码无点格式: 3位 (K70) 或 4位 (K700=K70.0, K219=K21.9)。
    匹配规则: cell==code (3位) 或 cell.startswith(code) 且第4位为数字 (4位子码)。
    扫描结果缓存到 pickle (重跑省时)。"""
    if cache_file and os.path.exists(cache_file):
        import pickle
        with open(cache_file, 'rb') as f:
            organ_dates = pickle.load(f)
        print(f'  缓存命中: {cache_file} (各器官命中: ' +
              ', '.join(f'{o}={len(v):,}' for o, v in organ_dates.items()) + ')')
        return organ_dates
    print('扫描诊断文件 (分块)...')
    organ_dates = {o: {} for o in list(ORGAN_ICD) + ['organ']}   # id -> min date(str)
    codes = {o: list(cs) for o, cs in ORGAN_ICD.items()}
    n = 0
    for chunk in pd.read_csv(DIAG_FILE, chunksize=40000):
        ids = chunk['Participant ID'].astype(str).values
        arr = chunk.iloc[:, 1:].values.astype(str)   # object array
        n += len(ids)
        # '$' 位置 = ICD 码部分长度 (单元格格式 'ICD$date')
        icd_len = np.char.find(arr, '$')
        hit = {o: np.zeros(arr.shape, dtype=bool) for o in codes}
        for o, cs in codes.items():
            for code in cs:
                m = np.char.startswith(arr, code)
                # ICD 部分: =code 或其后 1-2 位数字子码 (如 J96 / J969 / J9690)
                m &= (icd_len >= len(code)) & (icd_len <= len(code) + 2)
                rows, cols = np.where(m)
                for r, c in zip(rows, cols):
                    cell = arr[r, c]
                    icd = cell[:cell.find('$')]
                    tail = icd[len(code):]
                    # 子码必须全为数字 (排除 'K70X' 类假阳性)
                    if tail and not tail.isdigit():
                        continue
                    hit[o][r, c] = True
        hit['organ'] = (hit['heart'] | hit['lung'] | hit['liver'] | hit['renal']
                        | hit['hemat'] | hit['brain'])
        # 每人每器官最早日期
        for o, m in hit.items():
            rows, cols = np.where(m)
            for r, c in zip(rows, cols):
                d = arr[r, c].split('$')[1].strip()
                pid = ids[r]
                cur = organ_dates[o].get(pid)
                if cur is None or d < cur:
                    organ_dates[o][pid] = d
        if n % 200000 == 0:
            print(f'  已扫描 {n:,} 人')
    print(f'  完成: {n:,} 人, 各器官命中: ' +
          ', '.join(f'{o}={len(v):,}' for o, v in organ_dates.items()))
    if cache_file:
        import pickle
        with open(cache_file, 'wb') as f:
            pickle.dump(organ_dates, f)
        print(f'  缓存已保存: {cache_file}')
    return organ_dates


def main():
    # 1) 诊断日期 (带缓存)
    cache = os.path.join(OUT_DIR, 'organ_dates_cache.pkl')
    organ_dates = scan_diagnoses(cache_file=cache)
    # 2) 基线日期
    rec = pd.read_csv(RECRUIT_FILE,
                      usecols=['Participant ID',
                               'Date of attending assessment centre | Instance 0'])
    rec.columns = ['eid', 'baseline_date']
    rec['eid'] = rec['eid'].astype(str)
    rec['baseline_date'] = rec['baseline_date'].astype(str).str.strip()
    # 3) 死亡日期 (每人最早)
    death = pd.read_csv(DEATH_FILE)
    death['eid'] = death['Participant ID(participant - eid)'].astype(str)
    death = death.sort_values('Date of death').drop_duplicates('eid', keep='first')
    death_map = dict(zip(death['eid'], death['Date of death']))
    # 4) 失访日期 (修复: NaN 不应映射为 'nan' 字符串)
    lost = pd.read_csv(LOST_FILE,
                       usecols=['Participant ID', 'Date lost to follow-up'])
    lost.columns = ['eid', 'lost_date']
    lost['eid'] = lost['eid'].astype(str)
    lost = lost.dropna(subset=['lost_date'])
    lost_map = dict(zip(lost['eid'], lost['lost_date'].astype(str).str.strip()))

    # 5) 组装主表 (以基线人群为框)
    df = rec.copy()
    df['censor_date'] = CENSOR_DATE
    df['death_date'] = df['eid'].map(death_map)
    df['lost_date'] = df['eid'].map(lost_map)
    for o in list(ORGAN_ICD) + ['organ']:
        df[f'{o}_date'] = df['eid'].map(organ_dates[o])

    def days(a, b):
        """b - a 的天数 (a 缺失 -> nan)"""
        a = pd.to_datetime(a, errors='coerce')
        b = pd.to_datetime(b, errors='coerce')
        return (b - a).dt.days

    bl = pd.to_datetime(df['baseline_date'], errors='coerce')
    cn = pd.to_datetime(df['censor_date'], errors='coerce')
    dt_ = pd.to_datetime(df['death_date'], errors='coerce')
    lt = pd.to_datetime(df['lost_date'], errors='coerce')
    # 实际随访终点 = min(死亡, 失访, 管理性截止) —— 但"死亡"作为竞争/删失事件单独标记
    df['follow_end'] = pd.concat(
        [cn.rename('x'), lt.rename('x'), dt_.rename('x')], axis=1).min(axis=1)
    df['follow_time'] = (df['follow_end'] - bl).dt.days / 365.25

    for o in list(ORGAN_ICD) + ['organ']:
        od = pd.to_datetime(df[f'{o}_date'], errors='coerce')
        # 事件: 有诊断日期 且 在基线之后 且 不晚于随访终点
        df[f'{o}_event'] = ((od.notna()) & (od >= bl) & (od <= df['follow_end'])).astype(int)
        df[f'{o}_time'] = np.where(df[f'{o}_event'] == 1,
                                   (od - bl).dt.days / 365.25, df['follow_time'])
    # 死亡事件 (随访窗口内死亡, 与器官诊断无关的全因死亡)
    df['death_event'] = ((dt_.notna()) & (dt_ <= df['follow_end'])).astype(int)
    df['death_time'] = np.where(df['death_event'] == 1,
                                (dt_ - bl).dt.days / 365.25, df['follow_time'])
    # prevalent 标记 (基线前已有诊断 -> 现有分析排除)
    for o in list(ORGAN_ICD) + ['organ']:
        od = pd.to_datetime(df[f'{o}_date'], errors='coerce')
        df[f'{o}_prevalent'] = ((od.notna()) & (od < bl)).astype(int)

    df.to_csv(os.path.join(OUT_DIR, 'survival_matrix.csv'), index=False)
    print(f'\n✅ 生存矩阵已保存: {os.path.join(OUT_DIR, "survival_matrix.csv")} '
          f'({len(df):,} 人)')

    # ---------- 验证报告 ----------
    lines = [f'# 生存数据验证报告 (CENSOR={CENSOR_DATE})', '',
             f'基线人群: {len(df):,}', f'随访时间(年): 均值 {df["follow_time"].mean():.2f} '
             f'中位 {df["follow_time"].median():.2f} 范围 '
             f'{df["follow_time"].min():.2f}-{df["follow_time"].max():.2f}',
             f'死亡: {df["death_event"].sum():,} ({df["death_event"].mean():.2%})',
             f'失访: {df["lost_date"].notna().sum():,}']
    for o in list(ORGAN_ICD) + ['organ']:
        ev = df[f'{o}_event'].sum()
        prev = df[f'{o}_prevalent'].sum()
        t = df.loc[df[f'{o}_event'] == 1, f'{o}_time']
        lines.append(f'\n[{o}] 事件={ev:,} ({ev/len(df):.2%}) | prevalent 排除={prev:,} '
                     f'| 事件时间(年): 中位 {t.median():.2f} IQR '
                     f'{t.quantile(.25):.2f}-{t.quantile(.75):.2f}')
    # 与现有标签对比 (从 ZS 诊断矩阵)
    mat_file = os.path.join(config.XM_DIR, 'ZS', '8.7', 'data',
                            'all_icd_f_group_1000_25y_instance0.csv')
    if os.path.exists(mat_file):
        lines.append('\n===== 与现有 incident 标签一致性 =====')
        keep = ['heart_failure', 'lung_failure', 'liver_failure',
                'renal_failure', 'hemat_failure', 'brain_failure',
                'organ_failure']
        idx_cols = {o: ('heart' if o == 'heart_failure' else o[:-8]
                        if o != 'organ_failure' else 'organ') for o in keep}
        # 现有矩阵列名是 ICD 分组; 标签重建在 prep 阶段完成, 这里用 prep 标签文件对比
        prep_dir = os.path.join(config.RESULT_DIR, '01_prep')
        for lab in keep:
            # 找带该标签列的文件
            for fn in os.listdir(prep_dir):
                if fn.endswith('_prep.csv') and 'blood' in fn:
                    p = os.path.join(prep_dir, fn)
                    pp = pd.read_csv(p, usecols=['Participant ID', lab])
                    break
            else:
                continue
            short = idx_cols[lab]
            merged = df[['eid', f'{short}_event']].merge(
                pp.astype({'Participant ID': str}), left_on='eid',
                right_on='Participant ID', how='inner')
            agree = (merged[f'{short}_event'] == merged[lab]).mean()
            lines.append(f'{lab}: prep标签n={len(merged):,} | 日期重建vs标签一致率 '
                         f'{agree:.3%}')
    report = '\n'.join(lines)
    with open(os.path.join(OUT_DIR, 'validation_report.txt'), 'w') as f:
        f.write(report)
    print(report)


if __name__ == '__main__':
    main()
