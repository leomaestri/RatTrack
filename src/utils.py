from matplotlib.path import Path
from typing import List, Tuple
import numpy as np
import glob
import os


def poly_area(pts: np.ndarray) -> float:
    """Compute area of a polygon given as Nx2 array."""
    x, y = pts[:, 0], pts[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def load_detections(
    label_dir: str,
    ignore_frames: int,
    zones: List[List[Tuple[float, float]]]
) -> List[List[Tuple[int, float]]]:
    """
    Read frame_*.txt, skip ignore_frames, compute centroid+area,
    and assign (frame_idx, area) into one list per zone.
    """
    label_files = sorted(glob.glob(os.path.join(label_dir, 'frame_*.txt')))
    info_per_zone = [[] for _ in zones]
    for idx, lbl in enumerate(label_files):
        if idx < ignore_frames: continue
        eff = idx - ignore_frames
        lines = [l.split() for l in open(lbl) if l.strip()]
        for parts in lines:
            coords = np.array(list(map(float, parts[1:9]))).reshape(4, 2)
            centroid = coords.mean(axis=0)
            area = poly_area(coords)
            for zi, zone in enumerate(zones):
                if Path(zone).contains_point(centroid):
                    info_per_zone[zi].append((eff, area))
                    break
    return info_per_zone


def format_time(frame_idx: int, fps: float) -> str:
    """
    Convert frame index to MM:SS.ss format.
    """
    sec = frame_idx / fps
    m = int(sec // 60)
    s = sec - m * 60
    return f"{m:02d}:{s:05.2f}"
