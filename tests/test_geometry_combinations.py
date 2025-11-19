"""
Test script for geometry combination detection
Generates synthetic container data with various geometry combinations
and evaluates how well the algorithm detects them.
"""

import numpy as np
import pandas as pd
import sys
import os
from pathlib import Path
import tempfile
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container_geometry_analyzer_gui_v3_11_8 import (
    compute_areas,
    find_optimal_transitions_improved,
    segment_and_fit_optimized,
    DEFAULT_PARAMS
)

# ============================================================================
# GEOMETRIC VOLUME CALCULATIONS
# ============================================================================

def sphere_cap_volume(h, R):
    """
    Volume of a spherical cap
    h: height of cap
    R: radius of sphere
    Returns: volume
    """
    return (np.pi * h**2 / 3) * (3*R - h)

def sphere_cap_area(h, R):
    """Cross-sectional area at height h in a spherical cap (hemisphere in container)"""
    # For a sphere of radius R, at height h from bottom, radius is:
    r = np.sqrt(R**2 - (R - h)**2)
    return np.pi * r**2

def frustum_volume(h1, h2, r1, r2):
    """
    Volume of a frustum between heights h1 and h2
    r1: radius at h1 (bottom)
    r2: radius at h2 (top)
    """
    h = h2 - h1
    return (np.pi * h / 3) * (r1**2 + r1*r2 + r2**2)

def frustum_area(h, r1_bottom, r2_top, h_start):
    """Cross-sectional area at height h in a frustum"""
    # Linear interpolation of radius
    r = r1_bottom + (r2_top - r1_bottom) * (h - h_start) / (1.0)  # Assuming unit height range
    return np.pi * r**2

def cylinder_volume(h1, h2, r):
    """Volume of a cylinder"""
    return np.pi * r**2 * (h2 - h1)

def cylinder_area(r):
    """Cross-sectional area of a cylinder"""
    return np.pi * r**2

def cone_volume(h1, h2, r1, r2):
    """Volume of a cone (frustum where one radius = 0)"""
    # For a cone with apex at top, r2=0
    h = h2 - h1
    return (np.pi * h / 3) * r1**2

def cone_area(h, r1_bottom, h_start, h_end):
    """Cross-sectional area at height h in a cone"""
    # Linear interpolation from r1_bottom to 0
    r = r1_bottom * (1 - (h - h_start) / (h_end - h_start))
    return np.pi * r**2

# ============================================================================
# COMPOSITE CONTAINER BUILDERS
# ============================================================================

def build_sphere_frustum_cylinder(bottom_sphere_r, frustum_r1, frustum_r2, cylinder_r, n_points=100):
    """
    Build a container with: sphere (bottom) + frustum + cylinder (top)
    All segments must fit smoothly together.
    """
    heights = []
    volumes = []

    # 1. Sphere cap (hemisphere, bottom)
    h_sphere = bottom_sphere_r  # Full hemisphere height
    sphere_points = int(n_points * 0.3)
    h_sphere_vals = np.linspace(0, h_sphere, sphere_points)

    current_volume = 0
    for h in h_sphere_vals:
        current_volume += sphere_cap_volume(h, bottom_sphere_r)
        heights.append(h)
        volumes.append(current_volume)

    # 2. Frustum (middle) - must connect smoothly
    h_frustum_start = h_sphere
    h_frustum_end = h_frustum_start + 10  # 10mm frustum
    frustum_points = int(n_points * 0.35)
    h_frustum_vals = np.linspace(h_frustum_start, h_frustum_end, frustum_points)[1:]

    for h in h_frustum_vals:
        dh = h - h_frustum_start
        h_range = h_frustum_end - h_frustum_start
        frac = dh / h_range
        current_volume += frustum_volume(h - (h_frustum_vals[0] - h_frustum_start if len(heights) > 0 else 0),
                                        h,
                                        frustum_r1,
                                        frustum_r1 + (frustum_r2 - frustum_r1) * frac)
        heights.append(h)
        volumes.append(current_volume)

    # 3. Cylinder (top) - must connect to frustum_r2
    h_cyl_start = h_frustum_end
    h_cyl_end = h_cyl_start + 8  # 8mm cylinder
    cyl_points = int(n_points * 0.35)
    h_cyl_vals = np.linspace(h_cyl_start, h_cyl_end, cyl_points)[1:]

    for h in h_cyl_vals:
        current_volume += cylinder_volume(h - (h_cyl_vals[0] - h_cyl_start),
                                         h,
                                         cylinder_r)
        heights.append(h)
        volumes.append(current_volume)

    return np.array(heights), np.array(volumes)

def build_frustum_cylinder(frustum_r1, frustum_r2, cylinder_r, n_points=100):
    """Build a container with: frustum (bottom) + cylinder (top)"""
    heights = []
    volumes = []

    # Important: frustum must end with frustum_r2 == cylinder_r for smooth transition
    # Ensure cylinder_r is set correctly
    actual_cyl_r = frustum_r2  # Cylinder radius must match frustum top

    # 1. Frustum
    h_frustum_start = 0.0
    h_frustum_end = 10.0
    frustum_points = int(n_points * 0.5)
    h_frustum_vals = np.linspace(h_frustum_start, h_frustum_end, frustum_points)

    current_volume = 0.0
    for i, h in enumerate(h_frustum_vals):
        if i == 0:
            heights.append(h)
            volumes.append(current_volume)
            continue

        frac = (h - h_frustum_start) / (h_frustum_end - h_frustum_start)
        r = frustum_r1 + (frustum_r2 - frustum_r1) * frac
        r_prev = frustum_r1 + (frustum_r2 - frustum_r1) * ((h_frustum_vals[i-1] - h_frustum_start) / (h_frustum_end - h_frustum_start))
        dh = h - h_frustum_vals[i-1]
        current_volume += (np.pi * dh / 3) * (r_prev**2 + r_prev*r + r**2)
        heights.append(h)
        volumes.append(current_volume)

    # 2. Cylinder (must connect to frustum_r2)
    h_cyl_start = h_frustum_end
    h_cyl_end = h_cyl_start + 8.0
    cyl_points = int(n_points * 0.5)
    h_cyl_vals = np.linspace(h_cyl_start, h_cyl_end, cyl_points)[1:]

    for i, h in enumerate(h_cyl_vals):
        dh = h - h_cyl_vals[max(0, i-1)] if i > 0 else h - h_cyl_start
        current_volume += np.pi * actual_cyl_r**2 * dh
        heights.append(h)
        volumes.append(current_volume)

    return np.array(heights), np.array(volumes)

def build_cone_frustum_cylinder(cone_r, frustum_r2, cylinder_r, n_points=100):
    """Build a container with: cone (bottom) + frustum (middle) + cylinder (top)"""
    heights = []
    volumes = []

    # Ensure proper radius continuity
    frustum_r1 = cone_r  # Frustum must start at cone_r
    actual_cyl_r = frustum_r2  # Cylinder must match frustum top

    # 1. Cone (apex at bottom, opens upward)
    h_cone_start = 0.0
    h_cone_end = 8.0
    cone_points = int(n_points * 0.33)
    h_cone_vals = np.linspace(h_cone_start, h_cone_end, cone_points)

    current_volume = 0.0
    cone_apex_r = cone_r  # radius at top of cone

    for i, h in enumerate(h_cone_vals):
        if i == 0:
            heights.append(h)
            volumes.append(current_volume)
            continue
        # Linear radius: 0 at bottom, cone_r at top
        frac = (h - h_cone_start) / (h_cone_end - h_cone_start)
        r = cone_apex_r * frac
        r_prev = cone_apex_r * ((h_cone_vals[i-1] - h_cone_start) / (h_cone_end - h_cone_start))
        dh = h - h_cone_vals[i-1]
        current_volume += (np.pi * dh / 3) * (r_prev**2 + r_prev*r + r**2)
        heights.append(h)
        volumes.append(current_volume)

    # 2. Frustum (connects cone_r to frustum_r2)
    h_frustum_start = h_cone_end
    h_frustum_end = h_frustum_start + 6.0
    frustum_points = int(n_points * 0.33)
    h_frustum_vals = np.linspace(h_frustum_start, h_frustum_end, frustum_points)[1:]

    for i, h in enumerate(h_frustum_vals):
        frac = (h - h_frustum_start) / (h_frustum_end - h_frustum_start)
        r = frustum_r1 + (frustum_r2 - frustum_r1) * frac
        r_prev = frustum_r1 + (frustum_r2 - frustum_r1) * ((h_frustum_vals[i-1] - h_frustum_start) / (h_frustum_end - h_frustum_start)) if i > 0 else frustum_r1
        dh = h - (h_frustum_vals[i-1] if i > 0 else h_frustum_start)
        current_volume += (np.pi * dh / 3) * (r_prev**2 + r_prev*r + r**2)
        heights.append(h)
        volumes.append(current_volume)

    # 3. Cylinder (must match frustum_r2)
    h_cyl_start = h_frustum_end
    h_cyl_end = h_cyl_start + 8.0
    cyl_points = int(n_points * 0.34)
    h_cyl_vals = np.linspace(h_cyl_start, h_cyl_end, cyl_points)[1:]

    for i, h in enumerate(h_cyl_vals):
        dh = h - (h_cyl_vals[i-1] if i > 0 else h_cyl_start)
        current_volume += np.pi * actual_cyl_r**2 * dh
        heights.append(h)
        volumes.append(current_volume)

    return np.array(heights), np.array(volumes)

def build_semisphere_cylinder(sphere_r, cylinder_r, n_points=100):
    """Build a container with: semisphere (bottom) + cylinder (top)

    A semisphere is a complete hemisphere (height = radius).
    Provides a more practical test case than full sphere cap.
    """
    heights = []
    volumes = []

    # Semisphere: height from 0 to sphere_r (full hemisphere)
    h_semi_start = 0.0
    h_semi_end = sphere_r  # Hemisphere has height equal to radius
    semi_points = int(n_points * 0.5)
    h_semi_vals = np.linspace(h_semi_start, h_semi_end, semi_points)

    current_volume = 0.0

    for i, h in enumerate(h_semi_vals):
        if i == 0:
            heights.append(h)
            volumes.append(current_volume)
            continue

        # Sphere cap volume formula: V = π*h²/3 * (3R - h)
        # At height h, volume from apex
        r_at_h = np.sqrt(sphere_r**2 - (sphere_r - h)**2)  # radius at this height
        r_prev = np.sqrt(sphere_r**2 - (sphere_r - h_semi_vals[i-1])**2)

        # Use small segment volume approximation
        dh = h - h_semi_vals[i-1]
        # Average of the two cross-sectional areas times height
        area_curr = np.pi * r_at_h**2
        area_prev = np.pi * r_prev**2
        current_volume += (area_curr + area_prev) / 2 * dh

        heights.append(h)
        volumes.append(current_volume)

    # Cylinder: must connect to sphere_r (the cylinder radius at top of hemisphere)
    h_cyl_start = h_semi_end
    h_cyl_end = h_cyl_start + 10.0  # 10mm cylinder height
    cyl_points = int(n_points * 0.5)
    h_cyl_vals = np.linspace(h_cyl_start, h_cyl_end, cyl_points)[1:]

    for i, h in enumerate(h_cyl_vals):
        dh = h - (h_cyl_vals[i-1] if i > 0 else h_cyl_start)
        current_volume += np.pi * cylinder_r**2 * dh
        heights.append(h)
        volumes.append(current_volume)

    return np.array(heights), np.array(volumes)

# ============================================================================
# TEST RUNNER
# ============================================================================

def add_realistic_noise(volumes, noise_level=0.01):
    """Add realistic measurement noise to volume data"""
    noise = np.random.normal(0, noise_level * np.mean(volumes), len(volumes))
    return volumes + np.abs(noise)

def run_analysis(heights, volumes, combo_name, cyl_radius, show_debug=False):
    """Run analysis on synthetic data and return results"""

    # Create DataFrame (convert ml to mm3: 1 ml = 1000 mm3)
    df = pd.DataFrame({
        'Height_mm': heights,
        'Volume_mm3': volumes * 1000  # Convert mL to mm3
    })

    # Compute areas
    df_areas = compute_areas(df, verbose=False)

    # Show transition detection info if debug enabled
    if show_debug:
        area = df_areas['Area'].values
        print(f"      Area range: {area.min():.2f} - {area.max():.2f}")
        print(f"      Area range span: {area.max() - area.min():.2f}")
        print(f"      Num points: {len(area)}")

    # Segment and fit (internally calls find_optimal_transitions_improved)
    segments = segment_and_fit_optimized(df_areas, verbose=False)

    # Extract results
    detected_shapes = [seg[2] for seg in segments]
    fit_errors = []

    # Compute fit errors for diagnostics
    for start_idx, end_idx, shape, params in segments:
        h_start = df.iloc[start_idx]['Height_mm']
        h_end = df.iloc[end_idx]['Height_mm']
        v_start = df.iloc[start_idx]['Volume_mm3']
        v_end = df.iloc[end_idx]['Volume_mm3']

        fit_errors.append({
            'shape': shape,
            'h_start': h_start,
            'h_end': h_end,
            'height_range': h_end - h_start,
            'volume_range': v_end - v_start,
            'num_points': end_idx - start_idx + 1
        })

    return {
        'combo': combo_name,
        'cyl_radius': cyl_radius,
        'segments': segments,
        'detected_shapes': detected_shapes,
        'num_segments': len(segments),
        'fit_errors': fit_errors
    }

# ============================================================================
# MAIN TEST EXECUTION
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*80)
    print("GEOMETRY COMBINATION TEST SUITE")
    print("="*80)

    # Test combinations
    results = []

    cylinder_diameters = [10, 12, 14, 16]  # mm

    for cyl_d in cylinder_diameters:
        cyl_r = cyl_d / 2

        print(f"\n{'='*80}")
        print(f"Testing with Upper Cylinder Diameter = {cyl_d} mm (radius = {cyl_r} mm)")
        print(f"{'='*80}")

        # Test 1: Sphere + Frustum + Cylinder
        print("\n[1/4] Building: Sphere (bottom) + Frustum (middle) + Cylinder (top)")
        frustum_r1 = cyl_r + 1.5  # Bottom of frustum wider than top cylinder
        frustum_r2 = cyl_r        # Top of frustum matches cylinder
        sphere_r = 5.0

        try:
            h, v = build_sphere_frustum_cylinder(sphere_r, frustum_r1, frustum_r2, cyl_r, n_points=120)
            v = add_realistic_noise(v, noise_level=0.005)
            result = run_analysis(h, v, f"Sphere+Frustum+Cylinder(d={cyl_d})", cyl_d)
            results.append(result)
            print(f"    ✓ Detected {result['num_segments']} segments: {result['detected_shapes']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results.append({
                'combo': f"Sphere+Frustum+Cylinder(d={cyl_d})",
                'cyl_radius': cyl_r,
                'error': str(e)
            })

        # Test 2: Frustum + Cylinder
        print("\n[2/4] Building: Frustum (bottom) + Cylinder (top)")
        frustum_r1 = cyl_r + 1.0
        frustum_r2 = cyl_r

        try:
            h, v = build_frustum_cylinder(frustum_r1, frustum_r2, cyl_r, n_points=120)
            v = add_realistic_noise(v, noise_level=0.005)
            result = run_analysis(h, v, f"Frustum+Cylinder(d={cyl_d})", cyl_d)
            results.append(result)
            print(f"    ✓ Detected {result['num_segments']} segments: {result['detected_shapes']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results.append({
                'combo': f"Frustum+Cylinder(d={cyl_d})",
                'cyl_radius': cyl_r,
                'error': str(e)
            })

        # Test 3: Cone + Frustum + Cylinder
        print("\n[3/4] Building: Cone (bottom) + Frustum (middle) + Cylinder (top)")
        cone_r = 3.0  # Apex radius
        frustum_r2 = cyl_r

        try:
            h, v = build_cone_frustum_cylinder(cone_r, frustum_r2, cyl_r, n_points=120)
            v = add_realistic_noise(v, noise_level=0.005)
            result = run_analysis(h, v, f"Cone+Frustum+Cylinder(d={cyl_d})", cyl_d)
            results.append(result)
            print(f"    ✓ Detected {result['num_segments']} segments: {result['detected_shapes']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results.append({
                'combo': f"Cone+Frustum+Cylinder(d={cyl_d})",
                'cyl_radius': cyl_r,
                'error': str(e)
            })

        # Test 4: Semisphere + Cylinder
        print("\n[4/4] Building: Semisphere (bottom) + Cylinder (top)")
        sphere_r = cyl_r  # Hemisphere radius matches cylinder radius

        try:
            h, v = build_semisphere_cylinder(sphere_r, cyl_r, n_points=120)
            v = add_realistic_noise(v, noise_level=0.005)
            result = run_analysis(h, v, f"Semisphere+Cylinder(d={cyl_d})", cyl_d)
            results.append(result)
            print(f"    ✓ Detected {result['num_segments']} segments: {result['detected_shapes']}")
        except Exception as e:
            print(f"    ✗ Error: {e}")
            results.append({
                'combo': f"Semisphere+Cylinder(d={cyl_d})",
                'cyl_radius': cyl_r,
                'error': str(e)
            })

    # ========================================================================
    # SUMMARY AND EVALUATION
    # ========================================================================

    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    print("\nDetection Accuracy by Combination:")
    print("-" * 80)

    for result in results:
        if 'error' in result:
            print(f"{result['combo']:<50} ERROR: {result['error']}")
        else:
            combo_name = result['combo'].split('(')[0]
            expected_count = combo_name.count('+') + 1
            detected_count = result['num_segments']
            detected_shapes_str = ', '.join(result['detected_shapes'])

            status = "✓" if detected_count == expected_count else "✗"
            print(f"{result['combo']:<50} {status} {detected_count}/{expected_count} segments: [{detected_shapes_str}]")

    print("\n" + "="*80)
    print("DETAILED ANALYSIS")
    print("="*80)

    # Group by combination type
    combo_types = {}
    for result in results:
        if 'error' not in result:
            combo_type = result['combo'].split('(')[0]
            if combo_type not in combo_types:
                combo_types[combo_type] = []
            combo_types[combo_type].append(result)

    for combo_type, combo_results in sorted(combo_types.items()):
        print(f"\n{combo_type}:")
        print("-" * 80)

        total_tests = len(combo_results)
        correct_detections = sum(1 for r in combo_results if r['num_segments'] == combo_type.count('+') + 1)

        print(f"  Detection Rate: {correct_detections}/{total_tests} ({100*correct_detections//total_tests}%)")

        for result in combo_results:
            expected_count = combo_type.count('+') + 1
            detected_count = result['num_segments']
            match = "✓" if detected_count == expected_count else "✗"
            print(f"    {match} d={result['cyl_radius']*2:.0f}mm: {detected_count} segments detected")

    print("\n" + "="*80)
    print("RECOMMENDATIONS FOR ALGORITHM IMPROVEMENT")
    print("="*80)

    # Analyze failure patterns
    failures = [r for r in results if 'error' not in r and r['num_segments'] != len(r['combo'].split('(')[0].split('+'))]

    if failures:
        print("\n❌ FAILURES DETECTED:")
        for failure in failures:
            combo_type = failure['combo'].split('(')[0]
            expected = combo_type.count('+') + 1
            detected = failure['num_segments']
            print(f"\n  {failure['combo']}")
            print(f"    Expected: {expected} segments")
            print(f"    Detected: {detected} segments ({failure['detected_shapes']})")
            print(f"    Issue: {'Under-segmentation' if detected < expected else 'Over-segmentation'}")
    else:
        print("\n✓ All tests passed! All combinations detected correctly.")

    print("\n" + "="*80)
