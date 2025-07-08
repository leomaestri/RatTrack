# RatTrack

Easy tool for researchers to train, test and apply tracking of mice and rats in lab videos, adaptable to diverse workflows. Your feedback helps improve the project. To suggest features or collaborate, email [leonardo.maestri.data@gmail.com](mailto:leonardo.maestri.data@gmail.com) or connect on LinkedIn: linkedin.com/in/leonardo-maestri-data-scientist/

## Colab Notebooks

Get started immediately on Google Colab:

#### Train | Test

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leomaestri/RatTrack/blob/main/notebooks/train_yolov11.ipynb)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/leomaestri/RatTrack/blob/main/notebooks/test_yolov11.ipynb)

### Common Workflow

1) Open the Test Notebook.

2) Load your video and run inference.

3) Download the generated labels and annotated video.

3) Run interface.py locally, pointing it to the downloaded labels and reference frame.

---

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

---

## Interactive Zone Counter

Tool to define polygonal zones on a reference frame and compute illumination and escape-latency metrics from OBB detection labels.

**Script:** `interface.py`

### Usage

```bash
python interface.py \
  --label_dir /path/to/labels \
  --frame_img /path/to/frame.png \
  [--fps 10] \
  [--grid_spacing 30] \
  [--rect_alpha 0.25] \
  [--ignore_sec 0]
```

* **--label\_dir**
  Folder with per-frame detection `.txt` files. Generated from Test notebook
* **--frame\_img**
  Reference image (e.g. `frame_000100.png`) on which to draw zones.
* **--fps** *(default: 10)*
  Frames per second of the original video.
* **--grid\_spacing** *(default: 30)*
  Pixel spacing between grid lines.
* **--rect\_alpha** *(default: 0.25)*
  Polygon transparency.
* **--ignore\_sec** *(default: 0)*
  Seconds at start of video to skip in metrics.

### Interactive Workflow

1. **Draw zones**

   * Click to place vertices.
   * Press **SPACE** to close a polygon (minimum 3 points).
   * Press **Z** to undo the last point or remove the last zone.
   * Press **ENTER** when all zones are defined.
2. **Compute metrics**
   The script processes all labels and prints a table:

   ```
   Zone | First Detection | Illumination Time (s, %) | Escape Latency (s)
     1  |     00:12.34    |     45.60s, 15.2%         |      3.20
     2  |       N/A       |      0.00s,  0.0%         |      N/A
   ```

   * **First Detection**: timestamp (MM\:SS.ss) of first detection in each zone
   * **Illumination Time**: seconds and percent of 5-minute window where area remains “illuminated” (area ≥ 50% of its average)
   * **Escape Latency**: seconds until 4 consecutive frames without any detection (with +0.5 s offset)

---

## Model Training Notebook

**Notebook:** `notebooks/train_yolov11.ipynb`

Guides you through data preparation, model configuration and training (in Colab or locally).

**Key Steps**

1. **Environment Setup**

   * Detect Colab vs. local, install dependencies, clone repo if needed
   * Define `DATA_DIR`, `MODEL_DIR`, etc.
2. **Data Loading & Preprocessing**

   * Unzip and load `data/dataset`
   * (Optional) Visualize samples and annotations
3. **Model Configuration**

   * Set backbone, batch size, image size, learning rate, epochs, augmentations
4. **Training**

   * Launch `model.train(...)`
   * Monitor losses and metrics
5. **Saving & Exporting**

   * Save best `model.pt` to `models/`
   * (Optional) Export to ONNX or TorchScript

---

## Model Testing Notebook

**Notebook:** `notebooks/test_yolov11.ipynb`

Load the trained model and run inference on a test video, with annotated output.

**Key Steps**

1. **Environment Setup**

   * Detect Colab vs. local, install dependencies
   * Set `MODEL_PATH` to `data/model.pt` and `VIDEO_PATH` to `data/test_video.mp4`
2. **Load Model & Video**

   * `model = YOLO(MODEL_PATH)`
   * Open and inspect `VIDEO_PATH` (FPS, resolution)
3. **Inference**

   * Call `model.predict(source=VIDEO_PATH, ...)` with threshold and size
   * Stream or batch-process the video
4. **Visualization & Saving**

   * Display results inline or in an OpenCV window
   * Save annotated video to `runs/predict` or `output/`
5. **Optional Analysis**

   * Export per-frame boxes to `.txt` or `.csv`
   * Compute simple stats (detection counts, average confidence)

---

