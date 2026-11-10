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
05_shared_specific.py - 共享 vs 特异面板分析 (of825)
=====================================================
问题: 6 器官 × 8 模态的 Delong 面板中, 哪些分子是跨器官共享轴,
      哪些是器官特异? 共享分子是否与中介枢纽重叠?

输出: result/of825/05_survival/shared_specific/
  - shared_features_{modality}.csv      每模态: 特征 x 出现器官数
  - organ_overlap_{modality}.csv        器官对 Jaccard 重叠
  - shared_axis_mediation.csv           共享面板 ∩ 显著中介 (跨层共享轴)
  - 图: heatmap_{modality}.pdf (特征x器官出现矩阵, 共享>=2器官)
        jaccard_{modality}.pdf (器官对重叠热图)
"""
import os
import sys
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR', os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    '.cache', 'mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

FONT_DIR = os.path.join(config.BASE_DIR, '.cache', 'fonts')
for _f in ['LiberationSans-Regular.ttf', 'LiberationSans-Bold.ttf']:
    font_manager.fontManager.addfont(os.path.join(FONT_DIR, _f))
plt.rcParams['font.family'] = 'Liberation Sans'

OUT = os.path.join(config.RESULT_DIR, '05_survival', 'shared_specific')
os.makedirs(OUT, exist_ok=True)
ORGANS = ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']
MODALITIES = ['proteome', 'metabolome', 'blood', 'lifestyle', 'psych',
              'history', 'brain']
ORG_CN = {'heart': 'Heart', 'lung': 'Lung', 'liver': 'Liver',
          'renal': 'Renal', 'hemat': 'Hematologic', 'organ': 'Any-organ'}
N_SHARE = 3    # 共享定义: 出现在 >=3 器官 (不含 organ, 因它是并集)


def panel_of(organ, modality):
    f = os.path.join(config.RESULT_DIR, '02_ranking',
                     f'{organ}_{modality}', 'Delong_Selection_Results.csv')
    df = pd.read_csv(f)
    return df[df['Delong1'] < config.DELONG_P]['feature'].tolist()


def merge_panel_of(organ):
    """merge 面板 (去模态前缀)"""
    f = os.path.join(config.RESULT_DIR, '04_fusion', f'{organ}_merge',
                     'merge_features.csv')
    df = pd.read_csv(f)
    return df['feature'].tolist()


def main():
    all_rows = []
    for modality in MODALITIES + ['merge']:
        panels = {}
        for o in ORGANS:
            panels[o] = (merge_panel_of(o) if modality == 'merge'
                         else panel_of(o, modality))
        # 特征 -> 出现器官 (仅 5 单器官, 不含 organ 并集)
        single = {o: set(panels[o]) for o in ORGANS[:-1]}
        cnt = {}
        feats = set().union(*single.values())
        for f in feats:
            cnt[f] = sum(1 for s in single.values() if f in s)
        # merge 特征去前缀后归类 (proteome__GDF15 -> GDF15)
        if modality == 'merge':
            cnt = {}
            for f in feats:
                base = f.split('__')[1] if '__' in f else f
                cnt[base] = cnt.get(base, 0)
                if f in panels['organ']:
                    cnt[base] = max(cnt[base], 1)
        df = pd.DataFrame([{'feature': f, 'n_organs': n}
                           for f, n in cnt.items()])
        df = df.sort_values('n_organs', ascending=False)
        df.to_csv(os.path.join(OUT, f'shared_features_{modality}.csv'),
                  index=False)
        shared = df[df['n_organs'] >= N_SHARE]['feature'].tolist()
        print(f'[{modality}] 面板特征(5器官并)={len(feats)} | '
              f'共享(>=3器官)={len(shared)}: {", ".join(shared[:8])}')
        all_rows.append({'modality': modality, 'n_features': len(feats),
                         'n_shared_ge3': len(shared)})
        # Jaccard 器官对
        jac = pd.DataFrame(np.nan, index=ORGANS[:-1], columns=ORGANS[:-1])
        for a in ORGANS[:-1]:
            for b in ORGANS[:-1]:
                sa, sb = single[a], single[b]
                jac.loc[a, b] = len(sa & sb) / len(sa | sb) if sa | sb else np.nan
        jac.to_csv(os.path.join(OUT, f'organ_overlap_{modality}.csv'))
        # 热图: 共享(>=2)特征 x 器官
        feats2 = [f for f, n in cnt.items() if n >= 2]
        if feats2:
            mat = pd.DataFrame(0, index=ORGANS, columns=feats2)
            for o in ORGANS:
                for f in mat.columns:
                    mat.loc[o, f] = 1 if f in panels[o] else 0
            mat = mat.loc[:, mat.sum(axis=0).sort_values(ascending=False).index]
            fig, ax = plt.subplots(figsize=(max(6, len(feats2) * 0.42), 3.2))
            im = ax.imshow(mat.values, cmap='Reds', aspect='auto')
            ax.set_xticks(range(len(feats2)))
            ax.set_xticklabels(mat.columns, rotation=90, fontsize=7)
            ax.set_yticks(range(len(ORGANS)))
            ax.set_yticklabels([ORG_CN[o] for o in ORGANS], fontsize=8)
            ax.set_title(f'{modality}: features present in >=2 organs')
            fig.colorbar(im, shrink=0.6, label='present')
            fig.tight_layout()
            fig.savefig(os.path.join(OUT, f'heatmap_{modality}.pdf'), dpi=600)
            plt.close(fig)
    pd.DataFrame(all_rows).to_csv(
        os.path.join(OUT, 'shared_summary_all_modalities.csv'), index=False)

    # 跨层共享轴: 共享 proteome/metabolome/blood 特征 ∩ 显著中介
    med = pd.read_csv(os.path.join(config.RESULT_DIR, '06_mediation',
                                   'significant_mediators.csv'))
    med_feats = set()
    for x in med['Mediator']:
        med_feats.add(x.split('__')[1] if '__' in x else x)
    print(f'\n显著中介分子数: {len(med_feats)}')
    rows = []
    for modality in ['proteome', 'metabolome', 'blood']:
        df = pd.read_csv(os.path.join(OUT, f'shared_features_{modality}.csv'))
        shared = set(df[df['n_organs'] >= N_SHARE]['feature'])
        inter = shared & med_feats
        rows.append({'modality': modality, 'n_shared_ge3': len(shared),
                     'shared_in_mediation': len(inter),
                     'axis_molecules': ', '.join(sorted(inter))})
        print(f'[{modality}] 共享轴分子在显著中介中: {len(inter)}: '
              f'{", ".join(sorted(inter))[:120]}')
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'shared_axis_mediation.csv'),
                              index=False)
    print(f'\n✅ 共享/特异分析输出: {OUT}/')


if __name__ == '__main__':
    main()
