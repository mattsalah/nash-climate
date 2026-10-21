# nash-climate

Do countries' climate policies look like a non-cooperative (Nash) equilibrium, where each country abates only up to its own country-level social cost of carbon (CSCC), or like the cooperative optimum at the global SCC?

The pipeline compares predicted abatement under both benchmarks with the abatement that countries' policies actually delivered. Predicted abatement comes from RICE50x marginal abatement cost (MAC) curves combined with Ricke et al. (2018) CSCCs, plus the RICE50x results of Gazzotti et al. (2021). Delivered abatement is the counterfactual emissions avoided by policy density and stringency since 2015. Observed carbon prices and the OECD Environmental Policy Stringency index are also used.

# Key findings

1. **Predicted Nash abatement vs delivered abatement:** policy-density-implied abatement rises with predicted Nash abatement in the full sample (CSCC and RICE, most specs). The relationship is fragile without the US, China and India. Stringency-implied abatement is flat, and turns negative without those three.
2. **CSCC vs carbon prices:** carbon prices *fall* with own CSCC on all three measures (OECD, Dolphin, EPS carbon pricing score), mostly in ranks (Spearman ρ ≈ −0.4 to −0.6 in specs 1, 3 and 4). Controlling for GDP per capita weakens it but the rank relationship survives (partial ρ ≈ −0.3 to −0.46). It is mostly a contrast between Europe (low CSCCs, high prices) and the rest of the world: within Europe and outside Europe, the relationship is close to zero once GDP per capita is controlled.
3. **Implied carbon prices:** the abatement policies delivered implies carbon prices of $0–31/t in 2020 ($0–57/t in 2022). That is far below the global SCC ($135–781/t), so no country is near the cooperative benchmark. Implied prices are unrelated to actual carbon prices and show no consistent link with own CSCC.
4. **Country size:** larger countries have *more* policies but not *more stringent* ones. Population predicts policy counts strongly but not stringency. Explicit carbon pricing on the OECD EPS is lower in large countries, which are also the ones with the most predicted Nash abatement.
5. **Robustness:** controlling for lobbying (LobbyMap) or treating the EU as one cooperative player doesn't change these conclusions. The lobbying measure mostly proxies economy size, and the EU bloc's predicted Nash abatement is about zero.

6. **Green technology support:** green spending doesn't rise with own CSCC in specs 1, 3 or 4 on any measure (World Bank program counts, OECD EPS R&D scores, IEA public energy RD&D, IEA clean-energy spending commitments). Larger economies spend more in total, which spec 2, a near-proxy for GDP, picks up. Relative to GDP, spending *falls* with own CSCC in specs 1, 3 and 4 (ρ ≈ −0.3 to −0.55), mostly because richer countries spend more and have lower CSCCs; controlling for GDP per capita leaves rank correlations of about −0.3.

7. **Kitchen sink:** with population, own CSCC, corruption, inequality, 1995 fossil-fuel assets, land area and GDP per capita all included, income is the strongest predictor of carbon pricing and policy stringency. Corruption and inequality also lower carbon prices, robustly. Own CSCC is negative only because of the US, China and India, and 1995 fossil-fuel assets have no effect (the one exception is Norway). Whether a country prices carbon at all and how high are different processes: a Tobit model is rejected against a double hurdle, and income and corruption predict pricing at all.

8. **Timing of adoption:** own CSCC doesn't speed up the first adoption of a carbon price. Income is by far the strongest predictor of when a country adopts (hazard ratio about 3 per SD), and larger countries adopt earlier.

Overall, observed policy sits well below the cooperative benchmark and doesn't track own CSCC the way a Nash model predicts. The cross-country variation that does exist is mostly about income and size.

# Setup

1. Clone the [RICE50xmodel](https://github.com/witch-team/RICE50xmodel/tree/main) into `input/`.
2. Install [GAMS](https://www.gams.com/download/).
3. Configure the environment:
   ```
   source setup.sh
   ```
4. Download the source data:

| Data | Source | Location |
|---|---|---|
| RICE50x `data_ed58` | [RICE50x v2.6.0 release](https://github.com/witch-team/RICE50xmodel/releases/tag/v2.6.0) | `input/RICE50xmodel/data_ed58/` |
| Gazzotti et al. (2021) results | [NC2021_results_dataset.zip](https://github.com/witch-team/RICE50xmodel/releases/download/v1.0.0/NC2021_results_dataset.zip) | `input/NC2021_results_dataset/` |
| Annual CO2 emissions | [Our World in Data](https://ourworldindata.org/explorers/co2) (CO2, territorial, all fossil emissions, per country) | `input/annual-co2-emissions/` |
| Policy intensity replication package | [Nature Communications](https://www.nature.com/articles/s41467-026-68577-z#Sec9) | `input/policy_intensity/` |
| Structural breaks replication package | [PMC11717907](https://pmc.ncbi.nlm.nih.gov/articles/PMC11717907) | `input/structural_breaks/` |
| Stechemesser et al. (2024) policy-matched breaks | [Zenodo 12773811](https://zenodo.org/records/12773811) (`Policy_out.RDS`, `break_detection_regression_input.RDS`; downloaded automatically, read with `pip install rdata`) | `input/stechemesser/` |
| Country-level SCC (Ricke et al. 2018) | [Nature Climate Change, MOESM](https://www.nature.com/articles/s41558-018-0282-y#MOESM1) | `input/country_scc/` |
| OECD effective carbon rates | [OECD data explorer](https://data-explorer.oecd.org/vis?lc=en&fs[0]=Topic%2C1%7CTaxation%23TAX%23%7CTax%20and%20environment%23TAX_ENV%23&pg=0&fc=Topic&bp=true&snb=7&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NECR%40DF_NECRS&df[ag]=OECD.CTP.TPS&dq=._T._T.ECRATE%2BNETECR..EUR_TCO2E.MEANW.Q.A&to[TIME_PERIOD]=false&pd=2020%2C&vw=tb) | `input/carbon_pricing/carbon_pricing_oecd.csv` |
| Dolphin & Merkle (2024) carbon prices | [ecp_CO2.csv](https://github.com/g-dolphin/ECP/blob/main/_output/_dataset/v2025.0/ecp/ipcc/ecp_economy/ecp_CO2.csv) | `input/carbon_pricing/carbon_pricing_dolphin.csv` |
| World Bank Green Subsidies Database | [World Bank, Subsidies and Trade](https://www.worldbank.org/en/brief/2024/06/04/subsidies-and-trade) ([xlsx](https://documents1.worldbank.org/curated/en/099644006032423503/IDU1b117b6921f0b1ae4c1dd6fbd4c89d9.xlsx)) | `input/green_subsidies/wb_green_subsidies.xlsx` |
| IEA Energy Technology RD&D Budgets | [IEA data explorer](https://www.iea.org/data-and-statistics/data-tools/energy-technology-rdd-budgets-data-explorer) API; `python fetch_iea_rdd.py` (the zipped database needs an IEA login, the API doesn't) | `input/iea_rdd/` |
| IEA Government Energy Spending Tracker | [IEA policy database](https://www.iea.org/data-and-statistics/data-tools/government-energy-spending-tracker-policy-database) (archived Jan 2025), raw file [policies.json](https://iea.blob.core.windows.net/scripts/tsr-tracker/data/policies.json) (snapshot of 26 Sep 2024) | `input/iea_spending_tracker/policies.json` |
| Fossil fuel rents | WDI bulk CSVs (World Bank "Download CSV") for oil [`NY.GDP.PETR.RT.ZS`](https://data.worldbank.org/indicator/NY.GDP.PETR.RT.ZS), natural gas [`NY.GDP.NGAS.RT.ZS`](https://data.worldbank.org/indicator/NY.GDP.NGAS.RT.ZS) and coal [`NY.GDP.COAL.RT.ZS`](https://data.worldbank.org/indicator/NY.GDP.COAL.RT.ZS) rents, see below | `input/fossil_rents/API_NY.GDP.{PETR,NGAS,COAL}.RT.ZS_DS2_*.csv` |
| Fossil fuel subsoil assets | World Bank Data360 [Changing Wealth of Nations](https://data360.worldbank.org/en/dataset/WB_CWON) dataset, full CSV download (uses `WB_CWON_SAOI`, `WB_CWON_SAGA`, `WB_CWON_SACO`), see below | `input/fossil_rents/WB_CWON.csv` |
| Gini, land area, GDP per capita (constant), corruption | Downloaded by `python fetch_kitchen_sink_inputs.py`: WB API (`SI.POV.GINI`, [`AG.LND.TOTL.K2`](https://data.worldbank.org/indicator/AG.LND.TOTL.K2), `NY.GDP.PCAP.KD`) and the V-Dem political corruption index (`v2x_corr`) via [Our World in Data](https://ourworldindata.org/grapher/political-corruption-index) | `input/kitchen_sink/wb_indicators.csv`, `input/kitchen_sink/vdem_corruption.csv` |
| World Bank WDI population and GDP per capita | `WB_WDI_SP_POP_TOTL`, `WB_WDI_NY_GDP_PCAP_CD` | `input/wb_controls/pop_gdp_2015_2025.csv` |
| OECD Environmental Policy Stringency (EPS) | [OECD data explorer](https://data-explorer.oecd.org/vis?lc=en&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_EPS%40DF_EPS&df[ag]=OECD.ECO.MAD&dq=.A..&pd=,&to[TIME_PERIOD]=false&vw=tb), see below | `input/policy_stringency/oecd_eps.csv` |
| LobbyMap scores and headquarters | [LobbyMap](https://lobbymap.org/LobbyMapScores), downloaded by `python fetch_lobbymap.py` (~40 min) | `input/lobbymap/lobbymap_scores.csv` |

The EPS file covers all countries, years and instruments, downloaded through the SDMX API:
```
curl -L -o input/policy_stringency/oecd_eps.csv "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EPS@DF_EPS,/.A..?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
```

**Fossil fuel rents.** Each indicator page's "Download → CSV" gives a zip, also available from the API. Unzip all three into `input/fossil_rents/`, either flat or each in its own folder (`regress_kitchen_sink.py` finds `API_<indicator>_DS2_*.csv` anywhere under it):
```
mkdir -p input/fossil_rents
for code in NY.GDP.PETR.RT.ZS NY.GDP.NGAS.RT.ZS NY.GDP.COAL.RT.ZS; do
  curl -L -o "input/fossil_rents/$code.zip" "https://api.worldbank.org/v2/en/indicator/$code?downloadformat=csv"
  unzip -o "input/fossil_rents/$code.zip" -d "input/fossil_rents/" && rm "input/fossil_rents/$code.zip"
done
```

**Fossil fuel subsoil assets.** On the [WB_CWON dataset page](https://data360.worldbank.org/en/dataset/WB_CWON), download the full dataset as CSV and save it as `input/fossil_rents/WB_CWON.csv` (~200 MB). The script uses the oil, natural gas and coal subsoil components (`WB_CWON_SAOI`, `WB_CWON_SAGA`, `WB_CWON_SACO`) of nonrenewable natural capital, aggregation total, in real chained 2019 US$.

**Gini, land area, constant GDP per capita and corruption** are downloaded by `python fetch_kitchen_sink_inputs.py` into `input/kitchen_sink/`. It needs no manual steps.

**Country-name mappings** (`input/*_to_iso3.json`, `input/lobbymap/lobbymap_country_to_iso3.json`) are part of the repo. Everything else under `input/` is gitignored, so download it as above.

# Pipeline

First run `gams extract_macc.gms` and `policy_intensity_counterfactuals.do` (Stata). Then `execute.sh` runs everything else:

| Step | Script | Output |
|---|---|---|
| CSCC dataset | `generate_cscc_vs_cntfc.py` | `output/data/mitigation_cscc_v_cntfc_2020.csv` |
| Implied carbon prices | `generate_implied_carbon_price.py` | `output/data/implied_carbon_price_{2020,2022}.csv`, `output/regressions/implied_price_correlations.csv` |
| EPS stringency | `generate_eps_stringency.py` | `output/data/eps_stringency_2020.csv` |
| Structural break abatement (unattributed) | `generate_structural_break_abatement.py` | `output/data/structural_break_abatement.csv` |
| Policy-matched break abatement | `generate_policy_break_abatement.py` | `output/data/policy_break_abatement.csv` |
| Green subsidy counts | `generate_green_subsidies.py` | `output/data/green_subsidies.csv` |
| Green spending (EPS, IEA RD&D, IEA spending tracker) | `generate_green_spending.py` | `output/data/green_spending.csv` |
| LobbyMap country scores | `generate_lobbymap_country_scores.py` | `output/data/lobbymap_country_scores.csv` |
| RICE dataset | `generate_rice_vs_cntfc.py` | `output/data/mitigation_rice_v_cntfc_2022.csv` |
| MAC/MAB charts | `plot_MAC_MAB.py <country> <spec>` | `output/charts/mac_mab_*.png` |
| Predicted vs policy charts | `plot_pred_vs_policy.py <year> --dataset cscc\|rice --spec N` | `output/charts/{cscc,rice}_*plot_*.png` |
| Main regressions | `report_regression_coeffs.py` | `output/regressions/_regression_coefficients_table.csv` |
| Population regressions | `regress_population.py` | `output/regressions/population_regressions.csv` |
| EPS regressions | `regress_eps_stringency.py` | `output/regressions/eps_stringency_regressions.csv` |
| Carbon price vs CSCC by region | `regress_carbon_price_cscc.py` | `output/regressions/carbon_price_cscc_regressions.csv` |
| Green subsidy regressions | `regress_green_subsidies.py` | `output/regressions/green_subsidies_regressions.csv` |
| Green spending regressions | `regress_green_spending.py` | `output/regressions/green_spending_regressions.csv` |
| Kitchen sink regressions | `regress_kitchen_sink.py` | `output/regressions/kitchen_sink_regressions.csv`, `output/data/kitchen_sink_inputs.csv` |
| Tobit vs double hurdle (Dolphin price) | `regress_dolphin_hurdle.py` | `output/regressions/dolphin_hurdle_regressions.csv`, `output/regressions/dolphin_hurdle_lr_tests.csv` |
| Country-year policy panel | `generate_policy_panel.py` | `output/data/policy_panel.csv` |
| Carbon price adoption hazard | `regress_carbon_price_adoption.py` | `output/regressions/carbon_price_adoption_hazard.csv` |

Countries are keyed by lowercase ISO3 codes in an `n` column throughout. `n = 'eu'` is an EU aggregate row where one is built.

## MAC curves

`gams extract_macc.gms` extracts the RICE50x MAC curves without running the full model. It writes `macc_extract.gdx`, which has everything the model uses including SSP scaling, and `output/data/macc_ed_early.csv` with the raw coefficients for 2015, 2020 and 2025.

Each region's marginal abatement cost curve is

    MAC(μ) = a·μ + d·μ⁴

where μ is the abatement rate (0 = none, 1 = full) and MAC is in $/tCO2. Total abatement cost is the integral:

    ABATECOST(μ) = emi_bau · (a·μ²/2 + d·μ⁵/5)

| Column | Description |
|---|---|
| `sector` | Always `Total_CO2`, the economy-wide aggregate in the RICE50x cost equation. |
| `Dim2` | Coefficient: `a` is the linear term (c1), `d` the quartic term (c4). |
| `t` | Period: `1` = 2015, `2` = 2020, `3` = 2025. |
| `n` | Region in the RICE50x `ed58` mapping (e.g. `usa`, `chn`, `deu`). Some are aggregates (e.g. `rsam` = Rest of South America, `noap` = Non-OECD Asia Pacific). |
| `Val` | Coefficient in $/tCO2. 0 means no Enerdata coverage and should be treated as missing. Coverage is denser for Europe, sparser for African, South-East Asian and Latin American aggregates. |

| sector | Dim2 | t | n | Val |
|---|---|---|---|---|
| Total_CO2 | a | 1 | arg | 564.82 |
| Total_CO2 | d | 1 | arg | 5480.24 |
| Total_CO2 | a | 2 | usa | 812.70 |
| Total_CO2 | d | 2 | usa | 9633.49 |

- These are the **raw** Enerdata coefficients before SSP scaling, appropriate for backward-looking comparisons of observed abatement with 2015–2025 predictions.
- The coefficients are identical across the three periods.
- `d` is larger than `a` for every region (medians ~8,000 vs ~570). Because μ⁴ is tiny at low abatement, the linear term still dominates below μ ≈ (a/d)^(1/3) ≈ 0.4. The dispersion of `a` across countries is what matters at observed abatement levels. `Rscript plot_macc.R` plots it by year.

## Policy intensity counterfactuals

`policy_intensity_counterfactuals.do` (Stata) uses the policy intensity replication package. It estimates the emissions avoided by each country's policy density and stringency relative to holding policy at 2015 (also 2000, and zero) levels, through 2022. The output is `output/data/country_year_counterfactual_CO2.csv`.

`pct_diff_2015` (density) and `pct_diff_2015_strng` (stringency) are avoided emissions as a % of *actual* emissions, with confidence bounds. In the datasets below these are renamed `policy_den_cntfc` and `policy_strng_cntfc`.

## CSCC dataset

`generate_cscc_vs_cntfc.py` builds the main 2020 country dataset. It merges:
- four Ricke et al. CSCC specs (own and global, median and 66% range)
- the 2020 MAC curves
- the policy counterfactuals
- OECD (2021, effective carbon rate `ECRATE`) and Dolphin (2020) carbon prices
- World Bank population and GDP per capita

For each spec it solves MAC(μ) = SCC for the Nash (`noncoop_optimal_mu_specN`, own CSCC) and cooperative (`coop_optimal_mu_specN`, global SCC) abatement rates, and flags whether realized abatement falls in the Nash or cooperative range (with Monte Carlo draws).

| Spec | Run | Global SCC ($/t) |
|---|---|---|
| 1 | BHM short run, SSP2, RCP6.0, PRTP 2% | 418 |
| 2 | BHM long run, SSP2, RCP6.0, PRTP 2% | 781 |
| 3 | BHM rich/poor short run, SSP1, RCP4.5, PRTP 2% | 135 |
| 4 | BHM short run, SSP2, RCP6.0, fixed 3% discounting | 406 |

**EU aggregate row (`n = 'eu'`):** treats the EU as a single player, built from the EU27 members that have a counterfactual and MAC curves.
- **SCC:** the sum of member SCCs.
- **Abatement:** members abate until their own MAC reaches the common price; bloc μ is the BAU-weighted mean.
- **Realized abatement:** total avoided over total emissions.
- **Not filled in:** policy counts, stringency levels and carbon prices.

## RICE dataset

`generate_rice_vs_cntfc.py` takes the Gazzotti et al. (2021) `CBA_regional_data.csv`. It keeps the 2022 CBA results for `noncoop-pop` and `coop-pop` and pivots them to one row per region. Each column is the mitigation rate for one baseline (SSP1–5) × impact function (BHM-LR, BHM-LRdiff, BHM-SR, BHM-SRdiff, DJO, KAHN) × PRTP (0.001, 0.015, 0.03) combination. It then merges the 2022 policy counterfactuals, structural breaks and World Bank controls into `output/data/mitigation_rice_v_cntfc_2022.csv`. The regressions use specs 1–4 = `ssp2_BHM-SR_0.015`, `ssp2_BHM-LR_0.001`, `ssp1_BHM-SRdiff_0.03`, `ssp2_DJO_0.015`.

## Main regressions

`report_regression_coeffs.py` regresses each policy outcome on predicted Nash abatement for both datasets and all four specs, with HC1 standard errors. The outcomes are the density and stringency counterfactuals, the policy count and stringency index (levels and changes since 2015), and carbon prices on CSCC.

- **Control sets:** none, `gdppc`, `log_gdppc`, `lobby_pressure`, `log_gdppc + lobby_pressure`.
- **Samples:** `full`, `no_us_chn_ind`, `no_eu`, and `eu_bloc` (EU members replaced by the `eu` row).
- Set `MAKE_PLOTS = True` to also save partial-regression plots.

## Charts and web app

- **`plot_pred_vs_policy.py`:** scatter plots of predicted abatement against the policy counterfactuals, with error bars, fit lines and R².
- **`plot_MAC_MAB.py`:** draws one country's MAC curve against its marginal benefit (own and global SCC), marking realized abatement.
- **`plot_rice_predictions.py`:** bar charts of cooperative vs non-cooperative RICE abatement.

`webapp/` serves the MAC/MAB chart interactively. You pick a country, year, spec and abatement measure, and it shows where realized abatement sits relative to the Nash and cooperative optima, with an over/under-abatement verdict. It needs only the standard library; see `webapp/README.md`.

```
python webapp/server.py          # reads output/data/, serves http://127.0.0.1:8000/
python webapp/server.py --demo   # synthetic sample data, no pipeline needed
```

## Running BAU

```
gams run_rice50x.gms --policy=bau
```

# Alternative analyses

Robustness checks and alternative approaches to the Nash vs cooperative comparison.

## 1. Lobbying intensity (LobbyMap)

Does controlling for corporate climate lobbying change the cross-country regressions?

- **Data:** `fetch_lobbymap.py` scrapes the [LobbyMap scores](https://lobbymap.org/LobbyMapScores) league table (1,042 companies, 369 industry associations) and each organization's headquarters into `input/lobbymap/lobbymap_scores.csv`. The organization score (0–100, higher = more Paris-aligned) is the grade; letter bands are 5-point bins of it (F < 25, E- 25–30, …, A+ ≥ 95).
- **Country scores:** `generate_lobbymap_country_scores.py` assumes each organization lobbies only where it is headquartered (`input/lobbymap/lobbymap_country_to_iso3.json`). It computes the engagement-weighted score Σ(engagement × score) / Σ engagement per country.
  - Brussels-based European associations (BusinessEurope, Cefic, ACEA, …) go to the `eu` row, not Belgium. The `eu` row also includes every organization headquartered in an EU27 member.
  - Global associations (IIF, Ipieca, World Steel, …) are dropped, as are organizations with no score or engagement intensity.
- **Regressions:** `lobby_pressure` = weighted score × total engagement is added as a control in `report_regression_coeffs.py`. Countries without rated organizations drop out (CSCC n = 36, RICE n = 32).
- **Findings:**
  - The CSCC Nash-abatement slope on `policy_den_cntfc` survives in specs 1, 3 and 4.
  - The slopes on policy counts and on the RICE outcomes roughly halve and lose significance.
  - `lobby_pressure` is mostly a size proxy (correlation 0.68 with log GDP) and is insignificant once log GDP is controlled. Split into its parts, only total engagement matters, never the pro-climate score.
  - The product also mixes direction with volume: the US lobbies heavily against climate policy yet has the second-highest value.

## 2. EU as a single cooperative player

The `eu_bloc` sample in `report_regression_coeffs.py` replaces the EU27 members with the `eu` aggregate row.

- **Findings:** slopes are within ~0.01 of the `no_eu` sample. Most members have a negative own CSCC, so the summed EU SCC is negative in specs 1, 3 and 4 and the EU's predicted Nash abatement is 0. The bloc is a single point at the bottom of the x-axis.
- **Not covered:**
  - The `eu` row has no policy counts, stringency levels or carbon prices; those `eu_bloc` rows are left empty with a note.
  - The RICE outputs have no EU aggregate. A proper RICE version needs a RICE50x run with an EU coalition.

## 3. Population only

`regress_population.py` regresses observed 2020 policy density (`pol_dens_cum`), stringency (`strng_wght_ind`) and the Dolphin effective carbon price (all GHG) on population as a % of world population, with HC1 SEs.

| Outcome | Slope per 1pp of world pop | n | Without US/China/India |
|---|---|---|---|
| Policy density | +6.9 policies\*\*\* (R² 0.26) | 43 | +14.1, p = 0.06 |
| Policy stringency | ≈ 0 (p = 0.94) | 41 | −0.11, p = 0.07 |
| Dolphin carbon price | −$0.29/t\*\*\* (R² 0.004) | 165 | −1.28, p = 0.07 |

Larger countries have more climate policies but not more stringent ones or higher carbon prices, so policy density partly measures economy size.

## 4. Implied carbon price

This reverses the methodology. Instead of asking how much a country should abate at its SCC, it takes the abatement its policies actually delivered and asks what carbon price would justify it.

- **Method** (`generate_implied_carbon_price.py`):
  - Abatement is the density- and stringency-implied counterfactual, including CI bounds. It is converted from % of actual emissions to a share of BAU: μ = pct / (100 + pct).
  - Implied price = MAC(μ) = a·μ + d·μ⁴.
  - The EU price is the common price at which its 22 members' abatement, each read off its own MAC curve, adds up to the EU's actual abatement.
  - Each price is compared with own CSCC (the Nash benchmark), the global SCC (the cooperative benchmark) and the 2020 Dolphin carbon price.
- **Findings, 2020:**
  - Implied prices are $0–31/t: median $7.6 (density) and $11.6 (stringency); EU about $15 on both.
  - No country comes close to the global SCC.
  - Below own CSCC (density, spec 1): Brazil, China, Colombia, Indonesia, India, the US and South Africa.
  - Most other countries look "above Nash" only because 26–28 of 43 have a negative own CSCC in specs 1, 3 and 4. Spec 2 (all CSCCs positive) is the real test: 12 of 43 fall below Nash.
  - Implied prices are uncorrelated with actual Dolphin carbon prices (r = −0.02 density, 0.24 stringency). Norway, Sweden and Finland price carbon at $58–66/t but have implied prices of $6–26.
- **Correlations** (Pearson r, Spearman ρ in brackets):

| Implied price from | vs | 2020 | 2022 |
|---|---|---|---|
| Density | pop share | 0.39\*\* [0.46\*\*\*] | 0.28\* [0.45\*\*\*] |
| Density | pop share, no US/China/India | 0.19 [0.38\*\*] | 0.13 [0.35\*\*] |
| Stringency | pop share | −0.02 [−0.05] | −0.06 [−0.31\*] |
| Density | own CSCC, spec 2 | 0.23 [0.58\*\*\*] | 0.57\*\*\* [0.59\*\*\*] |
| Density | own CSCC, specs 1, 3, 4 | 0.24–0.32 [≈ 0.05] | 0.25–0.36 [≈ 0.07] |
| Stringency | own CSCC, any spec | ≈ 0 | negative, n.s. |

The positive population link with density-implied prices comes from China and India, though the rank correlation stays positive without them. Holding population share fixed, no own-CSCC effect is consistent across both years and both policy measures.

- **Sensitivity (2022):** the policy counterfactuals end in 2022 and the 2025 MAC coefficients are identical to 2020, so 2022 abatement is the latest available.
  - Implied prices rise: median $7.6 → $16.2 (density) and $11.6 → $15.0 (stringency); EU $15 → $23 and $15 → $20.
  - Rankings are stable (0.85 and 0.78 correlation with 2020). The biggest movers are the US (+$46) and the UK (+$26).
  - Still no country is above the global SCC, and fewer are below their own CSCC (density, spec 1: 7 → 4).
- **Caveat:** the abatement is incremental since 2015 but is read off a MAC curve starting at zero abatement, so 2015 policy is treated as the baseline. This is the same convention as the main comparison. Implied prices for total policy would be higher.

## 5. CSCC vs carbon prices, by region

`regress_carbon_price_cscc.py` regresses three carbon pricing measures on own CSCC (all four specs), with and without a GDP per capita control, with HC1 SEs. It runs on all countries, within Europe (EU27 + UK, Switzerland, Norway, Iceland) and outside Europe → `output/regressions/carbon_price_cscc_regressions.csv`. It also reports the matching partial correlations, Pearson and on ranks (partial Spearman).

| Measure | What it covers | n (all / Europe / non-Europe) |
|---|---|---|
| OECD effective carbon rate | €/tCO2e, 2021; carbon taxes, ETS **and fuel excise** | 72 / 27 / 45 |
| Dolphin & Merkle | $/tCO2e, 2020; explicit carbon pricing only | 165 / 29 / 136 |
| EPS `eps_carbon_price` | 0–6 score, 2020; CO2 tax and CO2 ETS | 40 / 24 / 16 |

The measures agree with each other mostly through the Europe vs rest-of-world gap. Correlations with `eps_carbon_price` are 0.72 for OECD and 0.86 for Dolphin overall. Within Europe and outside Europe, OECD falls to about 0.3 (it tracks fuel taxes), while Dolphin stays at 0.80–0.88.

Partial Spearman ρ with own CSCC, controlling for GDP per capita (no-control value in brackets):

| Region | Measure | Spec 1 | Spec 2 | Spec 3 | Spec 4 |
|---|---|---|---|---|---|
| All | OECD | −0.32\*\*\* [−0.53\*\*\*] | −0.36\*\*\* [−0.04] | −0.31\*\*\* [−0.54\*\*\*] | −0.28\*\* [−0.56\*\*\*] |
| | Dolphin | −0.41\*\*\* [−0.43\*\*\*] | +0.14\* [+0.40\*\*\*] | −0.38\*\*\* [−0.44\*\*\*] | −0.28\*\*\* [−0.44\*\*\*] |
| | EPS | −0.46\*\*\* [−0.57\*\*\*] | −0.38\*\* [−0.45\*\*\*] | −0.42\*\*\* [−0.52\*\*\*] | −0.46\*\*\* [−0.57\*\*\*] |
| Europe | OECD | −0.03 [−0.24] | +0.18 [+0.23] | −0.01 [−0.23] | +0.02 [−0.20] |
| | Dolphin | −0.25 [−0.37\*\*] | +0.23 [+0.30] | −0.29 [−0.39\*\*] | −0.30 [−0.40\*\*] |
| | EPS | −0.07 [−0.19] | −0.03 [−0.04] | −0.07 [−0.18] | −0.13 [−0.23] |
| Non-Europe | OECD | −0.18 [−0.15] | −0.26\* [−0.02] | −0.20 [−0.20] | −0.19 [−0.25] |
| | Dolphin | −0.07 [−0.01] | +0.28\*\*\* [+0.39\*\*\*] | −0.05 [−0.02] | +0.05 [−0.00] |
| | EPS | −0.27 [−0.33] | −0.05 [−0.03] | −0.25 [−0.35] | −0.19 [−0.30] |

- **All countries:** the negative relationship survives the GDP per capita control on every measure. On ranks it's −0.28 to −0.46 in specs 1, 3 and 4. The OECD Pearson slopes in specs 1, 3 and 4 lose significance with the control, but spec 2 strengthens (−0.38\*\*\*, as the OECD rate and spec-2 CSCC are both high in rich countries).
- **Within Europe:** nothing survives the control. Europe's spec-1 CSCCs span only −5 to +3.4 $/t. The one remaining signal is Dolphin spec 4 in Pearson terms (partial r = −0.49\*\*\*), driven by the Nordics' negative CSCCs and $58–66/t carbon taxes.
- **Outside Europe:** essentially zero in specs 1, 3 and 4. Spec 2 splits: Dolphin is positive in ranks (+0.28\*\*\*, many poor countries with low CSCC and no price) while OECD is negative (−0.26\*). The US, China and India, with high CSCCs and little carbon pricing, pull it negative.
- **Overall:** the negative full-sample result is mostly a between-region contrast that GDP per capita doesn't fully absorb. No region or measure shows the positive own-CSCC → carbon price link a Nash model predicts.

## 6. OECD EPS climate policy stringency

`generate_eps_stringency.py` turns the OECD EPS index (40 countries, 1990–2020, instruments scored 0–6) into a 2020 cross-country stringency measure. The output has one column per spec plus the 13 instrument scores.

The headline EPS is the equal-weighted mean of three pillars:

| Pillar | Instruments (weight within pillar) |
|---|---|
| Market-based | CO2 tax, NOx tax, SOx tax, diesel tax, CO2 trading scheme, renewable energy trading scheme (1/6 each) |
| Non-market (standards) | NOx, SOx and PM emission limits, sulphur content of diesel (1/4 each) |
| Technology support | low-carbon R&D (1/2), solar support, wind support (1/4 each) |

Each spec drops instruments but keeps this structure: pillars stay equally weighted, the remaining instruments keep their relative weights within a pillar, and a pillar with nothing left drops out. Rebuilding `eps` reproduces the official index exactly.

| Spec | Drops | What's left |
|---|---|---|
| `eps` | nothing | headline EPS |
| `eps_no_air` | NOx/SOx taxes, all emission limits (the whole non-market pillar) | market-based + technology support |
| `eps_climate` | also the diesel tax (a fuel excise, not a carbon price) | CO2 tax, CO2 ETS, renewable trading, solar/wind support, low-carbon R&D |
| `eps_carbon_price` | also renewable trading and technology support | CO2 tax and CO2 ETS only |

In 2020, `eps_no_air` and `eps_climate` are nearly identical (correlation 0.99) and correlate ~0.9 with the headline EPS. `eps_carbon_price` correlates only 0.57–0.68 with the others: the US, China, India, Australia and Brazil score 0–0.5, while Ireland and Iceland (3.5) and the Nordics and Switzerland (4.5) score highest.

`regress_eps_stringency.py` regresses each spec, one regressor at a time, on Nash abatement (`noncoop_optimal_mu_spec2`), cooperative abatement (`coop_optimal_mu_spec2`) and population share, with HC1 SEs.

| EPS spec | Nash μ (spec 2) | Coop μ (spec 2) | Pop share (pp of world) |
|---|---|---|---|
| `eps` | +0.000 (p = 0.99) | −0.041 (p = 0.21) | −0.011 (p = 0.54) |
| `eps_no_air` | −0.028 (p = 0.16) | −0.034 (p = 0.27) | −0.042\*\* |
| `eps_climate` | −0.016 (p = 0.45) | −0.023 (p = 0.47) | −0.028 (p = 0.18) |
| `eps_carbon_price` | −0.106\*\*\* (R² 0.10) | −0.037 (p = 0.28) | −0.125\*\*\* (R² 0.12) |

n = 40. Without the US, China and India (n = 37):
- Every population-share slope is negative and significant (−0.41 to −0.88).
- The Nash slope on `eps_carbon_price` steepens to −0.71\*\*\*.

No spec rises with Nash or cooperative abatement. Explicit carbon pricing is lower where predicted Nash abatement is higher. Those are mostly the large countries (Nash μ correlates 0.62 with population), so the two effects can't be separated with 40 countries.

## 7. Abatement implied by structural breaks

Two break datasets are aggregated into implied abatement by country. Only the first attributes breaks to policy.

### 7a. Policy-matched breaks (Stechemesser et al. 2024)

`generate_policy_break_abatement.py` uses the published results of [Stechemesser et al. (2024, *Science*)](https://doi.org/10.1126/science.adl6547), "Climate policies that achieved major emission reductions" → `output/data/policy_break_abatement.csv`.

**Source method:** sectoral CO2 (buildings, electricity & heat, industry, transport) for 41 countries in a developed and a developing sample, 2000–2021. Log emissions are regressed on log GDP, log GDP², log population, heating and cooling degree days, and dummies for EU-wide policies (ETS phases, appliance and vehicle standards), with country and year fixed effects. The model is saturated with country step and impulse indicators (GETS, p = 0.01). Only negative breaks are kept (69). Each break is then matched to policy adoptions or tightenings in the same country and sector, from the OECD Climate Actions and Policies Measurement Framework (CAPMF; IPAC for the US). The match requires the policy to fall within the break's confidence interval (`stat`, the paper's main version) or within ±2 years (`2y`).

**Aggregation:** the same as 7b. The counterfactual is E_cf = E_t · exp(−C_t) per country and sector, summed across the four sectors, in kt CO2, % of actual 4-sector CO2 and μ. Specs are match (`none` = all 69 breaks, `stat`, `2y`) × year (2020, 2021; the data end in 2021) × window (all breaks, or breaks after 2015). 47 breaks match a policy under `stat` and 59 under `2y`.

**Totals across the 50 countries, 2020:**

| Match | Breaks | Abated | μ | Since 2015: breaks | Since 2015: abated | Since 2015: μ |
|---|---|---|---|---|---|---|
| Policy within CI (`stat`) | 47 | 1,776 Mt | 6.2% | 17 | 1,396 Mt | 5.0% |
| Policy within ±2 years (`2y`) | 59 | 1,912 Mt | 6.7% | 19 | 1,399 Mt | 5.0% |
| Any break (`none`) | 69 | 2,029 Mt | 7.1% | 19 | 1,399 Mt | 5.0% |

**Findings:**
- **The scale matches the paper's.** The paper reports total reductions of 0.6–1.8 Gt CO2 for its 63 successful interventions. The method behind that range is behind the *Science* paywall and couldn't be checked, but the `stat` point estimate here (1.78 Gt) lies at its top, and coefficient ± 1.96 SE gives 0.87–2.76 Gt. The 47 matches here vs the paper's 63 probably reflect the paper's extra steps: per its replication code, it also credits 4 breaks to EU policies and merges breaks with overlapping confidence intervals.
- **The US power breaks are gone.** With degree-day controls and these four aggregated sectors, the US has only a −0.09 transport break in 2008, matched to fuel economy standards and vehicle support (118 Mt). Japan, Korea and Mexico have no positive breaks to offset, because only negative breaks are kept.
- **China dominates.** Two breaks give 1.25 Gt, 70% of the total: industry in 2016 (−0.23, matched to industrial fossil fuel subsidy reform and financing) and buildings in 2018 (−0.21, matched to appliance standards and building codes). The industry break coincides with the 2016 steel and coal capacity cuts, which are policy but not climate policy. It also coincides with the construction slowdown, which isn't policy at all. The largest clearly climate-driven attributions are the UK power sector (44 Mt, carbon price floor and coal phase-out), Germany and France.
- **Agrees with the policy density counterfactual.** Since 2015, policy-matched μ has a rank correlation of 0.45 (p = 0.003, n = 42) with `policy_den_cntfc`, which uses the same 2015 baseline. It is uncorrelated with `policy_strng_cntfc` (0.11), and weakly correlated with Nash μ, spec 2 (ρ = 0.29, p = 0.04, n = 49). Many countries have no breaks, so these correlations rest on ties at zero.

**Caveats:**
- Matching shows that the timing coincides with a policy change, not that the policy caused the break. CAPMF records many policy changes per country and sector, so the filter is loose: `stat` drops only 22 of 69 breaks, and `2y` only 10.
- Year fixed effects and the EU policy dummies absorb common shifts (e.g. the EU ETS), so this is country-specific abatement only, a lower bound.
- Only negative breaks are kept, so it is a gross measure. Policy-driven *increases* (e.g. nuclear phase-outs) aren't netted out.
- Gradual policy effects don't show up as steps.

### 7b. All breaks, unattributed (Tebecis & Crespo Cuaresma)

`generate_structural_break_abatement.py` turns the structural breaks dataset of [Tebecis & Crespo Cuaresma (2025, *Scientific Data*)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11717907) into the abatement implied by every detected break, by country → `output/data/structural_break_abatement.csv`.

**Source method:** for each gas × IPCC sector × country sample (EU15 or OECD) × target p-value (0.05, 0.01, 0.001), the paper estimates log emissions per capita on log GDP, log GDP² and log population, with country and year fixed effects. The model is saturated with country-specific step indicators and reduced by general-to-specific search (`getspanel`). Each break is a permanent level shift in log emissions from its year onward, relative to the other countries in the sample. Breaks are "abnormal" changes not explained by income or population, meant to be attributed to policy afterwards. The 37 sectors are leaf IPCC categories, so they add up across sectors.

**Aggregation:**
- **Counterfactual:** with C_t the sum of a country–sector's break coefficients up to year t, counterfactual emissions are E_cf = E_t · exp(−C_t) and abatement is E_cf − E_t. This is summed across sectors, using EDGAR sector emissions from the replication package (kt CO2 or kt CO2e).
- **Units:** results are in kt, as % of actual emissions, and as μ = abated / (actual + abated), the share of counterfactual emissions abated (the same basis as the MAC curves).
- **Zero artefacts:** the replication code sets zero emissions to 10⁻⁶ before taking logs, so sectors moving to or from ~0 produce coefficients up to ±20 log points (e.g. Italy's "other transportation" −19.5 then +20.0). Breaks where the sector emits < 1 kt in the break year or the year before are dropped (56 of 233 CO2 breaks at p = 0.01), as are breaks in sectors EDGAR doesn't report for that country.
- **Specs:** gas (CO2, all GHG) × p-value (0.05, 0.01, 0.001) × year (2020, 2022) × window (all breaks since 1996, or only breaks after 2015, the same baseline as the policy counterfactuals) × direction (net, or negative breaks only). Only the OECD sample is used (38 countries); the EU15 runs repeat the same countries with a different comparison group.

**Totals across the 38 OECD countries, 2020** (μ, % of counterfactual emissions):

| Gas | p-value | All breaks, net | All breaks, negative only | Since 2015, net | Since 2015, negative only |
|---|---|---|---|---|---|
| CO2 | 0.05 | 6.9% (825 Mt) | 11.9% | 3.2% | 3.3% |
| CO2 | 0.01 | 9.3% (1,133 Mt) | 13.1% | 3.5% | 3.5% |
| CO2 | 0.001 | 5.9% (698 Mt) | 9.0% | −0.1% | 0.0% |
| All GHG | 0.01 | 7.4% (1,157 Mt CO2e) | 12.1% | 2.7% | 3.0% |

**Not a policy measure.** Breaks here are any country-specific shift not explained by GDP and population: market shocks, accidents and data revisions as much as policy. The largest are the US power sector (shale gas displacing coal), Japan's post-Fukushima power jump and Mexican reclassifications. Of the large ones, only the UK's carbon price floor (2015) and Ontario's coal phase-out (Canada 2005) are clearly policy. Use 7a for policy abatement; this version is kept as an upper-bound comparison.

**Findings:**
- **The US dominates.** Its power sector (−0.36 in 2006, −0.23 in 2017) and refining (−0.48 in 2005) breaks give 1.4 Gt of abatement (μ = 24%), 122% of the net CO2 total at p = 0.01. Without the US, net abatement across the other 37 countries is *negative* (μ = −3.8%).
- **Positive breaks are large.** Japan's +0.53 power-sector break in 2011 (Fukushima nuclear shutdown) is about −180 Mt. Mexico and Korea also have net positive breaks.
- **Since 2015, almost nothing.** Only 19 CO2 breaks fall after 2015 at p = 0.01, and the ~400 Mt is almost entirely the 2017 US power break. At p = 0.001 that break isn't detected and the since-2015 total is ~0.
- **No agreement with the policy intensity counterfactuals.** Rank correlations between break-implied μ and `policy_den_cntfc` / `policy_strng_cntfc` range from −0.27 to +0.26, none significant.

**Caveats:**
- Year fixed effects absorb anything common to the sample, such as EU-wide policy or the overall OECD decarbonisation trend. Breaks only measure country-specific deviations, so this is a lower bound on policy abatement, not total abatement. The paper itself calls the estimates minimum effect sizes.
- Gradual policy effects don't show up as steps.
- Totals hinge on a handful of large breaks and on the significance threshold.
- Positive breaks include data reclassifications (e.g. Mexico carbonate uses +1.7, a jump from 1.9 to 13.5 Mt) and non-climate events, which is why the negative-only version is also reported.

## 8. Green subsidies (World Bank)

`generate_green_subsidies.py` counts programs in the World Bank [Green Subsidies Database](https://www.worldbank.org/en/brief/2024/06/04/subsidies-and-trade) → `output/data/green_subsidies.csv`. `regress_green_subsidies.py` regresses each count, one regressor at a time, on own CSCC (specs 1–4) and population share, with HC1 SEs and Spearman ρ → `output/regressions/green_subsidies_regressions.csv`.

**No amounts.** The database lists 1,480 programs with environmental objectives (name, form, sector, objective, central or subnational) for 20 economies in 2017, 2018, 2021 and 2022. It reports no spending, so total spend and spend as % of GDP can't be measured. Program counts stand in: all programs, central government only, R&D/innovation as the primary objective, and all and R&D programs per $1tn of GDP. The year is 2022 and the EU-level row is dropped (n = 19).

| Outcome | Spec 2 CSCC | Specs 1, 3, 4 | Population share |
|---|---|---|---|
| All programs | +0.84/$\*\*\* (R² 0.90), ρ = 0.38 (p = 0.11) | ≈ 0, ρ ≈ 0 | ≈ 0 (p = 0.21) |
| R&D/innovation programs | +0.16/$\*\*\* (R² 0.82), ρ = 0.45 (p = 0.06) | ≈ 0, ρ ≈ −0.15 | ≈ 0 (p = 0.69) |
| Programs per $1tn GDP | ≈ 0 (p = 0.55) | negative (spec 3 p = 0.01, spec 4 p = 0.03), ρ ≈ −0.2 to −0.3 | ≈ 0 (p = 0.15) |
| R&D programs per $1tn GDP | ≈ 0 (p = 0.30) | ≈ 0, ρ ≈ −0.25 to −0.30 | −0.05 (p = 0.07) |

Without the US, China and India (n = 16), no spec 2 slope is significant. Specs 1, 3 and 4 turn negative, significantly so for spec 4 (all programs p < 0.001, R&D per GDP p < 0.001; ρ ≈ −0.3 to −0.5, p = 0.05–0.2).

**Findings:**
- **No evidence that higher damages mean more green subsidies.** The only positive result is spec 2, where the US's CSCC ($214/t, 2.7× China's) is an outlier, and the US also has 182 of the 391 country-level programs. That one point drives the fit; ranks are weakly positive and not significant. In the other specs, high-damage countries (India, Brazil, China per GDP) run few programs.
- **Scaled by GDP, the relationship is flat or negative.** Australia, Canada, the Netherlands and the UK have the most programs per unit of GDP and low CSCCs.
- **Country size doesn't predict program counts either,** unlike policy density (section 3).

**Caveats:**
- Counts treat a small grant and the IRA tax credits alike, so they say nothing about spending.
- The 20 economies aren't a random sample, and there are no zeros: every included country has at least one program.
- Subnational coverage is uneven (the US, China, Australia and the UK account for nearly all subnational programs), which is why the central-government count is also reported.
- With n = 19 and one dominant observation, HC1 SEs understate uncertainty (the spec 2 p-values are essentially leverage).

## 9. Green technology spending (OECD EPS, IEA)

`generate_green_spending.py` builds three spending or support measures in long format (`n, year, measure, value`) → `output/data/green_spending.csv`. `regress_green_spending.py` regresses each measure in each cross-section year on own CSCC (specs 1–4) and population share, one at a time, with and without a GDP per capita control. It uses HC1 SEs and reports the (partial) Spearman ρ → `output/regressions/green_spending_regressions.csv`. The EU row is dropped.

| Source | Measures | Years (n) |
|---|---|---|
| OECD EPS | `eps_rd_sub`: low-carbon public R&D expenditure, scored by its size relative to GDP (0–6). `eps_techsup`: technology support sub-index (R&D plus solar and wind support). | 2015, 2020 (40); EPS ends in 2020 |
| IEA Energy Technology RD&D Budgets | Public energy RD&D in million USD (y−1 prices, PPP): `rdd_total`, `rdd_low_carbon` (total minus fossil fuels) and `rdd_renewables`, each also as % of GDP | 2015, 2020 (29), 2024 (27), 2025 (13, provisional) |
| IEA Government Energy Spending Tracker | Government budget commitments in billion USD: `gest_clean` (clean energy investment support, i.e. everything but consumer energy affordability) and `gest_innovation` (the "Fuels and technology innovation" category: hydrogen, CCUS, batteries, biofuels, critical minerals), each also as % of GDP | 2020 (commitments starting in 2020), 2024 (all commitments since 2020 as of Sept 2024) (70) |

The EPS stops in 2020 and the spending tracker starts in 2020, so only the RD&D data cover all three years requested (2015, 2020, 2025). 2024 is added because 2025 RD&D is provisional and covers only 13 countries.

**Rank correlations with own CSCC, full sample** (specs 1 / 3 / 4, † p < 0.05):

| Measure | Year | No controls | + GDP per capita |
|---|---|---|---|
| EPS R&D score | 2015 | −0.44† / −0.43† / −0.43† | −0.28 / −0.30 / −0.26 |
| EPS R&D score | 2020 | −0.50† / −0.49† / −0.48† | −0.35† / −0.38† / −0.33† |
| Low-carbon RD&D, % GDP | 2015 | −0.45† / −0.42† / −0.44† | −0.30 / −0.33 / −0.31 |
| Low-carbon RD&D, % GDP | 2020 | −0.56† / −0.53† / −0.55† | −0.41† / −0.41† / −0.39† |
| Low-carbon RD&D, % GDP | 2024 | −0.46† / −0.42† / −0.45† | −0.32 / −0.31 / −0.31 |
| Low-carbon RD&D, % GDP | 2025 | −0.56† / −0.54 / −0.55† | −0.25 / −0.38 / −0.30 |
| Clean spending commitments, % GDP | 2020 | −0.32† / −0.33† / −0.33† | −0.10 / −0.10 / −0.05 |
| Clean spending commitments, % GDP | 2024 | −0.43† / −0.46† / −0.43† | −0.24† / −0.26† / −0.19 |

**Findings:**
- **Spec 2 and population pick up economy size.** Spec 2 CSCC has a rank correlation of 0.93 with log GDP. In *levels*, every RD&D and spending-tracker measure rises with spec 2 (ρ ≈ +0.4 to +0.85) and with population share. RD&D as % of GDP doesn't (ρ ≈ +0.1 to +0.3, not significant). Spending-tracker commitments as % of GDP do rise with spec 2 (ρ = +0.24 to +0.48) and with population share, so large economies committed relatively more after 2020. That is the only positive result, and it reflects size rather than damages per se.
- **Relative to GDP, spending falls with own CSCC in specs 1, 3 and 4.** The EPS R&D score, RD&D as % of GDP and clean commitments as % of GDP all fall with own CSCC (ρ ≈ −0.3 to −0.55, mostly significant). Norway, France, Finland and Switzerland are among the most RD&D-intensive countries and have low CSCCs. Mexico, Spain and Türkiye are among the least and have high ones. Japan is the exception (high on both).
- **Mostly income.** Richer countries have lower CSCCs (ρ = −0.23 to −0.38 with log GDP per capita) and spend more relative to GDP. With a GDP per capita control, the OLS slopes are mostly insignificant, but the partial rank correlations stay at about −0.3 and never turn positive.
- **Excluding the US, China and India doesn't change this.** None of the three is in the RD&D data after 2015 (see caveats), and dropping them from the spending tracker leaves the negative intensity results intact or stronger.
- Together with section 8, outside spec 2's size effect, nothing suggests that countries with higher own damages support green technology more, as a Nash model would predict.

**Caveats:**
- **The US has no RD&D data after 2015.** The IEA estimates US budgets from 2016 onwards, and the explorer API doesn't serve those estimates. China and India aren't IEA members, so the RD&D sample is OECD-heavy (29 countries).
- RD&D per GDP uses the IEA's own GDP (backed out of its RD&D per thousand GDP ratio, PPP basis). Spending-tracker per GDP uses WB current-USD GDP (2020 for the 2020 cohort, 2023 for the cumulative total).
- **Spending-tracker values are in billions.** The explorer labels them "million USD", but the values are billions (e.g. IRA Sec. 13101 = 51.06). They are commitments, multi-year and announced, not disbursed spending. The 2024 total includes tranches that start after 2024.
- Spending-tracker totals follow the tracker's own aggregation (summing every record with a start year, technology and budget). The tracker has no fossil-fuel categories, so `gest_clean` is all investment support.

## 10. Kitchen sink

`regress_kitchen_sink.py` regresses each outcome jointly on seven country characteristics, with HC1 SEs → `output/regressions/kitchen_sink_regressions.csv` (spec `main`). The outcome and all regressors are standardised (mean 0, SD 1) within each estimation sample, so coefficients are the SDs of outcome change per 1 SD of the regressor. Multiply by the outcome SD in the table to get $/t, €/t or EPS points. A sensitivity check (spec `interactions`) adds interactions of corruption and inequality with fossil-fuel assets.

| Regressor | Definition |
|---|---|
| Population share | % of world population, 2020 |
| CSCC, spec 2 | own country SCC (Ricke et al.), $/tCO2 |
| Corruption | V-Dem political corruption index (`v2x_corr`), 2020; 0–1, higher = more corrupt |
| Gini | WB Gini index, latest year 2010–2020 |
| Fossil fuel assets, 1995 | oil + natural gas + coal subsoil assets (CWON), trillion real 2019 US$ |
| Land area | million km², 2020 |
| GDP per capita | current US$, 2020 (WB WDI) |

Fossil-fuel wealth is measured by subsoil assets rather than rents. 1995 rents (% of GDP) were dropped: they are noisy and move with fuel prices. They are still computed and saved in `output/data/kitchen_sink_inputs.csv`. A fuel missing from the assets data counts as zero when the country reports either of the other two. New Zealand has no WB Gini, so it drops out. Earlier versions also included the MAC curve coefficient *a* and rents; dropping them adds seven countries to the Dolphin sample.

**Standardised coefficients (robust SE), full sample:**

| | Dolphin carbon price (2020) | OECD effective carbon rate (2021) | EPS climate (2020) |
|---|---|---|---|
| Population share | +0.04 (0.03) | +0.04 (0.04) | +0.17\*\* (0.08) |
| CSCC, spec 2 | −0.15\*\* (0.07) | −0.17\*\*\* (0.05) | +0.05 (0.08) |
| Corruption | −0.21\*\* (0.10) | −0.43\*\*\* (0.10) | −0.07 (0.16) |
| Gini | −0.14\*\* (0.06) | −0.17\*\*\* (0.06) | −0.25\*\* (0.11) |
| Fossil fuel assets, 1995 | −0.00 (0.11) | +0.11 (0.08) | −0.01 (0.13) |
| Land area | −0.04 (0.08) | −0.28\*\*\* (0.09) | −0.22\*\*\* (0.08) |
| GDP per capita | +0.43\*\* (0.22) | +0.36\*\*\* (0.12) | +0.51\*\*\* (0.17) |
| n | 128 | 70 | 39 |
| R² | 0.41 | 0.75 | 0.54 |
| Outcome SD | $10.8/t | €39.2/t | 1.07 points |

\* p < 0.1, \*\* p < 0.05, \*\*\* p < 0.01.

**Without the US, China and India** (n = 125, 67, 36), corruption (both prices), Gini, land area (OECD, EPS) and GDP per capita keep their signs and significance. The spec 2 CSCC coefficients become insignificant on all three outcomes (−0.09, +0.07, +0.26), and population share loses its EPS effect.

**Positive carbon prices only.** The model is re-estimated on the two carbon prices after dropping countries with a zero price (samples `positive_price` and `positive_price_no_us_chn_ind`; EPS isn't filtered). This drops 88 of 128 countries from the Dolphin sample, leaving 40, mostly European plus a few large emitters such as Canada, China, Japan, Korea, Mexico, South Africa and the US. It drops 4 of 70 from the OECD sample.

| | Dolphin, price > 0 | OECD, price > 0 |
|---|---|---|
| Population share | +0.00 (0.05) | +0.04 (0.05) |
| CSCC, spec 2 | −0.67\*\* (0.26) | −0.17\*\*\* (0.05) |
| Corruption | −0.37\*\* (0.16) | −0.41\*\*\* (0.11) |
| Gini | −0.35\*\* (0.14) | −0.17\*\*\* (0.06) |
| Fossil fuel assets, 1995 | +0.64\*\* (0.32) | +0.13\* (0.08) |
| Land area | +0.03 (0.10) | −0.31\*\*\* (0.10) |
| GDP per capita | +0.10 (0.19) | +0.37\*\*\* (0.13) |
| n | 40 | 66 |
| R² | 0.40 | 0.75 |
| Outcome SD | $15.5/t | €38.8/t |

Without the US, China and India the Dolphin positive-price results are unstable (n = 38): corruption and Gini become insignificant, while population share (−0.99) and spec 2 CSCC (+0.79) flip into significance with opposite signs. The OECD results are unchanged.

**Findings:**
- **Income is the strongest predictor.** A 1 SD increase in GDP per capita goes with a 0.4–0.5 SD higher outcome (about $5/t, €14/t and 0.5 EPS points), with or without the US, China and India. Among countries with a positive Dolphin price, though, income doesn't predict the level (+0.10): it mainly predicts *whether* a country prices carbon (section 10b).
- **Corruption and inequality lower carbon prices with income controlled.** Corruption is significant for both prices (−0.21 and −0.43 SD) but not EPS. Gini is significant on all three outcomes (−0.14 to −0.25 SD) and among positive prices. Both hold without the US, China and India.
- **Own CSCC is negative for both prices, but only because of the US, China and India.** Those three have the highest spec 2 CSCCs ($214, $80 and $47/t) and low or zero carbon prices. Without them, the CSCC coefficients are insignificant on all three outcomes. This is consistent with section 5.
- **Larger land area goes with a lower OECD rate and EPS score** (−0.28 and −0.22 SD). Population share is significant only for EPS, and only with the US, China and India included.
- **1995 fossil-fuel assets don't predict carbon pricing or stringency.** The full-sample coefficients are −0.00, +0.11 and −0.01, all insignificant. The one significant result, +0.64 among positive Dolphin prices, is Norway: it has large reserves and the highest Dolphin price ($66/t), and without it the coefficient falls to 0.19 (p = 0.38). The OECD positive-price coefficient (+0.13, p < 0.1) turns negative without Russia.

**Sensitivity: interactions.** Spec `interactions` adds corruption × assets and Gini × assets (each the standardised product of the standardised terms, so main effects are at the mean of the terms they interact with). The only consistent interaction is Gini × assets for the full-sample Dolphin price (+0.12, p < 0.01, with or without the US, China and India). That is a floor effect: 69% of the Dolphin sample prices at zero, including 86% of the more-unequal half, so assets have nothing to lower there. Among positive Dolphin prices the interactions change sign and are unstable: corruption × assets −0.25 (p < 0.05) in the full sample, Gini × assets −0.21 (p < 0.05) without the US, China and India, on about 40 observations. For EPS, corruption × assets is −0.36 (p < 0.05) only without the US, China and India (n = 36). Nothing is significant for the OECD rate. Adding the interactions leaves GDP per capita, corruption (both prices), Gini and land area (OECD, EPS) with the same signs and significance. The spec 2 CSCC coefficients become insignificant everywhere except among positive Dolphin prices.

**Caveats:**
- **The EPS regression has 8 parameters on 39 observations** (10 with interactions), so its coefficients are imprecise.
- **The Dolphin price is zero for most countries,** so the full-sample OLS mixes whether a country prices carbon at all with how much. Section 10b models the two separately.
- GDP per capita, corruption and Gini are strongly correlated (corruption and GDP per capita correlate −0.71 to −0.86), so their separate coefficients are imprecise.
- Regressors are in levels, so heavy-tailed ones (land area, assets, population, GDP per capita) are driven by a few countries, as the Norway and Russia results show.

### 10b. Tobit vs double hurdle for the Dolphin price

Two thirds of countries have a zero Dolphin price, so `regress_dolphin_hurdle.py` fits two models built for zero-heavy outcomes on the kitchen-sink regressors, by maximum likelihood with robust (sandwich) SEs:

- **Tobit:** one latent price drives both margins, price = max(0, Xβ + ε). Each regressor has one coefficient for whether a country prices carbon and how high.
- **Cragg double hurdle:** a probit for whether the price is positive, plus a truncated normal regression for the price given that it is positive, with separate coefficients. Tobit is the special case in which the probit coefficients equal β/σ, so a likelihood-ratio test of Tobit against the hurdle (df = number of probit coefficients) tests whether one process drives both.

Regressors are standardised. The price is divided by its SD ($10.8/t) but not centred, so zero stays the censoring point. Effects are reported as average marginal effects (AMEs, delta-method SEs). The main spec has the seven main effects; as in section 10, a sensitivity spec adds the two interactions.

**Likelihood-ratio tests: Tobit is rejected in every spec.**

| Spec | Sample | n (positive) | LR statistic | df | p |
|---|---|---|---|---|---|
| Main effects | full | 128 (40) | 30.8 | 8 | 0.0002 |
| Main effects | without US, China, India | 125 (38) | 28.7 | 8 | 0.0004 |
| With interactions | full | 128 (40) | 39.9 | 10 | < 0.0001 |
| With interactions | without US, China, India | 125 (38) | 38.0 | 10 | < 0.0001 |

**Average marginal effects, main effects spec, full sample (robust SE):**

| | Tobit: E[price] (SD) | Hurdle: P(price > 0) | Hurdle: E[price \| price > 0] (SD) |
|---|---|---|---|
| Population share | +0.05 (0.03) | −0.07 (0.06) | −2.04 (1.33) |
| CSCC, spec 2 | −0.04 (0.04) | +0.31 (0.19) | −0.22 (0.38) |
| Corruption | −0.34\*\*\* (0.09) | −0.12\*\*\* (0.04) | −1.40\* (0.74) |
| Gini | −0.11\* (0.06) | −0.03 (0.04) | −0.38 (0.23) |
| Fossil fuel assets, 1995 | +0.00 (0.10) | −0.05 (0.05) | +0.61\*\*\* (0.21) |
| Land area | −0.00 (0.06) | −0.03 (0.07) | −0.03 (0.08) |
| GDP per capita | +0.13\* (0.08) | +0.09\* (0.05) | −0.05 (0.14) |
| n | 128 | 128 | 40 |

The participation column is the change in the probability of pricing carbon per 1 SD of the regressor (e.g. −0.12 = 12 percentage points). The other two columns are in SDs of the price.

**Findings:**
- **Whether a country prices carbon and how much are different processes.** The LR test rejects Tobit at p ≤ 0.0004 in all four specs, so a single latent price is the wrong model. Tobit's coefficients average two margins that respond to different things.
- **Participation is about corruption and income.** A 1 SD increase in corruption lowers the probability of pricing carbon by 12 percentage points (p < 0.01), with or without the US, China and India. A 1 SD increase in GDP per capita raises it by 9–10 points (p < 0.1).
- **Own CSCC doesn't predict participation.** The spec 2 CSCC AME is +0.31 (p = 0.10), driven by the US and China, which have high CSCCs and (sub-national or national) carbon prices. Without the US, China and India it is +0.04.
- **Among pricers, corruption goes with lower prices** (−1.40 SD, p < 0.1), and income doesn't. This matches the positive-price OLS above. The asset effect on the price level (+0.61, p < 0.01) is Norway again: without it, −0.42 (p = 0.79).
- **The intensity stage is poorly identified.** It has 38–40 observations, and prices are very right-skewed (Norway, Sweden and Finland are above $55/t). The truncated model therefore fits them as the far tail of a latent price centred well below zero, which inflates its marginal effects. Without the US, China and India, population share (−4.87 SD), spec 2 CSCC (+2.15 SD) and land area (−0.92 SD) become significant. With so few observations this instability, like the positive-price OLS, shouldn't be read as evidence.
- **Sensitivity: interactions.** Adding the two interactions doesn't change this, and Tobit is still rejected (p < 0.0001).

## 11. Timing of carbon price adoption

Section 10b found that the clearest signal is in *whether* a country prices carbon. The cross-sections use one year, so a time-invariant regressor like own CSCC has one observation per country however many years are pooled. The timing of adoption adds information instead. `regress_carbon_price_adoption.py` models *when* countries first adopt a positive Dolphin price, using 35 years of timing variation → `output/regressions/carbon_price_adoption_hazard.csv`.

`generate_policy_panel.py` builds the country-year panel it uses → `output/data/policy_panel.csv`:
- the Dolphin price, annual 1989–2024;
- log GDP per capita (constant 2015 US$) and V-Dem corruption;
- EU membership and EU ETS coverage (EU members from 2005; Norway, Iceland and Liechtenstein from 2008);
- the time-invariant kitchen-sink characteristics and own CSCC (all four specs).

**Method:**
- **Discrete-time hazard.** Each country is at risk from 1990 until its first year with a positive Dolphin price; that year is the event and later years are dropped.
- **Complementary log-log GLM.** This is the discrete-time analogue of a Cox proportional hazards model, so exp(coef) is a hazard ratio: the proportional change in the yearly adoption probability per 1 SD of the regressor. Standard errors are clustered by country.
- **Regressors.** Slim: own CSCC, log GDP per capita (t−1) and corruption (t−1). Full adds Gini, 1995 fossil assets, land area and population share. All are standardised, and every model includes a cubic in calendar time (the baseline hazard) and an EU ETS coverage dummy.
- **Samples.** 19 of the 44 adoptions are EU members in 2005, which came with the EU ETS rather than a national decision. The non-EU samples drop ever-EU members (the UK included), leaving 19 adoptions: Norway 1991, Canada 2007, Switzerland and Iceland 2008, the US 2009, New Zealand 2010, Ukraine 2011, Japan and Australia 2012, China 2013, Kazakhstan and Mexico 2014, Korea 2015, Chile and Colombia 2017, Argentina 2018, Singapore and South Africa 2019, Uruguay 2022 and Indonesia 2023.

**Hazard ratios, CSCC spec 2:**

| | Slim: all | Slim: non-EU | Slim: non-EU, no US/CHN/IND | Full: all | Full: non-EU | Full: non-EU, no US/CHN/IND |
|---|---|---|---|---|---|---|
| CSCC, spec 2 | 1.13\*\* | 1.21\*\*\* | 1.15 | 1.07 | 1.11 | 0.67 |
| Log GDP per capita (t−1) | 2.75\*\*\* | 3.38\*\*\* | 3.15\*\*\* | 3.08\*\*\* | 4.24\*\*\* | 5.71\*\*\* |
| Corruption (t−1) | 0.53\* | 0.67 | 0.63 | 0.57 | 0.72 | 0.60 |
| Gini | | | | 0.76 | 0.95 | 0.90 |
| Fossil fuel assets, 1995 | | | | 0.74 | 0.72 | 0.79 |
| Land area | | | | 1.33\*\* | 1.43\* | 1.25 |
| Population share | | | | 1.32\*\* | 1.42\*\* | 2.39\*\*\* |
| Countries | 159 | 134 | 131 | 127 | 103 | 100 |
| Adoptions | 44 | 19 | 17 | 42 | 18 | 16 |

A hazard ratio above 1 means earlier adoption (e.g. 2.75 = the yearly adoption probability is 2.75× higher per 1 SD).

**Own CSCC hazard ratio, all four specs:**

| Covariates | Sample | Spec 1 | Spec 2 | Spec 3 | Spec 4 |
|---|---|---|---|---|---|
| Slim | all | 0.85 | 1.13\*\* | 0.70 | 1.31 |
| Slim | non-EU | 0.78 | 1.21\*\*\* | 0.60 | 1.44\*\* |
| Slim | non-EU, no US/CHN/IND | 0.49\*\* | 1.15 | 0.57\*\* | 0.98 |
| Full | all | 0.69 | 1.07 | 0.69 | 0.92 |
| Full | non-EU | 0.62 | 1.11 | 0.61 | 0.99 |
| Full | non-EU, no US/CHN/IND | 0.50\*\*\* | 0.67 | 0.51\*\*\* | 0.87 |

**Findings:**
- **Income drives adoption timing.** 1 SD higher GDP per capita multiplies the yearly adoption probability by 2.8–5.7 (p < 0.01) in every sample and covariate set. Rich countries adopt carbon pricing first.
- **Own CSCC doesn't speed adoption.** Spec 2 (HR 1.13–1.21) is significant only in the slim model with the US and China included, both early large adopters with high spec 2 CSCCs. It vanishes once size is controlled (full: 1.07–1.11) or the US, China and India are dropped. Specs 1 and 3 point the other way: without the US, China and India, higher-CSCC countries adopt *later* (HR 0.49–0.57, p < 0.05).
- **Larger countries adopt earlier** (population share HR 1.3–2.4, land area 1.3–1.4) once income is controlled. That is consistent with section 3's finding that larger countries have more climate policies, and the opposite of a free-rider story in which small countries hold back.
- **Corruption delays adoption** in the full sample (HR 0.53, p < 0.1), but not significantly outside the EU. 1995 fossil assets and Gini are insignificant.

**Caveats:**
- **Only 16–19 adoptions outside the EU,** with 7–10 regressors plus the time cubic, so the non-EU full models are thin.
- **Adoption is any positive Dolphin price,** including sub-national schemes (RGGI for the US, provincial schemes for Canada, pilot ETSs for China) and very low coverage. The adoption year therefore marks a country's first carbon price, however small.
- The Gini, land area and population share regressors are measured around 2020, after many adoptions.

# Known issues

- **No EU aggregate in the RICE data,** and the CSCC `eu` row lacks policy counts, stringency levels and carbon prices.
- **Policy counterfactuals end in 2022,** so there is no true 2025 comparison.
- **`input/lobbymap/` and `input/policy_stringency/` aren't in `.gitignore`,** unlike the other downloaded inputs (the EPS file is 4.6MB).

# TODO

- Run with maxiso3 and the latest RICE50x version rather than the 2021 results
- Integrate empirical emissions
- RICE50x run with the EU as a coalition
