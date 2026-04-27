python generate_cscc_vs_cntfc.py
python generate_rice_vs_cntfc.py 2022
python plot_MAC_MAB.py usa 1
python plot_MAC_MAB.py chn 1
python plot_MAC_MAB.py ind 1
python plot_MAC_MAB.py usa 1 --outcome both
python plot_MAC_MAB.py chn 1 --outcome both
python plot_MAC_MAB.py ind 1 --outcome both
python plot_MAC_MAB.py usa 1 --no-global-scc
python plot_MAC_MAB.py usa 2 --no-global-scc
python plot_MAC_MAB.py usa 3 --no-global-scc
python plot_MAC_MAB.py usa 4 --no-global-scc
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 1
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 2
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 3
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 4
python plot_pred_vs_policy.py 2022 --dataset rice --spec 1
python plot_pred_vs_policy.py 2022 --dataset rice --spec 2
python plot_pred_vs_policy.py 2022 --dataset rice --spec 3
python plot_pred_vs_policy.py 2022 --dataset rice --spec 4
python plot_pred_vs_policy.py 2020 --dataset cscc --spec 1 --outcome strng
python plot_pred_vs_policy.py 2022 --dataset rice --spec 1 --outcome strng
python report_regression_coeffs.py