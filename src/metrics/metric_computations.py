def compute_illumination(frames, fps):
    """
    Compute illumination time and percentage over a 5-minute window.
    frames: list of frame indices with valid detections (already offset by +0.5s).
    fps: frames per second.
    Returns: (illum_seconds: float, illum_pct: float)
    """
    window_secs = 5 * 60
    t_illu = len(frames) / fps
    pct = (t_illu / window_secs) * 100
    return t_illu, pct


def compute_escape_latency(detection_set, start_frame, end_frame, fps):
    """
    Compute escape latency: time until 4 consecutive frames without detections.
    detection_set: set of frame indices with detections.
    start_frame: first frame to consider (offset applied).
    end_frame: last frame (exclusive).
    fps: frames per second.
    Returns: latency seconds (float) or None if never escaped.
    """
    for f in range(start_frame, end_frame - 3):
        if all((f + k) not in detection_set for k in range(4)):
            return (f - start_frame) / fps
    return None


def compute_transfer_count(detection_set, start_frame, end_frame, offset_frames):
    """
    Count number of times the object exited and re-entered the zone.
    Short gaps (< offset_frames) are ignored.
    detection_set: set of frame indices with detections.
    start_frame, end_frame: analysis window.
    offset_frames: minimum gap size in frames to count as a transfer.
    Returns: integer transfer count.
    """
    occupancy = [
        1 if f in detection_set else 0
        for f in range(start_frame, end_frame)
    ]
    in_zone = occupancy[0] == 1
    had_been_inside = in_zone
    exit_start = None
    transfers = 0

    for i, occ in enumerate(occupancy):
        if in_zone and occ == 0:
            in_zone = False
            exit_start = i
        elif not in_zone and occ == 1:
            if exit_start is not None and had_been_inside:
                gap = i - exit_start
                if gap >= offset_frames:
                    transfers += 1
            in_zone = True
            had_been_inside = True
            exit_start = None

    return transfers
