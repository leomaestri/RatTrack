import os
import csv


def report(rows):
    """
    Print aligned metrics table and write CSV to ../outputs/zone_metrics.csv.

    rows: List of tuples (zone_id, time_str, illum_sec, illum_pct, latency, transfers).
    """
    # 1) Print formats
    hdr_fmt = "{:<4} | {:<13} | {:<20} | {:<16} | {:<18}"
    row_fmt = "{:<4d} | {:<13s} | {:<20s} | {:<16s} | {:<18d}"

    # 2) Print header
    print()
    print(hdr_fmt.format(
        "Zone",
        "First Detection",
        "Illumination Time (s, %)",
        "Escape Latency (s)",
        "Transference Number"
    ))

    # 3) Prepare CSV
    script_dir = os.path.dirname(__file__)
    output_dir = os.path.join(script_dir, os.pardir, os.pardir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'zone_metrics.csv')
    with open(csv_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            'Zone',
            'First Detection',
            'Illumination Time (s)',
            'Illumination %',
            'Escape Latency (s)',
            'Transference Number'
        ])

        # 4) Iterate rows
        for zi, time_str, illum, pct, lat, transfers in rows:
            # Format values to print
            illum_str = f"{illum:.2f}s, {pct:.1f}%" if illum is not None else "N/A"
            lat_str = f"{lat:.2f}" if lat is not None else "N/A"

            # Print on console
            print(row_fmt.format(zi, time_str, illum_str, lat_str, transfers))

            # Write in CSV (no units)
            writer.writerow([
                zi,
                time_str,
                f"{illum:.2f}" if illum is not None else 'N/A',
                f"{pct:.1f}" if pct is not None else 'N/A',
                lat_str,
                transfers
            ])

    clean_path = os.path.normpath(csv_path)
    print(f"\nCSV saved to: {clean_path}")
