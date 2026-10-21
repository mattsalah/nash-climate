import os
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.base.model import GenericLikelihoodModel
from statsmodels.tools.sm_exceptions import ConvergenceWarning

# Most countries have a zero Dolphin & Merkle carbon price, so OLS mixes whether a country prices
# carbon with how much. This fits the kitchen sink regressors (regress_kitchen_sink.py) with
#   tobit     one latent price drives both: y = max(0, Xb + e), e ~ N(0, s^2)
#   hurdle    Cragg double hurdle: a probit for y > 0 and a truncated normal for y given y > 0,
#             with separate coefficients. Tobit is the special case probit coef = b / s, so a
#             likelihood-ratio test of tobit against the hurdle (df = number of probit coefs)
#             tests whether one process drives both margins
# Two specs: main effects only, and with the two interactions (the probit has only ~40 positives,
# so the larger spec may overfit). Regressors are standardised; the price is divided by its SD (not
# centred, so zero stays the censoring point), so coefficients are SDs of price per 1 SD. Robust
# (sandwich) SEs throughout. Probit results are also reported as average marginal effects on
# P(price > 0). Tobit and the truncated stage are also reported as average marginal effects on
# E[price] and E[price | price > 0] (delta-method SEs), in SDs of price

output_filename = 'output/regressions/dolphin_hurdle_regressions.csv'
lr_filename = 'output/regressions/dolphin_hurdle_lr_tests.csv'

Y_COL = 'carbon_price_dolphin_ghg'
MAIN = ['pop_share', 'scc_mid_spec2', 'vdem_corruption', 'gini', 'ff_assets_1995',
        'land_area', 'gdppc']
INTERACTIONS = {
    'corruption_x_ff_assets': ('vdem_corruption', 'ff_assets_1995'),
    'gini_x_ff_assets': ('gini', 'ff_assets_1995'),
}
SPECS = {'main': False, 'interactions': True}
SAMPLES = {
    'full': [],
    'no_us_chn_ind': ['usa', 'chn', 'ind'],
}

###### MODELS #######

class Tobit(GenericLikelihoodModel):
    # left-censored at zero; last parameter is log sigma
    def loglikeobs(self, params):
        b, sigma = params[:-1], np.exp(params[-1])
        xb = self.exog @ b
        y = self.endog
        return np.where(y > 0, stats.norm.logpdf((y - xb) / sigma) - np.log(sigma),
                        stats.norm.logcdf(-xb / sigma))


class TruncatedNormal(GenericLikelihoodModel):
    # y | y > 0, truncated from below at zero; last parameter is log sigma
    def loglikeobs(self, params):
        b, sigma = params[:-1], np.exp(params[-1])
        xb = self.exog @ b
        return (stats.norm.logpdf((self.endog - xb) / sigma) - np.log(sigma)
                - stats.norm.logcdf(xb / sigma))


def fit_mle(model_class, y, X):
    ols = sm.OLS(y, X).fit()
    start = np.append(ols.params.values, np.log(ols.resid.std()))
    model = model_class(y, X, extra_params_names=['log_sigma'])
    optimum = model.fit(start_params=start, method='bfgs', maxiter=5000, gtol=1e-6, disp=False)
    # evaluate at the optimum (no further iterations) to get robust (sandwich) SEs
    with warnings.catch_warnings():
        # maxiter=0 always reports non-convergence; convergence is taken from the first fit
        warnings.simplefilter('ignore', ConvergenceWarning)
        result = model.fit(start_params=optimum.params, method='bfgs', maxiter=0, disp=False, cov_type='HC0')
    result.mle_retvals['converged'] = optimum.mle_retvals['converged']
    result.mle_retvals['max_abs_grad'] = np.abs(model.score(optimum.params)).max()
    names = model.exog_names
    return (result, pd.Series(result.params, index=names), pd.Series(result.bse, index=names),
            pd.Series(result.pvalues, index=names))

def delta_ame(ame_fn, params, cov, names):
    # average marginal effects with delta-method SEs (numerical gradient)
    ame = ame_fn(params)
    eps = 1e-6
    jac = np.column_stack([(ame_fn(params + eps * np.eye(len(params))[i]) - ame) / eps for i in range(len(params))])
    se = np.sqrt(np.diag(jac @ cov @ jac.T))
    p = 2 * stats.norm.sf(np.abs(ame / se))
    return pd.Series(ame, index=names), pd.Series(se, index=names), pd.Series(p, index=names)


def tobit_ame(X):
    # dE[y]/dx = b * Phi(xb / sigma), averaged over all observations
    def fn(params):
        b, sigma = params[:-1], np.exp(params[-1])
        return b[1:] * stats.norm.cdf(X @ b / sigma).mean()
    return fn


def truncated_ame(X):
    # dE[y | y > 0]/dx = b * (1 - lambda(z) (z + lambda(z))), z = xb / sigma, averaged over the positives
    def fn(params):
        b, sigma = params[:-1], np.exp(params[-1])
        z = X @ b / sigma
        lam = np.exp(stats.norm.logpdf(z) - stats.norm.logcdf(z))
        return b[1:] * (1 - lam * (z + lam)).mean()
    return fn

###### DATA #######

df = pd.read_csv('output/data/kitchen_sink_inputs.csv')

###### REGRESSIONS #######

rows, lr_rows = [], []
for spec, with_interactions in SPECS.items():
    for sample, excluded in SAMPLES.items():
        data = df[~df['n'].isin(excluded)][['n', Y_COL] + MAIN].dropna()
        standardise = lambda x: (x - x.mean()) / x.std()
        X = standardise(data[MAIN])
        if with_interactions:
            for name, (a, b) in INTERACTIONS.items():
                X[name] = standardise(X[a] * X[b])
        X = sm.add_constant(X)
        y = data[Y_COL] / data[Y_COL].std()
        priced = (y > 0).astype(int)

        tobit, *tobit_est = fit_mle(Tobit, y, X)
        trunc, *trunc_est = fit_mle(TruncatedNormal, y[priced == 1], X[priced == 1])
        probit = sm.Probit(priced, X).fit(disp=False, cov_type='HC0', maxiter=500)
        ame = probit.get_margeff(at='overall')
        ame_params = pd.Series(ame.margeff, index=X.columns[1:])
        ame_se = pd.Series(ame.margeff_se, index=X.columns[1:])
        ame_p = pd.Series(ame.pvalues, index=X.columns[1:])

        # LR test of tobit (restricted) against the hurdle (unrestricted)
        ll_hurdle = probit.llf + trunc.llf
        lr = 2 * (ll_hurdle - tobit.llf)
        dof = X.shape[1]
        lr_rows.append({
            'spec': spec, 'sample': sample, 'n': len(y), 'n_positive': int(priced.sum()),
            'n_params_tobit': len(tobit.params), 'n_params_hurdle': len(probit.params) + len(trunc.params),
            'll_tobit': tobit.llf, 'll_probit': probit.llf, 'll_truncated': trunc.llf,
            'lr_stat': lr, 'lr_dof': dof, 'lr_p': stats.chi2.sf(lr, dof),
            'tobit_converged': tobit.mle_retvals['converged'],
            'truncated_converged': trunc.mle_retvals['converged'],
            'tobit_max_abs_grad': tobit.mle_retvals['max_abs_grad'],
            'truncated_max_abs_grad': trunc.mle_retvals['max_abs_grad'],
            'probit_converged': probit.mle_retvals['converged'],
            'probit_pseudo_r2': probit.prsquared,
        })

        names = list(X.columns[1:])
        Xv = X.values
        tobit_me = delta_ame(tobit_ame(Xv), tobit.params, tobit.cov_params(), names)
        trunc_me = delta_ame(truncated_ame(Xv[priced.values == 1]), trunc.params, trunc.cov_params(), names)

        stages = {
            'tobit': tuple(tobit_est),
            'hurdle_probit': (probit.params, probit.bse, probit.pvalues),
            'hurdle_probit_ame': (ame_params, ame_se, ame_p),
            'hurdle_truncated': tuple(trunc_est),
            'tobit_ame': tobit_me,
            'hurdle_truncated_ame': trunc_me,
        }
        for stage, (params, bse, pvalues) in stages.items():
            for x_col in params.index:
                rows.append({
                    'spec': spec, 'sample': sample, 'stage': stage, 'x_column': x_col,
                    'coef': params[x_col], 'robust_se': bse[x_col], 'p_value': pvalues[x_col],
                    'n': int(priced.sum()) if stage.startswith('hurdle_truncated') else len(y),
                    'y_sd': data[Y_COL].std(),
                })

###### SAVE ################

report = pd.DataFrame(rows)
lr_report = pd.DataFrame(lr_rows)
os.makedirs(os.path.dirname(output_filename), exist_ok=True)
report.to_csv(output_filename, index=False)
lr_report.to_csv(lr_filename, index=False)

pd.set_option('display.width', 250)
pd.set_option('display.max_rows', 1000)
print(lr_report.to_string(index=False, float_format='{:.3g}'.format))
print(f"\nSaved CSVs to {output_filename} and {lr_filename}")
