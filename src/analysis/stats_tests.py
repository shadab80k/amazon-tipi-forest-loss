"""
Statistical analysis for the TIPI forest-loss study.

Primary comparisons (paired, unit = Indigenous Land):
  inside vs 0-10 km ring, inside vs 10-50 km ring, on loss share
  (share of year-2000 tree cover with >30% canopy lost 2000-2023).
  -> Wilcoxon signed-rank + paired t, Cohen's dz, rank-biserial r.

Secondary:
  - group contrast TIPI vs other TIs inside-zone (Mann-Whitney U)
  - Spearman correlations of loss with road/city distance
  - concentration of pressure (Gini, top-quintile share)
Holm-Bonferroni adjustment within the family of primary+secondary tests.

Outputs:
  results/summary_stats.csv, results/statistical_tests.csv,
  results/key_stats.json
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RES = os.path.join(ROOT, "results")


def cohen_dz(x, y):
    d = x - y
    return float(d.mean() / d.std(ddof=1)) if d.std(ddof=1) > 0 else np.nan


def rank_biserial_wilcoxon(x, y):
    """Effect size r for paired Wilcoxon: (sum r+ - sum r-) / (sum r+ + sum r-)."""
    d = x - y
    d = d[d != 0]
    if len(d) == 0:
        return np.nan
    ranks = stats.rankdata(np.abs(d))
    rp = ranks[d > 0].sum()
    rm = ranks[d < 0].sum()
    return float((rp - rm) / (rp + rm))


def gini(arr):
    a = np.sort(np.asarray(arr, dtype=float))
    n = len(a)
    if n == 0 or a.sum() == 0:
        return np.nan
    cum = np.cumsum(a)
    return float((n + 1 - 2 * (cum / cum[-1]).sum()) / n)


def holm_bonferroni(pvals):
    """Holm-Bonferroni step-down adjusted p-values, indexed like the input."""
    arr = np.asarray(pvals, float)
    order = np.argsort(arr)
    m = len(arr)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        val = (m - rank) * arr[i]
        running = max(running, val)
        adj[i] = min(1.0, running)
    return adj


def main() -> int:
    z = pd.read_csv(os.path.join(RES, "zonal_results.csv"))
    acc = pd.read_csv(os.path.join(RES, "accessibility.csv"))
    z = z.merge(acc, on=["ti_name", "has_isolated"], how="left")

    wide = z.pivot(index=["ti_name", "has_isolated", "uf", "area_ha_official",
                          "dist_highway_km", "dist_city_km"],
                   columns="zone",
                   values=["loss_share_tree2000", "tree2000_px", "loss_px_2000_2023",
                           "tree2000_ha_approx", "loss_ha_approx", "zone_area_ha"])
    wide.columns = [f"{v}_{zn.replace('ring0_10km','ring1').replace('ring10_50km','ring2')}"
                    for v, zn in wide.columns]
    wide = wide.reset_index()

    tipi = wide[wide.has_isolated].copy()
    others = wide[~wide.has_isolated].copy()
    print(f"TIPI n={len(tipi)}; other TIs in extent n={len(others)}")

    # validity: need tree pixels in both zones for paired comparison
    tipi_v = tipi[(tipi.tree2000_px_inside > 0) & (tipi.tree2000_px_ring1 > 0)
                  & (tipi.tree2000_px_ring2 > 0)].copy()
    print(f"valid paired units: {len(tipi_v)}")

    tests = []
    pvals = []

    def paired(name, x, y):
        x = np.asarray(x, float); y = np.asarray(y, float)
        w = stats.wilcoxon(x, y, zero_method="wilcox", alternative="two-sided")
        t = stats.ttest_rel(x, y)
        n = int(np.sum((x - y) != 0))
        tests.append({"test": name, "n_pairs_with_diff": n,
                      "median_inside": float(np.median(x)),
                      "median_ring": float(np.median(y)),
                      "mean_inside": float(np.mean(x)), "mean_ring": float(np.mean(y)),
                      "wilcoxon_W": float(w.statistic), "wilcoxon_p": float(w.pvalue),
                      "paired_t": float(t.statistic), "paired_t_p": float(t.pvalue),
                      "cohens_dz": cohen_dz(x, y),
                      "rank_biserial_r": rank_biserial_wilcoxon(x, y)})
        pvals.append(w.pvalue)

    paired("inside_vs_ring1_loss_share", tipi_v.loss_share_tree2000_inside,
           tipi_v.loss_share_tree2000_ring1)
    paired("inside_vs_ring2_loss_share", tipi_v.loss_share_tree2000_inside,
           tipi_v.loss_share_tree2000_ring2)

    # group contrast (unpaired): TIPI vs others, inside zone
    others_v = others[others.tree2000_px_inside > 0]
    u = stats.mannwhitneyu(tipi_v.loss_share_tree2000_inside,
                           others_v.loss_share_tree2000_inside, alternative="two-sided")
    # rank-biserial for MWU
    n1, n2 = len(tipi_v), len(others_v)
    rbc = 2 * u.statistic / (n1 * n2) - 1
    tests.append({"test": "TIPI_vs_others_inside_MWU", "n_pairs_with_diff": 0,
                  "median_tipi": float(np.median(tipi_v.loss_share_tree2000_inside)),
                  "median_others": float(np.median(others_v.loss_share_tree2000_inside)),
                  "mannwhitney_U": float(u.statistic), "mwu_p": float(u.pvalue),
                  "rank_biserial_r": float(rbc)})
    pvals.append(u.pvalue)

    # correlations (ring1 pressure vs accessibility)
    for cov in ["dist_highway_km", "dist_city_km"]:
        sub = tipi_v[[cov, "loss_share_tree2000_ring1", "loss_share_tree2000_inside"]].dropna()
        rho1, p1 = stats.spearmanr(sub[cov], sub.loss_share_tree2000_ring1)
        tests.append({"test": f"spearman_{cov}_vs_ring1", "n": len(sub),
                      "rho": float(rho1), "p": float(p1)})
        pvals.append(p1)

    adj = holm_bonferroni(pvals)
    for i, a in enumerate(adj):
        tests[i]["p_holm_adj"] = float(a)

    tdf = pd.DataFrame(tests)
    tdf.to_csv(os.path.join(RES, "statistical_tests.csv"), index=False)

    # concentration of pressure
    g1 = gini(tipi_v.loss_share_tree2000_ring1)
    q_share = float(np.sort(tipi_v.loss_share_tree2000_ring1.values)[-max(1, len(tipi_v)//5):].sum()
                    / tipi_v.loss_share_tree2000_ring1.sum())
    # summary stats table
    desc = []
    for _, r in pd.concat([tipi_v.assign(grp="TIPI"), others_v.assign(grp="OtherTIs")]).groupby("grp"):
        pass
    for grp, dff in [("TIPI", tipi_v), ("OtherTIs", others_v)]:
        for zn in ["inside", "ring1", "ring2"]:
            desc.append({
                "group": grp, "zone": zn, "n": len(dff),
                "median_loss_share": float(dff[f"loss_share_tree2000_{zn}"].median()),
                "mean_loss_share": float(dff[f"loss_share_tree2000_{zn}"].mean()),
                "iqr_lo": float(dff[f"loss_share_tree2000_{zn}"].quantile(.25)),
                "iqr_hi": float(dff[f"loss_share_tree2000_{zn}"].quantile(.75)),
                "median_tree2000_ha": float(dff[f"tree2000_ha_approx_{zn}"].median()),
                "total_loss_ha": float(dff[f"loss_ha_approx_{zn}"].sum()),
                "median_dist_highway_km": float(dff["dist_highway_km"].median()),
            })
    ddf = pd.DataFrame(desc)
    ddf.to_csv(os.path.join(RES, "summary_stats.csv"), index=False)

    key = {
        "n_tipi": int(len(tipi_v)),
        "n_other_tis": int(len(others_v)),
        "gini_ring1": g1,
        "top20pct_share_ring1": q_share,
        "tests": tests,
        "window": "2000-2023 (GFC-2023-v1.11, canopy>30%)",
        "zones": "inside TI; 0-10 km ring; 10-50 km ring",
    }
    with open(os.path.join(RES, "key_stats.json"), "w") as f:
        json.dump(key, f, indent=1, default=float)
    print(tdf.to_string(max_colwidth=40))
    print("\n-> statistical_tests.csv, summary_stats.csv, key_stats.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
