# Data Dictionary & Provenance Documentation

This directory contains the derived, aggregated tabular datasets used in the study:

> **"Forest Loss Pressure on Indigenous Lands with Uncontacted Peoples in the Brazilian Amazon: An Open-Data Geospatial Assessment (2000–2023)"**

---

## 1. Ethical Governance & Non-Disclosure Notice
In strict accordance with Brazil's 1987 no-contact policy, ILO Convention 169, and international Indigenous data sovereignty principles, **no individual-level sighting coordinates, encampment locations, or sensitive point layers are published in this repository**. All data are aggregated to officially gazetted Indigenous Land (*Terra Indígena*) boundaries.

---

## 2. File Descriptions & Variable Schema

### 2.1 `zonal_results.csv` (708 rows $\times$ 39 columns)
The primary output of the 30-meter Hansen Global Forest Change (v1.11) zonal extraction engine. Each of the 236 territories (81 TIPI + 155 matched controls) has exactly 3 rows corresponding to its spatial zones (`inside`, `ring0_10km`, `ring10_50km`).

- `ti_name` (string): Official name of the Indigenous Land registered with FUNAI.
- `has_isolated` (boolean): `True` if territory hosts documented presence of uncontacted peoples (TIPI); `False` for control territories.
- `is_control` (boolean): `True` if territory belongs to the matched-control cohort.
- `uf` (string): Brazilian Federal State (e.g., AM, PA, MT, RO, MA, RR, AC).
- `fase` (string): Legal administrative demarcation stage (*Regularizada*, *Declarada*, *Delimitada*, *Homologada*, *Encaminhada*).
- `area_ha_official` (float): Officially gazetted territory surface area in hectares.
- `area_ha_geom` (float): Geodesic surface area in hectares calculated in EPSG:6933.
- `zone` (string): Analytical zone:
  - `inside`: Territory interior polygon.
  - `ring0_10km`: 0 to 10 km concentric buffer ring.
  - `ring10_50km`: 10 to 50 km concentric landscape buffer ring.
- `tree2000_px` (integer): Total pixel count of tree canopy cover (>30% threshold) in base year 2000.
- `loss_px_2000_2023` (integer): Total forest loss pixels detected over the 24-year study window (2001–2023).
- `loss_share_tree2000` (float): Primary response variable: $\frac{\text{loss\_px\_2000\_2023}}{\text{tree2000\_px}}$ (fraction of base tree cover lost).
- `tree2000_ha_approx` (float): Approximated tree cover area in hectares in 2000.
- `loss_ha_approx` (float): Approximated gross forest loss in hectares (2000–2023).
- `zone_area_ha` (float): Total geographic area of the zone in hectares.
- `loss_px_y2001` to `loss_px_y2023` (integers): Annual loss pixel counts for each individual year from 2001 to 2023.

---

### 2.2 `accessibility.csv` (647 rows $\times$ 5 columns)
Accessibility and distance covariates calculated from territory boundaries in EPSG:6933:
- `ti_name` (string): Indigenous Land name.
- `has_isolated` (boolean): TIPI designation.
- `dist_highway_km` (float): Euclidean distance (km) to nearest linear utility/pipeline corridor (`opi_ti_dutovias`).
- `dist_railway_km` (float): Euclidean distance (km) to nearest railway project/track (`opi_ti_ferrovias`).
- `dist_city_km` (float): Euclidean distance (km) to nearest municipal urban center (`opi_cidades`).

---

### 2.3 `summary_stats.csv` & `statistical_tests.csv`
Summary descriptive tables (medians, means, IQRs, totals) and formal hypothesis test outputs (Wilcoxon signed-rank $W$, paired $t$, Mann-Whitney $U$, Spearman $\rho$, Cohen's $d_z$, rank-biserial $r$, and Holm-Bonferroni adjusted $p$-values).

---

### 2.4 `key_stats.json`
Machine-readable single source of truth containing verified numerical anchors for automated integration into LaTeX tables and manuscript text.

