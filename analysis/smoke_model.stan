// Smoke-test Stan model — simplified §8 spec on UB-HI parent-county aggregate
//
// Outcome: firearm-death count per county over 2019-2023 (5-year cumulative)
// Exposure: log(5-year cumulative pop)
// Predictors: inequity_composite, pct_black, 5 standardized SES covariates
//
// Negative-binomial with intercept + linear predictors. No cell hierarchy
// (single cell UB-HI). Validates pipeline + convergence before production fit.
data {
  int<lower=1> N;
  int<lower=1> K;
  array[N] int<lower=0> deaths;
  vector[N] log_exposure;
  matrix[N, K] X;
}
parameters {
  real alpha;
  vector[K] beta;
  real<lower=0> phi;
}
model {
  // Weakly informative priors
  alpha ~ normal(0, 5);
  beta ~ normal(0, 1);
  phi ~ exponential(0.1);

  // Negative binomial likelihood (parameterization 2: mean and dispersion)
  deaths ~ neg_binomial_2_log(alpha + X * beta + log_exposure, phi);
}
generated quantities {
  vector[N] log_lik;
  array[N] int<lower=0> deaths_rep;
  for (n in 1:N) {
    log_lik[n] = neg_binomial_2_log_lpmf(deaths[n] | alpha + X[n] * beta + log_exposure[n], phi);
    deaths_rep[n] = neg_binomial_2_log_rng(alpha + X[n] * beta + log_exposure[n], phi);
  }
}
