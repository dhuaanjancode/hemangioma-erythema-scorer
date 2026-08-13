# Semi-Automated Erythema Quantification Tool for Infantile Haemangioma

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.1007%2Fs00383--XXXX-orange.svg)](https://doi.org/10.5281/zenodo.21912543)

A Python-based semi-automated tool for objective erythema quantification from serial
clinical photographs of infantile haemangioma (IH). Developed and validated at the
Department of Paediatric Surgery, All India Institute of Medical Sciences (AIIMS),
New Delhi, India.

---

## Overview

Monitoring the response of infantile haemangioma to propranolol treatment relies
predominantly on subjective clinical assessment. This tool computes the **erythema
index (EI)** and related colorimetric metrics from manually selected regions of
interest (ROI) in serial clinical photographs, providing an objective, reproducible,
and low-cost adjunct to clinical assessment.

The tool was evaluated in a prospective photographic registry of 49 infants receiving
propranolol, achieving an intra-rater ICC(A,1) of 0.990 (95% CI 0.97–1.00) on
re-rating of 251 photographs.

---

## Citation

If you use this tool in your research, please cite the associated publication:

> Kumar B, Jain V, Goel P, Yadav DK, Agarwala S, Dhua AK.
> **Semi-Automated Erythema Quantification in Infantile Haemangioma Receiving
> Propranolol: A Pilot Feasibility Study.**
> *Pediatric Surgery International.* 2026.
> DOI: [to be updated on publication]

A `CITATION.cff` file is provided in this repository for automated citation
generation by GitHub, Zenodo, and reference managers.

---

## Authors and Developers

| Name | Role | ORCID |
|---|---|---|
| **Anjan Kumar Dhua** | Conceptualisation, tool development, clinical validation, corresponding author | [0000-0003-2050-7872](https://orcid.org/0000-0003-2050-7872) |
| **Vishesh Jain** | Co-developer, data acquisition, clinical validation | [0000-0002-9273-097X](https://orcid.org/0000-0002-9273-097X) |
| **Prabudh Goel** | Co-developer, data acquisition, clinical validation | [0000-0001-6179-1625](https://orcid.org/0000-0001-6179-1625) |
| **Devendra Kumar Yadav** | Co-developer, data acquisition, clinical validation | [0000-0003-3158-3322](https://orcid.org/0000-0003-3158-3322) |

**Department of Paediatric Surgery**
All India Institute of Medical Sciences (AIIMS), New Delhi — 110029, India

---

## Requirements

```
Python 3.8+
opencv-python
numpy
Pillow
tkinter (included with standard Python installations)
```

Install dependencies:

```bash
pip install opencv-python numpy Pillow
```

---

## Usage

```bash
python hemangioma_scorer.py
```

1. Load a clinical photograph using the **Open Image** button
2. Draw a rectangular region of interest (ROI) over the haemangioma
3. Metrics are computed and displayed in real time:
   - Erythema Index: `EI = (R − G) / (R + G + B)`
   - Red ratio: `R / (R + G + B)`
   - Mean RGB channel values
   - Individual Typology Angle (ITA)
   - ROI pixel count
4. Export all metrics to CSV using the **Save** button

---

## Metrics

| Metric | Formula | Description |
|---|---|---|
| Erythema Index (EI) | `(R − G) / (R + G + B)` | Primary measure of relative redness; higher values indicate greater erythema |
| Red ratio | `R / (R + G + B)` | Normalised red channel contribution |
| Mean R, G, B | — | Mean pixel intensities within ROI (0–255) |
| ITA | `arctan((L* − 50) / b*) × (180/π)` | Individual Typology Angle; correlates with skin phototype |
| ROI pixel count | — | Number of pixels within the selected ROI; values < 1,500 px should be interpreted with caution |

---

## Validation

Intra-rater reliability (re-rating of 22 photographs from 5 patients, one-week washout):

| Metric | ICC(A,1) | 95% CI | Bland-Altman bias | LoA |
|---|---|---|---|---|
| Erythema Index | 0.990 | 0.97–1.00 | −0.005 EI units | −0.023 to +0.013 |

Cohort: 49 infants with superficial IH, Fitzpatrick phototype III–IV, AIIMS New Delhi.
Photography: Nikon D750 DSLR, ambient clinical lighting, no colorimetric calibration targets.
Usability: 242/251 photographs (96.4%) were analysable.

---

## Limitations

- EI is a colour-only metric; it does not capture lesion volume, surface area, or depth
- No colorimetric calibration reference patches were used in this validation cohort
- ROIs were manually selected; automated segmentation is under development
- Results are from a single-centre pilot; multicentre prospective validation is planned

---

## Licence

This project is licensed under the MIT Licence — see [LICENSE](LICENSE) for details.
The tool is provided for research purposes. It is not a validated clinical diagnostic
device and should not be used as the sole basis for clinical decision-making.

---

## Acknowledgements

This work was supported by the Department of Paediatric Surgery, AIIMS New Delhi.
Ethical approval: Institutional Ethics Committee, AIIMS New Delhi
(Ref. No.: AIIMSA1384/07.06.2024, RP-40/2024).
