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
organize_tables_final.py — 表格整理与正式命名 (可发表级)
=========================================================
输入: result908/tables(+pro/)  →  输出: result908/tables_final/
产物:
  Table1_*.csv/.xlsx                 主表 1
  TableS1_*                          补充表 S1(模型判别力:长表/矩阵/分析人群)
  TableS2a-g_*                       补充表 S2(各数据域入选特征; h=脑影像 标注 exploratory)
  TableS3_* / TableS4_* / TableS5_*  补充表 S3(中介)/S4(GO)/S5(代谢物注释)
  TableS6_*                          新增:结局定义/ICD 编码/随访
  Main_Tables.xlsx                   主表合集(1 sheet)
  Supplementary_Tables.xlsx          补充表合集(多 sheet)
  Tables_index.md / Tables_index.csv 表目录(正式名称+说明+文件对应)
"""
import os
import shutil
import pandas as pd
from openpyxl.styles import Font, Alignment
from openpyxl.utils import get_column_letter

T = _PROJECT + '/result/result908/tables'
OUT = _PROJECT + '/result/result908/tables_final'
os.makedirs(OUT, exist_ok=True)

# (源文件, 目标文件名, 表号, 正式标题, 一句话说明)
SPEC = [
    ('pro/Table1_main.csv', 'Table1_cohort_and_organ_events.csv', 'Table 1',
     'Baseline characteristics of participants and incident severe organ-failure events, overall and by organ system',
     'Characteristics of the run-in analysis cohort (n = 492,904) overall and in eight outcome groups '
     '(no organ failure, six organ systems and the composite outcome), with absolute standardised mean differences '
     '(SMD) for any organ failure versus no organ failure; outcome labels come from the diagnosis matrix with a '
     'one-year lag period.'),
    ('pro/TableS1_performance_long.csv', 'TableS1a_model_discrimination_long.csv', 'Table S1a',
     'External validation of organ-failure prediction models across seven data domains and multimodal fusion',
     'Harrell C-index and full-follow-up AUC with 95% bootstrap confidence intervals for every data domain x organ '
     'combination, together with test-set sample size and number of events (112 estimates).'),
    ('pro/TableS1_performance_matrix.xlsx', 'TableS1b_model_discrimination_matrix.xlsx', 'Table S1b',
     'External validation of organ-failure prediction models (matrix view by outcome)',
     'Same estimates as Table S1a arranged as two matrices (C-index; full-follow-up AUC) with modalities in rows and '
     'organ outcomes in columns.'),
    ('pro/TableS1_sample_sizes.csv', 'TableS1c_analysis_populations.csv', 'Table S1c',
     'Analysis populations and number of incident events by data domain and organ outcome',
     'External-validation sample size and number of events for each data domain and organ outcome '
     '(multimodal fusion column included).'),
    ('TableS2a_Proteomics.csv', 'TableS2a_selected_features_proteomics.csv', 'Table S2a',
     'DeLong forward selection of proteomic features, by organ outcome',
     'Stepwise candidate features for the Olink proteomic panel with cross-validated AUC and DeLong P value at each '
     'selection step; flagged as significant or not.'),
    ('TableS2b_Metabolomics.csv', 'TableS2b_selected_features_nmr_metabolomics.csv', 'Table S2b',
     'DeLong forward selection of NMR metabolomic features, by organ outcome',
     'Stepwise candidate features for the Nightingale NMR metabolomic panel with AUC and DeLong P value at each step.'),
    ('TableS2c_Biochemical_measures.csv', 'TableS2c_selected_features_blood_biochemistry.csv', 'Table S2c',
     'DeLong forward selection of blood biochemistry features, by organ outcome',
     'Stepwise candidate features for routine blood biochemistry with AUC and DeLong P value at each step.'),
    ('TableS2d_PRS.csv', 'TableS2d_selected_features_polygenic_risk.csv', 'Table S2d',
     'DeLong forward selection of polygenic risk scores, by organ outcome',
     'Stepwise candidate polygenic risk scores with AUC and DeLong P value at each step.'),
    ('TableS2e_Family_history.csv', 'TableS2e_selected_features_family_history.csv', 'Table S2e',
     'DeLong forward selection of family-history features, by organ outcome',
     'Stepwise candidate family-history variables with AUC and DeLong P value at each step.'),
    ('TableS2f_Lifestyle.csv', 'TableS2f_selected_features_lifestyle.csv', 'Table S2f',
     'DeLong forward selection of lifestyle features, by organ outcome',
     'Stepwise candidate lifestyle variables with AUC and DeLong P value at each step.'),
    ('TableS2g_Psychosocial.csv', 'TableS2g_selected_features_psychosocial.csv', 'Table S2g',
     'DeLong forward selection of psychosocial features, by organ outcome',
     'Stepwise candidate psychosocial variables with AUC and DeLong P value at each step.'),
    ('TableS2h_Brain_imaging.csv', 'TableS2h_selected_features_brain_imaging_EXPLORATORY.csv', 'Table S2h (exploratory)',
     'DeLong forward selection of brain-imaging features, by organ outcome (exploratory; not used in primary models)',
     'Imaging-derived phenotypes analysed separately because imaging follow-up starts later than the baseline visit; '
     'not included in the primary survival or fusion models.'),
    ('TableS3_mediation_all.csv', 'TableS3_mediation_pathways.csv', 'Table S3',
     'Causal mediation of healthy behaviour and psychological distress on organ failure through circulating biomarkers',
     'All significant exposure-organ-mediator pathways with natural indirect (ACME) and direct effects, proportion '
     'mediated and E-values; England participants with proteomics.'),
    ('TableS4_GO_enrichment_all.csv', 'TableS4_gene_ontology_enrichment.csv', 'Table S4',
     'Gene Ontology enrichment of organ-specific protein panels',
     'Biological process, cellular component and molecular function terms enriched among the proteins selected for '
     'each organ outcome (FDR < 0.05).'),
    ('pro/TableS7_PRS_abbreviations.csv', 'TableS7_polygenic_risk_score_abbreviations.csv', 'Table S7',
     'Polygenic risk scores: abbreviations, full names and source labels',
     'All 39 polygenic risk scores used in the polygenic-risk domain, with the abbreviation used in the figures '
     'and tables, the full trait name, trait category and the label in the source data.'),
    ('pro/TableS8_family_history_abbreviations.csv', 'TableS8_family_history_variable_names.csv', 'Table S8',
     'Family-history variables: UK Biobank fields, condition codes and full names',
     'All family-history features used in the family-history domain, with the UK Biobank field (20107 father, '
     '20110 mother, 20111 siblings), the shared condition code (Data-Coding 1010) and the corresponding disease name.'),
    ('TableS5_metabolite_mapping.csv', 'TableS5_metabolite_annotation.csv', 'Table S5',
     'Annotation of circulating metabolites measured by the Nightingale NMR platform',
     'Official biomarker names, descriptions, units, group and subgroup classification and UK Biobank field '
     'identifiers for the 325 NMR metabolites.'),
]

idx = []
for src, dst, num, title, desc in SPEC:
    s = os.path.join(T, src)
    if not os.path.exists(s):
        print('MISSING', src); continue
    shutil.copy2(s, os.path.join(OUT, dst))
    if src.endswith('.csv'):
        n = len(pd.read_csv(s))
    else:
        n = sum(len(pd.read_excel(s, sheet_name=sh)) for sh in pd.ExcelFile(s).sheet_names)
    idx.append(dict(Table=num, Title=title, Description=desc, File=dst,
                    Rows=n, Source=src.replace('pro/', 'tables/pro/')))

# ---------------- Table S6: 结局定义 ----------------
t1 = pd.read_csv(f'{T}/pro/Table1_main.csv')
prow = t1[t1.Characteristic.str.startswith('Participants')].iloc[0]
frow = t1[t1.Characteristic.str.startswith('Follow-up')].iloc[0]
DEF = [
    ('Heart failure', 'I50', 'Excluding I13 and I97', 'First recorded hospital diagnosis',
     'Heart failure', 'heart failure'),
    ('Respiratory failure', 'J96', '\u2014', 'First recorded hospital diagnosis',
     'Respiratory failure', 'respiratory failure'),
    ('Liver failure or cirrhosis', 'K72, K74', '\u2014', 'First recorded hospital diagnosis',
     'Liver failure/cirrhosis', 'liver failure/cirrhosis'),
    ('Kidney failure', 'N17, N19', '\u2014', 'First recorded hospital diagnosis',
     'Kidney failure', 'kidney failure'),
    ('Haematological failure', 'D68, D69 (D65 additionally available in the date-ascertained layer)',
     '\u2014', 'First recorded hospital diagnosis', 'Haematological failure', 'haematological failure'),
    ('Stroke', 'I60\u2013I64', '\u2014', 'UK Biobank national algorithms for stroke',
     'Stroke', 'stroke'),
    ('Any organ failure', 'First of the six events above', '\u2014', 'Composite of the six outcomes',
     'Any organ failure', 'any organ failure'),
]
rows = []
for outcome, codes, excl, source, col, key in DEF:
    rows.append(dict(Outcome=outcome, **{'ICD-10 codes': codes, 'Exclusions': excl,
                                         'Ascertainment': source,
                                         'Incident events, n (%)': prow[col],
                                         'Follow-up, median (IQR), years': frow[col]}))
s6 = pd.DataFrame(rows)
s6.to_csv(f'{OUT}/TableS6_outcome_definitions_and_followup.csv', index=False, encoding='utf-8-sig')
idx.append(dict(Table='Table S6',
                Title='Definitions, ICD-10 codes, ascertainment and follow-up of organ-failure outcomes',
                Description='Outcome definitions with ICD-10 code lists and exclusions, ascertainment source, number '
                            'of incident events and median follow-up. Prevalent disease and events occurring within the '
                            'first year after baseline (lag period) were not counted; follow-up was censored at death, '
                            'loss to follow-up or 31 October 2022.',
                File='TableS6_outcome_definitions_and_followup.csv', Rows=len(s6), Source='derived (Methods + Table 1)'))

# S2d: Feature 列改为 '全称 (PRS-缩写)'
_pm = pd.read_csv(os.path.join(T, 'pro', 'prs_abbr_map.csv'))
_map = dict(zip(_pm['PRS abbreviation'], _pm['Display']))
_hm = pd.read_csv(os.path.join(T, 'pro', 'history_name_map.csv'))
_hmap = dict(zip(_hm['Feature in data'], _hm['Display name']))
_s2e = f'{OUT}/TableS2e_selected_features_family_history.csv'
_e = pd.read_csv(_s2e)
_e['Feature'] = _e['Feature'].map(lambda x: _hmap.get(x, x))
_e.to_csv(_s2e, index=False, encoding='utf-8-sig')

_s2d = f'{OUT}/TableS2d_selected_features_polygenic_risk.csv'
_d = pd.read_csv(_s2d)
_d['Feature'] = _d['Feature'].map(lambda x: _map.get(x, x))
_d.to_csv(_s2d, index=False, encoding='utf-8-sig')

index = pd.DataFrame(idx)
index.to_csv(f'{OUT}/Tables_index.csv', index=False, encoding='utf-8-sig')

# ---------------- 合集 xlsx ----------------
with pd.ExcelWriter(f'{OUT}/Main_Tables.xlsx') as w:
    t1.to_excel(w, sheet_name='Table 1', index=False)
    ws = w.sheets['Table 1']
    for j in range(1, len(t1.columns) + 1):
        ws.column_dimensions[get_column_letter(j)].width = 34 if j == 1 else 17
    for c in ws[1]:
        c.font = Font(bold=True); c.alignment = Alignment(wrap_text=True, vertical='center')
    ws.freeze_panes = 'B2'
    # 追加表注(与 pro/Table1_main.xlsx 中一致)
    src = os.path.join(T, 'pro', 'Table1_main.xlsx')
    if os.path.exists(src):
        sws = pd.read_excel(src, sheet_name='Table1', header=None)
        notes = [str(v) for v in sws.iloc[len(t1) + 2:, 0].dropna().tolist()]
        for i, nt in enumerate(notes):
            c = ws.cell(row=len(t1) + 3 + i, column=1, value=nt)
            c.font = Font(size=9)

SHEETS = [('Table S1a', f'{OUT}/TableS1a_model_discrimination_long.csv'),
          ('Table S1c', f'{OUT}/TableS1c_analysis_populations.csv'),
          ('Table S2a', f'{OUT}/TableS2a_selected_features_proteomics.csv'),
          ('Table S2b', f'{OUT}/TableS2b_selected_features_nmr_metabolomics.csv'),
          ('Table S2c', f'{OUT}/TableS2c_selected_features_blood_biochemistry.csv'),
          ('Table S2d', f'{OUT}/TableS2d_selected_features_polygenic_risk.csv'),
          ('Table S2e', f'{OUT}/TableS2e_selected_features_family_history.csv'),
          ('Table S2f', f'{OUT}/TableS2f_selected_features_lifestyle.csv'),
          ('Table S2g', f'{OUT}/TableS2g_selected_features_psychosocial.csv'),
          ('Table S3', f'{OUT}/TableS3_mediation_pathways.csv'),
          ('Table S4', f'{OUT}/TableS4_gene_ontology_enrichment.csv'),
          ('Table S5', f'{OUT}/TableS5_metabolite_annotation.csv'),
          ('Table S6', f'{OUT}/TableS6_outcome_definitions_and_followup.csv'),
          ('Table S7', f'{OUT}/TableS7_polygenic_risk_score_abbreviations.csv'),
          ('Table S8', f'{OUT}/TableS8_family_history_variable_names.csv')]
with pd.ExcelWriter(f'{OUT}/Supplementary_Tables.xlsx') as w:
    for sh, path in SHEETS:
        pd.read_csv(path).to_excel(w, sheet_name=sh, index=False)
    for sh, path in SHEETS[:1]:
        pass
# 矩阵版作为单独 sheet 追加
with pd.ExcelWriter(f'{OUT}/Supplementary_Tables.xlsx', mode='a', if_sheet_exists='overlay') as w:
    for m in ['C-index', 'Full follow-up AUC']:
        pd.read_excel(f'{OUT}/TableS1b_model_discrimination_matrix.xlsx', sheet_name=m)\
          .to_excel(w, sheet_name=f'S1b {m[:12]}', index=False)

print('=== tables_final ===')
for _, r in index.iterrows():
    print(f"{r.Table:22s} {r.File:52s} rows={r.Rows}")
print('\nsaved: Main_Tables.xlsx, Supplementary_Tables.xlsx, Tables_index.md/.csv')

# ---------------- 目录 Markdown(含表注) ----------------
notes_t1 = []
_src = os.path.join(T, 'pro', 'Table1_main.xlsx')
if os.path.exists(_src):
    _w = pd.read_excel(_src, sheet_name='Table1', header=None)
    notes_t1 = [str(v) for v in _w.iloc[len(pd.read_csv(f'{T}/pro/Table1_main.csv')) + 2:, 0].dropna().tolist()]
L = ['# Tables \u2014 final set (result908)\n',
     'Version: diagnosis-label definitions with a one-year lag period; survival-layer outputs after the J96 '
     '(5-character subcode) fix.\n', '| Table | Title | File | Rows |', '|---|---|---|---|']
for _, r in index.iterrows():
    L.append(f'| **{r.Table}** | {r.Title} | `{r.File}` | {r.Rows} |')
L += ['\n## Descriptions\n']
for _, r in index.iterrows():
    L.append(f'**{r.Table}. {r.Title}**  \n{r.Description}  \nFile: `{r.File}` \u00b7 source: `{r.Source}` \u00b7 rows: {r.Rows}\n')
if notes_t1:
    L.append('## Table 1 footnote\n')
    L += [f'- {n}' for n in notes_t1]
L.append('\n## Bundles\n- `Main_Tables.xlsx` \u2014 Table 1 (single sheet, footnote included)\n'
         '- `Supplementary_Tables.xlsx` \u2014 Tables S1a, S1b (two matrices), S1c, S2a\u2013S2g, S3, S4, S5, S6\n')
L.append('## Naming conventions\n- Outcomes: heart failure; respiratory failure; liver failure/cirrhosis; kidney failure; '
         'haematological failure; stroke; composite any organ failure.\n- Data domains: proteomics; NMR metabolomics; '
         'blood biochemistry; polygenic risk score; family history; lifestyle; psychosocial (brain imaging exploratory only).\n')
open(f'{OUT}/Tables_index.md', 'w').write('\n'.join(L))
print('Tables_index.md regenerated (with Table 1 footnote)')
