#!/usr/bin/env bash
# Install the R packages required for the causal mediation step.
# Requires R >= 4.5 (tested with R 4.5.3 and mediation 4.5.1).
set -euo pipefail
RSCRIPT=${RSCRIPT:-Rscript}
"$RSCRIPT" -e 'install.packages(c("mediation", "MASS", "sandwich", "data.table"),
                                 repos = "https://cloud.r-project.org", Ncpus = 4)'
"$RSCRIPT" -e 'cat("mediation", as.character(packageVersion("mediation")), "\n")'
