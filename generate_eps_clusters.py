import os
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, squareform

# Do countries fall into groups that went in a price or a non-price direction? Each country's
# 2000-2020 path of the two EPS climate parts (generate_eps_stringency.py) is one point:
#   eps_carbon_price   CO2 tax and CO2 trading scheme
#   eps_nonprice       renewable trading schemes, low-carbon R&D, solar and wind support
# both 0-6, so 42 features on one scale, left unstandardised. K-means with k-means++ starts,
# best of RESTARTS by within-cluster sum of squares, for k = 2..6. Silhouette scores and
# agreement with Ward hierarchical clustering (adjusted Rand index) are printed for each k;
# memberships are saved for K

panel_filename = 'output/data/eps_stringency_panel.csv'
cluster_filename = 'output/data/eps_clusters.csv'
centroid_filename = 'output/data/eps_cluster_centroids.csv'
diagnostics_filename = 'output/regressions/eps_cluster_diagnostics.csv'

PARTS = ['eps_carbon_price', 'eps_nonprice']
YEARS = range(2000, 2021)
K_RANGE = range(2, 7)
K = 4
RESTARTS = 500
SEED = 0

###### DATA #######

panel = pd.read_csv(panel_filename)
panel = panel[panel['year'].isin(YEARS)]
names = panel.groupby('n')['country'].first()
F = panel.set_index(['n', 'year'])[PARTS].unstack('year')
assert not F.isna().any().any(), "EPS panel has gaps"
X = F.values

###### CLUSTERING #######

rng = np.random.default_rng(SEED)

def kmeans(X, k):
    best_sse, best_lab = np.inf, None
    for _ in range(RESTARTS):
        centres = [X[rng.integers(len(X))]]
        for _ in range(k - 1):
            d2 = ((X[:, None] - np.array(centres)[None]) ** 2).sum(-1).min(1)
            centres.append(X[rng.choice(len(X), p=d2 / d2.sum())])
        centres = np.array(centres)
        for _ in range(200):
            lab = ((X[:, None] - centres[None]) ** 2).sum(-1).argmin(1)
            new = np.array([X[lab == j].mean(0) if (lab == j).any() else centres[j] for j in range(k)])
            if np.allclose(new, centres):
                break
            centres = new
        sse = ((X - centres[lab]) ** 2).sum()
        if sse < best_sse:
            best_sse, best_lab = sse, lab
    return best_lab, best_sse

def silhouette(D, lab):
    s = []
    for i in range(len(lab)):
        same = lab == lab[i]
        if same.sum() == 1:
            s.append(0.0)
            continue
        a = D[i, same].sum() / (same.sum() - 1)
        b = min(D[i, lab == j].mean() for j in set(lab) if j != lab[i])
        s.append((b - a) / max(a, b))
    return float(np.mean(s))

def adjusted_rand(a, b):
    from math import comb
    ct = pd.crosstab(a, b).values
    sc = sum(comb(int(x), 2) for x in ct.ravel())
    sa = sum(comb(int(x), 2) for x in ct.sum(1))
    sb = sum(comb(int(x), 2) for x in ct.sum(0))
    expected = sa * sb / comb(len(a), 2)
    return (sc - expected) / ((sa + sb) / 2 - expected)

D = squareform(pdist(X))
ward = linkage(X, 'ward')
diag, labels = [], {}
for k in K_RANGE:
    lab, sse = kmeans(X, k)
    labels[k] = lab
    diag.append({'k': k, 'sse': sse, 'silhouette': silhouette(D, lab),
                 'ari_vs_ward': adjusted_rand(lab, fcluster(ward, k, 'maxclust')),
                 'smallest_cluster': int(np.bincount(lab).min())})
diag = pd.DataFrame(diag)

###### NAMES #######

# name the K clusters from their 2020 centroids, so names follow the data rather than run order:
# highest price score -> high price; lowest price + non-price -> low on both; of the other two, the
# one with the larger non-price minus price gap -> non-price-led, the other -> moderate price (it
# must have a price score above its non-price score)
lab = labels[K]
c2020 = pd.DataFrame({p: F[p][2020] for p in PARTS}).groupby(lab).mean()
assert K == 4, "naming rule below is written for four clusters"
price_led = c2020['eps_carbon_price'].idxmax()
low = c2020.sum(axis=1).drop(price_led).idxmin()
rest = c2020.drop([price_led, low])
nonprice_led = (rest['eps_nonprice'] - rest['eps_carbon_price']).idxmax()
moderate = rest.index.drop(nonprice_led)[0]
assert c2020.loc[moderate, 'eps_carbon_price'] > c2020.loc[moderate, 'eps_nonprice'], "naming rule doesn't fit"
NAMES = {price_led: 'High price', moderate: 'Moderate price', nonprice_led: 'Non-price-led', low: 'Low on both'}
ORDER = ['High price', 'Moderate price', 'Non-price-led', 'Low on both']

clusters = pd.DataFrame({'n': F.index, 'country': names.reindex(F.index).values,
                         'cluster': [NAMES[l] for l in lab]})
clusters['cluster_order'] = clusters['cluster'].map(ORDER.index)
for p in PARTS:
    clusters[f'{p}_2000'] = F[p][2000].values
    clusters[f'{p}_2020'] = F[p][2020].values
clusters = clusters.sort_values(['cluster_order', 'n'])

centroids = (panel.merge(clusters[['n', 'cluster', 'cluster_order']], on='n')
             .groupby(['cluster_order', 'cluster', 'year'])[PARTS].mean().reset_index())
centroids.insert(3, 'n_countries', centroids['cluster'].map(clusters['cluster'].value_counts()))

###### SAVE ################

for f in (cluster_filename, centroid_filename, diagnostics_filename):
    os.makedirs(os.path.dirname(f), exist_ok=True)
clusters.to_csv(cluster_filename, index=False)
centroids.to_csv(centroid_filename, index=False)
diag.to_csv(diagnostics_filename, index=False)

pd.set_option('display.width', 200)
print(f"{len(F)} countries, {X.shape[1]} features ({len(PARTS)} parts x {len(YEARS)} years)\n")
print(diag.to_string(index=False, float_format='{:.3f}'.format))
print(f"\nk = {K}:")
summary = clusters.groupby('cluster', sort=False).agg(
    n=('n', 'size'), **{f'{p}_{y}': (f'{p}_{y}', 'mean') for p in PARTS for y in (2000, 2020)},
    members=('n', ' '.join))
print(summary.to_string(float_format='{:.2f}'.format))
print(f"\nSaved {cluster_filename}, {centroid_filename} and {diagnostics_filename}")
