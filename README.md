# Hemangioma Erythema Scoring Tool

A semi-automated desktop tool for objective erythema quantification in serial
clinical photographs of infantile haemangioma (IH) treated with propranolol.

Developed for the study:

> [Author et al.] *Semi-Automated Erythema Quantification for Monitoring
> Propranolol Response in Infantile Haemangioma: A Pilot Feasibility Study.*
> Journal of Pediatric Surgery. [Year]. DOI: [to be added on publication]

---

## What it does

The tool allows a clinician or researcher to:

1. Open a serial clinical photograph of an infantile haemangioma
2. Draw a rectangle over the lesion (click and drag)
3. Get an instant erythema index (EI) score
4. Save results automatically to a CSV file
5. Progress through all photographs for all patients

**Erythema index formula:**

```
EI = (R - G) / (R + G + B)
```

where R, G, B are mean pixel intensities in the red, green, and blue channels
of the selected region of interest (ROI). This formula captures excess
redness over green, normalised for overall brightness, making it more
sensitive to haemangioma erythema than simple red-channel measurement alone
(Takiwaki H, J Med Invest 1998;44:121–126).

---

## Screenshots

![Tool screenshot](docs/screenshot.png)

*The tool showing a baseline photograph with ROI selection and real-time
erythema metrics.*

---

## Requirements

- Python 3.8 or later
- opencv-python
- pillow
- numpy

Install dependencies:

```bash
pip install opencv-python pillow numpy
```

---

## Installation

No installation required. Download `hemangioma_scorer.py` and run it directly.

```bash
git clone https://github.com/[yourusername]/hemangioma-erythema-scorer
cd hemangioma-erythema-scorer
pip install -r requirements.txt
python hemangioma_scorer.py
```

---

## Usage

### Quick start

```bash
python hemangioma_scorer.py
```

A file picker will open — select your `photos/` directory and the tool
will load all patient folders automatically.

### Set photos directory via environment variable

```bash
export IH_PHOTOS_DIR="/path/to/your/photos"
python hemangioma_scorer.py
```

### Expected folder structure

```
photos/
├── 107768186_Hala_Khalil/
│   ├── baseline/
│   │   └── 20240904_new.jpg
│   └── followups/
│       ├── 20250129_followup.jpg
│       └── 20250716_followup.jpg
├── 107026504_Samiya/
│   ├── baseline/
│   └── followups/
└── ...
```

- Patient folders should be named `[UHID]_[PatientName]` or any consistent format
- Each patient folder must contain a `baseline/` and a `followups/` subfolder
- Supported formats: JPEG, PNG, NEF (Nikon raw — automatically converted if a
  `photos_jpg/` sibling directory exists with pre-converted JPG files)

### Output files

Results are saved to a `results/` folder alongside your `photos/` folder:

| File | Contents |
|------|----------|
| `results/scores.csv` | Per-photograph erythema metrics |
| `results/progress.json` | Saves your position between sessions |

### Output columns in scores.csv

| Column | Description |
|--------|-------------|
| `timestamp` | Date and time of scoring |
| `uhid` | Patient identifier |
| `patient_name` | Patient name |
| `filename` | Photograph filename |
| `visit_type` | Baseline or Follow-up |
| `erythema_index` | Primary metric: (R-G)/(R+G+B) |
| `red_ratio` | R/(R+G+B) |
| `mean_r` | Mean red channel value (0–255) |
| `mean_g` | Mean green channel value (0–255) |
| `mean_b` | Mean blue channel value (0–255) |
| `ita` | Individual Typology Angle (skin tone) |
| `pixel_count` | Number of pixels in ROI |
| `roi_width` | ROI width in pixels |
| `roi_height` | ROI height in pixels |
| `roi_x1/y1/x2/y2` | ROI bounding box coordinates |
| `notes` | Free-text notes (e.g. reason for skip) |

---

## ROI placement guidelines

For reproducible measurements, follow these rules when drawing the rectangle:

- Include the **full visible lesion extent**
- Include approximately **2–5 mm of surrounding normal skin** as margin
- **Exclude** scale rulers, gloved hands, clothing, and background
- **Exclude** bright specular reflections if possible
- For multiple photographs of the same lesion, aim for consistent framing

If a photograph has inadequate illumination or the lesion is obscured, use
the **SKIP** button — skipped photos are recorded in the CSV with a note.

---

## NEF (Nikon raw) file support

The tool supports Nikon NEF raw files directly. For faster loading, you can
pre-convert NEF files to JPEG using the included conversion script:

```bash
pip install rawpy imageio
python convert_nef.py --photos-dir /path/to/photos
```

Converted files are saved to a `photos_jpg/` folder and loaded automatically
by the scoring tool.

---

## Citing this tool

If you use this tool in published research, please cite both the paper and
the software repository:

**Paper:**
```
[Author et al.] Semi-Automated Erythema Quantification for Monitoring
Propranolol Response in Infantile Haemangioma: A Pilot Feasibility Study.
Journal of Pediatric Surgery. [Year]. DOI: [to be added]
```

**Software:**
```
[Author name]. hemangioma-erythema-scorer [software]. GitHub; 2026.
Available at: https://github.com/[yourusername]/hemangioma-erythema-scorer
```

---

## Limitations

- This tool performs **semi-automated** scoring: ROI selection is manual
- No colour calibration is applied — photographs should ideally be taken
  under standardised lighting conditions with a reference colour card
- Inter-rater reliability has not been formally assessed in this version
- Designed for JPEG and NEF photographs; other raw formats not tested

See the paper for a full discussion of methodological limitations.

---

## Contributing

Pull requests and issues are welcome. If you use this tool in a study and
want to share your results or suggest improvements, please open an issue.

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Contact

[Your name]  
[Institution]  
[Email address]
