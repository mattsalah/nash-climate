python generate_cscc_vs_cntfc.py
python generate_implied_carbon_price.py
python generate_eps_stringency.py
python generate_structural_break_abatement.py
python generate_policy_break_abatement.py
python generate_green_subsidies.py
python generate_green_spending.py
python generate_lobbymap_country_scores.py
python generate_rice_vs_cntfc.py
python plot_MAC_MAB.py ind 1 --outcome both
python plot_MAC_MAB.py nld 2 --outcome both
python plot_MAC_MAB.py eu 2 --outcome both
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 1
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 2
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 3
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 4
python plot_pred_vs_policy.py 2022 --dataset rice --spec 1
python plot_pred_vs_policy.py 2022 --dataset rice --spec 2
python plot_pred_vs_policy.py 2022 --dataset rice --spec 3
python plot_pred_vs_policy.py 2022 --dataset rice --spec 4
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 1 --outcome strng
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 2 --outcome strng
python plot_pred_vs_policy.py 2022 --dataset rice --spec 1 --outcome strng
python report_regression_coeffs.py
python regress_population.py
python regress_eps_stringency.py
python regress_carbon_price_cscc.py
python regress_green_subsidies.py
python regress_green_spending.py
