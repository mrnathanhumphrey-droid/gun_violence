// Production v0.2 — extends v0.1 with race×inequity + geo×inequity interactions
//
// Adds to v0.1:
//   - race_x_inequity: pct_black × composite_mean interaction (fixed effect)
//   - geo_type fixed effects (urban / suburban / rural, baseline = rural)
//   - geo_type × inequity interaction
//   - per-unit log-rate components saved separately in generated quantities
//     to enable variance decomposition for §6 hypothesis dispositions
//
// Skipped from full §8 spec (data unavailable on disk):
//   - HOLC redlining (no county shapefile to join HOLC polygons against)
//   - Sundown towns (raw HTML page, not parsed)
//   - VRA preclearance (directory empty)
//   - Per-geo reporting-rate adjustment (no calibration data)
data {
  int<lower=1> N;
  int<lower=1> C;          // number of cells (8)
  int<lower=1> K;          // number of plain fixed-effect predictors
  int<lower=1> G;          // number of geo types (3: urban=1, suburban=2, rural=3)
  array[N] int<lower=1, upper=C> cell;
  array[N] int<lower=1, upper=G> geo_type;
  array[N] int<lower=0> deaths;
  vector[N] log_exposure;
  matrix[N, K] X;
  vector[N] inequity;           // standardized inequity composite
  vector[N] race_centered;      // standardized pct_black (centered + scaled)
}
parameters {
  real alpha;                              // grand intercept
  vector[C] alpha_cell_raw;                // non-centered cell intercept
  real<lower=0> sigma_cell;

  vector[C] beta_inequity_cell_raw;        // non-centered cell-level inequity slope
  real mu_beta_inequity;
  real<lower=0> sigma_beta_inequity;

  vector[K] beta;                          // plain fixed-effect predictor coefs

  // Interactions
  real beta_race_x_ineq;                   // pct_black × inequity (fixed)
  vector[G - 1] beta_geo;                  // urban / suburban offsets (rural = baseline 0)
  vector[G - 1] beta_geo_x_ineq;           // geo × inequity offsets (rural baseline 0)

  real<lower=0> phi;                       // dispersion
}
transformed parameters {
  vector[C] alpha_cell = sigma_cell * alpha_cell_raw;
  vector[C] beta_inequity_cell = mu_beta_inequity + sigma_beta_inequity * beta_inequity_cell_raw;

  // Geo full vectors with rural=0
  vector[G] beta_geo_full;
  vector[G] beta_geo_x_ineq_full;
  beta_geo_full[1] = beta_geo[1];          // urban
  beta_geo_full[2] = beta_geo[2];          // suburban
  beta_geo_full[3] = 0.0;                  // rural baseline
  beta_geo_x_ineq_full[1] = beta_geo_x_ineq[1];
  beta_geo_x_ineq_full[2] = beta_geo_x_ineq[2];
  beta_geo_x_ineq_full[3] = 0.0;
}
model {
  alpha ~ normal(-8, 3);
  alpha_cell_raw ~ std_normal();
  sigma_cell ~ exponential(1);
  beta_inequity_cell_raw ~ std_normal();
  mu_beta_inequity ~ normal(0, 1);
  sigma_beta_inequity ~ exponential(2);
  beta ~ normal(0, 1);
  beta_race_x_ineq ~ normal(0, 1);
  beta_geo ~ normal(0, 1);
  beta_geo_x_ineq ~ normal(0, 1);
  phi ~ exponential(0.1);

  vector[N] log_mu;
  for (n in 1:N) {
    log_mu[n] = alpha
              + alpha_cell[cell[n]]
              + beta_inequity_cell[cell[n]] * inequity[n]
              + X[n] * beta
              + beta_race_x_ineq * race_centered[n] * inequity[n]
              + beta_geo_full[geo_type[n]]
              + beta_geo_x_ineq_full[geo_type[n]] * inequity[n]
              + log_exposure[n];
  }
  deaths ~ neg_binomial_2_log(log_mu, phi);
}
generated quantities {
  vector[N] log_lik;
  array[N] int<lower=0> deaths_rep;

  // Decomposed log-mu components (for variance decomposition post-hoc)
  vector[N] eta_cell;        // alpha_cell + grand intercept (cell baseline contribution)
  vector[N] eta_inequity;    // cell-specific inequity slope × inequity
  vector[N] eta_race;        // race-related: pct_black main effect (part of X*beta) + race×ineq
  vector[N] eta_geo;         // geo main + geo×ineq
  vector[N] eta_ses;         // remaining SES covariates (X*beta minus pct_black)

  // To decompose X*beta, need pct_black index. Convention: race_centered IS pct_black
  // (standardized version), and beta[1] is pct_black's coef. SES = beta[2..K] terms.
  for (n in 1:N) {
    real lm = alpha
            + alpha_cell[cell[n]]
            + beta_inequity_cell[cell[n]] * inequity[n]
            + X[n] * beta
            + beta_race_x_ineq * race_centered[n] * inequity[n]
            + beta_geo_full[geo_type[n]]
            + beta_geo_x_ineq_full[geo_type[n]] * inequity[n]
            + log_exposure[n];
    log_lik[n] = neg_binomial_2_log_lpmf(deaths[n] | lm, phi);
    deaths_rep[n] = neg_binomial_2_log_rng(lm, phi);

    eta_cell[n]     = alpha + alpha_cell[cell[n]];
    eta_inequity[n] = beta_inequity_cell[cell[n]] * inequity[n];
    eta_race[n]     = X[n, 1] * beta[1] + beta_race_x_ineq * race_centered[n] * inequity[n];
    eta_geo[n]      = beta_geo_full[geo_type[n]]
                    + beta_geo_x_ineq_full[geo_type[n]] * inequity[n];
    real ses = 0;
    for (k in 2:K) ses += X[n, k] * beta[k];
    eta_ses[n] = ses;
  }
}
