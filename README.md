# Multi-domain pre-clinical prediction of severe organ failure (UK Biobank)

Code accompanying the manuscript **"Pre-clinical multi-domain profiling for the long-horizon
prediction of severe organ failure: a UK Biobank cohort study with external validation."**

Repository: <https://github.com/maochiyu24/ukb-organ-failure-prediction>

The repository contains the full analysis pipeline (data preparation, feature ranking, LightGBM
models, multimodal fusion, survival evaluation, causal mediation and GO/PPI annotation) and the
scripts that generate the main and supplementary figures and tables.

---

## 1. Study at a glance

| Item | Value |
|---|---|
| Cohort | 492,904 UK Biobank participants free of prevalent organ failure and of any organ event during a one-year lag period |
| Outcomes | Incident severe failure of six organ systems (heart, respiratory, liver, kidney, haematological, stroke) and the composite *any organ failure* |
| Follow-up | Median 13.7 years; censoring 31 October 2022 |
| Events | 52,283 any organ failure (10.6%); kidney 24,800; heart 16,616; stroke 12,064; respiratory 8,283; haematological 5,690; liver 2,722 |
| Development / external validation | England (437,461) and Scotland plus Wales (55,443) |
| Data domains | Proteomics, NMR metabolomics, blood biochemistry, polygenic risk scores, family history, lifestyle, psychosocial (imaging exploratory only) |
| Multimodal fusion cohort | Seven-domain measurement intersection: 29,370 (26,871 / 2,499) |
| Mediation cohort | 45,718 English participants with complete exposure, mediator and covariate data (proteomics panel) |
| Key analysis outputs | 313 significant mediation pathways; 1,988 enriched Gene Ontology terms; discrimination quantified by Harrell C-index and AUC with 1,000-bootstrap 95% CIs |

---

## 2. Repository layout

```text
.
|-- README.md
|-- LICENSE
|-- CITATION.cff
|-- requirements.txt
|-- environment.yml
|-- docs/
|   |-- REPRODUCIBILITY.md
|   `-- GITHUB_UPLOAD_WORKFLOW.md
|-- tools/
|   |-- run_all.sh
|   `-- make_manuscript_docx.py
`-- src/
    |-- config.py
    |-- naming.py
    |-- style.py
    |-- delong.py
    |-- 00_check_labels.py
    |-- 00_tune/
    |-- 01_prep/
    |-- 02_ranking/
    |-- 03_model/
    |-- 04_fusion/
    |-- 05_survival/
    |-- 06_mediation/
    |-- figures/
    `-- tables/
```

`src/config.py` holds analysis constants, ICD definitions and model parameters.

---

## 3. Data

The UK Biobank data are **not** included in this repository and cannot be redistributed. Access
requires an approved UK Biobank application; this study was conducted under **UK Biobank
Application 347405**. No participant-level data are included or publicly available.

The code is designed to run against a local, access-controlled analysis environment. Input files
must be obtained by the user through UK Biobank; no data or project-specific paths are shipped with
this repository.

---

## 4. Installation

```bash
git clone https://github.com/maochiyu24/ukb-organ-failure-prediction.git
cd ukb-organ-failure-prediction
conda env create -f environment.yml      # or: pip install -r requirements.txt
conda activate ukb-organ-failure
```

* Python 3.11.6 (tested). `scikit-survival` is required for the survival analyses
  (`pip install scikit-survival==0.28.0`); if it is installed into a separate directory, add that
  directory to `PYTHONPATH`.
* R >= 4.5 with the `mediation` package (4.5.1 tested) is required only for the causal mediation
  step (`src/06_mediation`).

---

## 5. Running the pipeline

Run the scripts in order from the repository root. Each stage consumes the outputs of the preceding
stage from the local analysis workspace configured by the user.

```bash
# 1) per-modality analysis matrices (incident-only labels, one-year lag)
python src/01_prep/prep_data.py

# 2) feature ranking and DeLong forward selection
python src/02_ranking/feature_ranking.py            # use --organ/--modality for parallel runs

# 3) per-modality LightGBM models and external validation
python src/03_model/train_model.py

# 4) multimodal fusion models (seven-domain intersection cohort)
python src/04_fusion/merge_fusion.py

# 5) survival data, C-index / time-dependent AUC, Kaplan-Meier, subgroups
python src/05_survival/01_build_survival_data.py
python src/05_survival/02_survival_metrics.py
python src/05_survival/02b_merge_survival_metrics.py
python src/05_survival/06_subgroup.py

# 6) causal mediation
python src/06_mediation/09_build_exposure_v2.py
python src/06_mediation/10_prep_mediation_v2.py
Rscript src/06_mediation/run_mediation_v2.R
python src/06_mediation/08_mediation_evalue.py

# 7) figures and tables
python src/figures/fig1_panels_runin.py
python src/figures/fig3_performance.py
python src/figures/fig5_subgroup_metrics.py
python src/figures/fig5cd_subgroup_forest.py
python src/tables/gen_table_s1.py
python src/tables/gen_tables_supplementary.py
```

A convenience wrapper is provided in `tools/run_all.sh`. Figure scripts are independent so that
individual panels can be regenerated.

---

## 6. Reproducibility notes

* Random seed **42** throughout (cross-validation, bootstrap); all confidence intervals use
  **1,000 bootstrap resamples**.
* Feature selection: hierarchical clustering on Spearman correlations (Ward linkage on
  `1 - |rho|`, distance threshold 0.5); 10-fold single-feature AUC; ensemble importance = mean of
  `|SHAP|` and total gain; top-90% cumulative importance retained; DeLong forward selection with
  *P* < 0.05, minimum 50 evaluation steps, stop after 5 consecutive non-significant steps, at most
  100 candidates.
* LightGBM: learning rate 0.01, 300 trees, 31 leaves, balanced class weights, subsample 0.7,
  5-fold internal cross-validation; external validation held out by region (Scotland and Wales).
* Mediation: quasi-Bayesian Monte-Carlo intervals from the R `mediation` package (1,000
  simulations), adjusted for age, sex and Townsend deprivation index; E-values for the mediation
  effect.
* Software versions, package list and exact parameters are given in
  [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md).

---

## 7. Citation

If you use this code, please cite the manuscript (citation will be updated on publication) and this
repository; a `CITATION.cff` file is provided.

---

## 8. Licence and contact

Released under the MIT Licence (see `LICENSE`). Data use is governed by the UK Biobank access terms.
Questions: yilitao0420@163.com; ffjin@njucm.edu.cn.
