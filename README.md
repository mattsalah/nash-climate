# nash-climate

Do countries' climate policies look like a non-cooperative (Nash) equilibrium, where each country abates only up to its own country-level social cost of carbon (CSCC), or like the cooperative optimum at the global SCC?

The pipeline compares predicted abatement under both benchmarks with the abatement that countries' policies actually delivered. Predicted abatement comes from RICE50x marginal abatement cost (MAC) curves combined with Ricke et al. (2018) CSCCs, plus the RICE50x results of Gazzotti et al. (2021). Delivered abatement is the counterfactual emissions avoided by policy density and stringency since 2015. Observed carbon prices and the OECD Environmental Policy Stringency index are also used.

# Key findings

1. **Predicted Nash abatement vs delivered abatement:** policy-density-implied abatement rises with predicted Nash abatement in the full sample (CSCC and RICE, most specs). The relationship is fragile without the US, China and India. Stringency-implied abatement is flat, and turns negative without those three.
2. **CSCC vs carbon prices:** carbon prices *fall* with own CSCC on all three measures (OECD, Dolphin, EPS carbon pricing score), mostly in ranks (Spearman ρ ≈ −0.4 to −0.6 in specs 1, 3 and 4). Controlling for GDP per capita weakens it but the rank relationship survives (partial ρ ≈ −0.3 to −0.46). It is mostly a contrast between Europe (low CSCCs, high prices) and the rest of the world: within Europe and outside Europe, the relationship is close to zero once GDP per capita is controlled.
3. **Implied carbon prices:** the abatement policies delivered implies carbon prices of $0–31/t in 2020 ($0–57/t in 2022). That is far below the global SCC ($135–781/t), so no country is near the cooperative benchmark. Implied prices are unrelated to actual carbon prices and show no consistent link with own CSCC.
4. **Country size:** larger countries have *more* policies but not *more stringent* ones. Population predicts policy counts strongly but not stringency. Explicit carbon pricing on the OECD EPS is lower in large countries, which are also the ones with the most predicted Nash abatement.
5. **Robustness:** controlling for lobbying (LobbyMap) or treating the EU as one cooperative player doesn't change these conclusions. The lobbying measure mostly proxies economy size, and the EU bloc's predicted Nash abatement is about zero.

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
| Country-level SCC (Ricke et al. 2018) | [Nature Climate Change, MOESM](https://www.nature.com/articles/s41558-018-0282-y#MOESM1) | `input/country_scc/` |
| OECD effective carbon rates | [OECD data explorer](https://data-explorer.oecd.org/vis?lc=en&fs[0]=Topic%2C1%7CTaxation%23TAX%23%7CTax%20and%20environment%23TAX_ENV%23&pg=0&fc=Topic&bp=true&snb=7&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_NECR%40DF_NECRS&df[ag]=OECD.CTP.TPS&dq=._T._T.ECRATE%2BNETECR..EUR_TCO2E.MEANW.Q.A&to[TIME_PERIOD]=false&pd=2020%2C&vw=tb) | `input/carbon_pricing/carbon_pricing_oecd.csv` |
| Dolphin & Merkle (2024) carbon prices | [ecp_CO2.csv](https://github.com/g-dolphin/ECP/blob/main/_output/_dataset/v2025.0/ecp/ipcc/ecp_economy/ecp_CO2.csv) | `input/carbon_pricing/carbon_pricing_dolphin.csv` |
| World Bank WDI population and GDP per capita | `WB_WDI_SP_POP_TOTL`, `WB_WDI_NY_GDP_PCAP_CD` | `input/wb_controls/pop_gdp_2015_2025.csv` |
| OECD Environmental Policy Stringency (EPS) | [OECD data explorer](https://data-explorer.oecd.org/vis?lc=en&df[ds]=dsDisseminateFinalDMZ&df[id]=DSD_EPS%40DF_EPS&df[ag]=OECD.ECO.MAD&dq=.A..&pd=,&to[TIME_PERIOD]=false&vw=tb), see below | `input/policy_stringency/oecd_eps.csv` |
| LobbyMap scores and headquarters | [LobbyMap](https://lobbymap.org/LobbyMapScores), already saved; refresh with `python fetch_lobbymap.py` (~40 min) | `input/lobbymap/lobbymap_scores.csv` |

The EPS file covers all countries, years and instruments, downloaded through the SDMX API:
```
curl -L -o input/policy_stringency/oecd_eps.csv "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EPS@DF_EPS,/.A..?dimensionAtObservation=AllDimensions&format=csvfilewithlabels"
```

# Pipeline

First run `gams extract_macc.gms` and `policy_intensity_counterfactuals.do` (Stata). Then `execute.sh` runs everything else:

| Step | Script | Output |
|---|---|---|
| CSCC dataset | `generate_cscc_vs_cntfc.py` | `output/data/mitigation_cscc_v_cntfc_2020.csv` |
| Implied carbon prices | `generate_implied_carbon_price.py` | `output/data/implied_carbon_price_{2020,2022}.csv`, `output/regressions/implied_price_correlations.csv` |
| EPS stringency | `generate_eps_stringency.py` | `output/data/eps_stringency_2020.csv` |
| LobbyMap country scores | `generate_lobbymap_country_scores.py` | `output/data/lobbymap_country_scores.csv` |
| RICE dataset | `generate_rice_vs_cntfc.py` | `output/data/mitigation_rice_v_cntfc_2022.csv` |
| MAC/MAB charts | `plot_MAC_MAB.py <country> <spec>` | `output/charts/mac_mab_*.png` |
| Predicted vs policy charts | `plot_pred_vs_policy.py <year> --dataset cscc\|rice --spec N` | `output/charts/{cscc,rice}_*plot_*.png` |
| Main regressions | `report_regression_coeffs.py` | `output/regressions/_regression_coefficients_table.csv` |
| Population regressions | `regress_population.py` | `output/regressions/population_regressions.csv` |
| EPS regressions | `regress_eps_stringency.py` | `output/regressions/eps_stringency_regressions.csv` |
| Carbon price vs CSCC by region | `regress_carbon_price_cscc.py` | `output/regressions/carbon_price_cscc_regressions.csv` |

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

# Known issues

- **No EU aggregate in the RICE data,** and the CSCC `eu` row lacks policy counts, stringency levels and carbon prices.
- **Policy counterfactuals end in 2022,** so there is no true 2025 comparison.
- **`input/lobbymap/` and `input/policy_stringency/` aren't in `.gitignore`,** unlike the other downloaded inputs (the EPS file is 4.6MB).

# TODO

- Run with maxiso3 and the latest RICE50x version rather than the 2021 results
- Integrate empirical emissions
- RICE50x run with the EU as a coalition
