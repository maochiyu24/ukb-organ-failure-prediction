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
04_plots.py - 时序分析主文图 (of825)
=====================================
图1: time-dependent AUC 曲线 (外部 Scot+Wal, 网格 2-15y, 多模态对比)
图2: C-index 森林图 (内部 England vs 外部, 各模态)
图3: 校准曲线 (Cox 预测 5y/10y 风险 vs KM 观测, 十分位, proteome)
输出: result/of825/05_survival/figs/{organ}_tdAUC_te.pdf | Cindex_forest.pdf
      | {organ}_proteome_calibration_{5y|10y}.pdf
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
from lifelines import CoxPHFitter, KaplanMeierFitter
from sksurv.metrics import cumulative_dynamic_auc
os.environ.setdefault('MPLCONFIGDIR', os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '.cache', 'mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from sksurv_load import load_organ_data

FONT_DIR = os.path.join(config.BASE_DIR, '.cache', 'fonts')
for _f in ['LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf']:
    font_manager.fontManager.addfont(os.path.join(FONT_DIR, _f))
plt.rcParams['font.family'] = 'Liberation Sans'

RESULT = os.path.join(config.RESULT_DIR, '05_survival')
FIG = os.path.join(RESULT, 'figs')
os.makedirs(FIG, exist_ok=True)
ORG_CN = {'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver',
          'renal': 'Renal',
          'brain': 'Brain', 'hemat': 'Hematologic', 'organ': 'Any-organ'}
COLORS = {'proteome': '#C00000', 'metabolome': '#4472C4', 'blood': '#70AD47',
          'lifestyle': '#ED7D31', 'merge': '#7030A0'}
MODS = ['proteome', 'metabolome', 'blood', 'lifestyle', 'merge']
TIMES = list(range(2, 16))


def td_auc_grid(organ, modality):
    """LGBM 概率在外部集上的 tdAUC 网格 (2-15y)"""
    feats, X, y, tr_mask = load_organ_data(organ, modality)
    pk = os.path.join(config.RESULT_DIR, '03_model', f'{organ}_{modality}',
                      f'{organ}_LightGBM_model.pkl')
    if not os.path.exists(pk):
        return None, None
    p = joblib.load(pk).predict_proba(X)[:, 1]
    y_tr, p_tr, y_te, p_te = y[tr_mask], p[tr_mask], y[~tr_mask], p[~tr_mask]
    tmax = float(y_te['time'].max())
    ts = [t for t in TIMES if t < tmax]
    try:
        a_tr, _ = cumulative_dynamic_auc(y_tr, y_tr, p_tr, ts)
        a_te, _ = cumulative_dynamic_auc(y_te, y_te, p_te, ts)
        return ts, (a_tr, a_te)
    except Exception:
        return None, None


def fig_tdauc(organ):
    fig, ax = plt.subplots(figsize=(7, 4.6))
    for m in MODS:
        if m == 'merge':
            pk = os.path.join(config.RESULT_DIR, '04_fusion', f'{organ}_merge',
                              f'{organ}_merge_model.pkl')
            mp = os.path.join(RESULT, 'metrics', f'merge_{organ}_survival_metrics.csv')
            if not (os.path.exists(pk) and os.path.exists(mp)):
                continue
            # merge 数据载入 (02b 逻辑)
            sys.path.insert(0, os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '04_fusion'))
            from merge_fusion import get_intersection, build_merge_matrix
            from sksurv_load import load_survival
            base, feat_origin = build_merge_matrix(organ, get_intersection())
            base['Participant ID'] = base['Participant ID'].astype(str)
            surv = load_survival()
            mm = base.merge(surv[['eid', f'{organ}_time', f'{organ}_event',
                                  f'{organ}_prevalent']], left_on='Participant ID',
                            right_on='eid', how='inner')
            mm = mm[mm[f'{organ}_prevalent'] == 0]
            feats = list(feat_origin.keys())
            y = np.array([(e, float(t)) for e, t in
                          zip(mm[f'{organ}_event'].values.astype(bool),
                              mm[f'{organ}_time'].values)],
                         dtype=[('event', 'bool'), ('time', 'float')])
            tr_mask = np.isin(mm['Region'].values, list(config.REGION_TRAIN))
            p = joblib.load(pk).predict_proba(mm[feats])[:, 1]
            y_tr, p_tr, y_te, p_te = y[tr_mask], p[tr_mask], y[~tr_mask], p[~tr_mask]
            ts = [t for t in TIMES if t < float(y_te['time'].max())]
            try:
                a_te, _ = cumulative_dynamic_auc(y_te, y_te, p_te, ts)
            except Exception:
                continue
        else:
            ts, res = td_auc_grid(organ, m)
            if res is None:
                continue
            _, a_te = res
        ax.plot(ts, a_te, lw=2.2, color=COLORS[m], label=m)
    ax.set_xlabel('Time since baseline (years)')
    ax.set_ylabel('Time-dependent AUC (external)')
    ax.set_title(f'{ORG_CN[organ]} | external validation (Scotland+Wales)')
    ax.set_ylim(0.4, 1.0)
    ax.axhline(0.5, color='gray', ls=':', lw=1)
    ax.grid(alpha=0.25, ls=':')
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, f'{organ}_tdAUC_te.pdf'), dpi=600)
    fig.savefig(os.path.join(FIG, f'{organ}_tdAUC_te.png'), dpi=300)
    plt.close(fig)


def fig_cindex_forest():
    df = pd.read_csv(os.path.join(RESULT, 'survival_metrics_all.csv'))
    df = df[df['modality'].isin(MODS)]
    order = ['proteome', 'metabolome', 'blood', 'lifestyle', 'merge']
    fig, ax = plt.subplots(figsize=(7.5, 5.6))
    ypos = 0
    xtr, xte = [], []
    for oi, o in enumerate(['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']):
        sub = df[df['organ'] == o]
        ymid = ypos + (len(order) - 1) / 2
        ax.text(-0.28, ymid, ORG_CN[o], va='center', ha='right', fontsize=9)
        for m in order:
            r = sub[sub['modality'] == m]
            if len(r):
                xtr.append((oi, ypos, r['Cindex_lgbm_tr'].iloc[0], m))
                xte.append((oi, ypos, r['Cindex_lgbm_te'].iloc[0], m))
                ypos += 1
        ypos += 0.8
    for oi, y, v, m in xtr:
        ax.plot(v, y, 'o', ms=5, color='#B0B0B0',
                mec=COLORS.get(m, 'k'), mew=1.2, zorder=3)
    for oi, y, v, m in xte:
        ax.plot(v, y, 's', ms=6, color=COLORS.get(m, 'k'), zorder=4)
    ax.axvline(0.5, color='gray', ls=':', lw=1)
    ax.set_xlabel('C-index')
    ax.set_xlim(0.35, 1.0)
    ax.set_yticks([])
    ax.invert_yaxis()
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], marker='s', ls='', color=COLORS[m], ms=7,
                label=m) for m in order]
    h.append(Line2D([0], [0], marker='o', ls='', color='#B0B0B0', ms=6,
                    label='internal (England)'))
    ax.legend(handles=h, frameon=False, fontsize=8, loc='lower right')
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, 'Cindex_forest.pdf'), dpi=600)
    fig.savefig(os.path.join(FIG, 'Cindex_forest.png'), dpi=300)
    plt.close(fig)
    print('✅ C-index 森林图')


def fig_calibration(organ, modality='proteome', years=(5, 10)):
    feats, X, y, tr_mask = load_organ_data(organ, modality)
    Xc = X.replace([np.inf, -np.inf], np.nan).fillna(X.median())
    df_all = pd.DataFrame(Xc.values, columns=feats)
    df_all['T'], df_all['E'] = y['time'], y['event'].astype(int)
    cph = CoxPHFitter(penalizer=0.05)
    cph.fit(df_all[tr_mask], duration_col='T', event_col='E',
            show_progress=False, fit_options={'step_size': 0.5})
    for yr in years:
        fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.2))
        for ax, mask, tag in [(axes[0], tr_mask, 'Internal (England)'),
                              (axes[1], ~tr_mask, 'External (Scot+Wal)')]:
            sf = cph.predict_survival_function(df_all[mask], times=[yr])
            risk = 1 - np.asarray(sf).ravel()
            T, E = y['time'][mask], y['event'][mask]
            # 十分位
            q = pd.qcut(pd.Series(risk), 10, labels=False, duplicates='drop')
            preds, obs = [], []
            for g in sorted(set(q)):
                gm = q == g
                if gm.sum() < 20:
                    continue
                preds.append(risk[gm].mean())
                kmf = KaplanMeierFitter()
                kmf.fit(T[gm], E[gm])
                s_km = kmf.predict(yr) if yr <= T[gm].max() else np.nan
                obs.append(1 - float(np.asarray(s_km).ravel()[0])
                           if not np.isnan(s_km) else np.nan)
            ax.plot(preds, obs, 'o', ms=6, color='#C00000', zorder=4)
            lim = [0, max(np.nanmax(preds), np.nanmax(obs)) * 1.1]
            ax.plot(lim, lim, '--', color='gray', lw=1)
            ax.set_xlabel('Predicted risk (Cox)')
            ax.set_ylabel('Observed (KM)')
            ax.set_title(f'{tag} | {yr}-year')
            ax.grid(alpha=0.25, ls=':')
        fig.suptitle(f'{ORG_CN[organ]} | {modality} calibration', fontweight='bold')
        fig.tight_layout(rect=[0, 0, 1, 0.94])
        fig.savefig(os.path.join(FIG, f'{organ}_{modality}_calibration_{yr}y.pdf'),
                    dpi=600)
        fig.savefig(os.path.join(FIG, f'{organ}_{modality}_calibration_{yr}y.png'),
                    dpi=300)
        plt.close(fig)
    print(f'✅ 校准曲线 {organ}/{modality}')


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', default=None)
    ap.add_argument('--skip-calibration', action='store_true')
    args = ap.parse_args()
    organs = [args.organ] if args.organ else \
        ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
    for o in organs:
        try:
            fig_tdauc(o)
        except Exception as e:
            print(f'  ✗ tdAUC {o}: {e}')
    fig_cindex_forest()
    if not args.skip_calibration:
        for o in organs:
            try:
                fig_calibration(o)
            except Exception as e:
                print(f'  ✗ 校准 {o}: {e}')
    print(f'✅ 图输出: {FIG}/')


if __name__ == '__main__':
    main()
