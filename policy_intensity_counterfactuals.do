***** MATTHEW SALAH Apr 2026
	
	clear 
	set more off
	use  policy_intensity/Climate_Policy_Emissions_Arvanitopoulos_Schaub_et_al_heiDATA_v3
	
****************
*** AVOIDED CO2 EMISSIONS DUE TO CLIMATE POLICIES
*** Counterfactual emissions path
*** Following Eskander & Fankhauser (2020)
****************

preserve

    * Drop most recent year if needed
    drop if year == 2023

    * Run regression with two-way fixed effects
    reghdfe CO2GDPPP_ln pol_dens_cum Ruleoflaw hp_GDPPP ///
        c.gdp_pc_ppp_ln##c.gdp_pc_ppp_ln ///
        imp_sh srv_sh temp_var, ///
        absorb(i.year i.id) vce(robust)

    est store R3

    * Display regression results with standard errors
    estimates restore R3
    estimates replay

    * Construct policy component
    gen b1_cnt = _b[c.pol_dens_cum] * pol_dens_cum

    * Generate 2015 policy level for each country
    bys id: egen pol_dens_cum_2015 = max(cond(year==2015, pol_dens_cum, .))

    * Counterfactual emissions (policy at 2015 level)
    gen b1_cnt_cf = _b[c.pol_dens_cum] * (pol_dens_cum - pol_dens_cum_2015)
    gen co2_cntfc = CO2_mt * exp(-b1_cnt_cf)

    * Absolute avoided emissions
    gen avoided_CO2 = co2_cntfc - CO2_mt

    * Percent difference (policy effect)
    gen pct_diff = 100 * (co2_cntfc - CO2_mt) / CO2_mt

    * Get standard error of the policy coefficient
    gen se_beta = _se[c.pol_dens_cum]

    * Standard error for log counterfactual
    gen se_ln_cntfc = (pol_dens_cum - pol_dens_cum_2015) * se_beta

    * Log counterfactual
    gen ln_cntfc = ln(CO2_mt) - b1_cnt_cf

    * 95% CI for log counterfactual
    gen ci_lower_ln = ln_cntfc - 1.96 * se_ln_cntfc
    gen ci_upper_ln = ln_cntfc + 1.96 * se_ln_cntfc

    * CI for counterfactual CO2
    gen ci_lower_co2 = exp(ci_lower_ln)
    gen ci_upper_co2 = exp(ci_upper_ln)

    * CI for avoided CO2
    gen ci_lower_avoided = ci_lower_co2 - CO2_mt
    gen ci_upper_avoided = ci_upper_co2 - CO2_mt

    * CI for percent difference
    gen ci_lower_pct = 100 * ci_lower_avoided / CO2_mt
    gen ci_upper_pct = 100 * ci_upper_avoided / CO2_mt

    * Filter to years post 2015
    drop if year <= 2015

    * Keep relevant variables
    keep id year CO2_mt co2_cntfc avoided_CO2 pct_diff ci_lower_pct ci_upper_pct

    * Export country-year panel
    export delimited using "output/data/country_year_counterfactual_CO2.csv", replace

restore
