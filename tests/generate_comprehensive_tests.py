#!/usr/bin/env python3
"""
Comprehensive Test Data Generator with Pipetting Error
=======================================================

Generates comprehensive test cases including:
- All segment combinations (1, 2, 3 segments per tube)
- Realistic 2% pipetting error added to volume data
- Full diameter range (5mm to 17mm)
- Multiple container types (cylinder, cone, sphere, frustum)

Testing matrix:
- 5 tube types × 3 diameters × 3 segment combinations = 45 base cases
- Each case tested with ideal data AND 2% pipetting error = 90 total tests
"""

import os
import sys
import numpy as np
import pandas as pd
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Shape volume functions
def volume_cylinder(h, R):
    """Cylinder: V = πR²h"""
    return np.pi * R**2 * h

def volume_cone(h, R, H):
    """Cone with apex at origin: V = (1/3)πR²h"""
    return (1/3) * np.pi * (R * h / H)**2 * h

def volume_sphere_cap(h, R):
    """Sphere cap: V = πh²(3R - h)/3"""
    return np.pi * h**2 * (3*R - h) / 3

def volume_frustum(h, r1, r2, H):
    """Frustum (truncated cone): V = (1/3)πh(r1² + r1*r2 + r2²)"""
    return (1/3) * np.pi * h * (r1**2 + r1*r2 + r2**2)

def add_pipetting_error(volume, error_percent=2.0):
    """Add realistic pipetting error (percentage of volume)"""
    # Pipetting error is typically gaussian noise
    error = np.random.normal(0, error_percent/100)
    return volume * (1 + error)

def generate_single_shape(shape_type, diameter_mm, height_mm, num_points=80, error_percent=0):
    """Generate single shape test case"""
    heights = np.linspace(0.1, height_mm, num_points)
    radius = diameter_mm / 2

    if shape_type == 'cylinder':
        volumes = volume_cylinder(heights, radius)
    elif shape_type == 'cone':
        volumes = volume_cone(heights, radius, height_mm)
    elif shape_type == 'sphere_cap':
        # Sphere cap with height = diameter
        R_sphere = radius
        volumes = volume_sphere_cap(np.minimum(heights, diameter_mm), R_sphere)
    elif shape_type == 'frustum':
        r1_start = radius * 0.5  # Start with 50% of final radius
        r2_end = radius
        volumes = volume_frustum(heights, r1_start + (r2_end - r1_start) * heights/height_mm, r1_start, height_mm)
    else:
        raise ValueError(f"Unknown shape: {shape_type}")

    # Add pipetting error if requested
    if error_percent > 0:
        np.random.seed(None)  # Different error each time
        volumes = np.array([add_pipetting_error(v, error_percent) for v in volumes])

    return heights, volumes

def generate_composite_shape(shapes, diameters, heights, num_points=80, error_percent=0):
    """Generate composite shape (multiple segments)"""
    total_height = sum(heights)
    all_heights = []
    all_volumes = []
    current_height = 0

    # Generate each segment
    for shape_type, diameter_mm, segment_height in zip(shapes, diameters, heights):
        h, v = generate_single_shape(shape_type, diameter_mm, segment_height, num_points//len(shapes), error_percent)

        # Shift to correct position and add cumulative volume from previous segments
        h_shifted = h + current_height
        if len(all_volumes) > 0:
            v_shifted = v + all_volumes[-1]
        else:
            v_shifted = v

        all_heights.append(h_shifted)
        all_volumes.append(v_shifted)
        current_height += segment_height

    # Combine all segments
    heights_combined = np.concatenate(all_heights)
    volumes_combined = np.concatenate(all_volumes)

    return heights_combined, volumes_combined

def save_test_case(filename, heights, volumes, description, expected_segments, expected_shapes):
    """Save test case to CSV"""
    df = pd.DataFrame({
        'Height_mm': heights,
        'Volume_ml': volumes
    })
    df.to_csv(filename, index=False)

    return {
        'file': filename,
        'description': description,
        'expected_segments': expected_segments,
        'expected_shapes': expected_shapes,
        'data_points': len(heights),
        'height_range': (float(heights[0]), float(heights[-1])),
        'volume_range': (float(volumes[0]), float(volumes[-1]))
    }

def main():
    """Generate comprehensive test suite"""
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST DATA GENERATION")
    print("="*80)

    test_data_dir = Path('test_data_comprehensive')
    test_data_dir.mkdir(exist_ok=True)

    metadata = {
        'generated': str(pd.Timestamp.now()),
        'error_scenarios': ['ideal', '2_percent_pipetting_error'],
        'tube_types': ['cylinder', 'cone', 'sphere_cap', 'frustum'],
        'segment_combinations': [1, 2, 3],
        'diameter_range_mm': [5, 10, 15],
        'test_cases': []
    }

    test_count = 0

    # Test matrix
    tube_types = ['cylinder', 'cone', 'sphere_cap', 'frustum']
    diameters = [5, 10, 15]  # Small, medium, large
    error_scenarios = [0, 2]  # Ideal and 2% pipetting error

    print(f"\nGenerating test cases...")
    print(f"Tube types: {len(tube_types)}")
    print(f"Diameters: {len(diameters)} ({diameters[0]}, {diameters[1]}, {diameters[2]}mm)")
    print(f"Error scenarios: {len(error_scenarios)} (ideal, 2% pipetting error)")

    # 1-SEGMENT CASES (Single cylinder, cone, etc.)
    print("\n1-SEGMENT CASES:")
    for tube_type in tube_types:
        for diameter in diameters:
            for error in error_scenarios:
                error_label = "_ideal" if error == 0 else "_2pct_error"
                filename = test_data_dir / f"{tube_type}_{diameter}mm{error_label}.csv"

                h, v = generate_single_shape(tube_type, diameter, height_mm=50, num_points=80, error_percent=error)

                meta = save_test_case(
                    str(filename),
                    h, v,
                    f"Single {tube_type}, {diameter}mm, {50}mm height, {error}% error",
                    expected_segments=1,
                    expected_shapes=[tube_type]
                )
                metadata['test_cases'].append(meta)
                test_count += 1
                print(f"  ✓ {filename.name}")

    # 2-SEGMENT CASES (Composites)
    print("\n2-SEGMENT CASES:")
    two_segment_combos = [
        (['cone', 'cylinder'], [10, 10], [25, 25]),
        (['sphere_cap', 'cylinder'], [10, 10], [25, 25]),
        (['frustum', 'cylinder'], [10, 10], [25, 25]),
        (['cone', 'frustum'], [10, 10], [25, 25]),
    ]

    for idx, (shapes, diameters_combo, heights_combo) in enumerate(two_segment_combos):
        for diameter_scale in [0.5, 1.0, 1.5]:  # Small, medium, large
            scaled_diameters = [d * diameter_scale for d in diameters_combo]

            for error in error_scenarios:
                error_label = "_ideal" if error == 0 else "_2pct_error"
                shape_names = '-'.join(shapes)
                scaled_dia_label = f"_{scaled_diameters[0]:.0f}mm"
                filename = test_data_dir / f"composite_{shape_names}{scaled_dia_label}{error_label}.csv"

                h, v = generate_composite_shape(shapes, scaled_diameters, heights_combo, error_percent=error)

                meta = save_test_case(
                    str(filename),
                    h, v,
                    f"Composite {shape_names}, {scaled_diameters[0]:.0f}mm, {error}% error",
                    expected_segments=2,
                    expected_shapes=shapes
                )
                metadata['test_cases'].append(meta)
                test_count += 1
                print(f"  ✓ {filename.name}")

    # 3-SEGMENT CASES
    print("\n3-SEGMENT CASES:")
    three_segment_combos = [
        (['cone', 'cylinder', 'frustum'], [10, 10, 10], [20, 20, 20]),
        (['sphere_cap', 'cylinder', 'cone'], [10, 10, 10], [20, 20, 20]),
    ]

    for idx, (shapes, diameters_combo, heights_combo) in enumerate(three_segment_combos):
        for diameter_scale in [0.75, 1.0]:  # Small/medium, medium
            scaled_diameters = [d * diameter_scale for d in diameters_combo]

            for error in error_scenarios:
                error_label = "_ideal" if error == 0 else "_2pct_error"
                shape_names = '-'.join(shapes)
                scaled_dia_label = f"_{scaled_diameters[0]:.0f}mm"
                filename = test_data_dir / f"composite3_{shape_names}{scaled_dia_label}{error_label}.csv"

                h, v = generate_composite_shape(shapes, scaled_diameters, heights_combo, error_percent=error)

                meta = save_test_case(
                    str(filename),
                    h, v,
                    f"Composite {shape_names}, {scaled_diameters[0]:.0f}mm, {error}% error",
                    expected_segments=3,
                    expected_shapes=shapes
                )
                metadata['test_cases'].append(meta)
                test_count += 1
                print(f"  ✓ {filename.name}")

    # Save metadata
    metadata_file = test_data_dir / 'comprehensive_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "="*80)
    print("GENERATION COMPLETE")
    print("="*80)
    print(f"Total test cases generated: {test_count}")
    print(f"Test data directory: {test_data_dir}")
    print(f"Metadata saved to: {metadata_file}")
    print("\nTest breakdown:")
    print(f"  1-segment cases: {len(tube_types) * len(diameters) * len(error_scenarios)} "
          f"(4 types × 3 diameters × 2 error scenarios)")
    print(f"  2-segment cases: {len(two_segment_combos) * 3 * len(error_scenarios)} "
          f"(4 combos × 3 scales × 2 error scenarios)")
    print(f"  3-segment cases: {len(three_segment_combos) * 2 * len(error_scenarios)} "
          f"(2 combos × 2 scales × 2 error scenarios)")
    print(f"  TOTAL: {test_count} test cases")

    print("\n" + "="*80)

if __name__ == '__main__':
    main()
