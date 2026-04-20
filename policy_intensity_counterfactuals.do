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

    * Construct policy component
    gen b1_cnt = _b[c.pol_dens_cum] * pol_dens_cum

    * Counterfactual emissions (no policy)
    gen co2_cntfc = CO2_mt * exp(-b1_cnt)

    * Absolute avoided emissions
    gen avoided_CO2 = co2_cntfc - CO2_mt

    * Percent difference (policy effect)
    gen pct_diff = 100 * (co2_cntfc - CO2_mt) / CO2_mt

    * Keep relevant variables
    keep id year CO2_mt co2_cntfc avoided_CO2 pct_diff

    * Export country-year panel
    export delimited using "output/data/country_year_counterfactual_CO2.csv", replace

restore
