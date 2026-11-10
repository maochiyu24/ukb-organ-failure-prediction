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
09_build_exposure_v2.py - UKB 暴露矩阵 v2 (不覆盖 v1)
======================================================
lifestyle_score_v2 (0-5): 对齐 Li et al. BMJ 2018 五因子
  吸烟(健康=Never/Previous) + 饮酒(健康=Never/特殊/从不) + BMI(18.5-25)
  + 运动(UKB 官方 'moderate/vigorous recommendation' 达标) + 饮食(见下)
lifestyle_score_v2_6 (0-6): + 睡眠(7-8h) [敏感性扩展]
psych_score_v2 (0-4): K6 式情绪困扰(抑郁/兴趣减退/神经质) + 焦虑(Worrier)
  + 社会隔离 + 近2年压力事件   [v1 三维 + 新增焦虑维]

饮食达标规则 (9Diet touchscreen, Instance 0; UKB 频率编码):
  5 条中 >=3 条达标:
   a. 蔬菜(熟/沙拉, 取高) >= 4 (>=5-6 次/周)
   b. 鲜果 >= 4
   c. 油鱼 >= 3 (>=2-4 次/周; NHS 每周 2 份鱼)
   d. 加工肉 <= 2 (<=1 次/周)
   e. 红肉(牛/羊/猪, 取高) <= 3 (<=2-4 次/周)
  ⚠ 数据中频率编码最大值=4 (未见 5=once or more daily),
    阈值参数化于 DIET_MIN, 可调重跑。

数据源: 1Baseline(Age/Sex) | Lifestyle_Instance0(吸烟/饮酒/BMI/睡眠) |
        4Physical_activity(达标) | 9Diet(饮食) |
        of825 psych_prep(抑郁/神经质/隔离/压力, 同 v1) | ZS Psychosocial(Worrier)
输出: result/of903/06_mediation_v2/data/ukb_full_exposure_matrix_v2.csv
"""
import os
import sys
import numpy as np
import pandas as pd

BASE = _PROJECT + ''
UKB = os.path.join(BASE, 'xm', 'UKB', 'Assessment_centre')
ZS = os.path.join(BASE, 'xm', 'ZS', '8.7', 'data')
OUT = os.path.join(BASE, 'result', 'of903', '06_mediation_v2', 'data')
os.makedirs(OUT, exist_ok=True)

DIET_MIN = 4      # 蔬菜/水果达标阈值 (>=5-6 次/周)
N_DIET_RULES = 3  # 5 条饮食规则中需达标的条数


def load_diet():
    d = pd.read_csv(os.path.join(UKB, '9Diet_participant.csv'), low_memory=False)
    keep = {'Participant ID'}
    for c in d.columns:
        if c.endswith('| Instance 0'):
            keep.add(c)
    d = d[list(keep)]
    d.columns = [c.replace(' | Instance 0', '') for c in d.columns]
    for c in d.columns:
        if c != 'Participant ID':
            d[c] = pd.to_numeric(d[c], errors='coerce')
            d.loc[d[c].isin([-1, -3, -10]), c] = np.nan
    return d


def main():
    # 1) 人口学
    bl = pd.read_csv(os.path.join(UKB, '1Baseline_characteristics_participant.csv'),
                     usecols=['Participant ID', 'Age at recruitment', 'Sex'])
    bl.columns = ['Participant ID', 'Age', 'Sex']
    # 2) 生活方式基础 (同 v1)
    li = pd.read_csv(os.path.join(ZS, 'Lifestyle_Instance0.csv'), low_memory=False)
    li = li[['Participant ID', 'Smoking status', 'Alcohol intake frequency.',
             'Sleep duration', 'Body mass index (BMI)',
             'Townsend deprivation index at recruitment']].copy()
    for c in li.columns[1:]:
        li[c] = pd.to_numeric(li[c], errors='coerce')
        li.loc[li[c].isin([-1, -3]), c] = np.nan
    # 3) 运动达标 (UKB 官方字段)
    pa = pd.read_csv(os.path.join(UKB, '4Physical_activity.csv'),
                     usecols=['Participant ID',
                              'At or above moderate/vigorous recommendation | Instance 0'])
    pa.columns = ['Participant ID', 'activity_ok']
    pa['activity_ok'] = pd.to_numeric(pa['activity_ok'], errors='coerce')
    # 4) 饮食
    diet = load_diet()
    # 5) 心理 (of825 psych_prep 编码版 + ZS Worrier)
    ps = pd.read_csv(os.path.join(BASE, 'result', 'of903', '01_prep',
                                  'psych_prep.csv'), low_memory=False)
    pcols = ['Participant ID', 'Neuroticism_score',
             'Frequency_of_depressed_mood_in_last_2_weeks',
             'Frequency_of_unenthusiasm___disinterest_in_last_2_weeks',
             'Loneliness__isolation', 'Frequency_of_friend_family_visits',
             'Able_to_confide'] + \
            [c for c in ps.columns if c.startswith('Illness__')]
    ps = ps[[c for c in pcols if c in ps.columns]].copy()
    wz = pd.read_csv(os.path.join(ZS, 'Psychosocial_factors_Instance0.csv'),
                     usecols=['Participant ID', 'Worrier / anxious feelings'])
    wz.columns = ['Participant ID', 'worrier']

    df = (bl.merge(li, on='Participant ID', how='left')
            .merge(pa, on='Participant ID', how='left')
            .merge(diet, on='Participant ID', how='left')
            .merge(ps, on='Participant ID', how='left')
            .merge(wz, on='Participant ID', how='left'))
    print(f'合并后: {len(df):,} 人')

    # ---------- lifestyle v2 成分 ----------
    df['smk_healthy'] = df['Smoking status'].isin([0, 1]).astype(float)
    df['alc_healthy'] = df['Alcohol intake frequency.'].isin([-1, 5, 6]).astype(float)
    df['bmi_healthy'] = df['Body mass index (BMI)'].between(18.5, 25,
                                                            inclusive='both').astype(float)
    df['slp_healthy'] = df['Sleep duration'].between(7, 8,
                                                     inclusive='both').astype(float)
    df['act_healthy'] = (df['activity_ok'] == 1).astype(float)
    # 饮食 5 规则
    veg = df[['Cooked vegetable intake', 'Salad / raw vegetable intake']].max(axis=1)
    fruit = df['Fresh fruit intake']
    oily = df['Oily fish intake']
    pmeat = df['Processed meat intake']
    rmeat = df[['Beef intake', 'Lamb/mutton intake', 'Pork intake']].max(axis=1)
    rules = pd.DataFrame({
        'r_veg': veg >= DIET_MIN, 'r_fruit': fruit >= DIET_MIN,
        'r_oily': oily >= 3, 'r_pmeat': pmeat <= 2, 'r_rmeat': rmeat <= 3})
    df['diet_healthy'] = (rules.sum(axis=1) >= N_DIET_RULES).astype(float)
    print('饮食规则达标率:', (rules.mean() * 100).round(1).to_dict())
    print(f'diet_healthy 率: {df["diet_healthy"].mean():.2%}')

    comp5 = ['smk_healthy', 'alc_healthy', 'bmi_healthy', 'act_healthy', 'diet_healthy']
    df['lifestyle_score_v2'] = df[comp5].sum(axis=1)
    df.loc[df[comp5].notna().sum(axis=1) < 4, 'lifestyle_score_v2'] = np.nan
    comp6 = comp5 + ['slp_healthy']
    df['lifestyle_score_v2_6'] = df[comp6].sum(axis=1)
    df.loc[df[comp6].notna().sum(axis=1) < 4, 'lifestyle_score_v2_6'] = np.nan

    # ---------- psych v2 (0-4) ----------
    neuro_med = df['Neuroticism_score'].median()
    df['emo_distress'] = ((df['Neuroticism_score'] > neuro_med) |
                          (df['Frequency_of_depressed_mood_in_last_2_weeks'] >= 3) |
                          (df['Frequency_of_unenthusiasm___disinterest_in_last_2_weeks'] >= 3)
                          ).astype(float)
    df['anxiety'] = (df['worrier'] == 1).astype(float)
    df['soc_isol'] = ((df['Loneliness__isolation'] == 1) |
                      (df['Frequency_of_friend_family_visits'] >= 5) |
                      (df['Able_to_confide'] == 1)).astype(float)
    stress_cols = [c for c in ps.columns
                   if c.startswith('Illness__injury__bereavement') and '__7' not in c]
    df['stress_ev'] = df[stress_cols].fillna(0).eq(1).any(axis=1).astype(float)
    compP = ['emo_distress', 'anxiety', 'soc_isol', 'stress_ev']
    df['psych_score_v2'] = df[compP].sum(axis=1)
    df.loc[df[compP].notna().sum(axis=1) < 3, 'psych_score_v2'] = np.nan

    # ---------- 输出 ----------
    keep = (['Participant ID', 'Age', 'Sex',
             'Townsend deprivation index at recruitment',
             'lifestyle_score_v2', 'lifestyle_score_v2_6', 'psych_score_v2'] +
            comp5 + ['slp_healthy'] + compP + ['Neuroticism_score'])
    out = df[[c for c in keep if c in df.columns]]
    out.to_csv(os.path.join(OUT, 'ukb_full_exposure_matrix_v2.csv'), index=False)
    print(f'\nlifestyle_score_v2 分布: '
          f'{out["lifestyle_score_v2"].value_counts(dropna=False).sort_index().to_dict()}')
    print(f'lifestyle_score_v2_6 分布: '
          f'{out["lifestyle_score_v2_6"].value_counts(dropna=False).sort_index().to_dict()}')
    print(f'psych_score_v2 分布: '
          f'{out["psych_score_v2"].value_counts(dropna=False).sort_index().to_dict()}')
    print(f'✅ 输出: {os.path.join(OUT, "ukb_full_exposure_matrix_v2.csv")} '
          f'({len(out):,} 人, {out.shape[1]} 列)')


if __name__ == '__main__':
    main()
