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
UKB 全人群暴露-协变量矩阵构建（502k，从完整数据开始）
======================================================
暴露:
  lifestyle_score (0-4): 吸烟/饮酒/睡眠/BMI（参考 Li et al. BMJ 2018 健康生活方式评分）
  psych_score (0-3): 情绪困扰 + 社会隔离 + 近期压力事件
    （参考 Kessler K6 结构 + UKB 社会隔离评分 + polysocial risk score）
协变量: Age, Sex, Townsend

数据源（全人群 502,131）:
  Age/Sex: UKB/Assessment_centre/1Baseline_characteristics_participant.csv
  Townsend/生活方式: ZS/8.7/data/Lifestyle_Instance0.csv
  心理: ZS/8.7/data/Psychosocial_factors_Instance0.csv

输出: result/of825/06_mediation/data/ukb_full_exposure_matrix.csv
"""
import os
import numpy as np
import pandas as pd

BASE = _PROJECT + ''
OUT = os.path.join(BASE, 'result', 'of825', '06_mediation', 'data')
os.makedirs(OUT, exist_ok=True)
UKB_RAW = os.path.join(BASE, 'xm', 'UKB', 'Assessment_centre')
ZS_DATA = os.path.join(BASE, 'xm', 'ZS', '8.7', 'data')


def main():
    # ---------- 1. Age/Sex（全人群）----------
    bl = pd.read_csv(os.path.join(UKB_RAW, '1Baseline_characteristics_participant.csv'),
                     usecols=['Participant ID', 'Sex', 'Age at recruitment'])
    bl = bl.rename(columns={'Sex': 'Sex', 'Age at recruitment': 'Age'})
    print(f'Baseline: {len(bl)} 行')

    # ---------- 2. 生活方式（全人群）----------
    li = pd.read_csv(os.path.join(ZS_DATA, 'Lifestyle_Instance0.csv'), low_memory=False)
    use = ['Participant ID', 'Townsend deprivation index at recruitment',
           'Smoking status', 'Alcohol intake frequency.', 'Sleep duration',
           'Body mass index (BMI)']
    use = [c for c in use if c in li.columns]
    li = li[use]
    print(f'Lifestyle: {len(li)} 行, 字段: {use}')

    # ---------- 3. 心理（全人群，用户编码版 psych_prep）----------
    ps = pd.read_csv(os.path.join(BASE, 'result', 'of825', '01_prep', 'psych_prep.csv'), low_memory=False)
    pcols = ['Participant ID', 'Neuroticism_score',
             'Frequency_of_depressed_mood_in_last_2_weeks',
             'Frequency_of_unenthusiasm___disinterest_in_last_2_weeks',
             'Loneliness__isolation', 'Frequency_of_friend_family_visits',
             'Able_to_confide']
    stress_cols = [c for c in ps.columns if c.startswith('Illness__injury__bereavement__stress')]
    pcols = [c for c in pcols if c in ps.columns]
    ps = ps[pcols + stress_cols]
    print(f'Psych(编码版): {len(ps)} 行, stress 展开列 {len(stress_cols)} 个')

    # ---------- 4. 合并 ----------
    df = bl.merge(li, on='Participant ID', how='left').merge(ps, on='Participant ID', how='left')
    print(f'合并后: {len(df)} 行')

    # ---------- 4.5 统一转数值 ----------
    num_cols = ['Townsend deprivation index at recruitment', 'Smoking status',
                'Alcohol intake frequency.', 'Sleep duration', 'Body mass index (BMI)',
                'Neuroticism_score', 'Frequency_of_depressed_mood_in_last_2_weeks',
                'Frequency_of_unenthusiasm___disinterest_in_last_2_weeks',
                'Loneliness__isolation', 'Frequency_of_friend_family_visits',
                'Able_to_confide'] + [c for c in df.columns if c.startswith('Illness__')]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    # UKB 缺失编码 -> NaN
    for c in num_cols:
        if c in df.columns:
            df.loc[df[c].isin([-3, -1]), c] = np.nan

    # ---------- 5. Lifestyle 评分（0-4）----------
    # 吸烟: 0=Never, 1=Previous, 2=Current -> 健康=0/1
    df['smk_healthy'] = df['Smoking status'].isin([0, 1]).astype(float)
    # 饮酒: UKB 编码: -1=Never, 1=Daily, 2=3-4/week, 3=1-2/week, 4=1-3/month, 5=special, 6=never -> 健康 = Never/特殊场合（-1, 5, 6）
    df['alc_healthy'] = df['Alcohol intake frequency.'].isin([-1, 5, 6]).astype(float)
    # 睡眠: 7-8 小时
    df['slp_healthy'] = df['Sleep duration'].between(7, 8, inclusive='both').astype(float)
    # BMI: 18.5-25
    df['bmi_healthy'] = df['Body mass index (BMI)'].between(18.5, 25, inclusive='both').astype(float)
    df['lifestyle_score'] = (df['smk_healthy'] + df['alc_healthy'] +
                             df['slp_healthy'] + df['bmi_healthy'])
    # 缺值处理: 任一因素缺失则该因素不算分（保留有至少 2 项的人）
    n_avail = df[['smk_healthy', 'alc_healthy', 'slp_healthy', 'bmi_healthy']].notna().sum(axis=1)
    df.loc[n_avail < 2, 'lifestyle_score'] = np.nan
    print(f'Lifestyle 评分分布: {df["lifestyle_score"].value_counts(dropna=False).sort_index().to_dict()}')

    # ---------- 6. Psych 评分（0-3）----------
    # 情绪困扰: 神经质 > 全人群中位数 或 频繁抑郁情绪/兴趣减退(UKB 1-2=几乎每天/一半以上天数)
    neuro_med = df['Neuroticism_score'].median()
    df['emo_distress'] = ((df['Neuroticism_score'] > neuro_med) |
                          (df['Frequency_of_depressed_mood_in_last_2_weeks'] >= 3) |
                          (df['Frequency_of_unenthusiasm___disinterest_in_last_2_weeks'] >= 3)).astype(float)
    # 社会隔离: 孤独=1(Yes) 或 探访<=1次/月(UKB 5=每月, 6=从不) 或 无法倾诉(Able=1)
    df['soc_isol'] = ((df['Loneliness__isolation'] == 1) |
                      (df['Frequency_of_friend_family_visits'] >= 5) |
                      (df['Able_to_confide'] == 1)).astype(float)
    # 压力事件: 近2年展开列任一==1（排除 __7 = None of the above 选项）
    stress_cols = [c for c in df.columns
                   if c.startswith('Illness__injury__bereavement') and '__7' not in c]
    df['stress_ev'] = df[stress_cols].fillna(0).eq(1).any(axis=1).astype(float)
    df['psych_score'] = df['emo_distress'] + df['soc_isol'] + df['stress_ev']
    n_avail_p = df[['emo_distress', 'soc_isol', 'stress_ev']].notna().sum(axis=1)
    df.loc[n_avail_p < 2, 'psych_score'] = np.nan
    print(f'Psych 评分分布: {df["psych_score"].value_counts(dropna=False).sort_index().to_dict()}')

    # ---------- 7. 保存 ----------
    keep = ['Participant ID', 'Age', 'Sex', 'Townsend deprivation index at recruitment',
            'lifestyle_score', 'psych_score',
            'smk_healthy', 'alc_healthy', 'slp_healthy', 'bmi_healthy',
            'emo_distress', 'soc_isol', 'stress_ev',
            'Smoking status', 'Alcohol intake frequency.', 'Sleep duration',
            'Body mass index (BMI)', 'Neuroticism_score']
    out = df[keep]
    out.to_csv(os.path.join(OUT, 'ukb_full_exposure_matrix.csv'), index=False)
    print(f'\n✅ 全人群暴露矩阵: {len(out)} 行 → {os.path.join(OUT, "ukb_full_exposure_matrix.csv")}')


if __name__ == '__main__':
    main()
