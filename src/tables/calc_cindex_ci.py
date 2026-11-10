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
"""外部测试 C-index + 1000x bootstrap 95%CI (沿用官方方法, 不改动):
  - 单模态: 05_survival/sksurv_load.load_organ_data + 03_model pkl
            (与 05_survival survival_metrics_all.csv 同一装载/模型/公式)
  - merge  : 官方 04_fusion 模型 + 05_survival 生存队列 (同 02b_merge_survival_metrics.py)
  - CI     : 同 code/of903/03_model/train_model.py bootstrap_ci 约定:
            每模型 np.random.default_rng(42), 1000 次重抽, 2.5/97.5 百分位,
            退化样本(事件类<2)跳过; lifelines.utils.concordance_index(time, -p, event)
  范围: 官方 survival_metrics_all.csv 中 modality != 'brain' 的 56 组合
        (7 模态 x 7 器官靶 + 7 merge); brain 影像模态因随访时间基准不一致不展示
  用法: OF_SLICE_K=0..N-1 OF_SLICE_N=N python calc_cindex_ci2.py  每片独立写盘
"""
import os, sys, glob
import numpy as np, pandas as pd, joblib
os.environ.setdefault('OF_RESULT_DIR', _PROJECT + '/result/of903')
os.environ.setdefault('OF_INCIDENT_ONLY', '1')
from sksurv_load import load_organ_data, load_survival
from merge_fusion import get_intersection, build_merge_matrix
from lifelines.utils import concordance_index

R = _PROJECT + '/result/of903'
CACHE = os.path.join(_PROJECT, 'cache')
K = int(os.environ.get('OF_SLICE_K', '0'))
N = int(os.environ.get('OF_SLICE_N', '1'))
NBOOT = 1000


def bootstrap_ci(tm, ev, p):
    """官方 bootstrap_ci 约定 (seed 42/模型, 1000x, 2.5-97.5 百分位)"""
    rng = np.random.default_rng(42)
    idx = np.arange(len(ev))
    ci0 = concordance_index(tm, -p, ev)          # 全量 C-index (官方公式)
    boot = []
    for _ in range(NBOOT):
        b = rng.choice(idx, len(idx), replace=True)
        if len(np.unique(ev[b])) < 2:
            continue
        boot.append(concordance_index(tm[b], -p[b], ev[b]))
    if not boot:
        return ci0, np.nan, np.nan
    return ci0, float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))


def single_combos():
    """官方 survival_metrics_all.csv 中非 brain 影像的全部组合 (56)"""
    m = pd.read_csv(f'{R}/05_survival/survival_metrics_all.csv')
    m = m[m['modality'] != 'brain']               # brain 时间基准不一致, 不展示
    return [(o, mo) for o, mo in zip(m.organ, m.modality)]


def eval_single(organ, modality):
    feats, X, y, tr = load_organ_data(organ, modality)
    Xte, yte = X[~tr], y[~tr]
    model = joblib.load(f'{R}/03_model/{organ}_{modality}/{organ}_LightGBM_model.pkl')
    p = model.predict_proba(Xte)[:, 1]
    ev, tm = yte['event'].astype(bool), yte['time'].astype(float)
    ci, lo, hi = bootstrap_ci(tm, ev, p)
    return dict(organ=organ, modality=modality, n=len(ev), n_event=int(ev.sum()),
                Cindex=ci, C_lo=lo, C_hi=hi)


def eval_merge(organ):
    """同 02b_merge_survival_metrics.py: merge 模型施加于生存队列 (交集人群)"""
    surv = load_survival()
    inter = get_intersection()
    base, feat_origin = build_merge_matrix(organ, inter)
    base['Participant ID'] = base['Participant ID'].astype(str)
    m = base.merge(surv[['eid', f'{organ}_time', f'{organ}_event',
                         f'{organ}_prevalent']], left_on='Participant ID',
                   right_on='eid', how='inner')
    m = m[m[f'{organ}_prevalent'] == 0]
    m = m[m[f'{organ}_event'].notna()]
    feats = list(feat_origin.keys())
    region = m['Region'].values
    te = ~np.isin(region, [1])                     # Region 2/3 = 外部测试
    Xte = m.loc[te, feats]
    model = joblib.load(f'{R}/04_fusion/{organ}_merge/{organ}_merge_model.pkl')
    p = model.predict_proba(Xte)[:, 1]
    ev = m.loc[te, f'{organ}_event'].astype(bool).values
    tm = m.loc[te, f'{organ}_time'].astype(float).values
    ci, lo, hi = bootstrap_ci(tm, ev, p)
    return dict(organ=organ, modality='merge', n=len(ev), n_event=int(ev.sum()),
                Cindex=ci, C_lo=lo, C_hi=hi)


def main():
    combos = single_combos()                       # 含 7 个 modality=='merge' 行
    jobs = [(o, mo) for o, mo in combos]
    mine = [j for i, j in enumerate(jobs) if i % N == K]
    print(f'slice {K}/{N}: {len(mine)} models of {len(jobs)}', flush=True)
    rows = []
    for o, mo in mine:
        try:
            r = eval_merge(o) if mo == 'merge' else eval_single(o, mo)
            # 与官方 survival_metrics_all 的 C-index 核对
            off = pd.read_csv(f'{R}/05_survival/survival_metrics_all.csv')
            v = off[(off.organ == o) & (off.modality == mo)]['Cindex_lgbm_te']
            if len(v):
                d = abs(r['Cindex'] - float(v.iloc[0]))
                if d > 1e-8:
                    print(f'  !! {o}/{mo}: computed {r["Cindex"]:.6f} vs official {float(v.iloc[0]):.6f}', flush=True)
            rows.append(r)
            print(f'  {o}/{mo} n={r["n"]} ev={r["n_event"]} C={r["Cindex"]:.4f} '
                  f'({r["C_lo"]:.4f}-{r["C_hi"]:.4f})', flush=True)
        except Exception as e:
            print(f'  ERR {o}/{mo}: {e}', flush=True)
    out = f'{CACHE}/cindex_slice_{K}.csv'
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f'saved {out} ({len(rows)})', flush=True)


if __name__ == '__main__':
    main()
