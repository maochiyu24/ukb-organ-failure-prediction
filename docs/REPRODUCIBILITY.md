# Software versions and parameters

## Python (3.11.6, tested)

| Package | Version |
|---|---|
| numpy | 2.4.6 |
| pandas | 2.3.3 |
| scipy | 1.17.1 |
| scikit-learn | 1.9.0 |
| lightgbm | 4.7.0 |
| shap | 0.51.0 |
| scikit-survival | 0.28.0 |
| lifelines | 0.30.3 |
| statsmodels | 0.14.6 |
| joblib | 1.5.3 |
| matplotlib | 3.11.1 |
| seaborn | 0.13.2 |
| openpyxl | 3.1.5 |
| pypdf | 6.18.0 |
| pypdfium2 | 5.13.0 |
| python-docx | 1.2.0 |

Figure assembly and PDF composition were additionally tested with Python 3.9.25 (matplotlib 3.9.4,
seaborn 0.13.2, Pillow 11.3.0, pypdf 6.18.0, pypdfium2 5.13.0).

## R (4.5.3, for mediation only)

* `mediation` 4.5.1 (MASS 7.3.66, sandwich 3.1.2, data.table 1.18.4).

## Analysis parameters

| Step | Setting |
|---|---|
| Random seed | 42 (all CV splits, bootstrap, permutation) |
| Development / validation | England (Region 1) vs Scotland + Wales (Region 2–3) |
| Lag period | 1 year after baseline; events in this window not counted, participants with only a first-year event excluded |
| Censoring | death, loss to follow-up, or 31 October 2022 |
| Redundancy clustering | Spearman correlation, Ward linkage on 1 − \|ρ\|, distance threshold 0.5 |
| Single-feature AUC | 10-fold CV, LightGBM with balanced class weights |
| Ensemble importance | mean of \|SHAP\| and total gain (10-fold CV) |
| Candidate retention | features accumulating top 90% of importance |
| DeLong forward selection | P < 0.05 vs previous step; ≥50 steps evaluated; stop after 5 consecutive non-significant steps; ≤100 candidates |
| LightGBM | lr 0.01, 300 trees, 31 leaves, balanced, subsample 0.7; 5-fold internal CV |
| Multimodal fusion | seven-domain measurement intersection (29,370; 26,871 / 2,499); grid-search CV |
| Performance metrics | Harrell C-index; full-follow-up AUC; time-dependent AUC at 3/5/10 years; 1,000 bootstrap 95% CIs |
| Subgroups | age <60/≥60 years; sex |
| Mediation | England, proteomics, both exposure scores (45,718 complete-case for proteomics); linear mediator model, logistic outcome model, age/sex/Townsend adjustment; `mediation::mediate`, 1,000 simulations; ACME, ADE, proportion mediated; E-values |
| GO enrichment | per-organ top-50 ensemble-ranked proteins; hypergeometric test against measured proteome; Benjamini–Hochberg FDR < 0.05 |
| PPI | STRING, top-100 ensemble-ranked proteins per organ; degree-based hubs |

## TRIPOD+AI mapping (checklist item → where addressed)

| Item | Location |
|---|---|
| Study design, setting, dates | Methods 2.1; `src/05_survival/01_build_survival_data.py` |
| Participants, eligibility, exclusions | Methods 2.1; `src/01_prep/prep_data.py` |
| Outcome definitions | Methods 2.2; `src/config.py` (`ORGAN_ICD`) |
| Predictors | Methods 2.3; `src/01_prep/prep_data.py` |
| Sample size / events | Methods 2.1; Tables 1 and S1 |
| Missing data | Methods 2.3–2.4; `src/01_prep/prep_data.py` |
| Model development | Methods 2.5–2.6; `src/02_ranking`, `src/03_model`, `src/04_fusion` |
| Model performance | Methods 2.7; `src/05_survival`, Table S1, Fig. 3 |
| Fairness / subgroups | Methods 2.7; `src/05_survival/06_subgroup.py`, Fig. 5C/D, Fig. S4 |
| Interpretation / clinical use | Discussion 4.4 |
| Registration / protocol | Data availability statement |
| Code and data availability | README (repository structure, data layout, software) |
