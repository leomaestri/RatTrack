"""
Interactive polygon zone counter for OBB detections, with 5-minute illumination and escape latency metrics.

Usage:
    python zone_counter.py \
      --label_dir /path/to/labels \
      --frame_img /path/to/frame.png \
      [--fps 10] \
      [--grid_spacing 100] \
      [--rect_alpha 0.3] \
      [--ignore_sec 0]

Draw polygon zones by clicking vertices. Press SPACE to close a polygon.
Press z to undo the last point or polygon.
Press ENTER to finish and compute metrics.
Outputs per-zone:
  - First detection time (MM:SS.ss)
  - Time in illuminated area: seconds and percentage of 5 minutes after first detection (+0.5s offset)
  - Escape latency: seconds until 4 consecutive frames without detections (+0.5s offset)
  - Frames at the start are ignored according to --ignore_sec
"""
import tkinter as tk
from tkinter import messagebox, ttk
import argparse
import matplotlib.pyplot as plt
from metrics.metric_computations import (
    compute_illumination,
    compute_escape_latency,
    compute_transfer_count,
)
from drawing import ZoneDrawer
from outputs_and_reporting.reporting import report
from utils import format_time, load_detections

# Globals for interactive drawing
zones = []  # list of polygons (each is a list of (x,y))
current_pts = []  # vertices of the polygon being drawn
pt_markers = []  # markers for current points
poly_patches = []  # Polygon patches for completed zones
text_labels = []  # text labels for zones
bg_img = None  # background image (numpy array)


def get_user_config():
    """
    Show a single Tkinter window with entries for all parameters.
    Returns an argparse.Namespace with the collected values.
    """
    root = tk.Tk()
    root.title("Zone Counter Configuration")

    # Row 0: Label Directory
    tk.Label(root, text="Label Directory").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    ent_label = tk.Entry(root, width=50)
    ent_label.grid(row=0, column=1, padx=5, pady=2)

    # Row 1: Frame Image
    tk.Label(root, text="Reference Frame Image").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    ent_frame = tk.Entry(root, width=50)
    ent_frame.grid(row=1, column=1, padx=5, pady=2)

    # Row 2: Ignore Start Time
    tk.Label(root, text="Experiment Start Time (MM:SS)").grid(row=2, column=0, sticky="w", padx=5, pady=2)
    ent_ignore = tk.Entry(root, width=10)
    ent_ignore.insert(0, "00:00")
    ent_ignore.grid(row=2, column=1, sticky="w", padx=5, pady=2)

    # Visual Parameters frame (rows 3+)
    vf = ttk.LabelFrame(root, text="Visual Parameters")
    vf.grid(row=3, column=0, columnspan=2, padx=5, pady=10, sticky="we")

    # Grid Spacing
    tk.Label(vf, text="Grid Spacing (px)").grid(row=0, column=0, sticky="w", padx=5, pady=2)
    ent_grid = tk.Entry(vf, width=10)
    ent_grid.insert(0, "50")
    ent_grid.grid(row=0, column=1, padx=5, pady=2)

    # Polygon Transparency
    tk.Label(vf, text="Polygon Transparency").grid(row=1, column=0, sticky="w", padx=5, pady=2)
    ent_alpha = tk.Entry(vf, width=10)
    ent_alpha.insert(0, "0.25")
    ent_alpha.grid(row=1, column=1, padx=5, pady=2)

    # --- Metrics Selection frame (rows 5+) ---
    mf = ttk.LabelFrame(root, text="Metrics Selection")
    mf.grid(row=5, column=0, columnspan=2, padx=5, pady=10, sticky="we")

    # First Detection
    var_fd = tk.BooleanVar(value=True)
    cb_fd = tk.Checkbutton(
        mf, text="First Detection:\t\ttime of first entry (MM:SS.ss)",
        variable=var_fd,
        anchor="w",
        justify="left",
    )
    cb_fd.grid(row=0, column=0, sticky="w", padx=5, pady=2)

    # Illumination Time
    var_illu = tk.BooleanVar(value=True)
    cb_illu = tk.Checkbutton(
        mf,
        text="Illumination Time (s, %):\ttime spent in zone over 5min",
        variable=var_illu,
        anchor="w",
        justify="left",
    )
    cb_illu.grid(row=1, column=0, sticky="w", padx=5, pady=2)

    # Escape Latency
    var_lat = tk.BooleanVar(value=True)
    cb_lat = tk.Checkbutton(
        mf,
        text="Escape Latency (s):\t\ttime until 4 consecutive misses",
        variable=var_lat,
        anchor="w",
        justify="left",
    )
    cb_lat.grid(row=2, column=0, sticky="w", padx=5, pady=2)

    # Transference Number
    var_trans = tk.BooleanVar(value=True)
    cb_trans = tk.Checkbutton(
        mf,
        text="Transference Number:\tnumber of exits & re-entries to the zone",
        variable=var_trans,
        anchor="w",
        justify="left",
    )
    cb_trans.grid(row=3, column=0, sticky="w", padx=5, pady=2)

    result = {}

    def on_submit():
        try:
            # Read and validate paths
            ld = ent_label.get().strip()
            fi = ent_frame.get().strip()

            if not ld or not fi:
                raise ValueError("Label directory and frame image cannot be empty.")

            # Parse Ignore Start Time MM:SS → seconds
            mm, ss = ent_ignore.get().split(":")
            ig_seconds = int(mm) * 60 + int(ss)

            # Visual params
            gs = int(ent_grid.get())
            ra = float(ent_alpha.get())
        except Exception as e:
            messagebox.showerror("Invalid input", str(e))
            return

        result['args'] = argparse.Namespace(
            label_dir=ld,
            frame_img=fi,
            fps=10.0,  # fixed default
            grid_spacing=gs,
            rect_alpha=ra,
            ignore_sec=ig_seconds,
            do_fd=var_fd.get(),
            do_illum=var_illu.get(),
            do_latency=var_lat.get(),
            do_transfer=var_trans.get(),
        )
        root.destroy()

    # Botón de aceptación (justo debajo del frame de métricas que está en la fila 5)
    btn = tk.Button(root, text="Aceptar", command=on_submit)
    btn.grid(row=6, column=0, columnspan=2, pady=10)

    root.mainloop()
    return result.get('args')


def compute_metrics(zones, args):
    ignore_frames = int(args.ignore_sec * args.fps)
    info_per_zone = load_detections(args.label_dir, ignore_frames, zones)

    window_frames = int(5 * 60 * args.fps)
    offset_frames = int(0.5 * args.fps)

    rows = []
    for zi, info in enumerate(info_per_zone, start=1):
        if not info:
            # no detections: all to None or 0
            rows.append((zi, 'N/A', None, None, None, 0))
            continue

        # first detection
        first_frame = min(f for f, _ in info)
        time_str = format_time(first_frame, args.fps)

        # threshold area
        avg_area = sum(a for _, a in info) / len(info)
        thr = avg_area * 0.5

        # analysis window
        start = first_frame + offset_frames
        end = start + window_frames

        # frames inside window & set of all frames
        dets_in = [f for f, a in info if start <= f < end and a >= thr]
        dets_set = {f for f, _ in info}

        # metrics
        t_illu, pct = compute_illumination(dets_in, args.fps) if args.do_illum else (None, None)
        lat = compute_escape_latency(dets_set, start, end, args.fps) if args.do_latency else None
        transfers = compute_transfer_count(dets_set, start, end, offset_frames) if args.do_transfer else None
        rows.append((zi, time_str, t_illu, pct, lat, transfers))

    return rows


if __name__ == '__main__':
    args = get_user_config()
    if args is None:
        raise RuntimeError("Configuration cancelled")

    print("\n-----CONFIG PARAMETERS-----")
    print(f"Reference frame:  {args.frame_img}")
    print(f"Labels from:      {args.label_dir}")
    print(f"FPS:              {args.fps}")
    print(f"Grid spacing:     {args.grid_spacing}")
    print(f"Polygon alpha:    {args.rect_alpha}")
    print(f"Ignore seconds:   {args.ignore_sec}")
    print("---------------------------")

    # 3) Read image and define zones
    img = plt.imread(args.frame_img)
    drawer = ZoneDrawer(img, rect_alpha=args.rect_alpha, grid_spacing=args.grid_spacing)
    zones = drawer.start()
    if not zones:
        raise RuntimeError("No zones defined")

    # 4) Compute metrics & report
    rows = compute_metrics(zones, args)
    report(rows)
