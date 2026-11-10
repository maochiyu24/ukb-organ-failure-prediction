# Multi-domain pre-clinical prediction of severe organ failure (UK Biobank)

Code accompanying the manuscript **"Pre-clinical multi-domain profiling for the long-horizon
prediction of severe organ failure: a UK Biobank cohort study with external validation."**

Repository: <https://github.com/maochiyu24/ukb-organ-failure-prediction>

The repository contains the full analysis pipeline (data preparation -> feature ranking ->
LightGBM models -> multimodal fusion -> survival evaluation -> causal mediation -> GO/PPI
annotation) and the scripts that generate every main and supplementary figure and table.

---

## 1. Study at a glance

| Item | Value |
|---|---|
| Cohort | 492,904 UK Biobank participants free of prevalent organ failure and of any organ event during a one-year lag period |
| Outcomes | Incident severe failure of six organ systems (heart, respiratory, liver, kidney, haematological, stroke) and the composite *any organ failure* |
| Follow-up | Median 13.7 years; censoring 31 October 2022 |
| Events | 52,283 any organ failure (10.6%); kidney 24,800; heart 16,616; stroke 12,064; respiratory 8,283; haematological 5,690; liver 2,722 |
| Development / external validation | England (437,461) -> Scotland and Wales (55,443) |
| Data domains | Proteomics, NMR metabolomics, blood biochemistry, polygenic risk scores, family history, lifestyle, psychosocial (imaging exploratory only) |
| Multimodal fusion cohort | Seven-domain measurement intersection: 29,370 (26,871 / 2,499) |
| Mediation cohort | 45,718 English participants with complete exposure, mediator and covariate data (proteomics panel) |
| Key analysis outputs | 313 significant mediation pathways; 1,988 enriched Gene Ontology terms; discrimination quantified by Harrell C-index and AUC with 1,000-bootstrap 95% CIs |

---

## 2. Repository layout

```text
.
|-- README.md
|-- LICENSE                      MIT
|-- CITATION.cff
|-- requirements.txt             pinned Python packages (Python 3.11.6)
|-- environment.yml              conda environment (incl. R 4.5 / r-mediation)
|-- docs/
|   |-- REPRODUCIBILITY.md       software versions, seeds, parameters
|   `-- GITHUB_UPLOAD_WORKFLOW.md
|-- tools/
|   |-- run_all.sh               end-to-end example run
|   `-- make_manuscript_docx.py  assembles the manuscript from Markdown sources
`-- src/
    |-- config.py                central paths / ICD definitions / model parameters
    |-- naming.py                display-name utilities (organs, proteins, metabolites)
    |-- style.py                 shared figure style
    |-- delong.py                DeLong test implementation
    |-- 00_check_labels.py       label-consistency checks against the diagnosis matrix
    |-- 00_tune/                 per-modality LightGBM tuning
    |-- 01_prep/                 build per-modality analysis matrices (incident-only labels)
    |-- 02_ranking/              clustering -> single-feature AUC -> SHAP/gain -> DeLong forward selection
    |-- 03_model/                per organ x domain LightGBM models and external validation
    |-- 04_fusion/               multimodal fusion models (seven-domain intersection cohort)
    |-- 05_survival/             survival data build, C-index/tdAUC, KM, subgroup analyses
    |-- 06_mediation/            exposure scores, mediation models, E-values
    |-- figures/                 Fig. 1-5 and Fig. S1-S4 generation/assembly
    `-- tables/                  Table 1 and supplementary tables S1-S7
```

---

## 3. Data access and input files

The UK Biobank data are **not** included in this repository and cannot be redistributed. Access
requires an approved UK Biobank application; this study was conducted under **UK Biobank
Application 347405**.

Input files are read from the project root; the exact paths expected by each script are defined in
`src/config.py` (modality matrices, diagnosis matrix, baseline characteristics, hospital diagnoses,
death register and region classification). The pipeline expects a project root that contains the
data tree:

```text
$UKB_PROJECT_ROOT/
|-- xm/            # UK Biobank-derived inputs (paths defined in src/config.py)
|-- result/        # analysis outputs
`-- cache/         # intermediate caches created by the pipeline
```

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

## 5. Configuration

All paths are controlled by environment variables (see `src/config.py`):

| Variable | Meaning | Default |
|---|---|---|
| `UKB_PROJECT_ROOT` | Project root containing `xm/`, `result/` and `cache/` | parent directory of the repository |
| `UKB_XM_DIR` | Directory with UK Biobank-derived inputs | `$UKB_PROJECT_ROOT/xm` |
| `OF_RESULT_DIR` | Directory for pipeline outputs (mirrors `result/of903`) | `$UKB_PROJECT_ROOT/result/of903` |
| `OF_INCIDENT_ONLY` | Use incident-only labels with a one-year lag (`1`, the analysis used in the paper) | `1` |

Example:

```bash
export UKB_PROJECT_ROOT=/data/ukb_organ_failure
export OF_RESULT_DIR=$UKB_PROJECT_ROOT/result/of903
export OF_INCIDENT_ONLY=1
```

---

## 6. Running the pipeline

The scripts are intended to be run in order; each stage reads the previous stage's outputs from
`$OF_RESULT_DIR`. Approximate runtimes assume 28 CPU cores.

```bash
# 1) per-modality analysis matrices (incident-only labels, one-year lag)
python src/01_prep/prep_data.py

# 2) feature ranking and DeLong forward selection (per organ x domain)
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

# 6) causal mediation (exposure scores -> circulating mediators -> organ outcomes)
python src/06_mediation/09_build_exposure_v2.py
python src/06_mediation/10_prep_mediation_v2.py
Rscript src/06_mediation/run_mediation_v2.R          # see docs; runs per organ in parallel
python src/06_mediation/08_mediation_evalue.py

# 7) figures and tables
python src/figures/fig1_panels_runin.py              # final Fig. 1 panels (run-in basis)
python src/figures/fig3_performance.py               # Fig. 3
python src/figures/fig5_subgroup_metrics.py          # subgroup cache for Fig. 5C/D
python src/figures/fig5cd_subgroup_forest.py         # Fig. 5C/D and Fig. S4G/H
python src/tables/gen_table_s1.py                    # Table S1
python src/tables/gen_tables_supplementary.py        # Tables S2-S5
```

A convenience wrapper is provided in `tools/run_all.sh`. The figure scripts are deliberately
independent (each writes a single panel/PDF+PNG) so that individual panels can be regenerated; the
output paths mirror the original project layout (`$UKB_PROJECT_ROOT/result/result906/panels`,
`figures_supp`, `tables`).

---

## 7. Reproducibility notes

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

## 8. Citation

If you use this code, please cite the manuscript (citation will be updated on publication) and this
repository; a `CITATION.cff` file is provided.

---

## 9. Licence and contact

Released under the MIT Licence (see `LICENSE`). Data use is governed by the UK Biobank access terms.
Questions: yilitao0420@163.com; ffjin@njucm.edu.cn.
