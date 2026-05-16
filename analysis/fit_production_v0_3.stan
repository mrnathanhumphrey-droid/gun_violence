// Production v0.3 — extends v0.2 with historical mechanism markers (HOLC + VRA)
//
// Adds to v0.2:
//   - holc_share_D       (continuous, county share of HOLC area in D-grade, 0 for non-HOLC)
//   - holc_any           (binary, 1 if any HOLC zone in county)
//   - vra_section4b      (binary, 1 if county was under VRA §4(b) preclearance pre-Shelby)
//
// Generated quantities additionally save eta_history per unit for H_HISTORICAL_MECHANISM
// variance-share computation.
//
// Skipped from full §8 spec (data not on disk):
//   - Sundown towns (HTML scrape pending v0.4)
//   - Per-geo reporting-rate adjustment (no NVDRS data on disk)
data {
  int<lower=1> N;
  int<lower=1> C;          // cells (8)
  int<lower=1> K;          // plain fixed-effect predictors (pct_black + 6 SES)
  int<lower=1> G;          // geo types (3: urban=1, suburban=2, rural=3)
  array[N] int<lower=1, upper=C> cell;
  array[N] int<lower=1, upper=G> geo_type;
  array[N] int<lower=0> deaths;
  vector[N] log_exposure;
  matrix[N, K] X;
  vector[N] inequity;
  vector[N] race_centered;

  // v0.3 historical mechanism features
  vector[N] holc_share_D;       // continuous, [0, 1]
  vector[N] holc_any;           // binary 0/1
  vector[N] vra_section4b;      // binary 0/1
}
parameters {
  real alpha;
  vector[C] alpha_cell_raw;
  real<lower=0> sigma_cell;

  vector[C] beta_inequity_cell_raw;
  real mu_beta_inequity;
  real<lower=0> sigma_beta_inequity;

  vector[K] beta;
  real beta_race_x_ineq;
  vector[G - 1] beta_geo;
  vector[G - 1] beta_geo_x_ineq;

  // v0.3 historical
  real beta_holc_share_D;
  real beta_holc_any;
  real beta_vra;

  real<lower=0> phi;
}
transformed parameters {
  vector[C] alpha_cell = sigma_cell * alpha_cell_raw;
  vector[C] beta_inequity_cell = mu_beta_inequity + sigma_beta_inequity * beta_inequity_cell_raw;

  vector[G] beta_geo_full;
  vector[G] beta_geo_x_ineq_full;
  beta_geo_full[1] = beta_geo[1];
  beta_geo_full[2] = beta_geo[2];
  beta_geo_full[3] = 0.0;
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
  beta_holc_share_D ~ normal(0, 1);
  beta_holc_any ~ normal(0, 1);
  beta_vra ~ normal(0, 1);
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
              + beta_holc_share_D * holc_share_D[n]
              + beta_holc_any * holc_any[n]
              + beta_vra * vra_section4b[n]
              + log_exposure[n];
  }
  deaths ~ neg_binomial_2_log(log_mu, phi);
}
generated quantities {
  vector[N] log_lik;
  array[N] int<lower=0> deaths_rep;

  vector[N] eta_cell;
  vector[N] eta_inequity;
  vector[N] eta_race;
  vector[N] eta_geo;
  vector[N] eta_ses;
  vector[N] eta_history;   // NEW in v0.3

  for (n in 1:N) {
    real lm = alpha
            + alpha_cell[cell[n]]
            + beta_inequity_cell[cell[n]] * inequity[n]
            + X[n] * beta
            + beta_race_x_ineq * race_centered[n] * inequity[n]
            + beta_geo_full[geo_type[n]]
            + beta_geo_x_ineq_full[geo_type[n]] * inequity[n]
            + beta_holc_share_D * holc_share_D[n]
            + beta_holc_any * holc_any[n]
            + beta_vra * vra_section4b[n]
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
    eta_history[n] = beta_holc_share_D * holc_share_D[n]
                   + beta_holc_any * holc_any[n]
                   + beta_vra * vra_section4b[n];
  }
}
