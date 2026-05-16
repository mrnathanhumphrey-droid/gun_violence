// Production v0.1 — hierarchical negative-binomial across 8 cells
//
// Outcome: 5-year cumulative firearm deaths per unit (county-aggregated)
// Hierarchy: cell intercepts + cell-level random slope on inequity composite
// Predictors: standardized inequity composite, race composition, 6 SES covariates
//
// v2 §8 model spec; reporting-rate-adjustment + interactions + historical
// mechanism markers deferred to v0.2.
data {
  int<lower=1> N;
  int<lower=1> C;          // number of cells (8)
  int<lower=1> K;          // number of fixed-effect predictors
  array[N] int<lower=1, upper=C> cell;
  array[N] int<lower=0> deaths;
  vector[N] log_exposure;
  matrix[N, K] X;
  vector[N] inequity;      // standardized inequity composite (for random slope)
}
parameters {
  real alpha;                          // grand intercept
  vector[C] alpha_cell_raw;            // non-centered cell intercept
  real<lower=0> sigma_cell;
  vector[C] beta_inequity_cell_raw;    // non-centered cell-level inequity slope
  real mu_beta_inequity;
  real<lower=0> sigma_beta_inequity;
  vector[K] beta;                      // fixed-effect predictor coefs
  real<lower=0> phi;                   // dispersion
}
transformed parameters {
  vector[C] alpha_cell = sigma_cell * alpha_cell_raw;
  vector[C] beta_inequity_cell = mu_beta_inequity + sigma_beta_inequity * beta_inequity_cell_raw;
}
model {
  // Priors
  alpha ~ normal(-8, 3);                       // log-rate scale (smoke posterior ~ -8.6)
  alpha_cell_raw ~ std_normal();
  sigma_cell ~ exponential(1);
  beta_inequity_cell_raw ~ std_normal();
  mu_beta_inequity ~ normal(0, 1);
  sigma_beta_inequity ~ exponential(2);
  beta ~ normal(0, 1);
  phi ~ exponential(0.1);

  // Linear predictor: cell intercept + cell-specific inequity slope + fixed covariates + offset
  vector[N] log_mu;
  for (n in 1:N) {
    log_mu[n] = alpha + alpha_cell[cell[n]] + beta_inequity_cell[cell[n]] * inequity[n]
              + X[n] * beta + log_exposure[n];
  }
  deaths ~ neg_binomial_2_log(log_mu, phi);
}
generated quantities {
  vector[N] log_lik;
  array[N] int<lower=0> deaths_rep;
  for (n in 1:N) {
    real lm = alpha + alpha_cell[cell[n]] + beta_inequity_cell[cell[n]] * inequity[n]
            + X[n] * beta + log_exposure[n];
    log_lik[n] = neg_binomial_2_log_lpmf(deaths[n] | lm, phi);
    deaths_rep[n] = neg_binomial_2_log_rng(lm, phi);
  }
}
