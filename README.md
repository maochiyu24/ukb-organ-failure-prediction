# Multi-domain pre-clinical prediction of severe organ failure (UK Biobank)

Core training and evaluation code accompanying the manuscript:

**"Pre-clinical multi-domain profiling for the long-horizon prediction of severe organ failure:
a UK Biobank cohort study with external validation."**

Repository: <https://github.com/maochiyu24/ukb-organ-failure-prediction>

This release contains the main model-development and evaluation pipeline only. Plotting,
table-generation, manuscript-generation, mediation and other auxiliary analysis scripts are not
included.

---

## Contents

| Path | Purpose |
|---|---|
| `src/config.py` | Analysis constants, ICD definitions and model parameters |
| `src/delong.py` | DeLong test for correlated ROC curves |
| `src/00_tune/tune_modality.py` | Per-modality LightGBM tuning |
| `src/01_prep/prep_data.py` | Build per-modality analysis matrices |
| `src/02_ranking/feature_ranking.py` | Feature ranking and DeLong forward selection |
| `src/03_model/train_model.py` | Per-modality LightGBM training and external validation |
| `src/04_fusion/merge_fusion.py` | Multimodal fusion models |
| `src/05_survival/01_build_survival_data.py` | Build survival analysis data |
| `src/05_survival/02_survival_metrics.py` | C-index, time-dependent AUC and survival metrics |
| `src/05_survival/02b_merge_survival_metrics.py` | Merge survival metric outputs |
| `src/05_survival/06_subgroup.py` | Sex and age subgroup evaluation |
| `src/05_survival/sksurv_load.py` | Survival data loading helper |

---

## Data

The UK Biobank data are **not** included in this repository and cannot be redistributed. Access
requires an approved UK Biobank application; this study was conducted under **UK Biobank
Application 347405**. No participant-level data are included or publicly available.

The code is designed to run against a local, access-controlled analysis environment. Input files
must be obtained by the user through UK Biobank.

---

## Installation

```bash
git clone https://github.com/maochiyu24/ukb-organ-failure-prediction.git
cd ukb-organ-failure-prediction
conda env create -f environment.yml      # or: pip install -r requirements.txt
conda activate ukb-organ-failure
```

* Python 3.11.6 (tested).
* `scikit-survival` is required for survival analyses
  (`pip install scikit-survival==0.28.0`).

---

## Running the core pipeline

```bash
python src/00_tune/tune_modality.py
python src/01_prep/prep_data.py
python src/02_ranking/feature_ranking.py
python src/03_model/train_model.py
python src/04_fusion/merge_fusion.py
python src/05_survival/01_build_survival_data.py
python src/05_survival/02_survival_metrics.py
python src/05_survival/02b_merge_survival_metrics.py
python src/05_survival/06_subgroup.py
```

Scripts are run in order from the repository root and read the outputs of preceding stages from
the local analysis workspace.

---

## Citation and licence

If you use this code, please cite the manuscript and this repository; a `CITATION.cff` file is
provided. Released under the MIT Licence (see `LICENSE`). Data use is governed by the UK Biobank
access terms.

Questions: yilitao0420@163.com; ffjin@njucm.edu.cn.
