# RatTrack

Easy tool for researchers to train, test and apply tracking of mice and rats in lab videos, adaptable to diverse workflows. Your feedback helps improve the project.  
To suggest features or collaborate, email [leonardo.maestri.data@gmail.com](mailto:leonardo.maestri.data@gmail.com) or connect on LinkedIn: linkedin.com/in/leonardo-maestri-data-scientist/

## Colab Notebooks

Get started immediately on Google Colab:

#### Train | Test

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leomaestri/RatTrack/blob/main/notebooks/train_yolov11.ipynb)  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leomaestri/RatTrack/blob/main/notebooks/test_yolov11.ipynb)

## Common Workflow

1. **Open the Test Notebook.**  
2. **Load your video and run inference.**  
3. **Run model inference** via **test_yolov11.ipynb** (or your own pipeline) to produce:  
   - Per-frame detection `.txt` labels in the format expected by the Zone Counter.  
   - A reference frame image (e.g. `frame_000100.png`) saved alongside the labels.  
4. **Launch the Zone Counter GUI:**  
   ```bash
   python interface.py
   ```
## Installation

1. (Optional) Create and activate a Python virtual environment:

   ```bash
   python3 -m venv .ratenv
   source .ratenv/bin/activate   # On Windows use `.venv\Scripts\activate`
   ```

2. Clone the repository:

   ```bash
   git clone https://github.com/leomaestri/RatTrack.git
   cd RatTrack
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
   System dependencies

   * Python 3.9+
   * tkinter GUI toolkit. On Debian/Ubuntu: 
   ```bash
   sudo apt-get install python3-tk
   ```
   On Fedora:   
   ```bash
   sudo dnf install python3-tkinter
   ```
   
---

## Interactive Zone Counter

Tool to define polygonal zones on a reference frame and compute illumination and escape-latency metrics from OBB detection labels.

**Script:** `interface.py`

### Usage

```bash
python interface.py
```
No command-line flags—everything is configured in the graphic interface.


### Configuration GUI

When you run `interface.py`, a window appears with these fields:

1. **Label Directory**  
   Path to the folder containing per-frame detection `.txt` files.

2. **Reference Frame Image**  
   Path to the single image (e.g. `frame_000100.png`) on which to draw zones.

3. **Experiment Start Time (MM:SS)**  
   Timestamp in **MM:SS** marking when the experiment truly begins; used to skip initial frames.

4. **Visual Parameters**  
   - **Grid Spacing (px):** pixel-spacing between grid lines.  
   - **Polygon Transparency:** alpha value for zone overlays.

5. **Metrics Selection** (all enabled by default)  
   - **First Detection:** time of the first entry into each zone (MM:SS.ss).  
   - **Illumination Time (s, %):** total seconds (and percent of 5 min) the zone stayed “illuminated” (area ≥ 50 % of its average).  
   - **Escape Latency (s):** seconds from first entry until 4 consecutive frames with no detection (+ 0.5 s offset).  
   - **Transference Number:** number of times the subject exited and re-entered the zone (gaps < 0.5 s ignored).

6. Click **Aceptar** to confirm and proceed to zone drawing.

![configuration_screen.png](docs%2Fimages%2Fconfiguration_screen.png)

### Interactive Workflow

1. **Draw zones**  
   - Click to place vertices.  
   - Press **SPACE** to close the current polygon (minimum 3 points).  
   - Press **Z** to undo the last point or remove the last closed zone.  
   - Press **ENTER** when all zones are defined.

![zone_delimitation_on_frame_of_reference.png](docs%2Fimages%2Fzone_delimitation_on_frame_of_reference.png)![zone_delimitation_on_reference_frame.png]

2. **Compute metrics**  
   After closing the drawing window, the script processes all labels, prints a neatly aligned table, and writes `outputs/zone_metrics.csv`:

   * **First Detection**: timestamp (MM\:SS.ss) of first detection in each zone
   * **Illumination Time**: seconds and percent of time-window where detection remains in the zone (≥ 50% average size of detection, "at least half the mouse/rat")
   * **Escape Latency**: seconds until 4 consecutive frames without any detection (with +0.5 s offset)
   * **Transference Number**: number of exits & re-entries to each zone

![console_metrics_output_example.png](docs%2Fimages%2Fconsole_metrics_output_example.png)

![csv_metrics_output_example.png](docs%2Fimages%2Fcsv_metrics_output_example.png)

---

## Model Training Notebook

**Notebook:** `notebooks/train_yolov11.ipynb`

Guides you through data preparation, model configuration and training (in Colab or locally).

---

## Model Testing Notebook

**Notebook:** `notebooks/test_yolov11.ipynb`

Load the trained model and run inference on a test video, producing `.txt` labels and annotated output. Also 3 reference frames to delimit detection zones of interest. 

---

