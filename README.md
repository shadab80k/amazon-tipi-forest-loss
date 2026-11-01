# Forest Loss Pressure on Indigenous Lands with Uncontacted Peoples in the Brazilian Amazon (2000–2023)

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.placeholder.svg)](https://doi.org/10.5281/zenodo.placeholder)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Open Science](https://img.shields.io/badge/Open_Data-100%25_Reproducible-green.svg)]()

This repository contains the complete reproducible data pipeline, analysis scripts, and statistical verification tests for the research paper:

> **"Forest Loss Pressure on Indigenous Lands with Uncontacted Peoples in the Brazilian Amazon: An Open-Data Geospatial Assessment (2000–2023)"**  
> **Author:** Mohd Shadab (Independent Researcher; BS in Data Science & Applications, IIT Madras)  
> **Preprint / Target Journal:** *Remote Sensing Applications: Society and Environment* (Elsevier) / *EarthArXiv*  
> **Code & Data Repository:** [https://github.com/shadab80k/amazon-tipi-forest-loss](https://github.com/shadab80k/amazon-tipi-forest-loss)

---

## 1. Research Overview
Brazil hosts the world's largest concentration of isolated Indigenous peoples (*povos indígenas isolados*), who depend entirely on undisturbed forest ecosystems and face severe existential threats from contact-related epidemics. 

While Indigenous Lands are known to inhibit deforestation generally, this project provides the **first territory-level quantitative assessment** separating the **81 Indigenous Lands hosting uncontacted peoples (TIPI)** from general Indigenous lands, evaluating them against:
1. **Concentric Buffer Rings** (0–10 km and 10–50 km) around each territory (within-unit paired design).
2. **155 Matched Control Indigenous Lands** from the same state and size class (across-unit design).

### Key Scientific Findings
- **Internal Protection:** Median forest loss inside TIPI over 2000–2023 was **1.01%** [IQR: 0.29% – 3.45%], compared to **3.66%** in the 0–10 km ring and **5.30%** in the 10–50 km ring (Wilcoxon signed-rank $p < 10^{-10}$, Cohen's $d_z = -0.725$, rank-biserial $r = -0.835$).
- **Matched Contrast:** TIPIs lost significantly less forest internally than matched non-isolated Indigenous lands (median 1.01% vs 2.51%, Mann–Whitney $U = 4252, p < 10^{-4}$).
- **Severe Spatial Concentration:** Deforestation in surrounding buffers is concentrated (Gini = 0.631), with the top 10 highest-pressure territories accounting for **48.5% (1.4 million ha)** of all 0–10 km ring loss.
- **Institutional Buffering Under Assault:** Territories such as Uru-Eu-Wau-Wau and Baú maintained near-zero internal deforestation (2.27% and 0.25%, respectively) despite catastrophic external destruction (35.15% and 23.54% loss share) in their immediate 0–10 km surrounding rings.
- **Accessibility Correlates:** Surrounding pressure correlates strongly with distance to municipal urban centers ($\rho = -0.457, p < 10^{-4}$), reflecting diffuse settlement frontiers.

---

## 2. Ethical Data Governance & Non-Contact Mandate
This study complies strictly with Brazil's official 1987 no-contact policy, ILO Convention 169, and UNDRIP:
- **No Field Contact:** Exclusively remote, public satellite imagery and administrative boundaries were used.
- **Zero Coordinate Disclosure:** Point-level sighting coordinates and confidential OPI records are strictly **excluded** from this public repository to protect isolated groups from illegal incursions. All provided data are aggregated to officially gazetted Indigenous Land (*Terra Indígena*) boundaries.

---

## 3. Repository Architecture

```text
amazon-tipi-forest-loss/
├── README.md                 # Master project documentation
├── LICENSE                   # MIT Open Source License
├── CITATION.cff              # Machine-readable software/dataset citation
├── requirements.txt          # Python environment dependencies
├── config.yaml               # Analysis configuration thresholds and parameters
├── paper/                    # Publication manuscript (LaTeX source, PDF, sections)
│   ├── manuscript.tex        # Master LaTeX document
│   ├── sec_*.tex             # Modular paper sections
│   ├── references.bib        # 23 verified BibTeX citations with direct DOIs
│   └── manuscript.pdf        # Compiled submission manuscript
├── data/
│   ├── README.md             # Complete data dictionary & schema
│   └── derived/
│       ├── zonal_results.csv # Primary dataset (708 rows x 39 cols: annual loss & tree cover)
│       ├── accessibility.csv # Infrastructure distances in EPSG:6933
│       ├── summary_stats.csv # Descriptive statistics table
│       ├── statistical_tests.csv # Formal hypothesis test statistics & Holm p-values
│       └── key_stats.json    # Machine-readable numerical single source of truth
├── figures/                  # High-resolution (300 dpi) publication figures
│   ├── fig1_study_area.png   # Study area map
│   ├── fig2_paired_zones.png # Paired inside vs 0-10km ring plot
│   ├── fig3_annual_curves.png# Annual loss trajectory (2001-2023)
│   ├── fig4_top_pressure.png # Top 20 pressure territories
│   └── fig5_accessibility.png# Accessibility scatter plot
├── tables/                   # Publication-ready LaTeX tables
│   ├── tab_descriptive.tex   # Table 1: Descriptive summary
│   ├── tab_tests.tex         # Table 2: Hypothesis test results
│   └── tab_top10.tex         # Table 3: Top pressure hotspot territories
├── scripts/
│   └── verify_stats.py       # Standalone verification script (runs in <2 seconds)
├── src/                      # Analysis & ingestion pipeline source code
│   ├── acquisition/          # Data scraping scripts (FUNAI, OPI, RAISG)
│   └── analysis/             # Zonal raster computation engine & statistical tests
├── tests/                    # Pytest test suite & regression tests
└── documentation/            # Supplementary research & ethics documentation
```

---

## 4. Quickstart: Reproducing Results in 2 Minutes

### 4.1 Clone Repository
```bash
git clone https://github.com/shadab80k/amazon-tipi-forest-loss.git
cd amazon-tipi-forest-loss
```

### 4.2 Setup Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 4.3 Run Statistical Verification
To independently reproduce every sample size, median, IQR, Wilcoxon test, Mann-Whitney U test, Spearman correlation, and Gini coefficient reported in the paper:
```bash
python scripts/verify_stats.py
```
*Expected Output:*
```text
=======================================================
SAMPLE SIZES:
  TIPI territories: 81
  Matched Control territories: 155
=======================================================
--- 1. DESCRIPTIVE STATISTICS ---
TIPI Inside:     1.01% [0.29% - 3.45%] | Mean: 3.13% | Total: 1,533,682 ha
TIPI Ring 1:      3.66% [0.83% - 14.50%] | Mean: 9.98% | Total: 2,880,999 ha
TIPI Ring 2:      5.30% [1.22% - 17.87%] | Mean: 10.98% | Total: 16,344,613 ha
Controls Inside:  2.51% [0.92% - 7.29%] | Mean: 6.75% | Total: 1,006,569 ha

--- 2. PRIMARY HYPOTHESIS TESTS ---
H1a (Inside vs Ring 1): Wilcoxon W=274.0, p=6.6640e-11 (Holm-adj p=2.6656e-10)
H1b (Inside vs Ring 2): Wilcoxon W=149.0, p=1.1065e-12 (Holm-adj p=5.5324e-12)
Group Contrast (TIPI vs Controls): Mann-Whitney U=4252.0, p=4.7701e-05 (Holm-adj p=9.5402e-05)
H2a (Distance to City): Spearman rho=-0.4568, p=1.8111e-05 (Holm-adj p=5.4332e-05)
```

---

## 5. Primary Data Sources
1. **Indigenous Lands Boundaries:** National Foundation of Indigenous Peoples (FUNAI), *Terras Indígenas do Brasil — Delimitações Oficiais*, exported via Esri BR_Content FeatureServer (657 polygons).
2. **Isolated Peoples Presence:** Observatório para a Proteção dos Povos Isolados e de Recente Contato (OPI), *Áreas de Ocupação* and registry records.
3. **Forest Loss (2000–2023):** Hansen/UMD Global Forest Change dataset (v1.11), 30 m spatial resolution, canopy cover threshold >30%.
4. **Amazon Biome Mask:** RAISG / OTCA 2024 *LimBiogeografico* layer.

---

## 6. Citation
```bibtex
@article{shadab2026tipi,
  author    = {Shadab, Mohd},
  title     = {Forest Loss Pressure on Indigenous Lands with Uncontacted Peoples in the Brazilian Amazon: An Open-Data Geospatial Assessment (2000--2023)},
  journal   = {Remote Sensing Applications: Society and Environment},
  year      = {2026},
  note      = {Under peer review; preprint available at EarthArXiv}
}
```

---

## 7. License
- **Code & Scripts:** Licensed under the [MIT License](LICENSE).
- **Data & Tables:** Licensed under [Creative Commons Attribution 4.0 International (CC-BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
