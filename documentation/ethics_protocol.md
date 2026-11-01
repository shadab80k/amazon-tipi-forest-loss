# Ethics & Data-Handling Protocol

This study concerns people in voluntary isolation who cannot consent to being studied.
The following protocol governs every artifact in this repository.

## 1. Non-contact principle

- No field work, overflights, interviews, or any interaction with isolated peoples is
  proposed, attempted, or implied by this study. Brazil's official no-contact policy
  (FUNAI, since 1987) and the epidemiological evidence on contact-related mortality
  (Walker et al. 2015) are treated as binding constraints on research design.

## 2. Location confidentiality

- **No coordinates of isolated-peoples records, occupation areas, or settlements are
  published.** The OPI record layer (`opi_povos_isolados_records.geojson`) is used only
  locally to validate the linkage between records and Indigenous Land names.
- All published outputs (figures, tables, CSVs in the paper) are aggregated to the level
  of Indigenous Land boundaries (public policy artifacts) or to regional summaries.
- Buffer statistics are reported as distributions across territories, never as maps of
  settlement locations.
- The repository's data directory containing sensitive point records is git-ignored by
  default (`.gitignore` excludes `data/raw/`), and no figure or table displays them.

## 3. Data sources and rights

| Source | License/status | Use in this study |
|---|---|---|
| FUNAI official TI delimitations (via Esri BR_Content public FeatureServer) | Brazilian public-administration geospatial data | Territory boundaries |
| OPI (plataforma.povosisolados.org) | Public-interest socioenvironmental observatory | Isolated-peoples occupation areas and record-TI linkage |
| Hansen/UMD Global Forest Change v1.11 | Open raster dataset (UMD/GLAD, free use with attribution) | Forest loss 2000–2023 |
| RAISG/OTCA 2024 Amazon biome boundary | Open regional dataset | Study-area mask |
| FUNAI audit report RA-028/2 (2024) | Public audit document (SEI 6990437) | Official counts of records and protection status |

## 4. Respectful language

- The term used is *isolated*/*uncontacted peoples* (Portuguese: *povos indígenas
  isolados*) — peoples, not "tribes"; groups are described by their own names where known.
- The study does not exoticize or speculate about lifeways; it analyses land and threat.

## 5. Limitations the ethics constraints impose

- No ground-truthing of loss events inside territories is possible.
- Territory boundaries have mapping uncertainty; FUNAI's own audit (2024) documents
  inconsistencies between FUNAI spreadsheets and protection ordinances.
- Aggregation at territory level cannot capture intra-territory variation.

## 6. Disclosure

- The study uses AI tools (code generation, drafting) under the author's direction; this
  will be disclosed in the manuscript's declarations per the target venue's policy
  (authorship and accountability remain with the human author).
- No funding, no conflicts of interest, no human subjects, no animal subjects.
