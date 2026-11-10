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
"""result906 tables v2: Table1 基线(行=指标, Overall/Training set/Test set) 主表;
S2 Delong分模态; S3 中介全量; S4 GO 全显著; S5 代谢物对照(官方325表)"""
import os, sys, glob
import numpy as np, pandas as pd
from naming import ORG_CN, MOD_LABEL, full_feature_name
R=_PROJECT + '/result/of903'
GO_DIR=f'{R}/input907_analysis_output/go_enrichment/top50'   # 907 版 GO(含 Stroke)
OUT=_PROJECT + '/result/result906/tables'
os.makedirs(OUT,exist_ok=True)
ORGS6=['heart','lung','liver','renal','hemat','brain']
def save(df,name):
    df.to_csv(f'{OUT}/{name}.csv',index=False,encoding='utf-8-sig'); print('saved',name,len(df))

# ============ Table 1 (主表, 行=指标; 列=Overall/Training set/Test set) ============
surv=pd.read_csv(f'{R}/05_survival/survival_matrix.csv',dtype={'eid':str})
bl=pd.read_csv(_PROJECT + '/xm/UKB/Assessment_centre/1Baseline_characteristics_participant.csv',
 usecols=['Participant ID','Age at recruitment','Sex','Townsend deprivation index at recruitment','Education score (England)','Income score (England)'])
bl.columns=['eid','Age','Sex','Townsend','Edu','Inc']; bl['eid']=bl['eid'].astype(str)
li=pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/Lifestyle_Instance0.csv',usecols=['Participant ID','Pack years of smoking','Sleep duration'])
li=li.rename(columns={'Participant ID':'eid','Pack years of smoking':'PackYrs','Sleep duration':'Sleep'})  # 按列名映射(文件列序为 Sleep 在前!)
li['eid']=li['eid'].astype(str)
cc=pd.read_csv(_PROJECT + '/xm/ZS/8.7/data/participant_country_classification.csv')
cc['Region']=cc['Country'].map({'England':1,'Scotland':2,'Wales':3}); cc['Participant ID']=cc['Participant ID'].astype(str)
d=surv.merge(bl,on='eid',how='left').merge(li,on='eid',how='left').merge(cc[['Participant ID','Region']],left_on='eid',right_on='Participant ID',how='left')
d=d[(d.Region.isin([1,2,3]))&(d.organ_prevalent==0)].copy()
for c in ['PackYrs','Sleep']:
    d[c]=pd.to_numeric(d[c],errors='coerce')
d.loc[d.PackYrs<0,'PackYrs']=np.nan; d.loc[(d.Sleep<0)|(d.Sleep>16),'Sleep']=np.nan
d['fu']=pd.to_numeric(d['follow_time'],errors='coerce')
d['Female']=(d.Sex==0)
# 列: Overall / Training set (England) / Test set (Scotland+Wales); 地名不出现于表内
cols=[('Overall',pd.Series(True,index=d.index)),
      ('Training set',d.Region==1),
      ('Test set',d.Region.isin([2,3]))]
def med_iqr(s): return f"{np.nanmedian(s):.2f} ({np.nanpercentile(s,25):.2f}-{np.nanpercentile(s,75):.2f})"
def pct(mask): 
    s=d.loc[mask]; n=len(s)
    return f"{int(n):,} ({n/len(d)*100:.1f}%)"
rows=[]
def addrow(label,fmt):
    rows.append([label]+[fmt(m) for _,m in cols])
addrow('Participants, n (% of overall)',lambda m: pct(m))
addrow('Age (years), mean ± SD',lambda m: f"{d.loc[m,'Age'].mean():.1f} ± {d.loc[m,'Age'].std():.1f}")
addrow('Female, n (%)',lambda m: f"{int(d.loc[m,'Female'].sum()):,} ({d.loc[m,'Female'].mean()*100:.1f}%)")
addrow('Townsend deprivation index, median (IQR)',lambda m: med_iqr(d.loc[m,'Townsend']))
addrow('Education score (IMD), median (IQR)',lambda m: med_iqr(d.loc[m,'Edu']))
addrow('Income score (IMD), median (IQR)',lambda m: med_iqr(d.loc[m,'Inc']))
addrow('Ever smokers, n (%)',lambda m: f"{int(d.loc[m,'PackYrs'].notna().sum()):,} ({d.loc[m,'PackYrs'].notna().mean()*100:.1f}%)")
addrow('Pack years of smoking (ever smokers), median (IQR)',lambda m: med_iqr(d.loc[m][d.loc[m,'PackYrs'].notna()]['PackYrs']))
addrow('Sleep duration (h), median (IQR)',lambda m: med_iqr(d.loc[m,'Sleep']))
addrow('Follow-up (years), median (IQR)',lambda m: med_iqr(d.loc[m,'fu']))
addrow('No organ failure event, n (%)',lambda m: f"{int((d.loc[m,'organ_event']==0).sum()):,} ({(d.loc[m,'organ_event']==0).mean()*100:.1f}%)")
addrow('Any organ failure event, n (%)',lambda m: f"{int((d.loc[m,'organ_event']==1).sum()):,} ({(d.loc[m,'organ_event']==1).mean()*100:.1f}%)")
for o in ORGS6:
    addrow(f'{ORG_CN[o]} event, n (%)',lambda m,o=o: f"{int((d.loc[m,f'{o}_event']==1).sum()):,} ({(d.loc[m,f'{o}_event']==1).mean()*100:.1f}%)")
t1=pd.DataFrame(rows,columns=['Characteristic']+[c[0] for c in cols])
save(t1,'Table1_baseline_rows')

# ============ S2: Delong 前向选择 (每模态一附表) ============
import re
MODS8=['proteome','metabolome','blood','prs','history','lifestyle','psych','brain']
S2_LETTER={m:chr(97+i) for i,m in enumerate(MODS8)}   # a..h 与模态顺序对应
for m in MODS8:
    rows=[]
    for f in sorted(glob.glob(f'{R}/02_ranking/*_{m}/Delong_Selection_Results.csv')):
        o=f.split('/')[-2].replace(f'_{m}','')
        dd=pd.read_csv(f)
        for i,r in dd.iterrows():
            rows.append(dict(System=ORG_CN.get(o,o),Step=i+1,Feature=full_feature_name(f'{m}__{r.feature}'),
                AUC_mean=round(r.AUC_mean,4),AUC_SD=round(r.AUC_std,4),
                Delong_p=round(r.Delong1,4),Significant=r.Delong1<0.05))
    if rows:
        save(pd.DataFrame(rows),f'TableS2{S2_LETTER[m]}_{MOD_LABEL[m].replace(" ","_")}')

# ============ S3: 中介全量 ============
res=pd.read_csv(f'{R}/06_mediation_v2/mediation_results_all_all_all.csv')
ev=pd.read_csv(f'{R}/06_mediation_v2/evalue_summary.csv')
from naming import mediator_name
EXP_DISP={'lifestyle_score_v2':'Healthy behaviour','psych_score_v2':'Psychological distress'}
PREF_PANEL={'proteome':'Proteomics','metabolome':'Metabolomics','blood':'Biochemical measures'}
sig=res[res.ACME_p<0.05].copy()
sig['Mediator_raw']=sig['Mediator']
# E-value 必须在展示名替换前按原始键 (Exposure/Organ/Mediator) join
emap=ev.set_index(['Exposure','Organ','Mediator'])['E_value_2unit']
sig['E_value_2unit']=sig.apply(lambda r: emap.get((r.Exposure,r.Organ,r.Mediator),np.nan),axis=1)
sig['Exposure']=sig.Exposure.map(EXP_DISP)
sig['Organ']=sig.Organ.map(ORG_CN)
# 三个中介面板用全文正式命名 (按 mediator 前缀: proteome/metabolome/blood)
sig['Panel']=sig.Mediator_raw.map(lambda x: PREF_PANEL.get(str(x).split('__')[0],'Other'))
sig['Mediator']=sig.Mediator_raw.apply(mediator_name)
t3=sig[['Exposure','Organ','Panel','Mediator','N','N_pos','ACME','ACME_lo','ACME_hi','ADE','ADE_lo','ADE_hi',
        'Prop_mediated','PM_lo','PM_hi','ACME_p','ADE_p','E_value_2unit']]
t3=t3.rename(columns={'Prop_mediated':'PM'})
save(t3.round({'ACME':5,'ACME_lo':5,'ACME_hi':5,'ADE':5,'ADE_lo':5,'ADE_hi':5,'PM':4,'PM_lo':4,'PM_hi':4,'ACME_p':6,'ADE_p':6,'E_value_2unit':2}),'TableS3_mediation_all')

# ============ S5: 代谢物缩写对照 (官方 325 代谢物表, 直接使用) ============
META_XLSX = _PROJECT + '/xm/ZS/data/代谢物325_简写_全称_组_亚组.xlsx'
s4 = pd.read_excel(META_XLSX, sheet_name=0)      # '简写': Biomarker/Description/...
save(s4, 'TableS5_metabolite_mapping')

# ============ S4: GO 全显著 (BP+CC+MF 全命名空间, 详细列) ============
NS_CN = {'biological_process': 'Biological process (BP)',
         'cellular_component': 'Cellular component (CC)',
         'molecular_function': 'Molecular function (MF)'}
rows = []
for o, lab in ORG_CN.items():
    fp = f'{GO_DIR}/{o}_GO_enrichment.csv'
    if not os.path.exists(fp):
        continue
    g = pd.read_csv(fp)
    g = g[g.p_adjust < 0.05].copy()
    g['Ontology'] = g.Namespace.map(NS_CN)
    g = g.sort_values(['Namespace', 'p_adjust'])
    for _, r in g.iterrows():
        rows.append(dict(System=lab, Ontology=r.Ontology,
                         GO_ID=r.GO_ID, GO_Name=r.GO_Name,
                         Fold_enrichment=round(r.Fold_enrichment, 2),
                         Count_in_test=int(r.Count_in_test), Test_size=int(r.Test_size),
                         Count_in_background=int(r.Count_in_background),
                         Background_size=int(r.Background_size),
                         Gene_ratio=round(r.Count_in_test / r.Test_size, 3),
                         p_value=float(r.p_value), FDR=float(r.p_adjust),
                         Genes=r.Genes))
save(pd.DataFrame(rows), 'TableS4_GO_enrichment_all')

# ============ S6 已取消 (对照表仅代谢组, 并入 S5; 全模态 mapping 不再输出) ============
print('all done')
