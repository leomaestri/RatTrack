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
Press 'z' to undo the last point or polygon.
Press ENTER to finish and compute metrics.
Outputs per-zone:
  - First detection time (MM:SS.ss)
  - Time in illuminated area: seconds and percentage of 5 minutes after first detection (+0.5s offset)
  - Escape latency: seconds until 4 consecutive frames without detections (+0.5s offset)
  - Frames at the start are ignored according to --ignore_sec
"""
import argparse
import glob
import os
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path

# Globals for interactive drawing
zones = []            # list of polygons (each is a list of (x,y))
current_pts = []      # vertices of the polygon being drawn
pt_markers = []       # markers for current points
poly_patches = []     # Polygon patches for completed zones
text_labels = []      # text labels for zones
bg_img = None         # background image (numpy array)


def on_click(event):
    if event.inaxes is None or on_click.finished:
        return
    x, y = event.xdata, event.ydata
    current_pts.append((x, y))
    marker = event.inaxes.scatter([x], [y], c='lime', s=50, zorder=5)
    pt_markers.append(marker)
    if len(current_pts) > 1:
        xs, ys = zip(*current_pts)
        event.inaxes.plot(xs, ys, c='lime', alpha=args.rect_alpha, zorder=4)
    plt.draw()


def on_key(event):
    ax = plt.gca()
    if event.key == ' ' and not on_click.finished:
        if len(current_pts) >= 3:
            poly = plt.Polygon(
                current_pts, closed=True, fill=True,
                edgecolor='lime', facecolor='lime',
                alpha=args.rect_alpha, zorder=3
            )
            ax.add_patch(poly)
            poly_patches.append(poly)
            x0, y0 = current_pts[0]
            txt = ax.text(
                x0 + 10, y0, str(len(zones) + 1),
                color='lime', fontsize=12, weight='bold', zorder=6
            )
            text_labels.append(txt)
            zones.append(current_pts.copy())
            for m in pt_markers:
                m.remove()
            pt_markers.clear()
            current_pts.clear()
            plt.draw()
    elif event.key == 'z' and not on_click.finished:
        if current_pts:
            pt_markers.pop().remove()
            current_pts.pop()
            plt.cla()
            draw_grid()
            redraw_all()
            plt.draw()
        elif zones:
            zones.pop()
            poly_patches.pop().remove()
            text_labels.pop().remove()
            plt.cla()
            draw_grid()
            redraw_all()
            plt.draw()
    elif event.key in ['enter', 'return']:
        on_click.finished = True
        plt.close()


def redraw_all():
    ax = plt.gca()
    ax.imshow(bg_img)
    for poly in poly_patches:
        ax.add_patch(poly)
    for txt in text_labels:
        ax.add_artist(txt)
    if len(current_pts) > 1:
        xs, ys = zip(*current_pts)
        ax.plot(xs, ys, c='lime', alpha=args.rect_alpha, zorder=4)
    for x, y in current_pts:
        ax.scatter([x], [y], c='lime', s=50, zorder=5)


def draw_grid():
    ax = plt.gca()
    ax.set_xticks(np.arange(0, img_w + 1, args.grid_spacing))
    ax.set_yticks(np.arange(0, img_h + 1, args.grid_spacing))
    ax.grid(True, color='white', linestyle='--', linewidth=0.5)


def compute_metrics():
    label_files = sorted(glob.glob(os.path.join(args.label_dir, 'frame_*.txt')))
    ignore_frames = int(args.ignore_sec * args.fps)

    # now store (frame_idx, area) per zone
    detection_info_per_zone = [[] for _ in zones]

    # helper to compute polygon area
    def poly_area(pts):
        x = pts[:, 0]
        y = pts[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))

    # iterate over all label files
    for idx, lbl in enumerate(label_files):
        if idx < ignore_frames:
            continue
        eff_idx = idx - ignore_frames
        with open(lbl) as f:
            lines = [l.split() for l in f if l.strip()]
        if not lines:
            continue
        for parts in lines:
            coords = list(map(float, parts[1:9]))
            det_pts = np.array(coords).reshape(4, 2)
            centroid = det_pts.mean(axis=0)
            area = poly_area(det_pts)
            for zi, zone in enumerate(zones):
                if Path(zone).contains_point(centroid):
                    detection_info_per_zone[zi].append((eff_idx, area))
                    break

    window_frames = int(5 * 60 * args.fps)
    offset_frames = int(0.5 * args.fps)

    print("\nZone | First Detection | Illumination Time (s, %) | Escape Latency (s)")
    for zi, info in enumerate(detection_info_per_zone):
        if not info:
            print(f"{zi + 1:4d} |      N/A       |    0.00s,  0.0%     |   N/A")
            continue

        # sort frames for first detection
        frames_sorted = sorted(f for f, _ in info)
        start = frames_sorted[0]
        # format MM:SS.ss
        first_sec = start / args.fps
        first_min = int(first_sec // 60)
        first_rem = first_sec - first_min * 60
        time_str = f"{first_min:02d}:{first_rem:05.2f}"

        # average area over all detections
        avg_area = sum(a for _, a in info) / len(info)
        threshold = avg_area * 0.5

        # metric window
        metric_start = start + offset_frames
        metric_end = metric_start + window_frames

        # filter frames within window with area >= threshold
        det_in_win = [
            f for f, a in info
            if metric_start <= f < metric_end and a >= threshold
        ]
        t_illu = len(det_in_win) / args.fps
        pct = (t_illu / (5 * 60)) * 100

        # escape latency (4 consecutive frames without any detection)
        det_set = set(f for f, _ in info)
        lat_sec = None
        for f in range(metric_start, metric_end - 3):
            if all((f + k) not in det_set for k in range(4)):
                lat_sec = (f - metric_start) / args.fps
                break
        lat_str = f"{lat_sec:.2f}" if lat_sec is not None else "N/A"

        print(f"{zi + 1:4d} |    {time_str}    | {t_illu:6.2f}s, {pct:5.1f}%     |   {lat_str:6}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--label_dir', required=True,
                        help='Path to inference labels')
    parser.add_argument('--frame_img', required=True,
                        help='Reference frame image')
    parser.add_argument('--fps', type=float, default=10.0,
                        help='Frames per second')
    parser.add_argument('--grid_spacing', type=int, default=30,
                        help='Grid line spacing')
    parser.add_argument('--rect_alpha', type=float, default=0.25,
                        help='Polygon transparency')
    parser.add_argument('--ignore_sec', type=float, default=0.0,
                        help='Seconds to ignore at beginning of video')
    args = parser.parse_args()

    print("\n-----CONFIG PARAMETERS-----")
    print(f"Reference frame:  {args.frame_img}")
    print(f"Labels from:      {args.label_dir}")
    print(f"FPS:              {args.fps}")
    print(f"Grid spacing:     {args.grid_spacing}")
    print(f"Polygon alpha:    {args.rect_alpha}")
    print(f"Ignore seconds:   {args.ignore_sec}")
    print("---------------------------")

    img = plt.imread(args.frame_img)
    img_h, img_w = img.shape[:2]
    bg_img = img

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(bg_img)
    draw_grid()
    on_click.finished = False
    fig.canvas.mpl_connect('button_press_event', on_click)
    fig.canvas.mpl_connect('key_press_event', on_key)
    ax.set_title("Click points; SPACE to close; Z to undo; ENTER to finish")
    plt.show()

    if not zones:
        raise RuntimeError("No zones defined")

    compute_metrics()
