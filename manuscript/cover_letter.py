"""
Step 4 (continued): Generate cover letter for npj Microgravity submission.
"""
# --- portable paths (de-sandboxed; replaces /mnt/results and /workspace) ---
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
REPO_ROOT = _os.path.abspath(_os.path.join(_HERE, '..'))
RESULTS = _os.environ.get("ASO_ROOT", REPO_ROOT)          # holds tables/ and figures/
ATLAS   = _os.environ.get("ASO_ATLAS", _os.path.join(REPO_ROOT, "atlas"))  # large intermediates (not shipped)
WORK    = _os.environ.get("ASO_WORK", _os.path.join(REPO_ROOT, "work"))    # scratch outputs
_os.makedirs(WORK, exist_ok=True)
# --- end portable paths ---

from docx import Document
from docx.shared import Pt, Inches

doc = Document()

# Set margins
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# Set default font
style = doc.styles['Normal']
style.font.name = 'Liberation Sans'
style.font.size = Pt(11)

doc.add_paragraph('November 20, 2026')
doc.add_paragraph('')
doc.add_paragraph('Editorial Team')
doc.add_paragraph('npj Microgravity')
doc.add_paragraph('Nature Portfolio')
doc.add_paragraph('')
doc.add_paragraph('Dear Editor,')
doc.add_paragraph('')
p = doc.add_paragraph(
    "We submit our manuscript entitled \"LASSO biomarker panel and single-cell atlas "
    "integration reveal Ca²⁺-dominated cell–cell communication in the Arabidopsis "
    "spaceflight response\" for consideration as a Research Article in npj Microgravity."
)
p = doc.add_paragraph(
    "This study integrates bulk spaceflight transcriptomics from the NASA Open Science "
    "Data Repository (156 samples across 6 studies) with single-cell analysis of the "
    "Arabidopsis seed-to-seed atlas (41,314 cells) to connect biomarker-level findings "
    "with cell-type-resolved signaling architecture. Three findings are particularly "
    "significant for the npj Microgravity readership:"
)
p = doc.add_paragraph(
    "1. A regularized LASSO/elastic-net biomarker panel (α = 0.5; mean cross-study AUC = 0.734, "
    "85 stable genes) that generalizes across ISS seedling studies, with GO enrichment revealing "
    "a biological split: flight-upregulated genes are enriched for stress and ER-proteostasis "
    "pathways, whereas ground-upregulated genes are enriched for flavonoid metabolism."
)
p = doc.add_paragraph(
    "2. Ca²⁺ is the dominant cell–cell communication pathway (10.2-fold higher than K⁺), "
    "consistent with its role as a primary gravity-perception second messenger, with guard "
    "cells acting as the dominant Ca²⁺ signaling source."
)
p = doc.add_paragraph(
    "3. A Ca²⁺/K⁺ crosstalk circuit—the CBL1–CIPK23–AKT1 cascade—that mechanistically "
    "connects Ca²⁺ sensing to K⁺ uptake, with CIPK23 most highly expressed in guard cells "
    "and AKT1 in epidermal cells. This circuit may serve as a cell-to-cell conduit for "
    "long-distance ion signaling under spaceflight conditions, with implications for "
    "stomatal regulation and turgor pressure in closed spacecraft atmospheres."
)
p = doc.add_paragraph(
    "All analysis code, data tables, and figures (7 main figures, Table 1, and supplementary "
    "materials) are openly available in a companion GitHub repository "
    "(https://github.com/dr-richard-barker/arabidopsis-spaceflight-omics-cellChat_Ca_signaling) "
    "with full reproducibility documentation and will be archived on Zenodo with a DOI upon "
    "acceptance. The manuscript has not been published elsewhere and is not under "
    "consideration by another journal."
)
p = doc.add_paragraph(
    "We believe this work is well suited for npj Microgravity as it advances "
    "understanding of the molecular signaling architecture underlying plant responses "
    "to the spaceflight environment, with direct relevance to space agriculture and "
    "bioregenerative life support systems."
)
doc.add_paragraph('')
doc.add_paragraph('Sincerely,')
doc.add_paragraph('')
doc.add_paragraph('Richard Barker')
doc.add_paragraph('GeneLab Plant Analysis Working Group, NASA Open Science Data Repository')
doc.add_paragraph('ORCID: https://orcid.org/0000-0002-8368-2825')
doc.add_paragraph('Corresponding author: dr.richard.barker@gmail.com')

out_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'cover_letter.docx')
doc.save(out_path)
print("Cover letter saved to " + out_path)
