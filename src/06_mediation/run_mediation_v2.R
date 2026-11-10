#!/usr/bin/env Rscript
# 中介分析（R mediation 包）
# 用法: Rscript run_mediation.R --organ heart --exposure lifestyle --mediators omics --sims 1000
#       Rscript run_mediation.R --organ all --exposure all --mediators all
suppressMessages({
  library(mediation)
  library(parallel)
})

args <- commandArgs(trailingOnly = TRUE)
get_arg <- function(key, default = NULL) {
  i <- match(key, args)
  if (is.na(i)) default else args[i + 1]
}
organ_arg <- get_arg('--organ', 'all')
expo_arg  <- get_arg('--exposure', 'all')
med_arg   <- get_arg('--mediators', 'all')
sims      <- as.integer(get_arg('--sims', '1000'))
ncpus     <- as.integer(get_arg('--ncpus', '10'))

# Paths are read from environment variables (see README / src/config.py)
PROJECT_ROOT <- Sys.getenv('UKB_PROJECT_ROOT', unset = normalizePath('..'))
RESULT_DIR   <- Sys.getenv('OF_RESULT_DIR', unset = file.path(PROJECT_ROOT, 'result', 'of903'))
DATA_DIR <- file.path(RESULT_DIR, '06_mediation_v2', 'data')
OUT_DIR  <- file.path(RESULT_DIR, '06_mediation_v2')
dir.create(OUT_DIR, showWarnings = FALSE)

ORGANS <- c('heart', 'lung', 'liver', 'renal', 'hemat', 'organ')
EXPOSURES <- c('lifestyle_score_v2', 'psych_score_v2')
COV <- c('Age', 'Sex', 'Townsend')

run_one <- function(df, expos, mediator, outcome, organ, label) {
  d <- df[complete.cases(df[, c(expos, mediator, outcome, COV)]), ]
  if (sum(d[[outcome]]) < 20 || nrow(d) < 200) {
    return(NULL)
  }
  f_med <- as.formula(paste(mediator, '~', paste(c(expos, COV), collapse = '+')))
  f_out <- as.formula(paste(outcome, '~', paste(c(expos, mediator, COV), collapse = '+')))
  med.fit <- lm(f_med, data = d)
  out.fit <- glm(f_out, data = d, family = binomial())
  med.out <- tryCatch(
    mediate(med.fit, out.fit, treat = expos, mediator = mediator,
            boot = FALSE, sims = sims, parallel = 'multicore', ncpus = ncpus),
    error = function(e) NULL)
  if (is.null(med.out)) return(NULL)
  s <- summary(med.out)
  data.frame(
    Organ = organ, Exposure = expos, Mediator = mediator, Set = label,
    N = nrow(d), N_pos = sum(d[[outcome]]),
    ACME = med.out$d0, ACME_lo = med.out$d0.ci[1], ACME_hi = med.out$d0.ci[2],
    ADE = med.out$z0, ADE_lo = med.out$z0.ci[1], ADE_hi = med.out$z0.ci[2],
    Prop_mediated = med.out$n0, PM_lo = med.out$n0.ci[1], PM_hi = med.out$n0.ci[2],
    ACME_p = s$d0.p, ADE_p = s$z0.p
  )
}

organs <- if (organ_arg == 'all') ORGANS else organ_arg
exposures <- if (expo_arg == 'all') EXPOSURES else expo_arg
cat(sprintf('参数: organs=%s exposures=%s sims=%d ncpus=%d\n',
            paste(organs, collapse = ','), paste(exposures, collapse = ','), sims, ncpus))

all_rows <- list()
for (organ in organs) {
  f <- file.path(DATA_DIR, paste0(organ, '_mediation_v2.csv'))
  if (!file.exists(f)) { cat('跳过:', organ, '(无数据)\n'); next }
  df <- read.csv(f, check.names = FALSE)
  names(df)[names(df) == 'Townsend deprivation index at recruitment'] <- 'Townsend'
  outcome <- if (organ == 'organ') 'organ_failure' else paste0(organ, '_failure')
  cat(sprintf('\n=== %s (n=%d, 阳性=%d) ===\n', organ, nrow(df), sum(df[[outcome]])))

  omics_cols <- grep('^(proteome|metabolome)__', names(df), value = TRUE)
  blood_cols <- grep('^blood__', names(df), value = TRUE)
  med_sets <- list()
  if (med_arg %in% c('all', 'omics')) med_sets[['omics']] <- omics_cols
  if (med_arg %in% c('all', 'blood')) med_sets[['blood']] <- blood_cols

  for (expo in exposures) {
    for (set_name in names(med_sets)) {
      cols <- med_sets[[set_name]]
      for (m in cols) {
        r <- run_one(df, expo, m, outcome, organ, set_name)
        if (!is.null(r)) {
          all_rows[[length(all_rows) + 1]] <- r
          cat(sprintf('  %-22s %-10s %-10s ACME=%.4f(p=%.3f) PM=%.3f\n',
                      m, expo, set_name, r$ACME, r$ACME_p, r$Prop_mediated))
        }
      }
    }
  }
}

if (length(all_rows) > 0) {
  res <- do.call(rbind, all_rows)
  out_csv <- file.path(OUT_DIR, paste0('mediation_results_', organ_arg, '_', expo_arg, '_', med_arg, '.csv'))
  write.csv(res, out_csv, row.names = FALSE)
  cat(sprintf('\n✅ 完成: %d 条结果 -> %s\n', nrow(res), out_csv))
} else {
  cat('\n无结果\n')
}
