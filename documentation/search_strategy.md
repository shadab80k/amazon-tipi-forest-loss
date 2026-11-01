# Phase 2 — Literature Search Strategy & Log

All searches performed 2026-10-29. Every citation in `paper/references.bib` was
verified against Crossref (`api.crossref.org`), PubMed E-utilities, or the
publisher page; two initially-guessed DOIs were found to be WRONG by this
process and corrected (Garnett 2018: `10.1038/s41893-018-0100-6`, not
...-0070-4; Andam 2008: `10.1073/pnas.0800437105`, not ...-3105). This is why
verification matters.

## Sources used

| Source | Role | Status |
|---|---|---|
| Google Scholar (via WebSearch mirrors of its index) | discovery | snippets only; no login |
| Crossref REST API | DOI/metadata verification | verified 15 works |
| PubMed E-utilities | biomedical verification (Walker 2015; Ritter 2025) | verified 2 works |
| Semantic Scholar API | DOI cross-check (partial index gaps found) | used cautiously |
| OpenAlex | rate-limited (shared-IP budget) on the day | not usable this session |
| FUNAI / gov.br | official audit PDF (SEI 6990437) | downloaded, read (8 pp, tables) |
| Survival International / press | 2025 global report facts | secondary coverage verified |
| OPI platform + GeoServer | isolated-peoples records/areas | data downloaded via WFS |
| RAISG/OTCA FeatureServer | biome boundary | data downloaded |

## Query log (abridged)

1. `isolated indigenous peoples Amazon satellite imagery detection research`
2. `uncontacted tribes research ethics no-contact policy FUNAI Survival International`
3. `indigenous lands deforestation Brazilian Amazon protected areas PNAS Nepstad 2006`
4. `Hansen 2013 Science high-resolution global maps forest cover change`
5. `RAISG povos indígenas isolados registros Amazônia`
6. `Walker Sattenspiel Hill mortality contact epidemics indigenous Amazonia`
7. `Blackman 2017 titling indigenous communities Peruvian Amazon PNAS`
8. `Baragwanath Bayi 2020 collective property rights deforestation PNAS`
9. `FUNAI povos isolados registros 2024 terras indígenas`
10. `Garnett 2018 Indigenous lands conservation Nature Sustainability`
11. `Kalamandeen 2018 small-scale deforestation Scientific Reports`
12. `Ferrante Fearnside BR-319 indigenous peoples threatened`
13. `Nolte 2013 governance avoided deforestation PNAS` / `Barber 2014 roads protected areas`
14. `PNAS 2025 Indigenous Territories Protected Areas ITPA Amazon human pressures`
15. `Survival International 2025 report uncontacted peoples 196 threats`
16. Venue checks: `Journal of Land Use Science scope/APC`, `RSASE Elsevier scope`,
    `EarthArXiv`, `URNCST Journal APC`.

## Coverage assessment

- 16 primary research papers verified (Nepstad 2006; Andam 2008; Soares-Filho 2010;
  Joppa & Pfaff 2010; Nolte 2013; Hansen 2013; Barber 2014; Walker 2015; Blackman 2017;
  Garnett 2018; Kalamandeen 2018; Ferrante 2020; Baragwanath & Bayi 2020; Andrade 2021;
  Baragwanath et al. 2023; Duarte Ritter et al. 2025) + 1 news feature (Pringle 2014)
  + 4 institutional/data sources + 2 policy instruments.
- Backward citation chasing via reference lists of Nepstad 2006 and Ritter 2025;
  forward chasing via "cited by" counts on Crossref records.
- Full texts read: FUNAI audit (complete PDF). Others verified at abstract/record level
  (disclosed per-item in `literature_matrix.csv`).
- Negative-results searches: no prior study found that quantifies forest loss specifically
  on isolated-peoples territories with matched controls (queries 1, 3, 11, 14 + manual
  follow-ups). Closest works documented in the gap analysis.
