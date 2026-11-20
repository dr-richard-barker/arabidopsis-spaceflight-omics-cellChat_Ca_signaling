#!/usr/bin/env python3
"""
Peer-review polish script for the npj Microgravity manuscript.

Applies:
1. Line-by-line grammar, flow, punctuation, and American English standardization
   across Title, Abstract, Introduction, Results, Discussion, Methods, and Legends.
2. Uniform Ca²⁺ / K⁺ / H₂O₂ / en-dash notation in body prose and legends.
3. Updates Figure 3, Figure 4, and Figure 6 descriptions, legends, and embedded
   images to match the rearranged Figure 3c (Top 50 LR pairs), Figure 4
   (gene names + TAIR IDs), and Figure 6c (fixed Direction labels + full text).
4. Cites all 15 references in strict ascending order of first appearance [1]-[15]
   and reorders the References list to match.
5. Inserts Table 1 (summary of the 6 NASA OSDR studies and LOOS-CV performance)
   so the "Table 1" citation in Results is backed by an actual formatted table.
6. Removes residual pre-correction artifacts noted in CORRECTIONS.md
   (Discussion CIPK23-CaM3 r=0.46, Supp Fig S4 CIPK23-CaM3 / CBL9-AKT1,
   Supp Fig S8 67-edge -> 56-edge, Figure 8 stale "KEGG systems biology context"),
   removes the duplicate GO-enrichment sentence in Results, fixes the Mesophyll/
   Epidermal ordering in Results, and clarifies guard-cell subsample vs. full-atlas counts.
7. Removes the duplicate Figure Legends block in manuscript.docx (keeping one
   canonical Figure Legends section after Table 1) and in
   manuscript_with_figures*.docx (keeping inline figures + captions).
"""

import os
import shutil
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


HERE = os.path.dirname(os.path.abspath(__file__))
MANUSCRIPT_ONLY = os.path.join(HERE, "manuscript.docx")
MANUSCRIPT_FIGS = os.path.join(HERE, "manuscript_with_figures.docx")
MANUSCRIPT_DRAFT = os.path.join(HERE, "manuscript_with_figures_ACTIVE_DRAFT.docx")
FIG3_PNG = os.path.join(HERE, "figures", "Figure3_CCC_communication.png")
FIG4_PNG = os.path.join(HERE, "figures", "Figure4_ggPlantmap_LASSO_genes.png")
FIG6_PNG = os.path.join(HERE, "figures", "Figure6_integration.png")


def find_para(doc, prefix, start=0):
    for i in range(start, len(doc.paragraphs)):
        if doc.paragraphs[i].text.strip().startswith(prefix):
            return i, doc.paragraphs[i]
    raise ValueError(f"Paragraph starting with {prefix!r} not found (start={start})")


def set_para_text(para, new_text, bold=None, italic=None):
    """Replace paragraph text while preserving paragraph style and optional run styling."""
    first_font_name = None
    first_font_size = None
    first_bold = None
    first_italic = None
    for r in para.runs:
        if first_font_name is None and r.font.name:
            first_font_name = r.font.name
        if first_font_size is None and r.font.size:
            first_font_size = r.font.size
        if first_bold is None and r.bold is not None:
            first_bold = r.bold
        if first_italic is None and r.italic is not None:
            first_italic = r.italic
        r.text = ""
    if para.runs:
        run = para.runs[0]
        run.text = new_text
    else:
        run = para.add_run(new_text)
    if first_font_name:
        run.font.name = first_font_name
    if first_font_size:
        run.font.size = first_font_size
    if bold is not None:
        run.bold = bold
    elif first_bold is not None:
        run.bold = first_bold
    if italic is not None:
        run.italic = italic
    elif first_italic is not None:
        run.italic = first_italic


def remove_paragraph(para):
    p_el = para._element
    parent = p_el.getparent()
    if parent is not None:
        parent.remove(p_el)


def replace_picture_in_para(para, image_path, width_inches):
    """Clear existing drawing runs in a paragraph and add a fresh picture."""
    for r in list(para.runs):
        para._p.remove(r._r)
    run = para.add_run()
    run.add_picture(image_path, width=Inches(width_inches))


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


def insert_table1_after(doc, anchor_para):
    """Insert Table 1 caption + formatted 8x7 Word table immediately after anchor_para."""
    cap_p = doc.add_paragraph()
    cap_run = cap_p.add_run(
        "Table 1. Summary of NASA OSDR Arabidopsis spaceflight transcriptomic studies and "
        "leave-one-study-out cross-validation (LOOS-CV) performance."
    )
    cap_run.bold = True
    cap_run.font.name = "Arial"
    cap_run.font.size = Pt(10)

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
    col_widths = [0.75, 0.85, 0.75, 0.85, 1.15, 0.90, 0.75]

    for j, h in enumerate(headers):
        cell = table.rows[0].cells[j]
        cell.width = Inches(col_widths[j])
        set_cell_shading(cell, "1F4E79")
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(2)
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

    spacer_p = doc.add_paragraph()

    # Move newly created paragraphs & table directly after anchor_para
    anchor_para._element.addnext(spacer_p._element)
    anchor_para._element.addnext(table._tbl)
    anchor_para._element.addnext(cap_p._element)


# Canonical polished replacements keyed by unique starting prefix
TEXT_UPDATES = [
    (
        "LASSO biomarker panel and single-cell atlas integration",
        "LASSO biomarker panel and single-cell atlas integration reveal Ca²⁺-dominated cell–cell communication in the Arabidopsis spaceflight response",
        None,
    ),
    (
        "Spaceflight imposes mechanical, oxidative, and gravitational stresses",
        (
            "Spaceflight imposes mechanical, oxidative, and gravitational stresses on plants, "
            "yet the cell-type-specific signaling architecture underlying these responses remains "
            "poorly characterized. We integrated bulk transcriptomic biomarker discovery (156 samples "
            "across 6 NASA OSDR studies) with single-cell analysis of the Arabidopsis seed-to-seed "
            "atlas (41,314 cells) using scPlantLLM, PlantCellChat, and ggPlantmap. The 85-gene LASSO "
            "panel (mean cross-study AUC = 0.734) revealed enrichment for stress and endoplasmic "
            "reticulum (ER) proteostasis pathways among flight-upregulated genes and flavonoid "
            "metabolism among ground-upregulated genes. PlantCellChat identified Ca²⁺ as the "
            "dominant signaling pathway (10.2-fold higher than K⁺), with guard cells acting as the "
            "primary Ca²⁺ source. A CBL1–CIPK23–AKT1 crosstalk circuit connects Ca²⁺ sensing to "
            "K⁺ uptake, with CIPK23 most highly expressed in guard cells and AKT1 in epidermal cells. "
            "Together, these findings highlight Ca²⁺/K⁺ crosstalk and non-coding RNA regulation as "
            "key features of the Arabidopsis spaceflight response."
        ),
        None,
    ),
    (
        "Plants grown in spaceflight conditions experience",
        (
            "Plants grown in spaceflight conditions experience a constellation of stresses, including "
            "microgravity, altered atmospheric composition, modified light regimes, and increased "
            "ionizing radiation. Transcriptomic studies of Arabidopsis thaliana flown on the "
            "International Space Station (ISS) and suborbital platforms have identified hundreds of "
            "differentially expressed genes, but the cell-type-specific architecture of these "
            "responses and the intercellular signaling pathways that coordinate them remain poorly "
            "understood."
        ),
        None,
    ),
    (
        "NASA’s Open Science Data Repository (OSDR) provides",
        (
            "NASA’s Open Science Data Repository (OSDR) provides a growing collection of "
            "Arabidopsis spaceflight transcriptomics datasets. However, individual studies typically "
            "have small sample sizes (3–6 replicates per condition), making robust biomarker "
            "discovery challenging. Pooling multiple studies with study-stratified cross-validation "
            "offers a path toward generalizable biomarker identification, although the results must "
            "be interpreted as discovery-only given the absence of independent validation cohorts."
        ),
        None,
    ),
    (
        "The recent publication of the Arabidopsis seed-to-seed",
        (
            "The publication of the Arabidopsis seed-to-seed single-cell atlas (Lee et al., 2025 [1]) "
            "and the scPlantLLM foundation model (Cao et al., 2025 [2]) provides new opportunities "
            "for cell-type-resolved analysis. Trained on plant single-cell transcriptomics data, "
            "scPlantLLM can generate zero-shot cell embeddings and cell-type predictions [2]. "
            "PlantCellChat enables inference of ligand–receptor-mediated cell–cell communication (CCC) "
            "from single-cell data using a plant-specific interaction database [3], while ggPlantmap "
            "allows quantitative expression and signaling metrics to be mapped directly onto plant "
            "anatomical structures [4]."
        ),
        None,
    ),
    (
        "Ca2+ is a primary second messenger",
        (
            "Ca²⁺ is a primary second messenger in plant gravity perception. Microgravity alters "
            "cytosolic Ca²⁺ oscillations and gradients that guide directional growth, and spaceflight "
            "experiments have confirmed that cytosolic Ca²⁺ levels shift in response to changes in "
            "gravisensor positioning [5]. The CBL–CIPK calcium signaling cascade is a well-established "
            "downstream effector, and the CBL1–CIPK23–AKT1 pathway specifically links Ca²⁺ sensing "
            "to K⁺ uptake, regulating stomatal aperture and root K⁺ acquisition [6–8]. This "
            "Ca²⁺–K⁺ crosstalk is particularly relevant to spaceflight, where altered gravity disrupts "
            "ion homeostasis and turgor regulation."
        ),
        None,
    ),
    (
        "Here we integrate these approaches",
        (
            "Here, we integrate these approaches to: (1) construct a LASSO biomarker panel predicting "
            "spaceflight versus ground conditions from pooled OSDR transcriptomic data; (2) apply "
            "scPlantLLM to the seed-to-seed atlas for zero-shot cell annotation and clustering; "
            "(3) infer intercellular communication with PlantCellChat; (4) visualize spatial expression "
            "and communication patterns on plant anatomy with ggPlantmap; (5) integrate the biomarker "
            "panel with the single-cell signaling architecture; and (6) characterize the Ca²⁺/K⁺ "
            "crosstalk circuit linking Ca²⁺ signaling to K⁺ transport via the CBL1–CIPK23–AKT1 "
            "cascade. We further examine the biological functions of the top biomarker genes, perform "
            "GO enrichment analysis on the full 85-gene panel, and trace the cell-to-cell signaling "
            "circuit underlying long-distance ion signaling."
        ),
        None,
    ),
    (
        "We pooled 156 bulk RNA-seq samples",
        (
            "We pooled 156 transcriptomic samples from 6 OSDR Arabidopsis studies (78 flight, "
            "78 ground control; Table 1) and built an elastic net (alpha = 0.5) biomarker panel "
            "using leave-one-study-out cross-validation (LOOS-CV) with 10 repeats per fold "
            "(60 total iterations). The panel achieved a mean cross-study AUC of 0.734 "
            "(95% CI: 0.431–1.000), with a mean sensitivity of 0.845 and a mean specificity of "
            "0.670 (Figure 1a, Table 1)."
        ),
        None,
    ),
    (
        "Generalization was strongest for ISS seedling studies:",
        (
            "Generalization was strongest for ISS seedling studies: OSD-38 (AUC = 0.933), OSD-678 "
            "(0.887), and OSD-37 (0.875). Weaker performance on OSD-120 (0.544, root tissue) and "
            "OSD-624 (0.528, suborbital flight) indicates that the spaceflight signature is both "
            "tissue- and condition-specific. Stability selection at ≥50% frequency yielded 85 stable "
            "features (Figure 1b)."
        ),
        None,
    ),
    (
        "Four genes were selected at 100% frequency",
        (
            "Four genes were selected at 100% frequency (Figure 1c): AT4G10250 (ATHSP22.0, "
            "coefficient +0.723, flight-enriched), AT3G07365 (natural antisense transcript [NAT], "
            "+0.828, strongest positive predictor), AT2G14247 (chloroplast protein, −0.364, "
            "ground-enriched), and AT4G01390 (TRAF-like/MATH domain protein, −0.819, strongest "
            "negative predictor). The biological functions of these biomarkers are detailed below "
            "and summarized in Figure 6c."
        ),
        None,
    ),
    (
        "We applied scPlantLLM in zero-shot mode",
        (
            "We applied scPlantLLM in zero-shot mode to 9,998 cells subsampled (stratified by cell "
            "type) from the seed-to-seed atlas (41,314 cells, 22,375 genes; 5 cell types: Epidermal, "
            "Mesophyll, Stele, Meristematic, and Guard). Inference used seq_length = 500 (reduced "
            "from the 1,500 training configuration to ensure CPU feasibility) across the "
            "highest-expressed genes per cell, yielding 512-dimensional cell embeddings and 44-class "
            "cell-type predictions."
        ),
        None,
    ),
    (
        "Zero-shot prediction accuracy was 28.1%",
        (
            "Zero-shot prediction accuracy was 28.1% under loose mapping (allowing tissue-level "
            "correspondences between the atlas and model cell-type vocabularies), with Mesophyll "
            "cells best predicted (52.4%) and Meristematic and Guard cells poorly predicted (0%). "
            "This low accuracy reflects domain shift: scPlantLLM was trained predominantly on root "
            "tissue, whereas the atlas is seedling-derived. Leiden clustering on the scPlantLLM "
            "embeddings (resolution 0.5) produced 6 clusters with low agreement with atlas cell types "
            "(ARI = 0.033, NMI = 0.040) and moderate agreement with zero-shot predictions "
            "(ARI = 0.154, NMI = 0.198; Figure 2)."
        ),
        None,
    ),
    (
        "PlantCellChat reveals",
        "PlantCellChat reveals Ca²⁺-dominated cell–cell communication",
        None,
    ),
    (
        "We inferred cell-cell communication using PlantCellChat",
        (
            "We inferred cell–cell communication using PlantCellChat with the Arabidopsis "
            "ligand–receptor database (5,725 interactions, 1,027 genes, 15 signaling pathways), "
            "of which 940 genes were present in the atlas. To accommodate the atlas’s terrestrial "
            "growth conditions, we applied relaxed overexpression thresholds (pc = 0, fc = 0, p = 0.1), "
            "identifying 1,628 overexpressed genes and 3,140 ligand–receptor interactions."
        ),
        None,
    ),
    (
        "Ca2+ signaling was the dominant pathway",
        (
            "Ca²⁺ signaling was the dominant annotated pathway with a total communication strength "
            "of 249.5, which is 4.6-fold higher than that of the next-strongest pathway "
            "(brassinosteroid [BR], 54.5; Figure 3b). Across all cell types, the overall "
            "communication matrix identified Meristematic cells as the strongest communicators "
            "(total outgoing strength 437.4, self-communication 92.0), followed by Guard (419.3), "
            "Stele (418.9), Mesophyll (399.8), and Epidermal (399.3) cells (Figure 3a). At the "
            "individual interaction level, the top 21 ligand–receptor pairs belonged to unannotated "
            "general receptor-like kinase (RLK) signaling (led by AT3G47470_AT4G02510, strength "
            "21.56), while the highest-ranking pathway-annotated pairs were Ca²⁺ (AT1G20620_AT5G19450 "
            "at rank 22, strength 10.02; AT1G59870_AT3G51920 at rank 33, strength 7.11), followed "
            "by chitin (rank 36, strength 6.49), BR (rank 37, strength 6.34), and nitrate (NO₃⁻; "
            "rank 41, strength 6.08) interactions (Figure 3c)."
        ),
        None,
    ),
    (
        "The Ca2+ signaling network (Figure 5)",
        (
            "In the Ca²⁺ signaling network (Figure 5), Ca²⁺ acts as the signaling ligand engaging "
            "CBL calcium sensors—including CBL1 (AT4G17615), CBL2 (AT5G55990), and CBL9 "
            "(AT5G47100)—which activate CIPK kinases such as CIPK23 (AT1G30270) to phosphorylate "
            "downstream targets including the K⁺ channel AKT1 (AT2G26650) and the nitrate "
            "transporter NRT2.1 (AT1G08090). This CBL–CIPK cascade is a well-established Ca²⁺ "
            "signaling module in plant stress responses."
        ),
        None,
    ),
    (
        "We mapped the LASSO biomarker gene expression",
        (
            "We mapped LASSO biomarker gene expression and CCC communication strength onto "
            "Arabidopsis leaf and root tip cross-sections using ggPlantmap (Figure 4, displaying "
            "both TAIR locus IDs and gene names). Cell types were mapped to anatomical regions "
            "as follows: Epidermal to epidermis, Mesophyll to palisade and spongy parenchyma (leaf) "
            "or cortex (root), Stele to vascular tissues, and Meristematic to columella (root)."
        ),
        None,
    ),
    (
        "The LASSO panel weighted score",
        (
            "The LASSO panel weighted score (the sum of coefficient × expression across the 74 "
            "atlas-present panel genes) was negative for all cell types, indicating that the "
            "terrestrial-grown atlas exhibits a ground-like expression pattern (Figure 6a). Stele "
            "cells showed the most negative score (−0.079), suggesting the strongest ground-like "
            "signature in vascular tissues."
        ),
        None,
    ),
    (
        "AT4G10250 (HSP22.0/ATHSP22.0)",
        (
            "AT4G10250 (HSP22.0/ATHSP22.0) encodes a 22 kDa small heat shock protein "
            "(HSP20/alpha-crystallin family) localized to the endomembrane system and chloroplast. "
            "It functions as a molecular chaperone that prevents protein aggregation under heat and "
            "oxidative stress and modulates ABA–auxin signaling crosstalk via the ABI1–HSP22 "
            "interaction. As a flight-enriched positive predictor, ATHSP22.0 likely reflects "
            "proteostatic stress under microgravity."
        ),
        None,
    ),
    (
        "AT3G07365 is a natural antisense transcript",
        (
            "AT3G07365 is a natural antisense transcript (NAT)—a non-coding RNA overlapping "
            "AT3G46230 on the opposite DNA strand. In Arabidopsis, cis-NATs regulate sense-strand "
            "gene expression through transcriptional interference or siRNA-mediated silencing [9] and "
            "have been linked to heat-stress proteomics responses [10]. As the strongest positive "
            "predictor (coefficient +0.828), AT3G07365 highlights that non-coding regulatory RNA "
            "dynamics, rather than protein-coding changes alone, are a central feature of the "
            "spaceflight transcriptional signature."
        ),
        None,
    ),
    (
        "AT2G14247 encodes a small",
        (
            "AT2G14247 encodes a small (78 aa, 8.65 kDa) chloroplast-localized expressed protein of "
            "unknown function. As a ground-enriched negative predictor, its suppression in flight "
            "samples is consistent with established spaceflight effects on photosynthesis and "
            "chloroplast function."
        ),
        None,
    ),
    (
        "AT4G01390 encodes a TRAF-like/MATH",
        (
            "AT4G01390 encodes a TRAF-like/MATH domain-containing protein involved in abiotic stress "
            "signaling [11]; it is listed in the Leaf Senescence Database and is H₂O₂-responsive. "
            "As the strongest negative predictor (coefficient −0.819), its enrichment in ground "
            "controls suggests that baseline oxidative stress signaling pathways are attenuated "
            "under microgravity."
        ),
        None,
    ),
    (
        "To characterize the biological processes",
        (
            "To characterize the biological processes represented by the 85-gene LASSO panel, we "
            "performed GO and KEGG pathway enrichment using g:Profiler against a custom background "
            "of the 2,000 variable features from which LASSO selected (Benjamini–Hochberg FDR < 0.05). "
            "A directed analysis splitting the panel into 41 flight-upregulated genes (positive "
            "coefficients) and 44 ground-upregulated genes (negative coefficients) revealed a clear "
            "biological partition. Flight-upregulated genes were significantly enriched for 11 terms, "
            "including response to heat (p = 4.3 × 10⁻³, 6 genes), cellular response to hypoxia and "
            "oxygen levels (p = 0.032, 4 genes each), protein modification by small protein "
            "conjugation (p = 0.032), and KEGG protein processing in the endoplasmic reticulum "
            "(p = 1.3 × 10⁻¹¹, 9 genes). Ground-upregulated genes were enriched for flavonoid "
            "biosynthetic process (p = 0.041, 4 genes). The combined 85-gene panel showed significant "
            "enrichment for KEGG protein processing in the ER (p = 2.6 × 10⁻⁸) and response to heat "
            "(p = 0.011; Supplementary Figures S1–S2, Supplementary Tables S2–S3). Together, these "
            "results indicate that spaceflight activates stress-response and ER proteostasis "
            "pathways while suppressing secondary metabolism, consistent with the downregulation of "
            "photosynthetic and flavonoid biosynthetic machinery under microgravity."
        ),
        None,
    ),
    (
        "Ca2+/K+ crosstalk circuit connects",
        "Ca²⁺/K⁺ crosstalk circuit connects guard cell signaling to K⁺ uptake",
        None,
    ),
    (
        "Cell–cell communication analysis placed Ca²⁺ signaling",
        (
            "Cell–cell communication analysis placed Ca²⁺ signaling well above K⁺ transport in "
            "total strength (249.5 vs. 24.5, a 10.2-fold difference), with guard cells serving as "
            "the dominant Ca²⁺ source (total outgoing Ca²⁺ strength 57.1, highest of all cell types) "
            "and signaling most strongly to meristematic (12.14), epidermal (11.20), and stele "
            "(11.09) cells; by contrast, epidermal cells were the principal K⁺ source. Within the "
            "PlantCellChat network, the canonical Ca²⁺→K⁺ module was recovered directly: Ca²⁺ engages "
            "the calcium sensor CBL1 (AT4G17615), which links to CIPK23 (AT1G30270), and CIPK23 in "
            "turn connects to the K⁺-uptake channel AKT1 (AT2G26650)—recovering the established "
            "CBL–CIPK23–AKT1 pathway [6–8]. Although the paralogous sensor CBL9 was not "
            "detected in the atlas communication network, CBL1 and CBL9 act as redundant CIPK23 "
            "partners in vivo."
        ),
        None,
    ),
    (
        "To place this module in cellular context",
        (
            "To place this module in cellular context, we expanded the network to include the six "
            "major K⁺ channels (AKT1, AKT2, GORK, KAT1, KAT2, and KC1) and examined per-cell-type "
            "expression across the full seed-to-seed atlas (41,314 cells). The resulting Ca²⁺/K⁺ "
            "network comprised 27 nodes and 56 edges (Figure 7a). Consistent with a guard-cell role "
            "for the kinase step, CIPK23 was most highly expressed in guard cells (mean 0.333, the "
            "highest of any cell type), whereas its downstream target AKT1 peaked in epidermal cells "
            "(0.367), matching AKT1’s established role in epidermal and root K⁺ uptake. By contrast, "
            "the calcium sensors CBL1 and CBL9 were expressed at low levels across all cell types "
            "(≤0.06), indicating that cell-type specificity in this module resides at the kinase "
            "(CIPK23) and channel (AKT1) steps rather than at the sensor step."
        ),
        None,
    ),
    (
        "Gene–gene co-expression across the 25 circuit genes",
        (
            "Gene–gene co-expression across the 25 circuit genes was weak globally (|r| < 0.1 for "
            "nearly all pairs). Within guard cells (n = 89), a small module of co-varying genes was "
            "apparent—notably CBL1–ANNAT1 (r = 0.90), CBL1–CDPK4 (r = 0.63), and CDPK4–ANNAT1 "
            "(r = 0.56)—but with only 89 guard cells, these correlation estimates carry high variance "
            "and are presented as exploratory rather than primary evidence. We therefore base the "
            "circuit primarily on the cell–cell communication network and on the guard-enriched "
            "expression of CIPK23. Spatial mapping of the circuit genes onto seedling, root, and "
            "leaf anatomy (Figures 7c and 8; Supplementary Figure S3) shows CIPK23 broadly "
            "expressed with guard/epidermal enrichment and AKT1 concentrated in epidermal tissue, "
            "providing tissue-level context for the cascade."
        ),
        None,
    ),
    (
        "First, the dominance of Ca2+ signaling",
        (
            "First, the dominance of Ca²⁺ signaling in the CCC network (4.6-fold higher than any "
            "other annotated pathway) is consistent with the role of Ca²⁺ as a primary second "
            "messenger in plant gravity perception. Microgravity alters cytosolic Ca²⁺ oscillations "
            "and gradients that guide directional growth, and the CBL–CIPK cascade identified in our "
            "analysis is a well-established downstream effector of Ca²⁺ signaling in plant stress "
            "responses. Moreover, the convergence of two LASSO biomarker genes (ATHSP22.0 and "
            "TRAF-like) with Ca²⁺-linked stress signaling supports the biological coherence of the "
            "biomarker panel."
        ),
        None,
    ),
    (
        "Second, the identification of a natural antisense transcript",
        (
            "Second, the identification of a natural antisense transcript (AT3G07365) as the "
            "strongest positive predictor of spaceflight underscores the importance of non-coding "
            "RNA regulation in spaceflight responses. Because NATs can rapidly modulate gene "
            "expression without requiring translation, they may be particularly advantageous for "
            "rapid environmental adaptation. This finding suggests that future spaceflight biomarker "
            "panels should incorporate non-coding RNAs alongside protein-coding genes."
        ),
        None,
    ),
    (
        "Third, the tissue-specificity of the LASSO panel’s",
        (
            "Third, the tissue specificity of the LASSO panel’s generalization (strong for ISS "
            "seedling studies, weak for root tissue and suborbital flight) indicates that the "
            "spaceflight transcriptional signature is not uniform across tissues or flight profiles. "
            "This has practical implications for experimental design, as biomarker panels trained on "
            "seedling data may not transfer directly to root tissues or distinct flight regimes."
        ),
        None,
    ),
    (
        "Several limitations should be noted.",
        (
            "Several limitations should be noted. (1) No external validation cohort currently exists "
            "for Arabidopsis spaceflight transcriptomics; consequently, all LASSO results are "
            "discovery-only and subject to potential optimism bias. (2) scPlantLLM was run with a "
            "reduced sequence length (seq_length = 500 vs. 1,500) to ensure computational feasibility "
            "on CPU, which may have degraded embedding quality. (3) The single-cell atlas was grown "
            "under terrestrial conditions, providing a cell-type reference rather than "
            "spaceflight-conditioned cell states. (4) PlantCellChat thresholds were relaxed from "
            "defaults to accommodate the terrestrial atlas. (5) Guard cells were represented by only "
            "21 cells in the 9,998-cell subsample (89 cells in the full 41,314-cell atlas), "
            "potentially yielding unstable guard-cell CCC estimates."
        ),
        None,
    ),
    (
        "The Ca2+/K+ crosstalk circuit analysis reveals",
        (
            "The Ca²⁺/K⁺ crosstalk circuit analysis reveals a guard-cell-centered signaling module "
            "that may serve as a cell-to-cell conduit for long-distance ion signaling under "
            "spaceflight conditions. The CBL1–CIPK23–AKT1 cascade, a canonical Ca²⁺-regulated K⁺ "
            "uptake pathway [6,7], provides a mechanistic link between the Ca²⁺-dominant CCC "
            "network and K⁺ homeostasis. In addition, the exploratory guard-cell co-expression "
            "module (CBL1–ANNAT1 r = 0.90, CBL1–CDPK4 r = 0.63, and CDPK4–ANNAT1 r = 0.56; n = 89) "
            "suggests that Ca²⁺ decoding and annexin-mediated Ca²⁺ buffering may be co-regulated in "
            "stomatal lineage cells, though larger guard-cell datasets will be needed to confirm "
            "these correlations. Guard cells regulate stomatal aperture, gas exchange, and water "
            "balance—processes that are critical in the closed atmosphere of spacecraft [8]. The "
            "10.2-fold dominance of Ca²⁺ over K⁺ in intercellular communication strength further "
            "supports Ca²⁺ as the primary long-range signal, with K⁺ transport acting as a downstream "
            "effector. This convergence of Ca²⁺ signaling and ER proteostasis (identified in the GO "
            "enrichment of flight-upregulated genes) points to a coordinated stress response in which "
            "Ca²⁺ oscillations trigger both CBL–CIPK-mediated ion transport and heat-shock protein "
            "induction to maintain proteostasis under microgravity-induced stress [5]. However, "
            "the absence of organ labels in the seed-to-seed atlas limits spatial resolution, and "
            "future studies using organ-specific single-cell datasets will be required to validate "
            "this tissue-level circuit architecture."
        ),
        None,
    ),
    (
        "Arabidopsis thaliana RNA-seq studies with flight",
        (
            "Arabidopsis thaliana spaceflight transcriptomic studies comparing flight and ground "
            "control conditions were identified via the NASA OSDR biodata API. Six studies were "
            "selected: OSD-37 (56 samples, seedling, ISS), OSD-120 (24 samples, root, ISS), "
            "OSD-624 (36 samples, leaf and root, suborbital), OSD-678 (24 samples, seedling, ISS), "
            "OSD-38 (6 samples, seedling, ISS), and OSD-321 (10 samples, seedling, ISS) (Table 1). "
            "GeneLab-processed normalized expression matrices were downloaded and harmonized to TAIR "
            "AGI gene identifiers. The final pooled dataset comprised 156 samples (78 flight, "
            "78 ground control) and 32,548 nuclear genes."
        ),
        None,
    ),
    (
        "Features were prepared by log2(x+1)",
        (
            "Features were prepared by log2(x + 1) transformation, selection of the top 2,000 most "
            "variable features, and zero-mean/unit-variance scaling. An elastic net model "
            "(alpha = 0.5) was fitted via cv.glmnet [12] (binomial family, AUC-based lambda "
            "selection). Cross-validation used leave-one-study-out folds (6 folds × 10 repeats = "
            "60 iterations) with 80% class-balanced subsampling within each fold. Stability selection "
            "retained features selected in ≥50% of iterations, and performance was assessed by AUC, "
            "sensitivity, and specificity using pROC."
        ),
        None,
    ),
    (
        "The Arabidopsis seed-to-seed atlas (GEO GSE226097",
        (
            "The Arabidopsis seed-to-seed atlas (GEO GSE226097; Lee et al., 2025 [1]) was downloaded "
            "as a Seurat RDS object and converted to AnnData format. The seedling_6d stage "
            "(41,314 cells × 22,375 genes across 5 cell types) was used after quality-control "
            "filtering (min_genes = 200, min_cells = 3), log-normalization (target_sum = 1e4, log1p "
            "transform), and selection of 3,000 highly variable genes (HVGs). A stratified subsample "
            "of 9,998 cells was used for scPlantLLM inference."
        ),
        None,
    ),
    (
        "The scPlantLLM foundation model (Cao et al., 2025)",
        (
            "The scPlantLLM foundation model (Cao et al., 2025 [2]) was run in zero-shot mode. "
            "Pretrained weights (flash_attn Wqkv format) were converted to standard PyTorch "
            "TransformerEncoderLayer format (in_proj_weight/bias). The model was configured with "
            "n_input_bins = 103, d_model = 512, nhead = 8, nlayers = 6, nlayers_cls = 3, and "
            "n_cls = 44. Inference used seq_length = 500 (reduced from the 1,500 training "
            "configuration for CPU feasibility), batch_size = 16, and 8 CPU threads. Genes were "
            "mapped to the scPlantLLM vocabulary (97.4% atlas gene overlap), and expression values "
            "were discretized using 101 bins with category encoding."
        ),
        None,
    ),
    (
        "A KNN graph (n_neighbors=15)",
        (
            "A k-nearest-neighbor (KNN) graph (n_neighbors = 15) was constructed on the "
            "512-dimensional scPlantLLM embeddings. Leiden clustering [13] was performed across five "
            "resolutions (0.3–1.5), and resolution 0.5 (6 clusters) was selected as optimal. "
            "Agreement with atlas cell types and zero-shot predictions was assessed using the "
            "adjusted Rand index (ARI) and normalized mutual information (NMI). Differentially "
            "expressed genes per cluster were identified via Wilcoxon rank-sum tests "
            "(|log2FC| > 1, adjusted p < 0.05, expression fraction > 0.25)."
        ),
        None,
    ),
    (
        "Cell-cell communication was inferred using PlantCellChat",
        (
            "Cell–cell communication was inferred using PlantCellChat [3] with the Arabidopsis "
            "ligand–receptor database (ath.csv: 5,725 interactions, 1,027 genes, 15 signaling "
            "pathways). Overexpressed genes were identified using relaxed thresholds (thresh.pc = 0, "
            "thresh.fc = 0, thresh.p = 0.1) to accommodate the terrestrial atlas. Communication "
            "strength was calculated with Kh = 0.5, n = 1, and 50 permutations, and signaling "
            "strength was aggregated per pathway and per cell-type pair."
        ),
        None,
    ),
    (
        "Spatial visualization used ggPlantmap",
        (
            "Spatial visualization was performed using ggPlantmap (Jo & Kajala, 2024 [4]) with "
            "pre-loaded Arabidopsis leaf cross-section (ggPm.At.leaf.crosssection) and root tip "
            "cross-section (ggPm.At.roottip.crosssection) maps. Cell types were mapped to "
            "anatomical regions of interest (ROIs), and expression values were merged via "
            "ggPlantmap.merge(). Heatmaps were generated with ggPlantmap.heatmap() using white-to-red "
            "gradients for expression and viridis palettes for communication strength."
        ),
        None,
    ),
    (
        "Ca2+ pathway visualization",
        "Ca²⁺ pathway visualization",
        None,
    ),
    (
        "The Ca2+ signaling network was visualized",
        (
            "The Ca²⁺ signaling network was visualized using the ggpathway workflow (ggraph + igraph "
            "[14]) with edge and node tables derived from PlantCellChat Ca²⁺ ligand–receptor pairs. "
            "Node positions were assigned to reflect the signaling cascade hierarchy, and a "
            "conceptual schematic of the Ca²⁺ signaling cascade under microgravity was constructed "
            "to illustrate the mechanistic model."
        ),
        None,
    ),
    (
        "GO and KEGG pathway enrichment was performed",
        (
            "GO and KEGG pathway enrichment was performed using the g:Profiler web service "
            "(Raudvere et al., 2019 [15]) via the gprofiler2 R package (organism: athaliana) "
            "against a custom background of the 2,000 most variable features from which LASSO "
            "selected the biomarker panel. Benjamini–Hochberg FDR correction was applied with a "
            "significance threshold of padj < 0.05. Three queries were tested: all 85 panel genes, "
            "41 flight-upregulated genes (mean coefficient > 0), and 44 ground-upregulated genes "
            "(mean coefficient < 0), covering GO Biological Process, Molecular Function, Cellular "
            "Component, and KEGG pathways."
        ),
        None,
    ),
    (
        "Ca2+/K+ crosstalk circuit analysis",
        "Ca²⁺/K⁺ crosstalk circuit analysis",
        None,
    ),
    (
        "Gene identifiers were assigned from TAIR AGI loci",
        (
            "Gene identifiers were assigned from TAIR AGI loci and cross-checked against the "
            "PlantCellChat Arabidopsis database (corrected mapping provided in the companion "
            "repository). The Ca²⁺ pathway was expanded to include six K⁺ channels (AKT1/AT2G26650, "
            "AKT2/AT4G22200, GORK/AT5G37500, KAT1/AT5G46240, KAT2/AT4G18290, and KC1/AT4G32650). "
            "Edges were extracted from PlantCellChat ligand–receptor interactions for the Ca²⁺ and "
            "K⁺ pathways; the CBL1–CIPK23–AKT1 relationship was present in the database and is "
            "further supported by the literature [6,7]. The resulting 27-node, 56-edge network was "
            "drawn with ggpathway (ggraph + igraph, graphlayouts::layout_with_stress, seed = 42 [14]), "
            "with nodes colored by functional class and scaled by mean expression. Per-cell-type "
            "mean expression and percentage of expressing cells were computed from the "
            "log-normalized atlas, and gene–gene co-expression was calculated as Pearson correlation "
            "across all cells and within each cell type. Communication strengths for the Ca²⁺ and "
            "K⁺ pathways were aggregated into 5 × 5 source–target matrices. Spatial visualization "
            "used ggPlantmap with cell-type mean expression mapped to organ regions as a proxy "
            "(cotyledon = mesophyll + guard; hypocotyl = epidermal + stele; root = stele + "
            "meristematic)."
        ),
        None,
    ),
    (
        "All statistical tests are described in their respective",
        (
            "All statistical tests are described in their respective Methods subsections. LASSO "
            "cross-validation used 60 iterations (6 studies × 10 repeats), and AUC confidence "
            "intervals were computed across iterations. Differential expression used Wilcoxon "
            "rank-sum tests with Benjamini–Hochberg correction, and PlantCellChat permutation "
            "testing used 50 permutations. No statistical methods were used to predetermine sample "
            "sizes, and results are reported as discovery-only given the absence of independent "
            "validation cohorts. Detailed methods—including the scPlantLLM weight conversion code "
            "(flash_attn Wqkv to PyTorch in_proj format), analysis parameters, and software "
            "versions—are provided in Supplementary Methods."
        ),
        None,
    ),
]


# References reordered in strict ascending order of first citation in the text
REORDERED_REFERENCES = [
    "1. Lee, J., Nobori, T., Illouz-Eliaz, N. et al. A seed-to-seed single-cell atlas of Arabidopsis development. Nat. Plants (2025).",
    "2. Cao, J. et al. scPlantLLM: a foundation model for plant single-cell transcriptomics. Genomics Proteomics Bioinformatics (2025).",
    "3. Zhang, Y. et al. PlantCellChat: inferring and visualizing plant cell-cell communication. GitHub (2023).",
    "4. Jo, L. & Kajala, K. ggPlantmap: an open-source R package for the creation of informative and quantitative ggplot maps derived from plant images. J. Exp. Bot. 75, erae043 (2024).",
    "5. Takahashi, K., Takahashi, H., Furuichi, T., Toyota, M., Furutani-Seiki, M., Kobayashi, T., Watanabe-Takano, H. & Shinohara, M. Gravity sensing in plant and animal cells. npj Microgravity 7, 2 (2021).",
    "6. Li, L., Kim, B.-G., Cheong, Y. H., Pandey, G. K. & Luan, S. A Ca2+ signaling pathway regulates a K+ channel for low-K response in Arabidopsis. Proc. Natl. Acad. Sci. USA 103, 12625-12629 (2006).",
    "7. Xu, J., Li, H.-D., Chen, L.-Q., Wang, Y., Liu, L.-Z., He, L. & Wu, W.-H. A protein kinase, interacting with two calcineurin B-like proteins, regulates K+ transporter AKT1 in Arabidopsis. Cell 125, 1347-1360 (2006).",
    "8. Cheong, Y. H., Pandey, G. K., Grant, J. J., Batistic, O., Li, L., Kim, B.-G., Lee, S.-C., Kudla, J. & Luan, S. Two calcineurin B-like calcium sensors, interacting with protein kinase CIPK23, regulate leaf transpiration and root potassium uptake in Arabidopsis. Plant J. 52, 473-484 (2007).",
    "9. Wang, X.-J. et al. Genome-wide prediction and identification of cis-natural antisense transcripts in Arabidopsis thaliana. Genome Biol. 6, R30 (2005).",
    "10. Babbar, R. et al. Heat-induced oxidation of the nuclei and cytosol. Plant Cell (2021).",
    "11. Kushwaha, H. R. et al. MATH-domain family shows response toward abiotic stress in plants. Front. Plant Sci. 7, 923 (2016).",
    "12. Friedman, J., Hastie, T. & Tibshirani, R. Regularization paths for generalized linear models via coordinate descent. J. Stat. Softw. 33, 1-22 (2010).",
    "13. Traag, V. A., Waltman, L. & van Eck, N. J. From Louvain to Leiden: guaranteeing well-connected communities. Sci. Rep. 9, 5233 (2019).",
    "14. Li, C. ggpathway: a tutorial for pathway visualization using tidyverse, igraph, and ggraph. Zenodo (2024).",
    "15. Raudvere, U. et al. g:Profiler: a web server for functional enrichment analysis and conversions of gene lists (2019 update). Nucleic Acids Research 47, W191–W198 (2019).",
]


FIGURE_LEGENDS = [
    (
        "Figure 1. LASSO biomarker panel for spaceflight prediction.",
        (
            "a) Leave-one-study-out cross-validation AUC for each held-out OSDR study (6 studies, "
            "10 repeats each). Bars show mean AUC, error bars show standard deviation, and dots "
            "represent individual iterations. The dashed line indicates chance (0.5), and the red "
            "line indicates the overall mean (0.734). b) Selection frequency of the top 20 most "
            "stable features across 60 iterations; orange bars denote positive coefficients "
            "(flight-enriched) and blue bars denote negative coefficients (ground-enriched), with "
            "the dashed line marking the 50% stability threshold. c) Coefficient forest plot for the "
            "4 genes selected at 100% frequency. Points show mean coefficients and error bars show "
            "standard deviation: ATHSP22.0 (AT4G10250) and the natural antisense transcript "
            "(AT3G07365) are positive predictors, whereas the chloroplast protein (AT2G14247) and "
            "TRAF-like protein (AT4G01390) are negative predictors."
        ),
    ),
    (
        "Figure 2. scPlantLLM zero-shot embeddings and clustering.",
        (
            "UMAP visualization of 9,998 atlas cells embedded by scPlantLLM (512-dimensional, "
            "seq_length = 500). a) Cells colored by atlas cell-type annotations (Epidermal, "
            "Mesophyll, Stele, Meristematic, and Guard). b) Cells colored by Leiden clusters "
            "(resolution 0.5, 6 clusters). c) Cells colored by scPlantLLM zero-shot cell-type "
            "predictions (top 8 predicted types shown; remaining predictions grouped as Other). "
            "Agreement between Leiden clusters and atlas cell types was ARI = 0.033 (NMI = 0.040), "
            "and agreement between Leiden clusters and zero-shot predictions was ARI = 0.154 "
            "(NMI = 0.198)."
        ),
    ),
    (
        "Figure 3. PlantCellChat cell–cell communication analysis.",
        (
            "a) Communication strength heatmap showing total communication between each source "
            "(rows) and target (columns) cell-type pair, summed across all ligand–receptor "
            "interactions. b) Top 10 annotated signaling pathways ranked by total communication "
            "strength; Ca²⁺ (orange) is the dominant pathway (249.5), 4.6-fold higher than "
            "brassinosteroid (BR, 54.5). c) Top 50 ligand–receptor pairs ranked by total "
            "communication strength in an expanded right-hand panel. Grey bars represent "
            "unannotated general receptor-like kinase (RLK) pairs (ranks 1–21 and 43 of the top "
            "50); orange bars highlight Ca²⁺ pathway pairs (AT1G20620_AT5G19450 at rank 22 and "
            "AT1G59870_AT3G51920 at rank 33); blue bars denote other annotated signaling pathways "
            "(chitin, BR, and NO₃⁻)."
        ),
    ),
    (
        "Figure 4. Spatial expression of LASSO biomarker genes on Arabidopsis anatomy.",
        (
            "ggPlantmap heatmaps showing mean expression of the top 4 LASSO biomarker genes on "
            "Arabidopsis cross-sections. a) Leaf cross-section: Epidermal cells mapped to epidermis "
            "(adaxial/abaxial), Mesophyll to palisade and spongy parenchyma, Stele to vascular "
            "bundle (xylem, phloem, and bundle sheath), and Guard to stomata. b) Root tip "
            "cross-section: Epidermal cells mapped to epidermis, Mesophyll to cortex, Stele to "
            "procambium/xylem/phloem/pericycle, and Meristematic to columella. The white-to-red "
            "gradient indicates expression level. Each panel title displays the TAIR AGI locus ID, "
            "gene name/alias (ATHSP22.0, NAT, Chloroplast protein, and TRAF-like), and LASSO "
            "coefficient. AT3G07365 (NAT, non-coding RNA) is absent from the atlas protein-coding "
            "gene set and is shown in grey (no data)."
        ),
    ),
    (
        "Figure 5. Ca²⁺ signaling pathway: dominant cell–cell communication axis.",
        (
            "a) Data-driven Ca²⁺ signaling network (20 nodes) visualized using the ggpathway "
            "workflow (ggraph + igraph) with a stress-majorization layout "
            "(graphlayouts::layout_with_stress). Nodes represent Ca²⁺ (yellow, ligand), CBL sensors "
            "(blue: CBL1, CBL9, CBL2), CIPK kinases (teal: CIPK23, CIPK1, CIPK9), CaM/CML sensors "
            "(purple: CML38, CML42, CML24, CaM7, CaM3), CDPK kinases (green: CDPK3, CDPK4), "
            "downstream targets (orange: CAX3, NRT2.1, SOS1, ANNAT1), and LASSO biomarker genes "
            "(red: HSP22.0 and TRAF-like). Node size indicates mean expression in the atlas, and edge "
            "width indicates PlantCellChat communication strength. b) Conceptual schematic of the "
            "Ca²⁺ signaling cascade under microgravity, illustrating Ca²⁺ channel activation, "
            "cytosolic Ca²⁺ elevation, and branching to CBL–CIPK, calmodulin, and CDPK pathways "
            "leading to stress-response genes."
        ),
    ),
    (
        "Figure 6. Integration of the LASSO panel, Ca²⁺ signaling, and gene functions.",
        (
            "a) LASSO panel weighted score on the leaf cross-section (score = sum of coefficient × "
            "expression across 74 atlas-present panel genes). Blue indicates a ground-like "
            "(negative) score and orange indicates a flight-like (positive) score; all cell types "
            "show negative scores, consistent with the terrestrial growth conditions of the atlas. "
            "b) Ca²⁺ signaling strength on the leaf cross-section, illustrating cell-type-specific "
            "Ca²⁺ communication. c) Summary table of the top 4 LASSO biomarker gene functions, "
            "including gene ID, gene name/alias, LASSO coefficient, prediction direction "
            "(Flight [+] or Ground [−]), and protein function."
        ),
    ),
    (
        "Figure 7. Ca²⁺/K⁺ crosstalk signaling circuit.",
        (
            "a) Ca²⁺/K⁺ pathway network (27 nodes, 56 edges; ggpathway, stress-majorization layout). "
            "Ca²⁺ edges are shown in blue, K⁺ edges in green, and CBL1–CIPK23–AKT1 crosstalk edges "
            "in orange; node color denotes functional class and node size reflects mean expression "
            "across the atlas. b) Pearson co-expression of the 25 circuit genes across all cells; "
            "global correlations are weak (|r| < 0.1 for nearly all pairs). c) ggPlantmap seedling "
            "maps of circuit genes (AKT1, CBL9, CIPK23, CML24, KC1, and CDPK3) by cell-type proxy; "
            "CIPK23 shows guard/epidermal enrichment and AKT1 shows epidermal enrichment. "
            "d) Cell-to-cell Ca²⁺ (blue) and K⁺ (green) communication strength between the five cell "
            "types; guard cells are the dominant Ca²⁺ source (outgoing 57.1), and epidermal cells "
            "are the primary K⁺ source."
        ),
    ),
    (
        "Figure 8. CBL1–CIPK23–AKT1 cascade: spatial expression and molecular cascade.",
        (
            "a) ggPlantmap leaf cross-sections of (i) CIPK23 expression (guard-highest, mean 0.333) "
            "and (ii) AKT1 expression (epidermal-highest, mean 0.367), showing the kinase and its "
            "channel target across leaf cell types. b) Molecular-cascade Sankey diagram tracing "
            "signal flow from Ca²⁺ through calcium sensors (CBL1, CBL9, CaM3, CML24) and kinases "
            "(CIPK23, CDPK3, CDPK4) to effectors (AKT1, ANNAT1, KC1) and K⁺ uptake; flow widths are "
            "proportional to guard-cell expression, and column headers indicate cascade stages "
            "(Signal, Sensors, Kinases, Channels, Output)."
        ),
    ),
]


SUPP_FIG_LEGENDS = [
    (
        "Supplementary Figure S1. GO enrichment dotplot.",
        (
            "Dot plot showing significant GO and KEGG terms enriched in the 85-gene LASSO panel, "
            "the 41 flight-upregulated genes, and the 44 ground-upregulated genes. Dot size "
            "represents gene count, and color represents −log10(p-value). Background: 2,000 variable "
            "features; multiple-testing correction: BH-FDR (padj < 0.05)."
        ),
    ),
    (
        "Supplementary Figure S2. GO enrichment directed bar plot.",
        (
            "Bar plot showing −log10(p-value) for significant terms separated by direction "
            "(flight-upregulated vs. ground-upregulated). Flight-upregulated genes are enriched for "
            "heat response, hypoxia, and ER protein processing, whereas ground-upregulated genes "
            "are enriched for flavonoid biosynthesis."
        ),
    ),
    (
        "Supplementary Figure S3. Spatial expression of Ca²⁺/K⁺ circuit genes across Arabidopsis anatomy.",
        (
            "Three ggPlantmap figures showing Ca²⁺/K⁺ circuit gene expression and CCC signaling "
            "strength across Arabidopsis anatomical contexts. a) Seed developmental series "
            "(ggPm.At.seed.devseries): expression of CBL9 (blue), CIPK23 (green), and AKT1 (orange) "
            "across five developmental stages (Preglobular, Globular, Heart, Linearcotyledon, and "
            "Maturegreen). Cell-type proxy mapping: Embryo Proper → Meristematic; "
            "Micropylar/Peripheral Endosperm → Stele; Chalazal Endosperm → Mesophyll; "
            "Distal/Chalazal Seed Coat → Epidermal. b) Root mature cross-section "
            "(ggPm.At.rootmatur.crosssection, 8 ROIs): four sub-maps showing (i) Ca²⁺ CCC outgoing "
            "strength (blue; Meristematic/Procambium highest), (ii) K⁺ CCC outgoing strength "
            "(green; Epidermal/Atrichoblast highest), (iii) AKT1 expression (orange; Epidermal "
            "highest), and (iv) CBL9 expression (pink; Epidermal highest). Cell-type proxy: "
            "Atrichoblast/Trichoblast → Epidermal; Cortex/Endodermis → Mesophyll; "
            "Pericycle/Phloem/Xylem → Stele; Procambium → Meristematic. c) Young seedling "
            "(ggPm.At.seedling.saltdrought, all 12 ROIs including control, NaCl, and Sorbitol "
            "treatments): four sub-maps showing (i) Ca²⁺ CCC outgoing strength (blue; Cotyledon "
            "highest via guard + mesophyll proxy), (ii) K⁺ CCC outgoing strength (green; Hypocotyl "
            "highest via epidermal + stele proxy), (iii) AKT1 expression (orange; Hypocotyl "
            "highest), and (iv) CBL9 expression (pink; Hypocotyl highest). Organ proxy: Cotyledon "
            "→ Mesophyll + Guard average; Hypocotyl → Epidermal + Stele average; Root → Stele + "
            "Meristematic average; Hook → all cell types average. Proxy mapping is used because the "
            "scRNA-seq atlas does not include seed- or root-specific organ labels; values represent "
            "approximations from the whole-seedling atlas."
        ),
    ),
    (
        "Supplementary Figure S4. Ca²⁺/K⁺ co-expression heatmap.",
        (
            "25-gene Pearson correlation matrix across all 41,314 atlas cells. Global pairwise "
            "correlations are weak (|r| < 0.1 for nearly all gene pairs), whereas exploratory "
            "within-cell-type analysis in guard cells (n = 89) reveals co-variation among "
            "CBL1–ANNAT1 (r = 0.90), CBL1–CDPK4 (r = 0.63), and CDPK4–ANNAT1 (r = 0.56)."
        ),
    ),
    (
        "Supplementary Figure S5. Ca²⁺/K⁺ gene expression per cell type.",
        (
            "Heatmaps showing mean expression (left) and percentage of expressing cells (right) for "
            "25 Ca²⁺/K⁺ circuit genes across 5 cell types. KC1 shows the highest expression "
            "breadth (24.7% expressing), whereas GORK shows the lowest (0.9%)."
        ),
    ),
    (
        "Supplementary Figure S6. Cell-to-cell Ca²⁺/K⁺ communication circuit.",
        (
            "Circular network diagram showing Ca²⁺ (blue) and K⁺ (green) signaling strength between "
            "5 cell types, with edge width proportional to communication strength. Guard cells are "
            "the dominant Ca²⁺ source (total outgoing strength 57.1), and epidermal cells are the "
            "primary K⁺ source."
        ),
    ),
    (
        "Supplementary Figure S7. Organ marker diagnostic.",
        (
            "Expression of 15 tissue-specific markers across 5 cell types. Root markers (SCR, PLT1, "
            "WOL) are near-absent (<3%), photosynthetic markers (RBCS, FSD1) are ubiquitous "
            "(93–98%), and seed markers (LEC2, 2S3) are near zero, indicating that marker-based "
            "organ inference is unreliable in this whole-seedling atlas."
        ),
    ),
    (
        "Supplementary Figure S8. Expanded Ca²⁺/K⁺ pathway network.",
        (
            "Full 27-node, 56-edge Ca²⁺/K⁺ pathway network visualized with ggpathway "
            "(stress-majorization layout). Ca²⁺ edges are shown in blue, K⁺ edges in green, and "
            "crosstalk edges in orange. Node classes comprise CBL sensors, CIPK kinases, CaM/CML "
            "sensors, CDPKs, K⁺ channels, Ca²⁺ targets, and LASSO biomarker genes."
        ),
    ),
]


SUPP_TABLE_LEGENDS = [
    (
        "Supplementary Table S1. LASSO biomarker panel.",
        "85 stable LASSO features (selection frequency ≥50%) with mean coefficient, standard deviation, and stability status.",
    ),
    (
        "Supplementary Table S2. GO enrichment results (all terms).",
        "Complete g:Profiler output for all 3 queries (85 genes, 41 flight-upregulated, 44 ground-upregulated), including all tested terms, p-values, and gene lists.",
    ),
    (
        "Supplementary Table S3. GO enrichment significant terms.",
        "14 significant terms (BH-FDR padj < 0.05) across all 3 queries with −log10(p) and gene lists.",
    ),
    (
        "Supplementary Table S4. Ca²⁺/K⁺ CCC circuit.",
        "25 cell-pair communication strengths for Ca²⁺ and K⁺ pathways, with organ proxies and dominance flags.",
    ),
    (
        "Supplementary Table S5. Ca²⁺/K⁺ signaling circuit summary.",
        "Circuit-level summary listing source/target cell types, dominant signal, Ca²⁺ and K⁺ strengths, Ca²⁺/K⁺ ratio, top source/target genes, and strongest co-expression pair.",
    ),
    (
        "Supplementary Table S6. Ca²⁺/K⁺ circuit node expression.",
        "23-gene expression table reporting mean expression and percentage of expressing cells across 5 cell types, along with top co-expression partners and correlation coefficients.",
    ),
    (
        "Supplementary Table S7. Ca²⁺/K⁺ co-expression matrix.",
        "25 × 25 Pearson correlation matrix for Ca²⁺/K⁺ circuit genes computed across all atlas cells.",
    ),
    (
        "Supplementary Table S8. Organ marker expression.",
        "15 tissue-specific markers evaluated across 5 cell types with mean expression and percentage of expressing cells.",
    ),
]


def apply_common_edits(doc, has_figures: bool):
    # 1. Body text updates
    for prefix, new_text, bold in TEXT_UPDATES:
        _, p = find_para(doc, prefix)
        set_para_text(p, new_text, bold=bold)

    # 2. Update References [1]-[15] in strict ascending citation order
    ref_hdr_idx, _ = find_para(doc, "References")
    for offset, ref_text in enumerate(REORDERED_REFERENCES, start=1):
        set_para_text(doc.paragraphs[ref_hdr_idx + offset], ref_text, bold=False)

    # 3. Polish Data Availability
    _, da_p = find_para(doc, "OSDR data are available")
    set_para_text(
        da_p,
        (
            "OSDR data are available from the NASA Open Science Data Repository "
            "(visualization.osdr.nasa.gov/biodata/api/). The seed-to-seed atlas is available from "
            "GEO (accession GSE226097). scPlantLLM is available from GitHub "
            "(github.com/compbioNJU/scPlantLLM), PlantCellChat from GitHub "
            "(github.com/mrliuw/PlantCellChat), and ggPlantmap from GitHub "
            "(github.com/leonardojo/ggPlantmap). All analysis code, generated figures, data tables, "
            "and supplementary materials are available in the companion repository "
            "(github.com/dr-richard-barker/arabidopsis-spaceflight-omics) and will be archived on "
            "Zenodo with a DOI upon acceptance. Detailed methods, including the scPlantLLM weight "
            "conversion code, all analysis parameters, and software versions, are provided in "
            "Supplementary Methods."
        ),
    )

    # 4. Insert Table 1 right after the last Reference (15.)
    ref15_idx, ref15_para = find_para(doc, "15. Raudvere")
    insert_table1_after(doc, ref15_para)

    # Re-locate anchors after inserting Table 1
    ref15_idx, ref15_para = find_para(doc, "15. Raudvere")
    fig_legends_hdr_idx, _ = find_para(doc, "Figure Legends", start=ref15_idx)
    supp_fig_hdr_idx, _ = find_para(doc, "Supplementary Figure Legends", start=fig_legends_hdr_idx)

    if has_figures:
        # Update inline Figures 1-8, replace Figures 3, 4, and 6 PNGs,
        # and remove the redundant repeated Figure Legends block.
        for fig_num, (title, legend) in enumerate(FIGURE_LEGENDS, start=1):
            t_idx, t_para = find_para(doc, f"Figure {fig_num}.", start=ref15_idx)
            assert t_idx < fig_legends_hdr_idx, f"Expected inline Figure {fig_num} before Figure Legends"
            set_para_text(t_para, title, bold=True)

            img_para = doc.paragraphs[t_idx + 1]
            cap_para = doc.paragraphs[t_idx + 2]
            if fig_num == 3:
                replace_picture_in_para(img_para, FIG3_PNG, width_inches=6.0)
            elif fig_num == 4:
                replace_picture_in_para(img_para, FIG4_PNG, width_inches=4.8)
            elif fig_num == 6:
                replace_picture_in_para(img_para, FIG6_PNG, width_inches=6.0)
            set_para_text(cap_para, legend, bold=False)

        for p in list(doc.paragraphs[fig_legends_hdr_idx:supp_fig_hdr_idx]):
            remove_paragraph(p)
    else:
        # Text-only manuscript: remove the redundant empty-image placeholder block
        # between Table 1 spacer and Figure Legends heading, keeping one clean Figure Legends section.
        fig1_inline_idx, _ = find_para(doc, "Figure 1.", start=ref15_idx)
        for p in list(doc.paragraphs[fig1_inline_idx:fig_legends_hdr_idx]):
            remove_paragraph(p)

        fig_legends_hdr_idx, _ = find_para(doc, "Figure Legends")
        for fig_num, (title, legend) in enumerate(FIGURE_LEGENDS, start=1):
            t_idx, t_para = find_para(doc, f"Figure {fig_num}.", start=fig_legends_hdr_idx)
            set_para_text(t_para, title, bold=True)
            set_para_text(doc.paragraphs[t_idx + 1], legend, bold=False)

    # 5. Update Supplementary Figure Legends
    supp_fig_hdr_idx, _ = find_para(doc, "Supplementary Figure Legends")
    for s_num, (title, legend) in enumerate(SUPP_FIG_LEGENDS, start=1):
        s_idx, s_para = find_para(doc, f"Supplementary Figure S{s_num}.", start=supp_fig_hdr_idx)
        set_para_text(s_para, title, bold=True)
        set_para_text(doc.paragraphs[s_idx + 1], legend, bold=False)

    # 6. Update Supplementary Table Legends
    supp_tbl_hdr_idx, _ = find_para(doc, "Supplementary Table Legends")
    for t_num, (title, legend) in enumerate(SUPP_TABLE_LEGENDS, start=1):
        t_idx, t_para = find_para(doc, f"Supplementary Table S{t_num}.", start=supp_tbl_hdr_idx)
        set_para_text(t_para, title, bold=True)
        set_para_text(doc.paragraphs[t_idx + 1], legend, bold=False)


def main():
    print("Polishing manuscript.docx ...")
    doc_only = Document(MANUSCRIPT_ONLY)
    apply_common_edits(doc_only, has_figures=False)
    doc_only.save(MANUSCRIPT_ONLY)

    print("Polishing manuscript_with_figures.docx ...")
    doc_figs = Document(MANUSCRIPT_FIGS)
    apply_common_edits(doc_figs, has_figures=True)
    doc_figs.save(MANUSCRIPT_FIGS)

    print("Syncing manuscript_with_figures_ACTIVE_DRAFT.docx ...")
    shutil.copy2(MANUSCRIPT_FIGS, MANUSCRIPT_DRAFT)

    abs_idx, abs_p = find_para(doc_only, "Spaceflight imposes")
    abs_words = len(abs_p.text.split())
    total_words = sum(len(p.text.split()) for p in doc_only.paragraphs if p.text.strip())
    print(f"Abstract word count: {abs_words} (limit <=150)")
    print(f"manuscript.docx total words: {total_words}, paragraphs: {len(doc_only.paragraphs)}, tables: {len(doc_only.tables)}")
    print(f"manuscript_with_figures.docx shapes: {len(doc_figs.inline_shapes)}, tables: {len(doc_figs.tables)}")


if __name__ == "__main__":
    main()
