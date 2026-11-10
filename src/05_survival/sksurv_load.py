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
"""sksurv_load.py - 02/03 共享的生存数据载入 (organ x modality -> X, y, tr_mask)"""
import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

RESULT = os.path.join(config.RESULT_DIR, '05_survival')
ORGAN_LABEL = {o: o + '_failure' if o != 'organ' else 'organ_failure'
               for o in ['heart', 'lung', 'liver', 'renal', 'hemat', 'brain', 'organ']}

_surv_df = None


def load_survival():
    global _surv_df
    if _surv_df is None:
        _surv_df = pd.read_csv(os.path.join(RESULT, 'survival_matrix.csv'),
                               dtype={'eid': str})
    return _surv_df


def load_organ_data(organ, modality, region_train=(1,)):
    """载入 prep 特征 + survival (对齐, 排除 prevalent)。
    返回 feats, X, y(structured: event/time), tr_mask(Region==1 England)"""
    label = ORGAN_LABEL[organ]
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
    region = m['Region'].values
    tr_mask = np.isin(region, list(region_train))
    X = m[feats]
    y = np.array([(e, float(ti)) for e, ti in zip(ev, t)],
                 dtype=[('event', 'bool'), ('time', 'float')])
    return feats, X, y, tr_mask
