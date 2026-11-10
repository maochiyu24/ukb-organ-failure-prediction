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
08_mediation_evalue.py - PM 稳定性筛选 + E-value (of825 中介补强)
=================================================================
① PM 稳定性筛选 (核心稳定集):
   显著 (ACME_p<0.05) 且 PM 95%CI 同号 (不跨0) 且 CI 宽度 <1.0
② E-value (VanderWeele & Ding 2017, 对 1SD 暴露的中介效应):
   ACME_1SD = ACME_per_unit x SD_exposure
   RR ≈ 1 + ACME_1SD / prev      (prev = 分析样本事件率)
   E-value = RR + sqrt(RR(RR-1))  (RR>1);  RR<1 时取 1/RR
   同时报告对 95%CI 靠 0 端的 E-value_CI (最保守)
输出: result/of903/06_mediation_v2/
  - core_stable_mediators.csv       PM 稳定显著中介 (主文 Table 3 依据)
  - unstable_mediators_list.csv     不稳定的显著中介 (移 supplement)
  - evalue_summary.csv              E-value 汇总
"""
import os
import sys
import numpy as np
import pandas as pd

BASE = _PROJECT + ''
RES = os.path.join(BASE, 'result', 'of903', '06_mediation_v2')
DATA = os.path.join(RES, 'data')
ALL = pd.read_csv(os.path.join(RES, 'mediation_results_all_all_all.csv'))

OUT_LABEL = {o: (o + '_failure' if o != 'organ' else 'organ_failure')
             for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']}

# ---------- ① PM 稳定性筛选 ----------
sig = ALL[ALL['ACME_p'] < 0.05].copy()
same_sign = (sig['PM_lo'] * sig['PM_hi']) > 0
width = (sig['PM_hi'] - sig['PM_lo']).abs()
stable = same_sign & (width < 1.0)
sig['PM_stable'] = stable
core = sig[stable].copy()
unstable = sig[~stable].copy()
core.to_csv(os.path.join(RES, 'core_stable_mediators.csv'), index=False)
unstable.to_csv(os.path.join(RES, 'unstable_mediators_list.csv'), index=False)
print(f'显著 {len(sig)} | PM 稳定核心集 {len(core)} | 不稳定 {len(unstable)}')
print('不稳定明细 (organ/mediator/PM/CI):')
for _, r in unstable.iterrows():
    med = r['Mediator'].split('__')[1] if '__' in r['Mediator'] else r['Mediator']
    print(f"  {r['Organ']:6s} {med:30s} PM={r['Prop_mediated']:.3f} "
          f"({r['PM_lo']:.2f}-{r['PM_hi']:.2f}) exp={r['Exposure']}")

# ---------- ② E-value ----------
def evalue_from_rr(rr):
    """VanderWeele & Ding (2017): RR>=1 时 E=RR+sqrt(RR(RR-1));
    保护性 (RR<1) 用倒数转换"""
    rr = abs(rr)
    if rr < 1:
        rr = 1 / rr
    if rr <= 1 or not np.isfinite(rr):
        return np.nan
    return rr + np.sqrt(rr * (rr - 1))

rows = []
for _, r in core.iterrows():
    organ = r['Organ']
    lab = OUT_LABEL[organ]
    df = pd.read_csv(os.path.join(DATA, f'{organ}_mediation_v2.csv'),
                     usecols=[r['Exposure'], lab])
    sd = df[r['Exposure']].std()
    prev = df[lab].mean()
    acme1 = r['ACME'] * sd                       # 1SD 暴露的中介效应 (概率)
    acme2 = r['ACME'] * 2                        # 增加 2 单位 (约 2 种健康行为)
    rr = 1 + acme1 / prev if prev > 0 else np.nan
    rr2 = 1 + acme2 / prev if prev > 0 else np.nan
    # CI 靠 0 端
    lo1, hi1 = r['ACME_lo'] * sd, r['ACME_hi'] * sd
    near0 = hi1 if r['ACME'] < 0 else lo1        # 保护性取上端; 风险性取下端
    rr_ci = 1 + near0 / prev if prev > 0 else np.nan
    rows.append({
        'Organ': organ, 'Exposure': r['Exposure'],
        'Mediator': r['Mediator'], 'ACME_1SD': acme1,
        'RR_approx': rr, 'E_value_1SD': evalue_from_rr(rr),
        'E_value_CI_near0': evalue_from_rr(rr_ci),
        'E_value_2unit': evalue_from_rr(rr2),
        'Prop_mediated': r['Prop_mediated'], 'ACME_p': r['ACME_p'],
        'PM_lo': r['PM_lo'], 'PM_hi': r['PM_hi'],
    })
ev = pd.DataFrame(rows)
ev.to_csv(os.path.join(RES, 'evalue_summary.csv'), index=False)
print(f'\nE-value 汇总: {len(ev)} 条 -> {RES}/evalue_summary.csv')
pd.set_option('display.width', 200)
g = ev[ev['Mediator'].str.contains('GDF15')]
print('\nGDF15 路径 E-value (1SD 暴露):')
print(g[['Organ', 'Exposure', 'ACME_1SD', 'RR_approx', 'E_value_1SD',
         'E_value_CI_near0', 'E_value_2unit']].round(3).to_string(index=False))
print(f"\nE-value 分布 (1SD): 中位 {ev['E_value_1SD'].median():.2f} | "
      f">=1.5: {(ev['E_value_1SD']>=1.5).sum()} 条")
print(f"E-value 分布 (2unit): 中位 {ev['E_value_2unit'].median():.2f} | "
      f">=1.5: {(ev['E_value_2unit']>=1.5).sum()} 条 | "
      f">=2.0: {(ev['E_value_2unit']>=2).sum()} 条")
