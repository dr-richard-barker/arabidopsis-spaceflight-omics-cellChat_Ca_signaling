#!/usr/bin/env python3
"""
Build the npj Microgravity submission-ready manuscript package (7 main figures).

Generates cleanly formatted, fully synchronized:
  - manuscript/manuscript.docx              (submission text + Table 1 + Figure Legends)
  - manuscript/manuscript_with_figures.docx (same text + Table 1 + 7 inline figures)
  - manuscript/manuscript_with_figures_ACTIVE_DRAFT.docx (exact sync copy)

Conforms to npj Microgravity (Nature Portfolio) formatting:
  - Title page block with author, affiliation, ORCID iD, and corresponding author
  - Unstructured Abstract <= 150 words with zero citations
  - Strict sequential figure citation order (Figure 1 -> Figure 7)
  - Strict sequential Nature superscript citations (1 -> 15) and complete references
  - True Word italics for species names, Latin phrases, and Arabidopsis gene symbols
  - Mandatory declarations (Data Availability, Code Availability, Acknowledgements,
    Author Contributions, Funding, Competing Interests) placed before References
"""

import os
import re
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


HERE = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPT_ONLY = os.path.join(HERE, "manuscript.docx")
MANUSCRIPT_FIGS = os.path.join(HERE, "manuscript_with_figures.docx")
MANUSCRIPT_DRAFT = os.path.join(HERE, "manuscript_with_figures_ACTIVE_DRAFT.docx")
FIGDIR = os.path.join(HERE, "figures")

REPO_URL = "https://github.com/dr-richard-barker/arabidopsis-spaceflight-omics-cellChat_Ca_signaling"

# Markup tokenizer supporting **bold**, *italic*, and ^superscript^
TOKEN_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|\^[^^]+\^)")


def add_rich_runs(para, text, font_name="Arial", font_size=10.5, base_bold=False, base_italic=False):
    for part in TOKEN_RE.split(text):
        if not part:
            continue
        bold = base_bold
        italic = base_italic
        sup = False
        content = part
        if part.startswith("**") and part.endswith("**"):
            bold = True
            content = part[2:-2]
        elif part.startswith("*") and part.endswith("*"):
            italic = True
            content = part[1:-1]
        elif part.startswith("^") and part.endswith("^"):
            sup = True
            content = part[1:-1]
        run = para.add_run(content)
        run.font.name = font_name
        run.font.size = Pt(font_size)
        run.bold = bold
        run.italic = italic
        if sup:
            run.font.superscript = True


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.keep_with_next = True
    if level == 1:
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(4)
        add_rich_runs(p, text, font_size=13, base_bold=True)
    else:
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(3)
        add_rich_runs(p, text, font_size=11, base_bold=True)
    return p


def add_body_para(doc, text, space_after=6, font_size=10.5, base_bold=False, base_italic=False):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.15
    add_rich_runs(p, text, font_size=font_size, base_bold=base_bold, base_italic=base_italic)
    return p


def set_cell_shading(cell, fill_hex):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill_hex)
    tc_pr.append(shd)


def set_table_borders(table):
    tbl_pr = table._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "6" if edge in ("top", "bottom") else "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), "999999" if edge == "insideH" else "333333")
        borders.append(el)
    for edge in ("left", "right", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "none")
        borders.append(el)
    tbl_pr.append(borders)


def add_table1(doc):
    p_cap = doc.add_paragraph()
    p_cap.paragraph_format.space_before = Pt(12)
    p_cap.paragraph_format.space_after = Pt(4)
    p_cap.paragraph_format.keep_with_next = True
    add_rich_runs(
        p_cap,
        "**Table 1.** Summary of NASA OSDR *Arabidopsis thaliana* spaceflight transcriptomic studies "
        "and leave-one-study-out cross-validation (LOOS-CV) performance.",
        font_size=10,
    )

    headers = [
        "Study ID",
        "Samples (F/G)",
        "Tissue",
        "Flight Profile",
        "Ecotype(s)",
        "LOOS-CV AUC (mean ± SD)",
        "Sensitivity / Specificity",
    ]
    rows_data = [
        ["OSD-37", "56 (28 / 28)", "Seedling", "ISS", "Ws, Cvi-0, Ler-0, Col-0", "0.875 ± 0.052", "0.864 / 0.779"],
        ["OSD-678", "24 (12 / 12)", "Seedling", "ISS", "Col-0, Unknown", "0.887 ± 0.023", "0.958 / 0.783"],
        ["OSD-38", "6 (3 / 3)", "Seedling", "ISS", "Col-0", "0.933 ± 0.094", "1.000 / 0.800"],
        ["OSD-321", "10 (5 / 5)", "Seedling", "ISS", "Col-0", "0.636 ± 0.149", "0.800 / 0.600"],
        ["OSD-120", "24 (12 / 12)", "Root", "ISS", "Col-0, Unknown", "0.544 ± 0.058", "0.658 / 0.575"],
        ["OSD-624", "36 (18 / 18)", "Leaf + root", "Suborbital", "Unknown", "0.528 ± 0.057", "0.789 / 0.483"],
        ["Pooled / Mean", "156 (78 / 78)", "Multi-tissue", "ISS + Suborbital", "Multiple", "0.734 (overall)", "0.845 / 0.670"],
    ]

    table = doc.add_table(rows=1 + len(rows_data), cols=len(headers))
    set_table_borders(table)
    col_widths = [0.78, 0.88, 0.76, 0.90, 1.25, 1.05, 0.88]

    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.width = Inches(col_widths[j])
        set_cell_shading(cell, "1F4E79")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Arial"
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    for i, row_vals in enumerate(rows_data, start=1):
        is_summary = i == len(rows_data)
        bg = "D9E2F3" if is_summary else ("F7F7F7" if i % 2 == 0 else None)
        for j, val in enumerate(row_vals):
            cell = table.rows[i].cells[j]
            cell.width = Inches(col_widths[j])
            if bg:
                set_cell_shading(cell, bg)
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            r = p.add_run(val)
            r.bold = is_summary or (j == 0)
            r.font.name = "Arial"
            r.font.size = Pt(8.5)

    p_note = doc.add_paragraph()
    p_note.paragraph_format.space_before = Pt(3)
    p_note.paragraph_format.space_after = Pt(10)
    add_rich_runs(
        p_note,
        "F/G, flight/ground control sample counts; ISS, International Space Station; SD, standard deviation across 10 repeats per held-out study.",
        font_size=8.5,
        base_italic=True,
    )


TITLE = (
    "LASSO biomarker panel and single-cell atlas integration reveal Ca²⁺-dominated "
    "cell–cell communication in the *Arabidopsis* spaceflight response"
)

ABSTRACT = (
    "Spaceflight imposes mechanical, oxidative, and gravitational stresses on plants, yet the "
    "cell-type-specific signaling architecture underlying these responses remains poorly "
    "characterized. We integrated bulk transcriptomic biomarker discovery (156 samples across "
    "6 NASA OSDR studies; elastic-net logistic regression, α = 0.5) with single-cell analysis "
    "of the *Arabidopsis* seed-to-seed atlas (41,314 cells) using scPlantLLM, PlantCellChat, "
    "and ggPlantmap. The 85-gene LASSO/elastic-net panel (mean cross-study AUC = 0.734) revealed "
    "enrichment for stress and endoplasmic reticulum (ER) proteostasis pathways among "
    "flight-upregulated genes and flavonoid metabolism among ground-upregulated genes. "
    "PlantCellChat identified Ca²⁺ as the dominant signaling pathway (10.2-fold higher than K⁺), "
    "with guard cells as the primary Ca²⁺ source. A CBL1–CIPK23–AKT1 crosstalk circuit connects "
    "Ca²⁺ sensing to K⁺ uptake, with *CIPK23* highest in guard cells and *AKT1* in epidermal cells. "
    "These findings highlight Ca²⁺/K⁺ crosstalk and non-coding RNA regulation in the *Arabidopsis* "
    "spaceflight response."
)

INTRO_PARAS = [
    (
        "Plants grown in spaceflight conditions experience a constellation of stresses, including "
        "microgravity, altered atmospheric composition, modified light regimes, and increased "
        "ionizing radiation. Transcriptomic studies of *Arabidopsis thaliana* flown on the "
        "International Space Station (ISS) and suborbital platforms have identified hundreds of "
        "differentially expressed genes, yet the cell-type-specific architecture of these responses "
        "and the intercellular signaling pathways that coordinate them remain poorly understood."
    ),
    (
        "NASA’s Open Science Data Repository (OSDR) provides a growing collection of *Arabidopsis* "
        "spaceflight transcriptomics datasets. However, individual studies typically have small "
        "sample sizes (3–6 replicates per condition), making robust biomarker discovery challenging. "
        "Pooling multiple studies with study-stratified cross-validation offers a path toward "
        "generalizable biomarker identification, although the resulting models must be interpreted "
        "as discovery-only given the absence of independent validation cohorts."
    ),
    (
        "The publication of the *Arabidopsis* seed-to-seed single-cell atlas^1^ and the scPlantLLM "
        "foundation model^2^ provides new opportunities for cell-type-resolved analysis. Trained on "
        "plant single-cell transcriptomics data, scPlantLLM generates zero-shot cell embeddings and "
        "cell-type predictions^2^. PlantCellChat enables inference of ligand–receptor-mediated "
        "cell–cell communication (CCC) from single-cell data using a plant-specific interaction "
        "database^3^, while ggPlantmap maps quantitative expression and signaling metrics directly "
        "onto plant anatomical structures^4^."
    ),
    (
        "Ca²⁺ is a primary second messenger in plant gravity perception. Microgravity alters "
        "cytosolic Ca²⁺ oscillations and gradients that guide directional growth, and spaceflight "
        "experiments have confirmed that cytosolic Ca²⁺ levels shift in response to changes in "
        "gravisensor positioning^5^. The CBL–CIPK calcium signaling cascade is a well-established "
        "downstream effector, and the CBL1–CIPK23–AKT1 pathway specifically links Ca²⁺ sensing to "
        "K⁺ uptake, regulating stomatal aperture and root K⁺ acquisition^6–8^. This Ca²⁺–K⁺ "
        "crosstalk is particularly relevant to spaceflight, where altered gravity disrupts ion "
        "homeostasis and turgor regulation."
    ),
    (
        "Here, we integrate these approaches to: (1) construct a regularized LASSO/elastic-net "
        "biomarker panel predicting spaceflight versus ground conditions from pooled OSDR "
        "transcriptomic data; (2) evaluate scPlantLLM on the seed-to-seed atlas for zero-shot "
        "cell annotation and clustering; (3) infer intercellular communication with PlantCellChat; "
        "(4) visualize spatial expression and communication patterns on plant anatomy with "
        "ggPlantmap; (5) integrate the biomarker panel with the single-cell signaling architecture; "
        "and (6) characterize the Ca²⁺/K⁺ crosstalk circuit linking Ca²⁺ signaling to K⁺ transport "
        "via the CBL1–CIPK23–AKT1 cascade. We further examine the biological functions of the top "
        "biomarker genes, perform Gene Ontology (GO) enrichment analysis on the full 85-gene panel, "
        "and trace the cell-to-cell signaling circuit underlying long-distance ion signaling."
    ),
]

RESULTS_SECTIONS = [
    (
        "LASSO/elastic-net biomarker panel predicts spaceflight response across studies",
        [
            (
                "We pooled 156 transcriptomic samples from 6 OSDR *Arabidopsis* studies (78 flight, "
                "78 ground control; Table 1) and trained an elastic-net regularized logistic "
                "regression model (α = 0.5, combining L1/LASSO and L2 penalties; hereafter referred "
                "to as the LASSO/elastic-net panel) using leave-one-study-out cross-validation "
                "(LOOS-CV) with 10 repeats per fold (60 total iterations). The panel achieved a mean "
                "cross-study AUC of 0.734 (empirical 2.5th–97.5th percentile across 60 iterations: "
                "0.431–1.000; SD = 0.188), with a mean sensitivity of 0.845 and a mean specificity "
                "of 0.670 (Figure 1a, Table 1)."
            ),
            (
                "Generalization was strongest for ISS seedling studies: OSD-38 (AUC = 0.933), "
                "OSD-678 (0.887), and OSD-37 (0.875). Weaker performance on OSD-120 (0.544, root "
                "tissue) and OSD-624 (0.528, suborbital flight) indicates that the spaceflight "
                "transcriptional signature is both tissue- and flight-profile-specific. Stability "
                "selection at ≥50% frequency across the 60 iterations yielded 85 stable biomarker "
                "features (Figure 1b; Supplementary Table S1)."
            ),
            (
                "Four genes were selected at 100% frequency (Figure 1c): *AT4G10250* (*ATHSP22.0*, "
                "mean coefficient +0.723, flight-enriched), *AT3G07365* (natural antisense "
                "transcript [NAT], +0.828, strongest positive predictor), *AT2G14247* (chloroplast "
                "protein, −0.364, ground-enriched), and *AT4G01390* (TRAF-like/MATH domain protein, "
                "−0.819, strongest negative predictor). The spatial distribution and biological "
                "functions of these four core biomarkers are examined in detail below."
            ),
        ],
    ),
    (
        "scPlantLLM zero-shot embeddings and clustering of the seed-to-seed atlas",
        [
            (
                "We applied scPlantLLM in zero-shot mode to 9,998 cells subsampled (stratified by "
                "cell type) from the seed-to-seed atlas (41,314 cells, 22,375 genes; 5 cell types: "
                "Epidermal, Mesophyll, Stele, Meristematic, and Guard). Inference used "
                "seq_length = 500 (reduced from the 1,500 training configuration to ensure CPU "
                "feasibility) across the highest-expressed genes per cell, yielding 512-dimensional "
                "cell embeddings and 44-class cell-type predictions (Figure 1d–f)."
            ),
            (
                "Zero-shot prediction accuracy was 28.1% under loose mapping (allowing tissue-level "
                "correspondences between atlas and model vocabularies), with Mesophyll cells best "
                "predicted (52.4%) and Meristematic and Guard cells poorly predicted (0%). This low "
                "transfer accuracy reflects domain shift: scPlantLLM was trained predominantly on "
                "root tissue, whereas the atlas is seedling-derived. Leiden clustering on the "
                "scPlantLLM embeddings (resolution 0.5) produced 6 clusters showing low agreement "
                "with atlas cell types (ARI = 0.033, NMI = 0.040) and moderate agreement with "
                "zero-shot predictions (ARI = 0.154, NMI = 0.198; Figure 1d–f)."
            ),
        ],
    ),
    (
        "PlantCellChat reveals Ca²⁺-dominated cell–cell communication",
        [
            (
                "We inferred cell–cell communication using PlantCellChat with the *Arabidopsis* "
                "ligand–receptor database (5,725 interactions, 1,027 genes, 15 signaling pathways), "
                "of which 940 genes were present in the atlas. To accommodate the atlas’s terrestrial "
                "growth conditions, we applied relaxed overexpression thresholds (pc = 0, fc = 0, "
                "p = 0.1), identifying 1,628 overexpressed genes and 3,140 ligand–receptor "
                "interactions."
            ),
            (
                "Ca²⁺ signaling was the dominant annotated pathway with a total communication "
                "strength of 249.5, which is 4.6-fold higher than that of the next-strongest "
                "pathway (brassinosteroid [BR], 54.5; Figure 2b). Across all cell types, the overall "
                "communication matrix identified Meristematic cells as the strongest communicators "
                "(total outgoing strength 437.4, self-communication 92.0), followed by Guard "
                "(419.3), Stele (418.9), Mesophyll (399.8), and Epidermal (399.3) cells "
                "(Figure 2a). At the individual interaction level, the top 21 ligand–receptor pairs "
                "belonged to unannotated general receptor-like kinase (RLK) signaling (led by "
                "AT3G47470_AT4G02510, strength 21.56), while the highest-ranking pathway-annotated "
                "pairs were Ca²⁺ (AT1G20620_AT5G19450 at rank 22, strength 10.02; "
                "AT1G59870_AT3G51920 at rank 33, strength 7.11), followed by chitin (rank 36, "
                "strength 6.49), BR (rank 37, strength 6.34), and nitrate (NO₃⁻; rank 41, strength "
                "6.08) interactions (Figure 2c)."
            ),
        ],
    ),
    (
        "Spatial visualization reveals cell-type-specific biomarker expression",
        [
            (
                "We mapped expression of the top four LASSO/elastic-net biomarkers onto *Arabidopsis* "
                "leaf and root tip cross-sections using ggPlantmap (Figure 3, displaying both TAIR "
                "locus IDs and gene names). Cell types were mapped to anatomical regions as follows: "
                "Epidermal to epidermis, Mesophyll to palisade and spongy parenchyma (leaf) or cortex "
                "(root), Stele to vascular tissues, and Meristematic to columella (root). Notably, "
                "*AT4G10250* (*ATHSP22.0*) exhibited zero baseline expression across all five cell "
                "types in the unstressed terrestrial atlas—consistent with its role as an inducible "
                "stress chaperone activated specifically under spaceflight—whereas the ground-enriched "
                "markers *AT2G14247* and *AT4G01390* showed clear mesophyll/cortical and stele "
                "enrichment, respectively (Figure 3a–b). *AT3G07365* (a non-coding RNA) is absent "
                "from the atlas protein-coding gene matrix."
            ),
        ],
    ),
    (
        "Ca²⁺ signaling pathway architecture connects stress sensors to downstream effectors",
        [
            (
                "To resolve the molecular topology of the dominant signaling axis, we constructed a "
                "20-node Ca²⁺ signaling network from PlantCellChat interactions (Figure 4a) paired "
                "with a conceptual microgravity cascade (Figure 4b). In this network, Ca²⁺ acts as "
                "the signaling ligand engaging CBL calcium sensors—including *CBL1* (*AT4G17615*), "
                "*CBL2* (*AT5G55990*), and *CBL9* (*AT5G47100*)—which activate CIPK kinases such as "
                "*CIPK23* (*AT1G30270*) to phosphorylate downstream targets including the K⁺ channel "
                "*AKT1* (*AT2G26650*) and the nitrate transporter *NRT2.1* (*AT1G08090*), alongside "
                "calmodulin/CML (*CaM3*, *CaM7*, *CML24*, *CML38*, *CML42*) and CDPK (*CDPK3*, "
                "*CDPK4*) branches. This CBL–CIPK cascade represents a well-established Ca²⁺ "
                "signaling module in plant stress responses."
            ),
        ],
    ),
    (
        "Cross-track integration and biological functions of top biomarker genes",
        [
            (
                "To integrate the bulk biomarker panel with single-cell signaling architecture, we "
                "computed a LASSO/elastic-net panel weighted score (the sum of coefficient × "
                "expression across the 74 atlas-present panel genes) for each cell type and mapped "
                "it alongside leaf Ca²⁺ communication strength (Figure 5a–b). Weighted scores were "
                "negative for all cell types, confirming that the terrestrial-grown atlas exhibits "
                "a ground-like transcriptional signature; Stele cells showed the most negative score "
                "(−0.079), indicating the strongest ground-like signature in vascular tissues. The "
                "four 100%-selected biomarkers represent distinct biological roles (Figure 5c):"
            ),
            (
                "*AT4G10250* (*HSP22.0*/*ATHSP22.0*) encodes a 22 kDa small heat shock protein "
                "(HSP20/alpha-crystallin family) localized to the endomembrane system and "
                "chloroplast. It functions as a molecular chaperone that prevents protein "
                "aggregation under heat and oxidative stress and modulates ABA–auxin signaling "
                "crosstalk via the ABI1–HSP22 interaction. As a flight-enriched positive predictor "
                "(+0.723) that is quiescent in unstressed terrestrial seedlings, *ATHSP22.0* likely "
                "reflects proteostatic stress under microgravity."
            ),
            (
                "*AT3G07365* is a natural antisense transcript (NAT)—a non-coding RNA overlapping "
                "*AT3G46230* on the opposite DNA strand. In *Arabidopsis*, *cis*-NATs regulate "
                "sense-strand gene expression through transcriptional interference or siRNA-mediated "
                "silencing^9^ and have been linked to heat-stress oxidative proteomics responses^10^. "
                "As the strongest positive predictor (+0.828), *AT3G07365* highlights that non-coding "
                "regulatory RNA dynamics, rather than protein-coding changes alone, are a central "
                "feature of the spaceflight transcriptional signature."
            ),
            (
                "*AT2G14247* encodes a small (78 aa, 8.65 kDa) chloroplast-localized expressed "
                "protein of unknown function. As a ground-enriched negative predictor (−0.364), its "
                "suppression in flight samples is consistent with established spaceflight effects on "
                "photosynthesis and chloroplast function."
            ),
            (
                "*AT4G01390* encodes a TRAF-like/MATH domain-containing protein involved in abiotic "
                "stress signaling^11^; it is listed in the Leaf Senescence Database and is "
                "H₂O₂-responsive. As the strongest negative predictor (−0.819), its enrichment in "
                "ground controls suggests that baseline oxidative stress signaling pathways are "
                "attenuated under microgravity."
            ),
        ],
    ),
    (
        "GO enrichment reveals stress and metabolic signatures in the biomarker panel",
        [
            (
                "To characterize the biological processes represented by the 85-gene panel, we "
                "performed GO and KEGG pathway enrichment using g:Profiler against a custom "
                "background of the 2,000 variable features from which the model selected "
                "(Benjamini–Hochberg FDR < 0.05). A directed analysis splitting the panel into 41 "
                "flight-upregulated genes (positive coefficients) and 44 ground-upregulated genes "
                "(negative coefficients) revealed a clear biological partition. Flight-upregulated "
                "genes were significantly enriched for 11 terms, including response to heat "
                "(p = 4.3 × 10⁻³, 6 genes), cellular response to hypoxia and oxygen levels "
                "(p = 0.032, 4 genes each), protein modification by small protein conjugation "
                "(p = 0.032), and KEGG protein processing in the endoplasmic reticulum "
                "(p = 1.3 × 10⁻¹¹, 9 genes). Ground-upregulated genes were enriched for flavonoid "
                "biosynthetic process (p = 0.041, 4 genes). The combined 85-gene panel showed "
                "significant enrichment for KEGG protein processing in the ER (p = 2.6 × 10⁻⁸) and "
                "response to heat (p = 0.011; Supplementary Figures S1–S2, Supplementary Tables "
                "S2–S3). Together, these results indicate that spaceflight activates stress-response "
                "and ER proteostasis pathways while suppressing secondary metabolism, consistent "
                "with the downregulation of photosynthetic and flavonoid biosynthetic machinery "
                "under microgravity."
            ),
        ],
    ),
    (
        "Ca²⁺/K⁺ crosstalk circuit connects guard cell signaling to K⁺ uptake",
        [
            (
                "Cell–cell communication analysis placed Ca²⁺ signaling well above K⁺ transport in "
                "total strength (249.5 vs. 24.5, a 10.2-fold difference), with guard cells serving "
                "as the dominant Ca²⁺ source (total outgoing Ca²⁺ strength 57.1, highest of all cell "
                "types) and signaling most strongly to meristematic (12.14), epidermal (11.20), and "
                "stele (11.09) cells; by contrast, epidermal cells were the principal K⁺ source "
                "(Figure 6d; Supplementary Tables S4–S5). Within the PlantCellChat network, the "
                "canonical Ca²⁺→K⁺ module was recovered directly: Ca²⁺ engages the calcium sensor "
                "*CBL1* (*AT4G17615*), which links to *CIPK23* (*AT1G30270*), and *CIPK23* in turn "
                "connects to the K⁺-uptake channel *AKT1* (*AT2G26650*)—recovering the established "
                "CBL–CIPK23–AKT1 pathway^6–8^. Although the paralogous sensor *CBL9* was not "
                "detected in the atlas communication network, *CBL1* and *CBL9* act as redundant "
                "*CIPK23* partners *in vivo*."
            ),
            (
                "To place this module in cellular context, we expanded the network to include the "
                "six major K⁺ channels (*AKT1*, *AKT2*, *GORK*, *KAT1*, *KAT2*, and *KC1*) and "
                "examined per-cell-type expression across the full seed-to-seed atlas (41,314 "
                "cells). The resulting Ca²⁺/K⁺ network comprised 27 nodes and 56 edges (Figure 6a; "
                "Supplementary Figure S8). Consistent with a guard-cell role for the kinase step, "
                "*CIPK23* was most highly expressed in guard cells (mean 0.333, 20.2% expressing; "
                "highest of any cell type), whereas its downstream target *AKT1* peaked in epidermal "
                "cells (mean 0.367, 16.7% expressing), matching *AKT1*’s established role in "
                "epidermal and root K⁺ uptake (Supplementary Figure S5, Supplementary Table S6). By "
                "contrast, the calcium sensors *CBL1* and *CBL9* were expressed at low levels across "
                "all cell types (≤0.06), indicating that cell-type specificity in this module "
                "resides at the kinase (*CIPK23*) and channel (*AKT1*) steps rather than at the "
                "sensor step."
            ),
            (
                "Gene–gene co-expression across the 25 circuit genes was weak globally (|r| < 0.1 "
                "for nearly all pairs; Figure 6b, Supplementary Figure S4, Supplementary Table S7). "
                "Within guard cells (n = 89), a small module of co-varying genes was "
                "apparent—notably *CBL1*–*ANNAT1* (r = 0.90), *CBL1*–*CDPK4* (r = 0.63), and "
                "*CDPK4*–*ANNAT1* (r = 0.56)—but with only 89 guard cells, these correlation "
                "estimates carry high variance and are presented as exploratory rather than primary "
                "evidence. We therefore base the circuit primarily on the cell–cell communication "
                "network and on the guard-enriched expression of *CIPK23*. Spatial mapping of the "
                "circuit genes onto seedling, root, and leaf anatomy (Figures 6c and 7a; "
                "Supplementary Figure S3) and molecular-cascade Sankey tracing (Figure 7b) show "
                "*CIPK23* broadly expressed with guard/epidermal enrichment and *AKT1* concentrated "
                "in epidermal tissue, providing tissue-level context for the cascade."
            ),
        ],
    ),
]

DISCUSSION_PARAS = [
    (
        "This study integrates bulk spaceflight transcriptomics with single-cell atlas analysis to "
        "connect biomarker-level findings with cell-type-resolved signaling architecture. Four "
        "findings are particularly noteworthy."
    ),
    (
        "First, the dominance of Ca²⁺ signaling in the CCC network (4.6-fold higher than any other "
        "annotated pathway) is consistent with the role of Ca²⁺ as a primary second messenger in "
        "plant gravity perception. Microgravity alters cytosolic Ca²⁺ oscillations and gradients "
        "that guide directional growth, and the CBL–CIPK cascade identified in our analysis is a "
        "well-established downstream effector of Ca²⁺ signaling in plant stress responses. Moreover, "
        "the convergence of two core LASSO/elastic-net biomarker genes (*ATHSP22.0* and *TRAF-like*) "
        "with Ca²⁺-linked stress signaling—together with *ATHSP22.0*’s complete quiescence in "
        "unstressed terrestrial seedlings—supports the biological coherence of the biomarker panel."
    ),
    (
        "Second, the identification of a natural antisense transcript (*AT3G07365*) as the "
        "strongest positive predictor of spaceflight underscores the importance of non-coding RNA "
        "regulation in spaceflight responses. Because *cis*-NATs can rapidly modulate gene "
        "expression without requiring translation^9^, they may be particularly advantageous for "
        "rapid adaptation to orbital environments. This finding indicates that future spaceflight "
        "biomarker panels and single-cell reference matrices should retain non-coding RNAs "
        "alongside protein-coding genes."
    ),
    (
        "Third, the tissue specificity of the panel’s generalization (strong for ISS seedling "
        "studies, weak for root tissue and suborbital flight) indicates that the spaceflight "
        "transcriptional signature is not uniform across organs or flight profiles. Practically, "
        "biomarker panels trained predominantly on ISS seedling data should not be assumed to "
        "transfer directly to root tissues or short-duration suborbital flights without "
        "tissue-specific recalibration."
    ),
    (
        "Fourth, the Ca²⁺/K⁺ crosstalk circuit analysis reveals a guard-cell-centered signaling "
        "module that may serve as a cell-to-cell conduit for long-distance ion signaling under "
        "spaceflight conditions. The CBL1–CIPK23–AKT1 cascade, a canonical Ca²⁺-regulated K⁺ "
        "uptake pathway^6,7^, provides a mechanistic link between the Ca²⁺-dominant CCC network "
        "and K⁺ homeostasis. In addition, the exploratory guard-cell co-expression module "
        "(*CBL1*–*ANNAT1* r = 0.90, *CBL1*–*CDPK4* r = 0.63, and *CDPK4*–*ANNAT1* r = 0.56; "
        "n = 89) suggests that Ca²⁺ decoding and annexin-mediated Ca²⁺ buffering may be "
        "co-regulated in stomatal lineage cells, though larger guard-cell datasets will be needed "
        "to confirm these correlations. Guard cells regulate stomatal aperture, gas exchange, and "
        "water balance—processes that are critical in the closed atmosphere of spacecraft^8^. The "
        "10.2-fold dominance of Ca²⁺ over K⁺ in intercellular communication strength further "
        "supports Ca²⁺ as the primary long-range signal, with K⁺ transport acting as a downstream "
        "effector. This convergence of Ca²⁺ signaling and ER proteostasis (identified in the GO "
        "enrichment of flight-upregulated genes) points to a coordinated stress response in which "
        "Ca²⁺ oscillations trigger both CBL–CIPK-mediated ion transport and heat-shock protein "
        "induction to maintain proteostasis under microgravity-induced stress^5^."
    ),
    (
        "Several methodological limitations should be noted. (1) No independent external validation "
        "cohort currently exists for *Arabidopsis* spaceflight transcriptomics; consequently, all "
        "biomarker results are discovery-only and subject to potential optimism bias. (2) "
        "scPlantLLM was run with a reduced sequence length (seq_length = 500 vs. 1,500) to ensure "
        "CPU feasibility, which may have degraded embedding quality alongside root-to-seedling "
        "domain shift. (3) The single-cell atlas was grown under terrestrial conditions, providing "
        "a baseline cell-type reference rather than spaceflight-conditioned cell states. (4) "
        "PlantCellChat thresholds were relaxed from defaults to accommodate the terrestrial atlas. "
        "(5) Guard cells were represented by only 21 cells in the 9,998-cell subsample (89 cells "
        "in the full 41,314-cell atlas), potentially yielding high-variance guard-cell CCC and "
        "co-expression estimates. (6) The absence of organ labels in the seed-to-seed atlas limits "
        "anatomical resolution, necessitating cell-type proxy mapping."
    ),
    (
        "In summary, integrating multi-study spaceflight transcriptomics with single-cell "
        "communication inference establishes a testable mechanistic hypothesis linking orbital "
        "proteostatic stress, non-coding RNA regulation, and guard-cell-centered Ca²⁺/K⁺ "
        "signaling. Future spaceflight single-cell RNA-seq experiments across defined organs "
        "(roots, leaves, and stomatal lineages) will be essential to validate these candidate "
        "biomarkers and intercellular circuits directly under microgravity, informing crop "
        "engineering for bioregenerative life support systems."
    ),
]

METHODS_SECTIONS = [
    (
        "OSDR data retrieval and harmonization",
        (
            "*Arabidopsis thaliana* spaceflight transcriptomic studies comparing flight and ground "
            "control conditions were identified via the NASA OSDR biodata API. Six studies were "
            "selected: OSD-37 (56 samples, seedling, ISS), OSD-120 (24 samples, root, ISS), "
            "OSD-624 (36 samples, leaf and root, suborbital), OSD-678 (24 samples, seedling, ISS), "
            "OSD-38 (6 samples, seedling, ISS), and OSD-321 (10 samples, seedling, ISS) (Table 1). "
            "GeneLab-processed normalized expression matrices were downloaded and harmonized to "
            "TAIR AGI gene identifiers. The final pooled dataset comprised 156 samples (78 flight, "
            "78 ground control) and 32,548 nuclear genes."
        ),
    ),
    (
        "LASSO/elastic-net biomarker panel",
        (
            "Features were prepared by log2(x + 1) transformation, selection of the top 2,000 most "
            "variable features, and zero-mean/unit-variance scaling. An elastic-net regularized "
            "logistic regression model (α = 0.5, combining L1/LASSO and L2 penalties) was fitted "
            "via cv.glmnet^12^ (binomial family, AUC-based lambda selection). Cross-validation used "
            "leave-one-study-out folds (6 folds × 10 repeats = 60 iterations) with 80% "
            "class-balanced subsampling within each fold. Stability selection retained features "
            "selected in ≥50% of iterations, and performance was assessed by AUC, sensitivity, and "
            "specificity using pROC."
        ),
    ),
    (
        "Atlas data and preprocessing",
        (
            "The *Arabidopsis* seed-to-seed atlas (GEO accession GSE226097^1^) was downloaded as a "
            "Seurat RDS object and converted to AnnData format. The seedling_6d stage (41,314 cells "
            "× 22,375 genes across 5 cell types) was used after quality-control filtering "
            "(min_genes = 200, min_cells = 3), log-normalization (target_sum = 1e4, log1p "
            "transform), and selection of 3,000 highly variable genes (HVGs). A stratified "
            "subsample of 9,998 cells was used for scPlantLLM inference."
        ),
    ),
    (
        "scPlantLLM zero-shot inference",
        (
            "The scPlantLLM foundation model^2^ was run in zero-shot mode. Pretrained weights "
            "(flash_attn Wqkv format) were converted to standard PyTorch TransformerEncoderLayer "
            "format (in_proj_weight/bias). The model was configured with n_input_bins = 103, "
            "d_model = 512, nhead = 8, nlayers = 6, nlayers_cls = 3, and n_cls = 44. Inference "
            "used seq_length = 500 (reduced from the 1,500 training configuration for CPU "
            "feasibility), batch_size = 16, and 8 CPU threads. Genes were mapped to the scPlantLLM "
            "vocabulary (97.4% atlas gene overlap), and expression values were discretized using "
            "101 bins with category encoding."
        ),
    ),
    (
        "Clustering and differential expression",
        (
            "A k-nearest-neighbor (KNN) graph (n_neighbors = 15) was constructed on the "
            "512-dimensional scPlantLLM embeddings. Leiden clustering^13^ was performed across five "
            "resolutions (0.3–1.5), and resolution 0.5 (6 clusters) was selected as optimal. "
            "Agreement with atlas cell types and zero-shot predictions was assessed using the "
            "adjusted Rand index (ARI) and normalized mutual information (NMI). Differentially "
            "expressed genes per cluster were identified via Wilcoxon rank-sum tests "
            "(|log2FC| > 1, adjusted p < 0.05, expression fraction > 0.25)."
        ),
    ),
    (
        "PlantCellChat cell–cell communication",
        (
            "Cell–cell communication was inferred using PlantCellChat^3^ with the *Arabidopsis* "
            "ligand–receptor database (ath.csv: 5,725 interactions, 1,027 genes, 15 signaling "
            "pathways). Overexpressed genes were identified using relaxed thresholds "
            "(thresh.pc = 0, thresh.fc = 0, thresh.p = 0.1) to accommodate the terrestrial atlas. "
            "Communication strength was calculated with Kh = 0.5, n = 1, and 50 permutations, and "
            "signaling strength was aggregated per pathway and per cell-type pair."
        ),
    ),
    (
        "ggPlantmap spatial visualization",
        (
            "Spatial visualization was performed using ggPlantmap^4^ with pre-loaded *Arabidopsis* "
            "leaf cross-section (ggPm.At.leaf.crosssection) and root tip cross-section "
            "(ggPm.At.roottip.crosssection) maps. Cell types were mapped to anatomical regions of "
            "interest (ROIs), and expression values were merged via ggPlantmap.merge(). Heatmaps "
            "were generated with ggPlantmap.heatmap() using white-to-red gradients for expression "
            "and viridis palettes for communication strength."
        ),
    ),
    (
        "Ca²⁺ pathway visualization",
        (
            "The Ca²⁺ signaling network was visualized using the ggpathway workflow (ggraph + "
            "igraph^14^) with edge and node tables derived from PlantCellChat Ca²⁺ ligand–receptor "
            "pairs using stress-majorization layout (graphlayouts::layout_with_stress). A "
            "conceptual schematic of the Ca²⁺ signaling cascade under microgravity was constructed "
            "to illustrate the mechanistic model."
        ),
    ),
    (
        "GO enrichment analysis",
        (
            "GO and KEGG pathway enrichment was performed using the g:Profiler web service^15^ via "
            "the gprofiler2 R package (organism: athaliana) against a custom background of the "
            "2,000 most variable features from which the regularized model selected the biomarker "
            "panel. Benjamini–Hochberg FDR correction was applied with a significance threshold of "
            "padj < 0.05. Three queries were tested: all 85 panel genes, 41 flight-upregulated "
            "genes (mean coefficient > 0), and 44 ground-upregulated genes (mean coefficient < 0), "
            "covering GO Biological Process, Molecular Function, Cellular Component, and KEGG "
            "pathways."
        ),
    ),
    (
        "Ca²⁺/K⁺ crosstalk circuit analysis",
        (
            "Gene identifiers were assigned from TAIR AGI loci and cross-checked against the "
            "PlantCellChat *Arabidopsis* database (corrected mapping provided in the companion "
            "repository). The Ca²⁺ pathway was expanded to include six K⁺ channels "
            "(*AKT1*/*AT2G26650*, *AKT2*/*AT4G22200*, *GORK*/*AT5G37500*, *KAT1*/*AT5G46240*, "
            "*KAT2*/*AT4G18290*, and *KC1*/*AT4G32650*). Edges were extracted from PlantCellChat "
            "ligand–receptor interactions for the Ca²⁺ and K⁺ pathways; the CBL1–CIPK23–AKT1 "
            "relationship was present in the database and is further supported by the "
            "literature^6,7^. The resulting 27-node, 56-edge network was drawn with ggpathway "
            "(ggraph + igraph, graphlayouts::layout_with_stress, seed = 42^14^), with nodes "
            "colored by functional class and scaled by mean expression. Per-cell-type mean "
            "expression and percentage of expressing cells were computed from the log-normalized "
            "atlas, and gene–gene co-expression was calculated as Pearson correlation across all "
            "cells and within each cell type. Communication strengths for the Ca²⁺ and K⁺ pathways "
            "were aggregated into 5 × 5 source–target matrices. Spatial visualization used "
            "ggPlantmap with cell-type mean expression mapped to organ regions as a proxy "
            "(cotyledon = mesophyll + guard; hypocotyl = epidermal + stele; root = stele + "
            "meristematic; Supplementary Figure S7)."
        ),
    ),
    (
        "Statistics and reproducibility",
        (
            "All statistical tests are described in their respective Methods subsections. "
            "Cross-validation used 60 iterations (6 studies × 10 repeats), and the reported "
            "cross-study AUC interval (0.431–1.000) represents the empirical 2.5th–97.5th "
            "percentile across the 60 iterations. Differential expression used Wilcoxon rank-sum "
            "tests with Benjamini–Hochberg correction, and PlantCellChat permutation testing used "
            "50 permutations. No statistical methods were used to predetermine sample sizes, and "
            "results are reported as discovery-only given the absence of independent validation "
            "cohorts. Detailed methods—including the scPlantLLM weight conversion code "
            "(flash_attn Wqkv to PyTorch in_proj format), analysis parameters, and software "
            "versions—are provided in Supplementary Methods."
        ),
    ),
]

DECLARATIONS = [
    (
        "Data Availability",
        (
            "All primary datasets analyzed in this study are publicly available. Spaceflight "
            "transcriptomic datasets (OSD-37, OSD-120, OSD-321, OSD-38, OSD-624, and OSD-678) are "
            "available from the NASA Open Science Data Repository "
            "(https://visualization.osdr.nasa.gov/biodata/api/). The *Arabidopsis* seed-to-seed "
            "single-cell atlas is available from the Gene Expression Omnibus (GEO accession "
            "GSE226097). Processed summary tables, gene-mapping audits, and supplementary datasets "
            "are deposited in the companion GitHub repository (" + REPO_URL + ") and will be "
            "archived on Zenodo with a persistent DOI upon acceptance."
        ),
    ),
    (
        "Code Availability",
        (
            "All custom Python and R analysis scripts, figure generation pipelines, scPlantLLM "
            "weight conversion utilities, and manuscript build scripts are openly available under "
            "the MIT License at " + REPO_URL + ". Third-party tools used in this work are publicly "
            "available at https://github.com/compbioNJU/scPlantLLM (scPlantLLM), "
            "https://github.com/mrliuw/PlantCellChat (PlantCellChat), and "
            "https://github.com/leonardojo/ggPlantmap (ggPlantmap)."
        ),
    ),
    (
        "Acknowledgements",
        (
            "We thank the NASA GeneLab team and the Plant Analysis Working Group for valuable "
            "discussions and community support. This work utilizes open-access data from the NASA "
            "Open Science Data Repository (OSDR)."
        ),
    ),
    (
        "Author Contributions",
        "R.B. conceived the study, designed the analysis, performed all computational work, generated the figures, and wrote the manuscript.",
    ),
    (
        "Funding",
        (
            "This research was conducted as a community analysis within the NASA GeneLab Plant "
            "Analysis Working Group using publicly available datasets from the NASA Open Science "
            "Data Repository and received no specific external grant funding."
        ),
    ),
    (
        "Competing Interests",
        "The author declares no competing interests.",
    ),
]

REFERENCES = [
    "1. Lee, J., Nobori, T., Illouz-Eliaz, N. et al. A single-cell, spatial transcriptomic atlas of the *Arabidopsis* life cycle. *Nat. Plants* (2025). https://doi.org/10.1038/s41477-025-02072-z",
    "2. Cao, G. et al. scPlantLLM: a foundation model for exploring single-cell expression atlases in plants. *Genomics Proteomics Bioinformatics* **23**, qzaf024 (2025). https://doi.org/10.1093/gpbjnl/qzaf024",
    "3. Zhang, Y. et al. PlantCellChat: inferring and visualizing plant cell-cell communication. GitHub https://github.com/mrliuw/PlantCellChat (2023).",
    "4. Jo, L. & Kajala, K. ggPlantmap: an open-source R package for the creation of informative and quantitative ggplot maps derived from plant images. *J. Exp. Bot.* **75**, erae043 (2024).",
    "5. Takahashi, K. et al. Gravity sensing in plant and animal cells. *npj Microgravity* **7**, 2 (2021).",
    "6. Li, L., Kim, B.-G., Cheong, Y. H., Pandey, G. K. & Luan, S. A Ca²⁺ signaling pathway regulates a K⁺ channel for low-K response in *Arabidopsis*. *Proc. Natl. Acad. Sci. USA* **103**, 12625–12629 (2006).",
    "7. Xu, J. et al. A protein kinase, interacting with two calcineurin B-like proteins, regulates K⁺ transporter AKT1 in *Arabidopsis*. *Cell* **125**, 1347–1360 (2006).",
    "8. Cheong, Y. H. et al. Two calcineurin B-like calcium sensors, interacting with protein kinase CIPK23, regulate leaf transpiration and root potassium uptake in *Arabidopsis*. *Plant J.* **52**, 473–484 (2007).",
    "9. Wang, X.-J. et al. Genome-wide prediction and identification of *cis*-natural antisense transcripts in *Arabidopsis thaliana*. *Genome Biol.* **6**, R30 (2005).",
    "10. Babbar, R., Karpinska, B., Grover, A. & Foyer, C. H. Heat-induced oxidation of the nuclei and cytosol. *Front. Plant Sci.* **11**, 617779 (2021). https://doi.org/10.3389/fpls.2020.617779",
    "11. Kushwaha, H. R. et al. MATH-domain family shows response toward abiotic stress in plants. *Front. Plant Sci.* **7**, 923 (2016).",
    "12. Friedman, J., Hastie, T. & Tibshirani, R. Regularization paths for generalized linear models via coordinate descent. *J. Stat. Softw.* **33**, 1–22 (2010).",
    "13. Traag, V. A., Waltman, L. & van Eck, N. J. From Louvain to Leiden: guaranteeing well-connected communities. *Sci. Rep.* **9**, 5233 (2019).",
    "14. Li, C. ggpathway: a tutorial for pathway visualization using tidyverse, igraph, and ggraph. GitHub https://github.com/cxli233/ggpathway (2024).",
    "15. Raudvere, U. et al. g:Profiler: a web server for functional enrichment analysis and conversions of gene lists (2019 update). *Nucleic Acids Res.* **47**, W191–W198 (2019).",
]

# 7 renumbered main figures: (filename, width_inches, title, legend)
FIGURES = [
    (
        "Figure1_LASSO_and_scPlantLLM.png",
        6.2,
        "**Figure 1.** LASSO/elastic-net biomarker panel and scPlantLLM single-cell atlas embeddings.",
        (
            "**a** Leave-one-study-out cross-validation AUC for each held-out OSDR study (6 studies, "
            "10 repeats each). Bars show mean AUC, error bars show standard deviation (upper bound "
            "capped at 1.0), and dots show individual iterations; dashed line indicates chance (0.5) "
            "and red line indicates overall mean (0.734). **b** Selection frequency of the top 20 "
            "most stable features across 60 iterations; orange bars denote positive coefficients "
            "(flight-enriched) and blue bars denote negative coefficients (ground-enriched), with "
            "the dashed line marking the 50% stability threshold. **c** Coefficient forest plot for "
            "the 4 genes selected at 100% frequency (*ATHSP22.0*/*AT4G10250* and the natural "
            "antisense transcript *AT3G07365* positive; chloroplast protein *AT2G14247* and "
            "TRAF-like protein *AT4G01390* negative; error bars show SD). **d–f** UMAP visualizations "
            "of 9,998 atlas cells embedded by scPlantLLM (512-dimensional, seq_length = 500) colored "
            "by (**d**) atlas cell-type annotations (Epidermal, Mesophyll, Stele, Meristematic, "
            "Guard), (**e**) Leiden clusters (resolution 0.5, 6 clusters; ARI = 0.033 vs. atlas cell "
            "types), and (**f**) scPlantLLM zero-shot predictions (top 8 classes shown; ARI = 0.154 "
            "vs. Leiden clusters)."
        ),
    ),
    (
        "Figure2_CCC_communication.png",
        6.2,
        "**Figure 2.** PlantCellChat cell–cell communication analysis.",
        (
            "**a** Communication strength heatmap showing total communication between each source "
            "(rows) and target (columns) cell-type pair, summed across all ligand–receptor "
            "interactions. **b** Top 10 annotated signaling pathways ranked by total communication "
            "strength; Ca²⁺ (orange) is the dominant pathway (249.5), 4.6-fold higher than "
            "brassinosteroid (BR, 54.5). **c** Top 50 ligand–receptor pairs ranked by total "
            "communication strength in an expanded right-hand panel. Grey bars represent "
            "unannotated general receptor-like kinase (RLK) pairs (ranks 1–21 and 43 of the top "
            "50); orange bars highlight Ca²⁺ pathway pairs (AT1G20620_AT5G19450 at rank 22 and "
            "AT1G59870_AT3G51920 at rank 33); blue bars denote other annotated signaling pathways "
            "(chitin, BR, and NO₃⁻)."
        ),
    ),
    (
        "Figure3_ggPlantmap_LASSO_genes.png",
        4.6,
        "**Figure 3.** Spatial expression of LASSO/elastic-net biomarker genes on *Arabidopsis* anatomy.",
        (
            "ggPlantmap heatmaps showing mean expression of the top 4 biomarker genes on "
            "*Arabidopsis* cross-sections. **a** Leaf cross-section: Epidermal cells mapped to "
            "epidermis (adaxial/abaxial), Mesophyll to palisade and spongy parenchyma, Stele to "
            "vascular bundle (xylem, phloem, and bundle sheath), and Guard to stomata. **b** Root "
            "tip cross-section: Epidermal cells mapped to epidermis, Mesophyll to cortex, Stele to "
            "procambium/xylem/phloem/pericycle, and Meristematic to columella. The white-to-red "
            "gradient indicates mean expression level; panel titles display the TAIR AGI locus ID, "
            "gene name/alias (*ATHSP22.0*, *NAT*, *Chloroplast protein*, and *TRAF-like*), and "
            "model coefficient. *AT4G10250* (*ATHSP22.0*) shows zero baseline expression across all "
            "cell types in the unstressed terrestrial atlas (colorbar at 0), consistent with "
            "spaceflight-specific induction; *AT3G07365* (non-coding RNA) is absent from the atlas "
            "protein-coding gene set and is shown in grey (no data)."
        ),
    ),
    (
        "Figure4_Ca2_pathway.png",
        6.2,
        "**Figure 4.** Ca²⁺ signaling pathway: dominant cell–cell communication axis.",
        (
            "**a** Data-driven Ca²⁺ signaling network (20 nodes) visualized using the ggpathway "
            "workflow (ggraph + igraph) with a stress-majorization layout "
            "(graphlayouts::layout_with_stress). Nodes represent Ca²⁺ (yellow, ligand), CBL sensors "
            "(dark blue: *CBL1*, *CBL9*, *CBL2*), CIPK kinases (green: *CIPK23*, *CIPK1*, *CIPK9*), "
            "CaM/CML sensors (pink: *CML38*, *CML42*, *CML24*, *CaM7*, *CaM3*), CDPK kinases "
            "(orange: *CDPK3*, *CDPK4*), downstream targets (light blue: *CAX3*, *NRT2.1*, *SOS1*, "
            "*ANNAT1*), and LASSO/elastic-net biomarker genes (red-orange: *HSP22.0* and "
            "*TRAF-like*). Node size indicates mean expression in the atlas, and edge width/opacity "
            "reflects PlantCellChat communication strength. **b** Conceptual schematic of the Ca²⁺ "
            "signaling cascade under microgravity, illustrating Ca²⁺ channel activation, cytosolic "
            "Ca²⁺ elevation, and branching to CBL–CIPK, calmodulin, and CDPK pathways leading to "
            "stress-response genes."
        ),
    ),
    (
        "Figure5_integration.png",
        6.2,
        "**Figure 5.** Integration of the LASSO/elastic-net panel, Ca²⁺ signaling, and gene functions.",
        (
            "**a** Biomarker panel weighted score on the leaf cross-section (score = sum of "
            "coefficient × expression across 74 atlas-present panel genes). Blue indicates a "
            "ground-like (negative) score; all cell types show negative scores, consistent with "
            "the terrestrial growth conditions of the atlas. **b** Ca²⁺ signaling strength on the "
            "leaf cross-section, illustrating cell-type-specific Ca²⁺ communication. **c** Summary "
            "table of the top 4 biomarker gene functions, including TAIR gene ID, gene name/alias, "
            "mean coefficient, prediction direction (Flight [+] or Ground [−]), and protein function."
        ),
    ),
    (
        "Figure6_ca2_k_circuit_composite.png",
        5.8,
        "**Figure 6.** Ca²⁺/K⁺ crosstalk signaling circuit in the *Arabidopsis* seedling single-cell atlas.",
        (
            "**a** Ca²⁺/K⁺ pathway network (27 nodes, 56 edges; ggpathway, stress-majorization "
            "layout). Ca²⁺ edges are shown in blue, K⁺ edges in green, and crosstalk edges in "
            "orange; node color denotes functional class and node size reflects mean expression "
            "across the atlas. **b** Global Pearson co-expression of the 25 circuit genes across "
            "all 41,314 atlas cells; global correlations are weak (|r| < 0.1 for nearly all pairs). "
            "**c** ggPlantmap seedling maps of six circuit genes (*AKT1*, *CBL9*, *CIPK23*, "
            "*CML24*, *KC1*, and *CDPK3*) by cell-type proxy; *CIPK23* shows guard/epidermal "
            "enrichment and *AKT1* shows epidermal enrichment. **d** Cell-to-cell Ca²⁺ (blue) and "
            "K⁺ (green) communication strength between the five cell types; guard cells are the "
            "dominant Ca²⁺ source (outgoing 57.1), and epidermal cells are the primary K⁺ source."
        ),
    ),
    (
        "Figure7_sankey_ca2_k_cascade.png",
        4.6,
        "**Figure 7.** CBL1–CIPK23–AKT1 cascade: spatial expression and molecular cascade.",
        (
            "**a** ggPlantmap leaf cross-sections of (i) *CIPK23* expression (guard-highest, mean "
            "0.333) and (ii) *AKT1* expression (epidermal-highest, mean 0.367), showing the kinase "
            "and its channel target across leaf cell types. **b** Molecular-cascade Sankey diagram "
            "tracing signal flow from Ca²⁺ through calcium sensors (*CBL1*, *CBL9*, *CaM3*, "
            "*CML24*) and kinases (*CIPK23*, *CDPK3*, *CDPK4*) to effectors (*AKT1*, *ANNAT1*, "
            "*KC1*) and K⁺ uptake; node heights are proportional to guard-cell expression, italic "
            "edge badges denote exploratory guard-cell Pearson r values (n = 89), and column "
            "headers indicate cascade stages (Signal, Sensors, Kinases, Channels, Output)."
        ),
    ),
]

SUPP_FIGS = [
    (
        "**Supplementary Figure S1.** GO enrichment dotplot.",
        (
            "Dot plot showing significant GO and KEGG terms enriched in the 85-gene panel, "
            "41 flight-upregulated genes, and 44 ground-upregulated genes. Dot size represents "
            "gene count, and color represents −log10(p-value). Background: 2,000 variable "
            "features; multiple-testing correction: BH-FDR (padj < 0.05)."
        ),
    ),
    (
        "**Supplementary Figure S2.** GO enrichment directed bar plot.",
        (
            "Bar plot showing −log10(p-value) for significant terms separated by direction "
            "(flight-upregulated vs. ground-upregulated). Flight-upregulated genes are enriched "
            "for heat response, hypoxia, and ER protein processing, whereas ground-upregulated "
            "genes are enriched for flavonoid biosynthesis."
        ),
    ),
    (
        "**Supplementary Figure S3.** Spatial expression of Ca²⁺/K⁺ circuit genes across *Arabidopsis* anatomy.",
        (
            "Three ggPlantmap figures showing Ca²⁺/K⁺ circuit gene expression and CCC signaling "
            "strength across *Arabidopsis* anatomical contexts: (**a**) seed developmental series "
            "(ggPm.At.seed.devseries), (**b**) root mature cross-section "
            "(ggPm.At.rootmatur.crosssection, 8 ROIs), and (**c**) young seedling "
            "(ggPm.At.seedling.saltdrought, 12 ROIs). Cell-type proxy mapping is used because the "
            "scRNA-seq atlas does not include organ-specific labels; values represent "
            "approximations from the whole-seedling atlas."
        ),
    ),
    (
        "**Supplementary Figure S4.** Ca²⁺/K⁺ co-expression heatmap.",
        (
            "25-gene Pearson correlation matrix across all 41,314 atlas cells. Global pairwise "
            "correlations are weak (|r| < 0.1 for nearly all gene pairs), whereas exploratory "
            "within-cell-type analysis in guard cells (n = 89) reveals co-variation among "
            "*CBL1*–*ANNAT1* (r = 0.90), *CBL1*–*CDPK4* (r = 0.63), and *CDPK4*–*ANNAT1* (r = 0.56)."
        ),
    ),
    (
        "**Supplementary Figure S5.** Ca²⁺/K⁺ gene expression per cell type.",
        (
            "Heatmaps showing mean expression (left) and percentage of expressing cells (right) "
            "for 25 Ca²⁺/K⁺ circuit genes across 5 cell types. *CIPK9* (16.9–23.2%) and *CIPK1* "
            "(18.0–22.9%) show the broadest expression, with *CIPK23* peaking in guard cells "
            "(20.2%, mean 0.333) and *AKT1* peaking in epidermal cells (16.7%, mean 0.367), "
            "whereas *NRT2.1* shows the lowest expression (0.0–0.2%)."
        ),
    ),
    (
        "**Supplementary Figure S6.** Cell-to-cell Ca²⁺/K⁺ communication circuit.",
        (
            "Circular network diagram showing Ca²⁺ (blue) and K⁺ (green) signaling strength "
            "between 5 cell types, with edge width proportional to communication strength. Guard "
            "cells are the dominant Ca²⁺ source (total outgoing strength 57.1), and epidermal "
            "cells are the primary K⁺ source."
        ),
    ),
    (
        "**Supplementary Figure S7.** Organ marker diagnostic.",
        (
            "Expression of 15 tissue-specific markers across 5 cell types. Root markers (*SCR*, "
            "*PLT1*, *WOL*) are near-absent (<3%), photosynthetic markers (*RBCS*, *FSD1*) are "
            "ubiquitous (93–98%), and seed markers (*LEC2*, *2S3*) are near zero, indicating that "
            "marker-based organ inference is unreliable in this whole-seedling atlas."
        ),
    ),
    (
        "**Supplementary Figure S8.** Expanded Ca²⁺/K⁺ pathway network.",
        (
            "Full 27-node, 56-edge Ca²⁺/K⁺ pathway network visualized with ggpathway "
            "(stress-majorization layout). Ca²⁺ edges are shown in blue, K⁺ edges in green, and "
            "crosstalk edges in orange. Node classes comprise CBL sensors, CIPK kinases, CaM/CML "
            "sensors, CDPKs, K⁺ channels, Ca²⁺ targets, and LASSO/elastic-net biomarker genes."
        ),
    ),
]

SUPP_TABLES = [
    ("**Supplementary Table S1.** LASSO/elastic-net biomarker panel.", "85 stable features (selection frequency ≥50%) with mean coefficient, standard deviation, and stability status."),
    ("**Supplementary Table S2.** GO enrichment results (all terms).", "Complete g:Profiler output for all 3 queries (85 genes, 41 flight-upregulated, 44 ground-upregulated), including all tested terms, p-values, and gene lists."),
    ("**Supplementary Table S3.** GO enrichment significant terms.", "14 significant terms (BH-FDR padj < 0.05) across all 3 queries with −log10(p) and gene lists."),
    ("**Supplementary Table S4.** Ca²⁺/K⁺ CCC circuit.", "25 cell-pair communication strengths for Ca²⁺ and K⁺ pathways, with organ proxies and dominance flags."),
    ("**Supplementary Table S5.** Ca²⁺/K⁺ signaling circuit summary.", "Circuit-level summary listing source/target cell types, dominant signal, Ca²⁺ and K⁺ strengths, Ca²⁺/K⁺ ratio, top source/target genes, and strongest co-expression pair."),
    ("**Supplementary Table S6.** Ca²⁺/K⁺ circuit node expression.", "23-gene expression table reporting mean expression and percentage of expressing cells across 5 cell types, along with top co-expression partners and correlation coefficients."),
    ("**Supplementary Table S7.** Ca²⁺/K⁺ co-expression matrix.", "25 × 25 Pearson correlation matrix for Ca²⁺/K⁺ circuit genes computed across all atlas cells."),
    ("**Supplementary Table S8.** Organ marker expression.", "15 tissue-specific markers evaluated across 5 cell types with mean expression and percentage of expressing cells."),
]


def build_manuscript(output_path: str, embed_figures: bool):
    doc = Document()
    for sec in doc.sections:
        sec.page_width = Inches(8.5)
        sec.page_height = Inches(11.0)
        sec.top_margin = Inches(1.0)
        sec.bottom_margin = Inches(1.0)
        sec.left_margin = Inches(1.0)
        sec.right_margin = Inches(1.0)

    # Title page block
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(10)
    add_rich_runs(p_title, TITLE, font_size=16, base_bold=True)

    add_body_para(doc, "**Richard Barker**", space_after=2, font_size=11)
    add_body_para(doc, "GeneLab Plant Analysis Working Group, NASA Open Science Data Repository", space_after=2, font_size=10)
    add_body_para(doc, "ORCID: https://orcid.org/0000-0002-8368-2825", space_after=2, font_size=9.5)
    add_body_para(doc, "Corresponding author: dr.richard.barker@gmail.com", space_after=10, font_size=9.5, base_italic=True)

    # Abstract
    add_heading(doc, "Abstract", level=1)
    add_body_para(doc, ABSTRACT, space_after=8)

    # Introduction
    add_heading(doc, "Introduction", level=1)
    for para in INTRO_PARAS:
        add_body_para(doc, para)

    # Results
    add_heading(doc, "Results", level=1)
    for subhead, paras in RESULTS_SECTIONS:
        add_heading(doc, subhead, level=2)
        for para in paras:
            add_body_para(doc, para)

    # Discussion
    add_heading(doc, "Discussion", level=1)
    for para in DISCUSSION_PARAS:
        add_body_para(doc, para)

    # Methods
    add_heading(doc, "Methods", level=1)
    for subhead, body in METHODS_SECTIONS:
        add_heading(doc, subhead, level=2)
        add_body_para(doc, body)

    # Mandatory npj Microgravity Declarations (before References)
    for title, text in DECLARATIONS:
        add_heading(doc, title, level=1)
        add_body_para(doc, text)

    # References
    add_heading(doc, "References", level=1)
    for ref in REFERENCES:
        add_body_para(doc, ref, space_after=3, font_size=9.5)

    # Table 1
    add_heading(doc, "Tables", level=1)
    add_table1(doc)

    # Figures / Figure Legends
    if embed_figures:
        add_heading(doc, "Figures", level=1)
        for fname, width_in, ftitle, flegend in FIGURES:
            p_t = add_body_para(doc, ftitle, space_after=4, font_size=10.5)
            p_t.paragraph_format.keep_with_next = True
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(2)
            p_img.paragraph_format.space_after = Pt(4)
            p_img.paragraph_format.keep_with_next = True
            p_img.add_run().add_picture(os.path.join(FIGDIR, fname), width=Inches(width_in))
            add_body_para(doc, flegend, space_after=12, font_size=9.5)
    else:
        add_heading(doc, "Figure Legends", level=1)
        for _, _, ftitle, flegend in FIGURES:
            p_t = add_body_para(doc, ftitle, space_after=2, font_size=10)
            p_t.paragraph_format.keep_with_next = True
            add_body_para(doc, flegend, space_after=8, font_size=9.5)

    # Supplementary Legends
    add_heading(doc, "Supplementary Figure Legends", level=1)
    for stitle, slegend in SUPP_FIGS:
        p_t = add_body_para(doc, stitle, space_after=2, font_size=10)
        p_t.paragraph_format.keep_with_next = True
        add_body_para(doc, slegend, space_after=6, font_size=9.5)

    add_heading(doc, "Supplementary Table Legends", level=1)
    for ttitle, tlegend in SUPP_TABLES:
        p_t = add_body_para(doc, ttitle, space_after=2, font_size=10)
        p_t.paragraph_format.keep_with_next = True
        add_body_para(doc, tlegend, space_after=6, font_size=9.5)

    doc.save(output_path)


def main():
    print("Building submission manuscript.docx (7 figures, separate legends) ...")
    build_manuscript(MANUSCRIPT_ONLY, embed_figures=False)

    print("Building manuscript_with_figures.docx (7 inline figures) ...")
    build_manuscript(MANUSCRIPT_FIGS, embed_figures=True)

    print("Syncing manuscript_with_figures_ACTIVE_DRAFT.docx ...")
    shutil.copy2(MANUSCRIPT_FIGS, MANUSCRIPT_DRAFT)

    abs_plain = re.sub(r"[\*^]", "", ABSTRACT)
    print(f"Abstract word count: {len(abs_plain.split())} (limit <=150)")
    doc_f = Document(MANUSCRIPT_FIGS)
    print(f"manuscript_with_figures.docx: {len(doc_f.inline_shapes)} inline figures, {len(doc_f.tables)} table")


if __name__ == "__main__":
    main()
