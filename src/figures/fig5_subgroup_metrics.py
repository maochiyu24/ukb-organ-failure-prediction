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
"""Fig5 亚组指标重算: 7 organ merge 测试集 (2499) per subgroup C-index/AUC + bootstrap CI
Age<60/Age>=60 (切点60) + Female/Male; 核对 subgroup_cindex.csv merge 行
输出 .te_cache/subgroup_merge_metrics.csv
"""
import os, sys, time
import numpy as np, pandas as pd, joblib
R=_PROJECT + '/result/of903'
CACHE=os.path.join(_PROJECT, 'cache')
OUT=f'{CACHE}/subgroup_merge_metrics.csv'
MODS=['proteome','metabolome','blood','prs','history','lifestyle','psych']
ORG7=[('heart','Heart'),('lung','Lung'),('liver','Liver'),('renal','Kidney'),('hemat','Hematologic'),('brain','Stroke'),('organ','Any organ failure')]
if os.path.exists(OUT):
    print('cached'); raise SystemExit
surv=pd.read_csv(f'{R}/05_survival/survival_matrix.csv',dtype={'eid':str})
bl=pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
               usecols=['Participant ID','Age at recruitment','Sex'])
bl.columns=['eid','Age','Sex']; bl['eid']=bl['eid'].astype(str)
from lifelines.utils import concordance_index
from sklearn.metrics import roc_auc_score

def te_proba(organ):
    mf=pd.read_csv(f'{R}/04_fusion/{organ}_merge/merge_features.csv')
    feat_cols=list(mf['feature']); base=None
    for mod in MODS:
        sel=mf[mf['modality']==mod]
        if sel.empty: continue
        tab=pd.read_pickle(f'{CACHE}/{mod}_te.pkl')
        ren={orig:f'{mod}__{orig}' for orig in sel['original'] if orig in tab.columns}
        if not ren: continue
        sub=tab[['Participant ID']+list(ren)].rename(columns=ren)
        base=sub if base is None else base.merge(sub,on='Participant ID',how='inner')
    test=base.merge(surv[['eid',f'{organ}_time',f'{organ}_event']],left_on='Participant ID',right_on='eid',how='inner')
    test=test[test[f'{organ}_event'].notna()].reset_index(drop=True)
    X=test[feat_cols]
    model=joblib.load(f'{R}/04_fusion/{organ}_merge/{organ}_merge_model.pkl')
    test['p']=model.predict_proba(X)[:,1]
    test=test.merge(bl,on='eid',how='left')
    return test

rng=np.random.default_rng(42)
rows=[]; nboot=1000
for o,lab in ORG7:
    t=te_proba(o)
    t['sg']=np.where(t['Age']<60,'Age<60','Age>=60')
    t['sx']=np.where(t['Sex']==0,'Female','Male')
    for sg,key in [('age','sg'),('sex','sx')]:
        for g in t[key].unique():
            s=t[t[key]==g]
            if len(s)<20 or s[f'{o}_event'].sum()<5: continue
            y=s[f'{o}_event'].astype(int).values; tm=s[f'{o}_time'].values; p=s['p'].values
            ci=concordance_index(tm,-p,y)   # 高p=高险 -> -p
            auc=roc_auc_score(y,p)
            boot_c=[]; boot_a=[]
            idx=np.arange(len(y))
            for _ in range(nboot):
                b=rng.choice(idx,len(idx),replace=True)
                if len(np.unique(y[b]))>1:
                    boot_c.append(concordance_index(tm[b],-p[b],y[b]))
                    boot_a.append(roc_auc_score(y[b],p[b]))
            rows.append(dict(organ=o,Organ=lab,Subgroup=g,Category=('Age' if key=='age' else 'Sex'),
                             n=len(s),n_event=int(y.sum()),Cindex=ci,
                             C_lo=np.percentile(boot_c,2.5),C_hi=np.percentile(boot_c,97.5),
                             AUC=auc,A_lo=np.percentile(boot_a,2.5),A_hi=np.percentile(boot_a,97.5)))
    print(lab,'done')
res=pd.DataFrame(rows)
res.to_csv(OUT,index=False)
# 核对 heart merge
h=res[(res.organ=='heart')&(res.Subgroup=='Female')]
print('heart Female Cindex=',h.Cindex.iloc[0],'(official 0.906090)')
print(res[res.organ=='heart'].to_string(index=False))
