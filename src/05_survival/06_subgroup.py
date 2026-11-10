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
06_subgroup.py - 性别/年龄亚组的时序判别性能 (of825)
====================================================
对每器官 x 主模态 (proteome/metabolome/blood/lifestyle/merge):
  亚组 = Sex (0=F / 1=M) | Age (<60 / >=60, 基线年龄)
  每亚组内: LGBM 概率的 C-index (England 内部 / Scot+Wal 外部)
输出:
  result/of825/05_survival/subgroup/subgroup_cindex.csv
  result/of825/05_survival/subgroup/subgroup_forest.pdf (外部 C-index 森林图)
"""
import os
import sys
import numpy as np
import pandas as pd
import joblib
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
from sksurv_load import load_organ_data, load_survival

FONT_DIR = os.path.join(config.BASE_DIR, '.cache', 'fonts')
for _f in ['LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf']:
    font_manager.fontManager.addfont(os.path.join(FONT_DIR, _f))
plt.rcParams['font.family'] = 'Liberation Sans'

OUT = os.path.join(config.RESULT_DIR, '05_survival', 'subgroup')
os.makedirs(OUT, exist_ok=True)
ORG_CN = {'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver',
          'renal': 'Renal',
          'brain': 'Brain', 'hemat': 'Hematologic', 'organ': 'Any-organ'}
COLORS = {'proteome': '#C00000', 'metabolome': '#4472C4', 'blood': '#70AD47',
          'lifestyle': '#ED7D31', 'merge': '#7030A0'}

DEMO_FILE = os.path.join(config.XM_DIR, 'UKB', 'Assessment_centre',
                         '1Baseline_characteristics_participant.csv')


def load_demo():
    d = pd.read_csv(DEMO_FILE, usecols=['Participant ID', 'Age at recruitment',
                                        'Sex'])
    d['Participant ID'] = d['Participant ID'].astype(str)
    return d


def load_organ_with_ids(organ, modality):
    """带样本 ID 的数据加载 (非 merge)"""
    label = organ + ('_failure' if organ != 'organ' else '_failure')
    surv = load_survival()
    rank_dir = os.path.join(config.RESULT_DIR, '02_ranking', f'{organ}_{modality}')
    sel = pd.read_csv(os.path.join(rank_dir, 'Delong_Selection_Results.csv'))
    feats = sel[sel['Delong1'] < config.DELONG_P]['feature'].tolist()
    if not feats:
        feats = sel['feature'].head(1).tolist()
    prep = pd.read_csv(os.path.join(config.RESULT_DIR, '01_prep',
                                    f'{modality}_prep.csv'),
                       usecols=['Participant ID', 'Region', label] + feats)
    prep['Participant ID'] = prep['Participant ID'].astype(str)
    m = prep.merge(surv[['eid', f'{organ}_time', f'{organ}_event',
                         f'{organ}_prevalent']], left_on='Participant ID',
                   right_on='eid', how='inner')
    m = m[m[f'{organ}_prevalent'] == 0]
    m = m[m[f'{organ}_event'].notna()]
    t = m[f'{organ}_time'].values
    ev = m[f'{organ}_event'].values.astype(bool)
    tr_mask = np.isin(m['Region'].values, list(config.REGION_TRAIN))
    y = np.array([(e, float(ti)) for e, ti in zip(ev, t)],
                 dtype=[('event', 'bool'), ('time', 'float')])
    return m['Participant ID'].values, m[feats], y, tr_mask


def cindex_sub(organ, modality, demo):
    if modality == 'merge':
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
        X = mm[feats]
        y = np.array([(e, float(t)) for e, t in
                      zip(mm[f'{organ}_event'].values.astype(bool),
                          mm[f'{organ}_time'].values)],
                     dtype=[('event', 'bool'), ('time', 'float')])
        tr_mask = np.isin(mm['Region'].values, list(config.REGION_TRAIN))
        pk = os.path.join(config.RESULT_DIR, '04_fusion', f'{organ}_merge',
                          f'{organ}_merge_model.pkl')
        ids = mm['Participant ID'].values
    else:
        ids, X, y, tr_mask = load_organ_with_ids(organ, modality)
        pk = os.path.join(config.RESULT_DIR, '03_model', f'{organ}_{modality}',
                          f'{organ}_LightGBM_model.pkl')
    p = joblib.load(pk).predict_proba(X)[:, 1]
    rows = []
    for name, mask_sub in subgroup_masks(demo, ids):
        for tag, m2 in [('tr', tr_mask), ('te', ~tr_mask)]:
            m = mask_sub & m2
            if m.sum() < 200 or y['event'][m].sum() < 10:
                continue
            rows.append({'organ': organ, 'modality': modality, 'subgroup': name,
                         'set': tag, 'n': int(m.sum()),
                         'n_event': int(y['event'][m].sum()),
                         'Cindex': concordance_index(y['time'][m], -p[m],
                                                     y['event'][m])})
    return rows


def subgroup_masks(demo, ids):
    dm = demo.set_index('Participant ID').loc[ids]
    out = []
    out.append(('Female', (dm['Sex'] == 0).values))
    out.append(('Male', (dm['Sex'] == 1).values))
    out.append(('Age<60', (dm['Age at recruitment'] < 60).values))
    out.append(('Age>=60', (dm['Age at recruitment'] >= 60).values))
    return out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--organ', default=None)
    args = ap.parse_args()
    demo = load_demo()
    print(f'人口学: {len(demo):,} 人 (Sex 缺失 {demo["Sex"].isna().sum():,}, '
          f'Age 缺失 {demo["Age at recruitment"].isna().sum():,})')
    organs = [args.organ] if args.organ else \
        ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
    rows = []
    for o in organs:
        for m in ['proteome', 'metabolome', 'blood', 'lifestyle']:
            try:
                rows += cindex_sub(o, m, demo)
            except ValueError as e:
                pass
            except Exception as e:
                print(f'  ✗ {o}/{m}: {e}')
        try:
            rows += cindex_sub(o, 'merge', demo)
        except Exception as e:
            print(f'  ✗ {o}/merge: {e}')
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, 'subgroup_cindex.csv'), index=False)
    # 外部 C-index 森林图: 每器官 x 亚组, 模态点
    te = df[df['set'] == 'te']
    fig, ax = plt.subplots(figsize=(8, 7))
    ypos = 0
    yt = []
    for o in organs:
        sub = te[te['organ'] == o]
        for sg in ['Female', 'Male', 'Age<60', 'Age>=60']:
            s2 = sub[sub['subgroup'] == sg]
            for _, r in s2.iterrows():
                ax.plot(r['Cindex'], ypos, 's', ms=6,
                        color=COLORS.get(r['modality'], 'k'), zorder=4)
            ax.text(-0.30, ypos, f'{ORG_CN[o]} {sg}', ha='right', va='center',
                    fontsize=8)
            yt.append(ypos)
            ypos += 1
        ypos += 0.6
    from matplotlib.lines import Line2D
    h = [Line2D([0], [0], marker='s', ls='', color=COLORS[m], ms=7, label=m)
         for m in ['proteome', 'metabolome', 'blood', 'lifestyle', 'merge']]
    ax.legend(handles=h, frameon=False, fontsize=8, loc='lower right')
    ax.axvline(0.5, color='gray', ls=':', lw=1)
    ax.set_xlabel('External C-index (Scotland+Wales)')
    ax.set_xlim(0.3, 1.0)
    ax.set_yticks([])
    ax.invert_yaxis()
    fig.subplots_adjust(left=0.17, right=0.99, bottom=0.08)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(os.path.join(OUT, 'subgroup_forest.pdf'), dpi=600)
    fig.savefig(os.path.join(OUT, 'subgroup_forest.png'), dpi=300)
    plt.close(fig)
    print(f'✅ 亚组分析: {OUT}/subgroup_cindex.csv ({len(df)} 行) + 森林图')


if __name__ == '__main__':
    main()
