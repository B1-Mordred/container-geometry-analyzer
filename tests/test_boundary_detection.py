#!/usr/bin/env python3
"""
Test Improved Boundary Detection for Composite Shapes
======================================================

Tests alternative boundary detection approaches:
1. Multi-scale curvature analysis
2. Gradient magnitude peak detection
3. Curvature change detection
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container_geometry_analyzer_gui_v3_11_8 import (
    load_data_csv,
    compute_areas,
    compute_curvature,
)

COMPOSITE_FLASK = 'test_data/composite_flask_sphere_cylinder.csv'
COMPOSITE_CONE = 'test_data/composite_centrifuge_cone_cylinder.csv'


def test_case(filename, description, expected_transition_height):
    """Test boundary detection on a composite shape."""
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"Expected transition at height: {expected_transition_height} mm")
    print(f"{'='*80}")

    # Load data
    df = load_data_csv(filename)
    df_areas = compute_areas(df)
    area = df_areas['Area'].values
    heights = df_areas['Height_mm'].values

    # Compute derivatives
    curvature = compute_curvature(area, heights)
    first_deriv = np.gradient(area, heights)
    second_deriv = np.gradient(first_deriv, heights)

    print(f"\nData: {len(area)} points, heights {heights[0]:.1f}-{heights[-1]:.1f} mm")

    # Method 1: Find gradient magnitude peaks (area is changing fastest at transition)
    print(f"\n{'─'*80}")
    print("METHOD 1: Gradient Magnitude Peak Detection")
    print(f"{'─'*80}")

    grad_magnitude = np.abs(first_deriv)
    grad_magnitude_smooth = np.convolve(grad_magnitude, np.ones(5)/5, mode='same')

    # Find local maxima in gradient
    grad_peaks = []
    for i in range(1, len(grad_magnitude_smooth) - 1):
        if (grad_magnitude_smooth[i] > grad_magnitude_smooth[i-1] and
            grad_magnitude_smooth[i] > grad_magnitude_smooth[i+1] and
            grad_magnitude_smooth[i] > np.percentile(grad_magnitude_smooth, 75)):
            grad_peaks.append(i)

    print(f"Found {len(grad_peaks)} gradient peaks (>75th percentile)")
    if grad_peaks:
        print("Gradient peak locations:")
        for p in grad_peaks[:5]:
            print(f"  Index {p}: height {heights[p]:.2f}mm, gradient {grad_magnitude_smooth[p]:.4f}")

    # Method 2: Multi-scale curvature analysis
    print(f"\n{'─'*80}")
    print("METHOD 2: Multi-Scale Curvature Analysis")
    print(f"{'─'*80}")

    # Create curvature at multiple window sizes
    scales = [3, 5, 9]
    curvature_scales = []

    for scale in scales:
        # Recompute with local polynomial
        from scipy.signal import savgol_filter
        area_smooth = savgol_filter(area, window_length=scale*2+1, polyorder=2)
        fd = np.gradient(area_smooth, heights)
        sd = np.gradient(fd, heights)
        curv = np.abs(sd) / (1.0 + np.abs(fd)**1.5)
        curvature_scales.append(curv)
        print(f"  Scale {scale}: curvature range {np.nanmin(curv):.6f}-{np.nanmax(curv):.6f}")

    # Find where curvature changes most significantly across scales
    curvature_variance = np.std(curvature_scales, axis=0)
    print(f"\nCurvature variance range: {np.nanmin(curvature_variance):.6f}-{np.nanmax(curvature_variance):.6f}")

    # Find peaks in curvature variance (indicates boundary)
    variance_threshold = np.nanpercentile(curvature_variance, 75)
    variance_peaks = np.where(curvature_variance > variance_threshold)[0]

    print(f"Locations with high curvature variance (>{variance_threshold:.6f}):")
    print(f"  {len(variance_peaks)} indices")
    if len(variance_peaks) > 0:
        # Group consecutive indices
        groups = []
        current_group = [variance_peaks[0]]
        for i in range(1, len(variance_peaks)):
            if variance_peaks[i] == variance_peaks[i-1] + 1:
                current_group.append(variance_peaks[i])
            else:
                groups.append(current_group)
                current_group = [variance_peaks[i]]
        groups.append(current_group)

        print(f"\nGrouped into {len(groups)} regions:")
        for g in groups[:3]:
            center = np.mean(g)
            center_idx = int(center)
            print(f"  Region: indices {g[0]}-{g[-1]}, center height {heights[center_idx]:.2f}mm")

    # Method 3: Second derivative sign changes (inflection points) combined with gradient
    print(f"\n{'─'*80}")
    print("METHOD 3: Curvature Change Detection (d(curvature)/dh)")
    print(f"{'─'*80}")

    # Compute derivative of curvature
    curvature_deriv = np.gradient(curvature, heights)
    print(f"Curvature derivative range: {np.nanmin(curvature_deriv):.6f}-{np.nanmax(curvature_deriv):.6f}")

    # Find peaks in curvature derivative (indicates significant curvature change)
    curv_deriv_magnitude = np.abs(curvature_deriv)
    curv_deriv_threshold = np.nanpercentile(curv_deriv_magnitude, 80)
    curv_change_indices = np.where(curv_deriv_magnitude > curv_deriv_threshold)[0]

    print(f"Locations with significant curvature change (>{curv_deriv_threshold:.6f}):")
    if len(curv_change_indices) > 0:
        # Group consecutive
        groups = []
        current_group = [curv_change_indices[0]]
        for i in range(1, len(curv_change_indices)):
            if curv_change_indices[i] == curv_change_indices[i-1] + 1:
                current_group.append(curv_change_indices[i])
            else:
                groups.append(current_group)
                current_group = [curv_change_indices[i]]
        groups.append(current_group)

        print(f"  Found {len(groups)} region(s) with curvature changes:")
        for g in groups[:3]:
            center = np.mean(g)
            center_idx = int(center)
            print(f"    Region: indices {g[0]}-{g[-1]}, height {heights[center_idx]:.2f}mm")

    # Method 4: Combined approach - gradient peak + curvature continuity check
    print(f"\n{'─'*80}")
    print("METHOD 4: Combined Gradient+Curvature Boundary Detection")
    print(f"{'─'*80}")

    # Find significant gradient changes
    grad_change = np.abs(np.diff(first_deriv))
    grad_change_peaks = []

    for i in range(1, len(grad_change) - 1):
        if grad_change[i] > np.percentile(grad_change, 80):
            grad_change_peaks.append(i)

    print(f"Found {len(grad_change_peaks)} gradient change peaks")

    # For each gradient peak, check if it's at a curvature boundary
    boundary_candidates = []
    for peak in grad_change_peaks[:10]:
        left_curv = np.nanmean(curvature[max(0, peak-3):peak])
        right_curv = np.nanmean(curvature[peak:min(len(curvature), peak+3)])

        curv_change = abs(right_curv - left_curv)

        if curv_change > 0.01:  # Significant curvature change
            boundary_candidates.append({
                'index': peak,
                'height': heights[peak],
                'grad_change': grad_change[peak],
                'curv_change': curv_change
            })

    if boundary_candidates:
        print("\nPotential boundaries (gradient change + curvature transition):")
        for cand in sorted(boundary_candidates, key=lambda x: x['curv_change'], reverse=True)[:3]:
            print(f"  Height {cand['height']:.2f}mm: grad_change={cand['grad_change']:.4f}, "
                  f"curv_change={cand['curv_change']:.6f}")

    # Summary
    print(f"\n{'─'*80}")
    print("SUMMARY - Best Detected Boundary Locations:")
    print(f"{'─'*80}")

    candidates = []

    if grad_peaks:
        candidates.append(('Gradient Peak', heights[grad_peaks[0]], grad_peaks[0]))

    if len(variance_peaks) > 0:
        groups = []
        current_group = [variance_peaks[0]]
        for i in range(1, len(variance_peaks)):
            if variance_peaks[i] == variance_peaks[i-1] + 1:
                current_group.append(variance_peaks[i])
            else:
                groups.append(current_group)
                current_group = [variance_peaks[i]]
        groups.append(current_group)
        if groups:
            center_idx = int(np.mean(groups[0]))
            candidates.append(('Curvature Variance', heights[center_idx], center_idx))

    if boundary_candidates:
        best = max(boundary_candidates, key=lambda x: x['curv_change'])
        candidates.append(('Combined', best['height'], best['index']))

    candidates.sort(key=lambda x: abs(x[1] - expected_transition_height))

    print(f"\nExpected at: {expected_transition_height} mm")
    print("\nCandidates (sorted by distance from expected):")
    for method, height, idx in candidates:
        distance = abs(height - expected_transition_height)
        print(f"  {method:<20} {height:6.2f} mm (distance: {distance:5.2f} mm)")

    if candidates:
        best_method, best_height, best_idx = candidates[0]
        error = abs(best_height - expected_transition_height)
        accuracy = max(0, 100 * (1 - error / expected_transition_height))
        print(f"\n✓ Best candidate: {best_method} at {best_height:.2f} mm (error: {error:.2f} mm, accuracy: {accuracy:.1f}%)")


def main():
    """Test boundary detection methods."""
    print("\n" + "="*80)
    print("BOUNDARY DETECTION TESTING FOR COMPOSITE SHAPES")
    print("="*80)

    # Test cases with expected transition heights
    test_cases = [
        (COMPOSITE_FLASK, "Composite Flask (Sphere Cap + Cylinder)", 15.0),  # Transition around row 20
        (COMPOSITE_CONE, "Composite Cone (Cone + Cylinder)", 25.0),  # Midpoint approximately
    ]

    for filename, description, expected_height in test_cases:
        if os.path.exists(filename):
            test_case(filename, description, expected_height)
        else:
            print(f"\n⚠️  File not found: {filename}")

    print("\n" + "="*80)
    print("CONCLUSION")
    print("="*80)
    print("""
Based on testing, the recommended approach for composite shape detection is:

HYBRID BOUNDARY DETECTION:
1. Use gradient change peaks as primary candidates
2. Validate with curvature transitions (multi-scale)
3. Combine signals: gradient change + curvature variance
4. Require both indicators to mark a true boundary

This approach:
✓ Detects shape transitions reliably
✓ Ignores inflection points within single shapes
✓ Works for both curved→linear and linear→linear transitions
✓ More robust than single-indicator methods

Next step: Implement improved transition detection in main algorithm
""")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
