#!/usr/bin/env python3
"""
Diagnostic script to analyze sphere cap container detection
Run with: python diagnose_sphere_cap.py
"""

import sys
import os
import logging
import tempfile

# Setup logging to show DEBUG output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s | %(message)s'
)

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container_geometry_analyzer_gui_v3_11_8 import (
    load_data_csv, compute_areas, DEFAULT_PARAMS,
    segment_and_fit_optimized, create_enhanced_profile,
    AnalysisJob
)
import pandas as pd
from io import StringIO

# User's sphere cap data
sphere_cap_csv = """Height_mm,Volume_mL
6.183,0.02
7.79,0.04
8.918,0.06
9.815,0.08
10.573,0.1
11.236,0.12
11.828,0.14
12.366,0.16
12.862,0.18
13.321,0.2
13.751,0.22
14.156,0.24
14.539,0.26
14.902,0.28
15.249,0.3
15.581,0.32
15.899,0.34
16.204,0.36
16.499,0.38
16.784,0.4
17.059,0.42
17.325,0.44
17.584,0.46
17.835,0.48
18.08,0.5
18.318,0.52
18.551,0.54
18.783,0.56
19.016,0.58
19.249,0.6
19.482,0.62
19.714,0.64
19.947,0.66
20.18,0.68
20.413,0.7
20.645,0.72
20.878,0.74
21.111,0.76
21.344,0.78
21.576,0.8
21.809,0.82
22.042,0.84
22.275,0.86
22.507,0.88
22.74,0.9
22.973,0.92
23.206,0.94
23.438,0.96
23.671,0.98
23.904,1.0
24.137,1.02
24.369,1.04
24.602,1.06
24.835,1.08
25.068,1.1
25.3,1.12
25.533,1.14
25.766,1.16
25.999,1.18
26.231,1.2
26.464,1.22
26.697,1.24
26.929,1.26
27.162,1.28
27.395,1.3
27.628,1.32
27.86,1.34
28.093,1.36
28.326,1.38
28.559,1.4
28.791,1.42
29.024,1.44
29.257,1.46
29.49,1.48
29.722,1.5"""

print("=" * 80)
print("SPHERE CAP CONTAINER DIAGNOSTICS")
print("=" * 80)
print()

# Create temp file in cross-platform way
temp_dir = tempfile.gettempdir()
test_file = os.path.join(temp_dir, 'sphere_cap_test.csv')

print(f"Test data saved to: {test_file}")
print()

# Save test data to temp file
with open(test_file, 'w') as f:
    f.write(sphere_cap_csv)

# Enable debug mode
print("=" * 80)
print("ANALYSIS CONFIGURATION")
print("=" * 80)
print(f"Transition detection method: {DEFAULT_PARAMS['transition_detection_method']}")
print(f"Debug mode: ENABLED")
print()

# Override to enable debug
DEFAULT_PARAMS['debug_transitions'] = True

print("=" * 80)
print("STARTING ANALYSIS...")
print("=" * 80)
print()

try:
    job = AnalysisJob(test_file)

    # Step 1: Load data
    print("\n[1/4] Loading CSV data...")
    df = load_data_csv(test_file, job=job, verbose=True)
    print(f"      Loaded {len(df)} data points")
    print(f"      Height range: {df['Height_mm'].min():.2f} - {df['Height_mm'].max():.2f} mm")
    print(f"      Volume range: {df['Volume_ml'].min():.2f} - {df['Volume_ml'].max():.2f} mL")

    # Step 2: Compute areas
    print("\n[2/4] Computing cross-sectional areas...")
    df_areas = compute_areas(df, job=job, verbose=True)
    print(f"      Area range: {df_areas['Area'].min():.4f} - {df_areas['Area'].max():.4f} mm²")

    # Step 3: Segmentation and fitting
    print("\n[3/4] Detecting transitions and fitting shapes...")
    print("      (Debug output below shows all shape fitting errors)")
    print()
    segments = segment_and_fit_optimized(df_areas, job=job, verbose=True)

    # Step 4: Generate profile
    print("\n[4/4] Generating smooth profile...")
    z_smooth, r_smooth = create_enhanced_profile(segments, df_areas, job=job, verbose=True)

    job.finalize()
    summary = job.get_summary()

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Duration: {summary['duration']:.2f} seconds")
    print(f"Segments detected: {len(segments)}")
    print()

    print("Segment details:")
    for i, (start_idx, end_idx, shape, params) in enumerate(segments):
        h_start = df_areas.iloc[start_idx]['Height_mm']
        h_end = df_areas.iloc[end_idx]['Height_mm']

        print(f"  Segment {i}: {shape:<12} | Height {h_start:6.2f}-{h_end:6.2f} mm | Params: {params}")

    print()
    print("=" * 80)
    print("INTERPRETATION")
    print("=" * 80)

    if len(segments) == 1:  # Only 1 segment (entire container)
        start_idx, end_idx, shape, params = segments[0]
        print(f"\n⚠️  SINGLE SEGMENT DETECTED: {shape}")
        print()
        print("This means the improved algorithm treated the entire container as ONE shape.")
        print()
        if shape == 'sphere_cap':
            print("✓ GOOD: Correctly identified as SPHERE CAP!")
            print("  The smooth curvature was detected by the multi-derivative analysis.")
        elif shape == 'frustum':
            print("⚠️  ISSUE: Identified as FRUSTUM instead of SPHERE CAP")
            print("  The sphere cap fit error was higher than frustum error.")
            print("  This may be due to:")
            print("    - Sphere cap fitting bounds being too restrictive")
            print("    - Frustum being too flexible and fitting well by chance")
            print("    - Need to improve sphere cap fitting logic")
        else:
            print(f"  Shape: {shape}")
    else:
        print(f"\n✓ MULTIPLE SEGMENTS DETECTED: {len(segments)} segments")
        print()
        print("This means the improved algorithm detected transitions within the container.")
        print("Each segment was fitted to its best matching shape.")
        print()

        # Check if any segment is sphere cap
        shapes = [seg[2] for seg in segments]
        if 'sphere_cap' in shapes:
            sphere_cap_indices = [i for i, seg in enumerate(segments) if seg[2] == 'sphere_cap']
            print(f"✓ Segment(s) {sphere_cap_indices} identified as SPHERE CAP - good!")
        else:
            print("ℹ️  No sphere cap segments detected")

    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("To improve sphere cap detection:")
    print()
    print("1. Check the fit error comparison (shown above)")
    print("   - If sphere cap error >> frustum error:")
    print("     → Improve sphere cap fitting (bounds, initial guess)")
    print()
    print("2. Verify the transition detection is working")
    print("   - Check if curvature changes are being detected")
    print("   - Look at 1st/2nd derivative ranges in debug output")
    print()
    print("3. Fine-tune shape preference logic")
    print("   - Add penalties for over-flexible models")
    print("   - Prefer simpler models when errors are similar")
    print()

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
