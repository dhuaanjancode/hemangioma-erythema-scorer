"""
Hemangioma Erythema Scoring Tool
=================================
A semi-automated desktop tool for quantifying erythema in serial clinical
photographs of infantile haemangioma (IH) treated with propranolol.

Usage
-----
    python hemangioma_scorer.py

    The tool will ask you to select your photos directory on first run.
    Or set an environment variable to skip the prompt:

        export IH_PHOTOS_DIR="/path/to/your/photos"
        python hemangioma_scorer.py

Folder structure expected
-------------------------
    photos/
    └── [UHID]_[PatientName]/
        ├── baseline/      <- baseline photographs
        └── followups/     <- follow-up photographs

Output
------
    results/scores.csv      -- per-photograph erythema metrics
    results/progress.json   -- saves your position between sessions

    Output files are saved in a results/ folder alongside your photos/ folder.

Requirements
------------
    pip install opencv-python pillow numpy

Citation
--------
    If you use this tool in published research, please cite:
    [Author et al. Title. Journal of Pediatric Surgery. Year. DOI.]
    https://github.com/[yourusername]/hemangioma-erythema-scorer

License
-------
    MIT License -- see LICENSE file.

Author
------
    [Your name], [Institution]
    [Contact email]
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk
import csv
import json
from pathlib import Path
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────
# Set via environment variable, or leave blank to choose interactively.
DEFAULT_PHOTOS_DIR = os.environ.get("IH_PHOTOS_DIR", "")

# ── Colour scheme ──────────────────────────────────────────────────────────────
BG      = "#1a1a2e"
PANEL   = "#16213e"
ACCENT  = "#e94560"
TEXT    = "#eaeaea"
MUTED   = "#8892a4"
SUCCESS = "#4ecca3"
WARNING = "#ffd460"
CARD    = "#0f3460"


# ── Helper functions ───────────────────────────────────────────────────────────

def find_jpg_for_nef(nef_path):
    """
    For NEF (Nikon raw) files, look for a converted JPG in a sibling
    photos_jpg directory. Returns the original path if no JPG is found.
    """
    p = Path(nef_path)
    if p.suffix.lower() != ".nef":
        return p
    # Walk up to find a photos_jpg sibling directory
    candidate = p.parent.parent.parent  # patient_folder level
    jpg_candidate = candidate.parent.parent / "photos_jpg"
    if jpg_candidate.exists():
        try:
            photos_root = candidate.parent
            rel = p.relative_to(photos_root / "photos")
            jpg = photos_root / "photos_jpg" / rel.with_suffix(".jpg")
            if jpg.exists():
                return jpg
        except Exception:
            pass
    return p


def load_patients(photos_dir):
    """Return list of patient dicts from the photos directory."""
    patients = []
    for d in sorted(Path(photos_dir).iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            parts = d.name.split("_", 1)
            patients.append({
                "uhid":   parts[0],
                "name":   parts[1].replace("_", " ") if len(parts) > 1 else d.name,
                "folder": d,
            })
    return patients


def load_patient_photos(patient_folder):
    """Return all photos for a patient, baseline before followups."""
    photos = []
    for subfolder, visit_type in [("baseline", "Baseline"), ("followups", "Follow-up")]:
        sub = patient_folder / subfolder
        if sub.exists():
            for f in sorted(sub.iterdir()):
                if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".nef"]:
                    photos.append({
                        "path":       str(f),
                        "filename":   f.name,
                        "visit_type": visit_type,
                        "stem":       f.stem,
                    })
    return photos


def calculate_erythema(image_bgr, x1, y1, x2, y2):
    """
    Calculate erythema metrics from a selected region of interest (ROI).

    Primary metric -- Erythema Index (EI):

        EI = (R - G) / (R + G + B)

    This formula captures excess redness over green, normalised for overall
    brightness. It is more sensitive than R/(R+G+B) alone because it
    amplifies the chromatic difference between haemangioma tissue (high R,
    low G) and surrounding normal skin, producing a larger measurable
    signal. Reference: Takiwaki H, J Med Invest 1998;44:121-126.

    Returns a dict of metrics, or None if the ROI is invalid.
    """
    roi = image_bgr[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    roi_f = roi.astype(np.float32)
    B, G, R = roi_f[:,:,0], roi_f[:,:,1], roi_f[:,:,2]
    total = R + G + B + 1e-6  # avoid division by zero

    # Individual Typology Angle (skin tone indicator)
    roi_lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, b_lab = roi_lab[:,:,0], roi_lab[:,:,2] - 128
    ita = float(np.mean(np.degrees(np.arctan((L - 50) / (b_lab + 1e-6)))))

    return {
        "erythema_index": round(float(np.mean((R - G) / total)), 4),
        "red_ratio":      round(float(np.mean(R / total)),       4),
        "mean_r":         round(float(np.mean(R)),               1),
        "mean_g":         round(float(np.mean(G)),               1),
        "mean_b":         round(float(np.mean(B)),               1),
        "ita":            round(ita,                             2),
        "pixel_count":    roi.shape[0] * roi.shape[1],
        "roi_width":      x2 - x1,
        "roi_height":     y2 - y1,
    }


def load_progress(results_dir):
    f = Path(results_dir) / "progress.json"
    return json.loads(f.read_text()) if f.exists() else {}


def save_progress(results_dir, progress):
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    (Path(results_dir) / "progress.json").write_text(json.dumps(progress))


def load_existing_scores(results_dir):
    p = Path(results_dir) / "scores.csv"
    if not p.exists():
        return set()
    with open(p) as f:
        return {f"{r['uhid']}_{r['filename']}" for r in csv.DictReader(f)}


def save_score(results_dir, row_data):
    p = Path(results_dir) / "scores.csv"
    fields = [
        "timestamp", "uhid", "patient_name", "filename", "visit_type",
        "erythema_index", "red_ratio", "mean_r", "mean_g", "mean_b",
        "ita", "pixel_count", "roi_width", "roi_height",
        "roi_x1", "roi_y1", "roi_x2", "roi_y2", "notes",
    ]
    write_header = not p.exists()
    with open(p, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        w.writerow({k: row_data.get(k, "") for k in fields})


# ── Main application ───────────────────────────────────────────────────────────

class ScoringApp:
    def __init__(self, root, photos_dir):
        self.root        = root
        self.photos_dir  = Path(photos_dir)
        self.results_dir = self.photos_dir.parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.root.title("Hemangioma Erythema Scoring Tool")
        self.root.configure(bg=BG)
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)

        self.patients          = load_patients(self.photos_dir)
        self.current_patient   = None
        self.current_photos    = []
        self.current_photo_idx = 0
        self.current_image_cv  = None
        self.scale_factor      = 1.0
        self.display_offset_x  = 0
        self.display_offset_y  = 0
        self.scored            = load_existing_scores(self.results_dir)
        self.progress          = load_progress(self.results_dir)
        self.drawing           = False
        self.roi_start         = None
        self.roi_end           = None
        self.roi_rect_id       = None
        self.current_roi       = None
        self.current_metrics   = None

        self._build_ui()
        if self.patients:
            self.patient_var.set(
                f"{self.patients[0]['uhid']} -- {self.patients[0]['name']}"
            )
            self._on_patient_change()

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        header = tk.Frame(self.root, bg=ACCENT, height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="HEMANGIOMA SCORING TOOL",
                 bg=ACCENT, fg="white",
                 font=("Courier", 14, "bold")).pack(side="left", padx=20, pady=12)
        self.progress_label = tk.Label(header, text="", bg=ACCENT, fg="white",
                                        font=("Courier", 11))
        self.progress_label.pack(side="right", padx=20)

        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main, bg=PANEL, width=280)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_left(left)

        centre = tk.Frame(main, bg=BG)
        centre.pack(side="left", fill="both", expand=True)
        self._build_canvas(centre)

        right = tk.Frame(main, bg=PANEL, width=240)
        right.pack(side="right", fill="y", padx=(10, 0))
        right.pack_propagate(False)
        self._build_right(right)

    def _build_left(self, parent):
        tk.Label(parent, text="PATIENT", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(anchor="w", padx=15, pady=(15, 3))
        names = [f"{p['uhid']} -- {p['name']}" for p in self.patients]
        self.patient_var = tk.StringVar()
        combo = ttk.Combobox(parent, textvariable=self.patient_var,
                              values=names, state="readonly", font=("Courier", 10))
        combo.pack(fill="x", padx=15, pady=(0, 10))
        combo.bind("<<ComboboxSelected>>", lambda e: self._on_patient_change())
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=CARD, background=CARD,
                         foreground=TEXT, selectbackground=ACCENT)

        tk.Label(parent, text="VISIT PHOTOS", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(anchor="w", padx=15, pady=(10, 3))
        lf = tk.Frame(parent, bg=PANEL)
        lf.pack(fill="both", expand=True, padx=15)
        sb = tk.Scrollbar(lf, bg=PANEL)
        sb.pack(side="right", fill="y")
        self.photo_listbox = tk.Listbox(lf, bg=CARD, fg=TEXT,
                                         selectbackground=ACCENT,
                                         font=("Courier", 9),
                                         yscrollcommand=sb.set,
                                         borderwidth=0, highlightthickness=0)
        self.photo_listbox.pack(fill="both", expand=True)
        sb.config(command=self.photo_listbox.yview)
        self.photo_listbox.bind("<<ListboxSelect>>", self._on_photo_select)

        tk.Label(parent, text="NOTES", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(anchor="w", padx=15, pady=(10, 3))
        self.notes_text = tk.Text(parent, bg=CARD, fg=TEXT,
                                   font=("Courier", 9), height=4,
                                   borderwidth=0, highlightthickness=0)
        self.notes_text.pack(fill="x", padx=15, pady=(0, 15))

    def _build_canvas(self, parent):
        tk.Label(parent, text="Draw rectangle over lesion  |  Click & Drag",
                 bg=BG, fg=MUTED, font=("Courier", 9)).pack(anchor="w", pady=(0, 5))
        cf = tk.Frame(parent, bg=CARD, bd=2, relief="flat")
        cf.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(cf, bg="#0a0a0a", cursor="crosshair",
                                 highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>",  self._on_mouse_press)
        self.canvas.bind("<B1-Motion>",       self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)

        ctrl = tk.Frame(parent, bg=BG)
        ctrl.pack(fill="x", pady=(8, 0))
        tk.Button(ctrl, text="< PREV", bg=CARD, fg=TEXT, font=("Courier", 10),
                  relief="flat", padx=15, pady=8,
                  command=self._prev_photo).pack(side="left")
        self.photo_info_label = tk.Label(ctrl, text="", bg=BG, fg=MUTED,
                                          font=("Courier", 9))
        self.photo_info_label.pack(side="left", expand=True)
        tk.Button(ctrl, text="NEXT >", bg=CARD, fg=TEXT, font=("Courier", 10),
                  relief="flat", padx=15, pady=8,
                  command=self._next_photo).pack(side="right")

    def _build_right(self, parent):
        tk.Label(parent, text="ERYTHEMA METRICS", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(anchor="w", padx=15, pady=(15, 10))
        self.metric_vars = {}
        for key, label, desc in [
            ("erythema_index", "ERYTHEMA INDEX", "Primary metric"),
            ("red_ratio",      "RED RATIO",       "R/(R+G+B)"),
            ("mean_r",         "MEAN RED",         "Avg R channel"),
            ("mean_g",         "MEAN GREEN",        "Avg G channel"),
            ("mean_b",         "MEAN BLUE",         "Avg B channel"),
            ("ita",            "ITA ANGLE",         "Skin tone"),
            ("pixel_count",    "PIXELS",            "ROI area"),
        ]:
            fr = tk.Frame(parent, bg=CARD, pady=8)
            fr.pack(fill="x", padx=15, pady=3)
            tk.Label(fr, text=label, bg=CARD, fg=MUTED,
                     font=("Courier", 7)).pack(anchor="w", padx=10)
            var = tk.StringVar(value="--")
            self.metric_vars[key] = var
            tk.Label(fr, textvariable=var, bg=CARD, fg=SUCCESS,
                     font=("Courier", 14, "bold")).pack(anchor="w", padx=10)
            tk.Label(fr, text=desc, bg=CARD, fg=MUTED,
                     font=("Courier", 7)).pack(anchor="w", padx=10)

        tk.Label(parent, text="ROI COLOUR", bg=PANEL, fg=MUTED,
                 font=("Courier", 9)).pack(anchor="w", padx=15, pady=(15, 5))
        self.colour_swatch = tk.Canvas(parent, bg="#333", height=50,
                                        highlightthickness=0)
        self.colour_swatch.pack(fill="x", padx=15)

        self.save_btn = tk.Button(parent, text="SAVE & NEXT >",
                                   bg=ACCENT, fg="white",
                                   font=("Courier", 11, "bold"),
                                   relief="flat", pady=12,
                                   command=self._save_and_next, state="disabled")
        self.save_btn.pack(fill="x", padx=15, pady=(20, 5))
        self.skip_btn = tk.Button(parent, text="SKIP (no lesion visible)",
                                   bg=PANEL, fg=MUTED, font=("Courier", 8),
                                   relief="flat", pady=6, command=self._skip_photo)
        self.skip_btn.pack(fill="x", padx=15)
        self.scored_label = tk.Label(parent, text="", bg=PANEL, fg=WARNING,
                                      font=("Courier", 8), wraplength=200)
        self.scored_label.pack(padx=15, pady=10)

    # ── Logic ──────────────────────────────────────────────────────────────────

    def _on_patient_change(self):
        sel  = self.patient_var.get()
        uhid = sel.split(" -- ")[0]
        self.current_patient = next(
            (p for p in self.patients if p["uhid"] == uhid), None
        )
        if not self.current_patient:
            return
        self.current_photos    = load_patient_photos(self.current_patient["folder"])
        self.current_photo_idx = min(
            self.progress.get(uhid, 0), max(0, len(self.current_photos) - 1)
        )
        self._update_photo_list()
        self._load_current_photo()
        self._update_progress_label()

    def _on_photo_select(self, event):
        sel = self.photo_listbox.curselection()
        if sel:
            self.current_photo_idx = sel[0]
            self._load_current_photo()

    def _load_current_photo(self):
        if not self.current_photos:
            return
        photo = self.current_photos[self.current_photo_idx]
        path  = find_jpg_for_nef(photo["path"])
        self.photo_info_label.config(
            text=f"{self.current_photo_idx+1}/{len(self.current_photos)}"
                 f"  |  {photo['visit_type']}  |  {photo['stem']}"
        )
        key = f"{self.current_patient['uhid']}_{photo['filename']}"
        self.scored_label.config(
            text="[✓] Already scored" if key in self.scored else ""
        )
        img = cv2.imread(str(path))
        if img is None:
            self._show_error(f"Could not load: {Path(path).name}")
            return
        self.current_image_cv = img
        self.current_roi      = None
        self.current_metrics  = None
        self._reset_metrics()
        self.save_btn.config(state="disabled")
        self._display_image(img)

    def _display_image(self, img_bgr):
        self.canvas.update_idletasks()
        cw = max(self.canvas.winfo_width(),  700)
        ch = max(self.canvas.winfo_height(), 550)
        h, w  = img_bgr.shape[:2]
        scale = min(cw / w, ch / h, 1.0)
        self.scale_factor     = scale
        nw, nh                = int(w * scale), int(h * scale)
        self.display_offset_x = (cw - nw) // 2
        self.display_offset_y = (ch - nh) // 2
        rgb       = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        resized   = cv2.resize(rgb, (nw, nh))
        self._tk_img = ImageTk.PhotoImage(Image.fromarray(resized))
        self.canvas.delete("all")
        self.canvas.create_image(
            self.display_offset_x, self.display_offset_y,
            anchor="nw", image=self._tk_img
        )
        self.roi_rect_id = None

    def _canvas_to_image(self, cx, cy):
        ix = int((cx - self.display_offset_x) / self.scale_factor)
        iy = int((cy - self.display_offset_y) / self.scale_factor)
        if self.current_image_cv is not None:
            h, w = self.current_image_cv.shape[:2]
            ix, iy = max(0, min(ix, w-1)), max(0, min(iy, h-1))
        return ix, iy

    def _on_mouse_press(self, event):
        self.drawing   = True
        self.roi_start = (event.x, event.y)
        if self.roi_rect_id:
            self.canvas.delete(self.roi_rect_id)

    def _on_mouse_drag(self, event):
        if not self.drawing:
            return
        if self.roi_rect_id:
            self.canvas.delete(self.roi_rect_id)
        self.roi_rect_id = self.canvas.create_rectangle(
            self.roi_start[0], self.roi_start[1], event.x, event.y,
            outline=ACCENT, width=2, dash=(4, 4)
        )

    def _on_mouse_release(self, event):
        if not self.drawing:
            return
        self.drawing = False
        x1, y1 = self._canvas_to_image(*self.roi_start)
        x2, y2 = self._canvas_to_image(event.x, event.y)
        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)
        if (x2-x1) < 10 or (y2-y1) < 10:
            messagebox.showwarning("Too small",
                "Please draw a larger rectangle over the lesion.")
            return
        self.current_roi     = (x1, y1, x2, y2)
        self.current_metrics = calculate_erythema(
            self.current_image_cv, x1, y1, x2, y2
        )
        if self.current_metrics:
            self._update_metrics(self.current_metrics)
            self.save_btn.config(state="normal")

    def _update_metrics(self, m):
        for k, var in self.metric_vars.items():
            var.set(str(m.get(k, "--")))
        r, g, b = int(m["mean_r"]), int(m["mean_g"]), int(m["mean_b"])
        col = f"#{r:02x}{g:02x}{b:02x}"
        self.colour_swatch.config(bg=col)
        self.colour_swatch.delete("all")
        self.colour_swatch.create_text(
            60, 25, text=f"RGB ({r}, {g}, {b})",
            fill="white" if r+g+b < 380 else "black",
            font=("Courier", 9)
        )

    def _reset_metrics(self):
        for var in self.metric_vars.values():
            var.set("--")
        self.colour_swatch.config(bg="#333")
        self.colour_swatch.delete("all")

    def _save_and_next(self):
        if not self.current_metrics or not self.current_roi:
            return
        photo = self.current_photos[self.current_photo_idx]
        x1, y1, x2, y2 = self.current_roi
        row = {
            "timestamp":    datetime.now().isoformat(),
            "uhid":         self.current_patient["uhid"],
            "patient_name": self.current_patient["name"],
            "filename":     photo["filename"],
            "visit_type":   photo["visit_type"],
            "roi_x1": x1, "roi_y1": y1, "roi_x2": x2, "roi_y2": y2,
            "notes":  self.notes_text.get("1.0", tk.END).strip(),
            **self.current_metrics,
        }
        save_score(self.results_dir, row)
        self.scored.add(f"{self.current_patient['uhid']}_{photo['filename']}")
        self.notes_text.delete("1.0", tk.END)
        self._next_photo()
        self._update_photo_list()
        self._update_progress_label()

    def _skip_photo(self):
        photo = self.current_photos[self.current_photo_idx]
        save_score(self.results_dir, {
            "timestamp":    datetime.now().isoformat(),
            "uhid":         self.current_patient["uhid"],
            "patient_name": self.current_patient["name"],
            "filename":     photo["filename"],
            "visit_type":   photo["visit_type"],
            "notes":        "SKIPPED - lesion not visible",
        })
        self._next_photo()

    def _next_photo(self):
        if self.current_photo_idx < len(self.current_photos) - 1:
            self.current_photo_idx += 1
            self._save_progress()
            self._load_current_photo()
            self._sync_list()
        else:
            messagebox.showinfo("Patient complete",
                f"All photos scored for {self.current_patient['name']}!\n\n"
                "Select the next patient from the dropdown.")

    def _prev_photo(self):
        if self.current_photo_idx > 0:
            self.current_photo_idx -= 1
            self._load_current_photo()
            self._sync_list()

    def _sync_list(self):
        self.photo_listbox.selection_clear(0, tk.END)
        self.photo_listbox.selection_set(self.current_photo_idx)
        self.photo_listbox.see(self.current_photo_idx)

    def _update_photo_list(self):
        self.photo_listbox.delete(0, tk.END)
        for photo in self.current_photos:
            key = f"{self.current_patient['uhid']}_{photo['filename']}"
            prefix = "[✓] " if key in self.scored else "    "
            self.photo_listbox.insert(
                tk.END, f"{prefix}{photo['visit_type']}  {photo['stem']}"
            )
        self._sync_list()

    def _save_progress(self):
        if self.current_patient:
            self.progress[self.current_patient["uhid"]] = self.current_photo_idx
            save_progress(self.results_dir, self.progress)

    def _update_progress_label(self):
        self.progress_label.config(text=f"{len(self.scored)} photos scored")

    def _show_error(self, msg):
        self.canvas.delete("all")
        self.canvas.create_text(350, 300, text=f"[!] {msg}",
            fill=ACCENT, font=("Courier", 12), width=400)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    try:
        import cv2
        from PIL import Image
        import numpy
    except ImportError:
        import subprocess, sys
        print("Installing required packages...")
        subprocess.run([sys.executable, "-m", "pip", "install",
                        "opencv-python", "pillow", "numpy"], check=True)

    photos_dir = DEFAULT_PHOTOS_DIR

    if not photos_dir or not Path(photos_dir).exists():
        root = tk.Tk()
        root.withdraw()
        photos_dir = filedialog.askdirectory(
            title="Select your photos directory "
                  "(folder containing patient subfolders)"
        )
        root.destroy()

    if not photos_dir:
        print("No directory selected. Exiting.")
        return

    root = tk.Tk()
    app  = ScoringApp(root, photos_dir)

    def on_resize(event):
        if app.current_image_cv is not None:
            app._display_image(app.current_image_cv)
            if app.current_roi:
                x1, y1, x2, y2 = app.current_roi
                app.canvas.create_rectangle(
                    int(x1*app.scale_factor)+app.display_offset_x,
                    int(y1*app.scale_factor)+app.display_offset_y,
                    int(x2*app.scale_factor)+app.display_offset_x,
                    int(y2*app.scale_factor)+app.display_offset_y,
                    outline=ACCENT, width=2, dash=(4, 4)
                )

    root.bind("<Configure>", on_resize)
    root.mainloop()


if __name__ == "__main__":
    main()
