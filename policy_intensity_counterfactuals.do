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

    * Generate policy levels for different baseline years
    bys id: egen pol_dens_cum_2015 = max(cond(year==2015, pol_dens_cum, .))
    bys id: egen pol_dens_cum_2000 = max(cond(year==2000, pol_dens_cum, .))
    bys id: egen strng_wght_ind_2015 = max(cond(year==2015, strng_wght_ind, .))
    bys id: egen strng_wght_ind_2000 = max(cond(year==2000, strng_wght_ind, .))

    * Get standard error of the policy coefficient for pol_dens_cum model
    gen se_beta = _se[c.pol_dens_cum]

    *** SCENARIO 1: Policy held at 2015 levels (pol_dens_cum) ***
    gen b1_cnt_cf_2015 = _b[c.pol_dens_cum] * (pol_dens_cum - pol_dens_cum_2015)
    gen co2_cntfc_2015 = CO2_mt * exp(-b1_cnt_cf_2015)
    gen avoided_CO2_2015 = co2_cntfc_2015 - CO2_mt
    gen pct_diff_2015 = 100 * (co2_cntfc_2015 - CO2_mt) / CO2_mt
    gen se_ln_cntfc_2015 = (pol_dens_cum - pol_dens_cum_2015) * se_beta
    gen ln_cntfc_2015 = ln(CO2_mt) - b1_cnt_cf_2015
    gen ci_lower_ln_2015 = ln_cntfc_2015 - 1.96 * se_ln_cntfc_2015
    gen ci_upper_ln_2015 = ln_cntfc_2015 + 1.96 * se_ln_cntfc_2015
    gen ci_lower_co2_2015 = exp(ci_lower_ln_2015)
    gen ci_upper_co2_2015 = exp(ci_upper_ln_2015)
    gen ci_lower_avoided_2015 = ci_lower_co2_2015 - CO2_mt
    gen ci_upper_avoided_2015 = ci_upper_co2_2015 - CO2_mt
    gen ci_lower_pct_2015 = 100 * ci_lower_avoided_2015 / CO2_mt
    gen ci_upper_pct_2015 = 100 * ci_upper_avoided_2015 / CO2_mt

    *** SCENARIO 2: Policy held at 2000 levels (pol_dens_cum) ***
    gen b1_cnt_cf_2000 = _b[c.pol_dens_cum] * (pol_dens_cum - pol_dens_cum_2000)
    gen co2_cntfc_2000 = CO2_mt * exp(-b1_cnt_cf_2000)
    gen avoided_CO2_2000 = co2_cntfc_2000 - CO2_mt
    gen pct_diff_2000 = 100 * (co2_cntfc_2000 - CO2_mt) / CO2_mt
    gen se_ln_cntfc_2000 = (pol_dens_cum - pol_dens_cum_2000) * se_beta
    gen ln_cntfc_2000 = ln(CO2_mt) - b1_cnt_cf_2000
    gen ci_lower_ln_2000 = ln_cntfc_2000 - 1.96 * se_ln_cntfc_2000
    gen ci_upper_ln_2000 = ln_cntfc_2000 + 1.96 * se_ln_cntfc_2000
    gen ci_lower_co2_2000 = exp(ci_lower_ln_2000)
    gen ci_upper_co2_2000 = exp(ci_upper_ln_2000)
    gen ci_lower_avoided_2000 = ci_lower_co2_2000 - CO2_mt
    gen ci_upper_avoided_2000 = ci_upper_co2_2000 - CO2_mt
    gen ci_lower_pct_2000 = 100 * ci_lower_avoided_2000 / CO2_mt
    gen ci_upper_pct_2000 = 100 * ci_upper_avoided_2000 / CO2_mt

    *** SCENARIO 3: Policy held at zero (pol_dens_cum) ***
    gen b1_cnt_cf_zero = _b[c.pol_dens_cum] * (pol_dens_cum - 0)
    gen co2_cntfc_zero = CO2_mt * exp(-b1_cnt_cf_zero)
    gen avoided_CO2_zero = co2_cntfc_zero - CO2_mt
    gen pct_diff_zero = 100 * (co2_cntfc_zero - CO2_mt) / CO2_mt
    gen se_ln_cntfc_zero = (pol_dens_cum - 0) * se_beta
    gen ln_cntfc_zero = ln(CO2_mt) - b1_cnt_cf_zero
    gen ci_lower_ln_zero = ln_cntfc_zero - 1.96 * se_ln_cntfc_zero
    gen ci_upper_ln_zero = ln_cntfc_zero + 1.96 * se_ln_cntfc_zero
    gen ci_lower_co2_zero = exp(ci_lower_ln_zero)
    gen ci_upper_co2_zero = exp(ci_upper_ln_zero)
    gen ci_lower_avoided_zero = ci_lower_co2_zero - CO2_mt
    gen ci_upper_avoided_zero = ci_upper_co2_zero - CO2_mt
    gen ci_lower_pct_zero = 100 * ci_lower_avoided_zero / CO2_mt
    gen ci_upper_pct_zero = 100 * ci_upper_avoided_zero / CO2_mt

    * Re-run regression for strng_wght_ind model
    reghdfe CO2GDPPP_ln strng_wght_ind Ruleoflaw hp_GDPPP ///
        c.gdp_pc_ppp_ln##c.gdp_pc_ppp_ln ///
        imp_sh srv_sh temp_var, ///
        absorb(i.year i.id) vce(robust)

    est store R4

    * Get standard error of the policy coefficient for strng_wght_ind model
    gen se_beta_strng = _se[c.strng_wght_ind]

    *** STRNG SCENARIO 1: Policy held at 2015 levels (strng_wght_ind) ***
    gen b1_cnt_cf_2015_strng = _b[c.strng_wght_ind] * (strng_wght_ind - strng_wght_ind_2015)
    gen co2_cntfc_2015_strng = CO2_mt * exp(-b1_cnt_cf_2015_strng)
    gen avoided_CO2_2015_strng = co2_cntfc_2015_strng - CO2_mt
    gen pct_diff_2015_strng = 100 * (co2_cntfc_2015_strng - CO2_mt) / CO2_mt
    gen se_ln_cntfc_2015_strng = (strng_wght_ind - strng_wght_ind_2015) * se_beta_strng
    gen ln_cntfc_2015_strng = ln(CO2_mt) - b1_cnt_cf_2015_strng
    gen ci_lower_ln_2015_strng = ln_cntfc_2015_strng - 1.96 * se_ln_cntfc_2015_strng
    gen ci_upper_ln_2015_strng = ln_cntfc_2015_strng + 1.96 * se_ln_cntfc_2015_strng
    gen ci_lower_co2_2015_strng = exp(ci_lower_ln_2015_strng)
    gen ci_upper_co2_2015_strng = exp(ci_upper_ln_2015_strng)
    gen ci_lower_avoided_2015_strng = ci_lower_co2_2015_strng - CO2_mt
    gen ci_upper_avoided_2015_strng = ci_upper_co2_2015_strng - CO2_mt
    gen ci_lower_pct_2015_strng = 100 * ci_lower_avoided_2015_strng / CO2_mt
    gen ci_upper_pct_2015_strng = 100 * ci_upper_avoided_2015_strng / CO2_mt

    *** STRNG SCENARIO 2: Policy held at 2000 levels (strng_wght_ind) ***
    gen b1_cnt_cf_2000_strng = _b[c.strng_wght_ind] * (strng_wght_ind - strng_wght_ind_2000)
    gen co2_cntfc_2000_strng = CO2_mt * exp(-b1_cnt_cf_2000_strng)
    gen avoided_CO2_2000_strng = co2_cntfc_2000_strng - CO2_mt
    gen pct_diff_2000_strng = 100 * (co2_cntfc_2000_strng - CO2_mt) / CO2_mt
    gen se_ln_cntfc_2000_strng = (strng_wght_ind - strng_wght_ind_2000) * se_beta_strng
    gen ln_cntfc_2000_strng = ln(CO2_mt) - b1_cnt_cf_2000_strng
    gen ci_lower_ln_2000_strng = ln_cntfc_2000_strng - 1.96 * se_ln_cntfc_2000_strng
    gen ci_upper_ln_2000_strng = ln_cntfc_2000_strng + 1.96 * se_ln_cntfc_2000_strng
    gen ci_lower_co2_2000_strng = exp(ci_lower_ln_2000_strng)
    gen ci_upper_co2_2000_strng = exp(ci_upper_ln_2000_strng)
    gen ci_lower_avoided_2000_strng = ci_lower_co2_2000_strng - CO2_mt
    gen ci_upper_avoided_2000_strng = ci_upper_co2_2000_strng - CO2_mt
    gen ci_lower_pct_2000_strng = 100 * ci_lower_avoided_2000_strng / CO2_mt
    gen ci_upper_pct_2000_strng = 100 * ci_upper_avoided_2000_strng / CO2_mt

    *** STRNG SCENARIO 3: Policy held at zero (strng_wght_ind) ***
    gen b1_cnt_cf_zero_strng = _b[c.strng_wght_ind] * (strng_wght_ind - 0)
    gen co2_cntfc_zero_strng = CO2_mt * exp(-b1_cnt_cf_zero_strng)
    gen avoided_CO2_zero_strng = co2_cntfc_zero_strng - CO2_mt
    gen pct_diff_zero_strng = 100 * (co2_cntfc_zero_strng - CO2_mt) / CO2_mt
    gen se_ln_cntfc_zero_strng = (strng_wght_ind - 0) * se_beta_strng
    gen ln_cntfc_zero_strng = ln(CO2_mt) - b1_cnt_cf_zero_strng
    gen ci_lower_ln_zero_strng = ln_cntfc_zero_strng - 1.96 * se_ln_cntfc_zero_strng
    gen ci_upper_ln_zero_strng = ln_cntfc_zero_strng + 1.96 * se_ln_cntfc_zero_strng
    gen ci_lower_co2_zero_strng = exp(ci_lower_ln_zero_strng)
    gen ci_upper_co2_zero_strng = exp(ci_upper_ln_zero_strng)
    gen ci_lower_avoided_zero_strng = ci_lower_co2_zero_strng - CO2_mt
    gen ci_upper_avoided_zero_strng = ci_upper_co2_zero_strng - CO2_mt
    gen ci_lower_pct_zero_strng = 100 * ci_lower_avoided_zero_strng / CO2_mt
    gen ci_upper_pct_zero_strng = 100 * ci_upper_avoided_zero_strng / CO2_mt         

    * Keep relevant variables - all three scenarios for both models
    keep id year CO2_mt strng_wght_ind pol_dens_cum ///
         co2_cntfc_2015 avoided_CO2_2015 pct_diff_2015 ci_lower_pct_2015 ci_upper_pct_2015 ///
         co2_cntfc_2000 avoided_CO2_2000 pct_diff_2000 ci_lower_pct_2000 ci_upper_pct_2000 ///
         co2_cntfc_zero avoided_CO2_zero pct_diff_zero ci_lower_pct_zero ci_upper_pct_zero ///
         co2_cntfc_2015_strng avoided_CO2_2015_strng pct_diff_2015_strng ci_lower_pct_2015_strng ci_upper_pct_2015_strng ///
         co2_cntfc_2000_strng avoided_CO2_2000_strng pct_diff_2000_strng ci_lower_pct_2000_strng ci_upper_pct_2000_strng ///
         co2_cntfc_zero_strng avoided_CO2_zero_strng pct_diff_zero_strng ci_lower_pct_zero_strng ci_upper_pct_zero_strng

    * Export country-year panel
    export delimited using "output/data/country_year_counterfactual_CO2.csv", replace

restore
