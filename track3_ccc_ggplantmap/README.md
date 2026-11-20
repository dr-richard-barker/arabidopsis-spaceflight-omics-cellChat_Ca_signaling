# Track 3: Cell-Cell Communication, Spatial Visualization, and GO Enrichment

## Overview
Characterizes intercellular signaling using PlantCellChat, visualizes expression on plant anatomy with ggPlantmap, constructs a Ca2+ pathway network, and performs GO enrichment analysis on the 85-gene LASSO panel.

## Scripts
| Script | Description |
|--------|-------------|
| `04_ggplantmap_composites.R` | ggPlantmap spatial visualization composites |
| `05_ca2_pathway.R` | Ca2+ pathway network (stress-majorization layout) |
| `06_gene_functions.py` | Gene function annotations for top 4 LASSO genes |
| `07_go_enrichment.R` | GO/KEGG enrichment via g:Profiler (custom background, BH-FDR) |
| `08_ca2_k_pathway_network.R` | Expanded Ca2+/K+ pathway network (27 nodes, 56 edges) with ggpathway |
| `09_ca2_k_coexpression.py` | Per-cell-type co-expression matrices for 25 Ca2+/K+ genes |
| `10_organ_marker_analysis.py` | Tissue-specific marker diagnostic for organ inference |
| `11_ca2_k_ccc_circuit.py` | Ca2+ and K+ cell-to-cell communication circuit |
| `12_ggplantmap_ca2_k_circuit.R` | ggPlantmap maps (seedling, root tip, leaf) for circuit genes |
| `13_circuit_summary_table.py` | Ca2+/K+ signaling circuit summary tables |
| `14_figure7_composite.py` | Figure 6 composite (network, heatmap, spatial map, CCC circuit) |
| `15_sankey_ca2_k_cascade.py` | Two-panel Sankey (cell-type flow + molecular cascade) |
| `16_ggplantmap_montage.py` | Supplementary ggPlantmap montage (3-panel stack) |
| `17_reassemble_figure5.py` | Figure 4 reassembly (refined 20-node network) |
| `22_make_sankey_panel_b.py` | **Figure 7 panel b**: CBL1-CIPK23-AKT1 molecular cascade Sankey |
| `23_composite_figure8_new.py` | Combine ggPlantmap leaf maps (`28_fig8_leaf_corrected.R`) + Sankey panel b into Figure 7 |

## Data
| File | Description |
|------|-------------|
| `ccc_communication_strength.csv` | 5×5 cell type communication strength matrix |
| `ccc_full_communication_table.csv` | All 72,350 LR interactions with probabilities |
| `ccc_lr_pairs.csv` | PlantCellChat LR database (3,140 interactions) |
| `ccc_lr_pairs_with_strength.csv` | 2,894 measured LR pairs with total communication |
| `ccc_per_signal_strength.csv` | Per-signal, per-cell-type communication strength |
| `ccc_signaling_strength.csv` | Total strength per signaling pathway |
| `ccc_diffexp_signaling.csv` | Differential signaling genes |
| `gene_function_annotations.csv` | Top 4 LASSO gene annotations (12 fields each) |
| `ca2_signaling_analysis.json` | Ca2+ pathway analysis summary |
| `go_enrichment_85_genes.csv` | Full GO enrichment results (1,481 terms) |
| `go_enrichment_significant.csv` | 14 significant terms (BH-FDR < 0.05) |
| `go_enrichment_summary.csv` | Summary with -log10(p) and gene lists |

## Key Results
- Ca2+ signaling dominates: strength = 249.5 (4.6× next pathway)
- GO enrichment: flight-up genes → heat/ER-proteostasis; ground-up → flavonoid metabolism
- Ca2+ network: 20 nodes, 43 edges, stress-majorization layout
- Ca2+/K+ crosstalk circuit: CBL1-CIPK23-AKT1 cascade (27 nodes, 56 edges), guard-cell CIPK23 (0.333) and epidermal AKT1 (0.367), exploratory guard-cell co-expression (CBL1-ANNAT1 r = 0.90, CBL1-CDPK4 r = 0.63, CDPK4-ANNAT1 r = 0.56)
- Ca2+ 10.2-fold stronger than K+ signaling; guard cells dominant Ca2+ source (outgoing strength 57.1)
- Figure 7 maps CIPK23 and AKT1 onto leaf cross-sections (panel a) and traces the Ca2+ → CBL1/CBL9/CaM3/CML24 → CIPK23 → AKT1/KC1 cascade (panel b)

## Input Data (external)
- PlantCellChat: https://github.com/mrliuw/PlantCellChat
- ggPlantmap: https://github.com/leonardojo/ggPlantmap (Jo & Kajala, J Exp Bot 2024)
- ggpathway: https://github.com/cxli233/ggpathway
- g:Profiler: https://biit.cs.ut.ee/gprofiler (organism: athaliana)
