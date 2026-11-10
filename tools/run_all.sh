#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Example end-to-end run for the UK Biobank organ-failure prediction pipeline.
# Edit the three environment variables below before running.
# Runtime: several hours on 28 CPU cores (dominated by feature ranking,
# 56 organ x domain models, and the R mediation step).
# ---------------------------------------------------------------------------
set -euo pipefail

export UKB_PROJECT_ROOT="${UKB_PROJECT_ROOT:-/data/ukb_organ_failure}"
export OF_RESULT_DIR="${OF_RESULT_DIR:-$UKB_PROJECT_ROOT/result/of903}"
export OF_INCIDENT_ONLY=1        # incident-only labels with a one-year lag
export PYTHONPATH="$UKB_PROJECT_ROOT/src:${PYTHONPATH:-}"

PY=${PYTHON:-python}
RSCRIPT=${RSCRIPT:-Rscript}
mkdir -p "$OF_RESULT_DIR"
mkdir -p "$UKB_PROJECT_ROOT/cache"

echo "[1/8] Data preparation (per-modality matrices, incident-only labels)"
$PY src/01_prep/prep_data.py

echo "[2/8] Feature ranking and DeLong forward selection"
$PY src/02_ranking/feature_ranking.py

echo "[3/8] Per-modality LightGBM models and external validation"
$PY src/03_model/train_model.py

echo "[4/8] Multimodal fusion models"
$PY src/04_fusion/merge_fusion.py

echo "[5/8] Survival analysis"
$PY src/05_survival/01_build_survival_data.py
$PY src/05_survival/02_survival_metrics.py
$PY src/05_survival/02b_merge_survival_metrics.py
$PY src/05_survival/06_subgroup.py

echo "[6/8] Causal mediation"
$PY src/06_mediation/09_build_exposure_v2.py
$PY src/06_mediation/10_prep_mediation_v2.py
# R mediation: run one organ per process (memory/CPU permitting)
for organ in heart lung liver renal hemat brain organ; do
  $RSCRIPT src/06_mediation/run_mediation_v2.R --organ "$organ" --sims 1000 --ncpus 4 &
done
wait
$PY src/06_mediation/08_mediation_evalue.py

echo "[7/8] Figures (main panels; see README for the full list)"
$PY src/figures/fig1_panels_runin.py
$PY src/figures/fig2_protein_importance.py
$PY src/figures/fig3_performance.py
$PY src/figures/fig5_subgroup_metrics.py
$PY src/figures/fig5cd_subgroup_forest.py
$PY src/figures/figS1_flowchart.py

echo "[8/8] Tables"
$PY src/tables/gen_table1.py
$PY src/tables/gen_table_s1.py
$PY src/tables/gen_tables_supplementary.py
$PY src/tables/gen_prs_abbreviations.py
$PY src/tables/gen_family_history_names.py
$PY src/tables/organize_tables.py

echo "Done. Outputs are under $OF_RESULT_DIR and $UKB_PROJECT_ROOT/result/result906/"
