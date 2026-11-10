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
03_km_plots.py - KM 风险分层图 (90%Sn / 90%Sp 阈值)
====================================================
规则 (用户确认): 阈值在 England 训练集确定:
  - t90sn: 90% 事件者的风险分数 >= t90sn
  - t90sp: 90% 非事件者的风险分数 <  t90sp
  三组: low (p < t90sn) | mid (t90sn <= p < t90sp) | high (p >= t90sp)
输出: result/of825/05_survival/figs/{organ}_{modality}_KM_{tr|te}.pdf/png
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
from lifelines import KaplanMeierFitter, statistics
from lifelines.utils import concordance_index
os.environ.setdefault('MPLCONFIGDIR', os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '.cache', 'mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from sksurv_load import load_organ_data   # 复用 02 的数据载入

FONT_DIR = os.path.join(config.BASE_DIR, '.cache', 'fonts')
for _f in ['LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf']:
    font_manager.fontManager.addfont(os.path.join(FONT_DIR, _f))
plt.rcParams['font.family'] = 'Liberation Sans'

RESULT = os.path.join(config.RESULT_DIR, '05_survival')
FIG_DIR = os.path.join(RESULT, 'figs')
os.makedirs(FIG_DIR, exist_ok=True)

ORG_CN = {'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver',
          'renal': 'Renal', 'hemat': 'Hematologic', 'organ': 'Any-organ'}


def km_panel(ax, T, E, G, title, colors=('#C00000', '#4472C4', '#70AD47')):
    kmf = KaplanMeierFitter()
    labels = ['Low risk', 'Mid risk', 'High risk']
    for g in [0, 1, 2]:
        mask = G == g
        if mask.sum() < 20:
            continue
        kmf.fit(T[mask], E[mask], label=f'{labels[g]} (n={mask.sum():,})')
        kmf.plot_survival_function(ax=ax, color=colors[g], lw=2,
                                   ci_show=False, label=labels[g])
    # 组间 log-rank (低 vs 高风险)
    if (G == 0).sum() > 20 and (G == 2).sum() > 20:
        try:
            res = statistics.logrank_test(T[G == 0], T[G == 2],
                                          E[G == 0], E[G == 2])
            ax.set_title(f'{title}\nlog-rank p={res.p_value:.2e}', fontsize=10)
        except Exception:
            ax.set_title(title, fontsize=10)
    else:
        ax.set_title(title, fontsize=10)
    ax.set_xlabel('Years since baseline')
    ax.set_ylabel('Event-free probability')
    ax.set_ylim(0.70, 1.0)
    ax.set_yticks([0.7, 0.8, 0.9, 1.0])
    ax.grid(alpha=0.25, ls=':')
    ax.legend(frameon=False, fontsize=8, loc='lower left')


def plot_one(organ, modality):
    feats, X, y, tr_mask = load_organ_data(organ, modality)
    met = pd.read_csv(os.path.join(RESULT, 'metrics',
                                   f'{organ}_{modality}_survival_metrics.csv'))
    t_sn, t_sp = met['t90sn'].iloc[0], met['t90sp'].iloc[0]
    pk = os.path.join(config.RESULT_DIR, '03_model', f'{organ}_{modality}',
                      f'{organ}_LightGBM_model.pkl')
    p = joblib.load(pk).predict_proba(X)[:, 1]
    T, E = y['time'], y['event']
    G = np.where(p < t_sn, 0, np.where(p < t_sp, 1, 2))
    for tag, mask in [('tr', tr_mask), ('te', ~tr_mask)]:
        fig, ax = plt.subplots(figsize=(6.2, 4.6))
        where = 'Internal (England)' if tag == 'tr' else 'External (Scotland+Wales)'
        km_panel(ax, T[mask], E[mask], G[mask],
                 f'{ORG_CN[organ]} | {modality} | {where}')
        fig.tight_layout()
        fig.savefig(os.path.join(FIG_DIR, f'{organ}_{modality}_KM_{tag}.pdf'),
                    dpi=600)
        fig.savefig(os.path.join(FIG_DIR, f'{organ}_{modality}_KM_{tag}.png'),
                    dpi=300)
        plt.close(fig)
        ne = E[mask].sum()
        print(f'  [{organ}/{modality}/{tag}] low={np.sum(G[mask]==0):,} '
              f'mid={np.sum(G[mask]==1):,} high={np.sum(G[mask]==2):,} '
              f'事件={ne:,} C-index={concordance_index(T[mask], -p[mask], E[mask]):.3f}')


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', default=None)
    ap.add_argument('--modality', default=None)
    args = ap.parse_args()
    organs = [args.organ] if args.organ else \
        ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
    mods = [args.modality] if args.modality else \
        ['proteome', 'metabolome', 'prs', 'lifestyle', 'psych',
         'blood', 'brain', 'history']
    for o in organs:
        for m in mods:
            mp = os.path.join(RESULT, 'metrics', f'{o}_{m}_survival_metrics.csv')
            pk = os.path.join(config.RESULT_DIR, '03_model', f'{o}_{m}',
                              f'{o}_LightGBM_model.pkl')
            if os.path.exists(mp) and os.path.exists(pk):
                try:
                    plot_one(o, m)
                except Exception as e:
                    print(f'  ✗ {o}/{m}: {e}')
    print(f'✅ KM 图输出: {FIG_DIR}/')


if __name__ == '__main__':
    main()
