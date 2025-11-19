"""
Generate Synthetic Test Data for Container Geometry Analyzer
=============================================================

Creates realistic container data with various geometries, diameters,
and height ranges for testing algorithm improvements.

Author: Container Geometry Analyzer Team
Date: 2025-11-19
"""

import numpy as np
import pandas as pd
import os


def add_measurement_noise(values, noise_level=0.02):
    """Add realistic measurement noise (default 2%)."""
    noise = np.random.normal(0, noise_level * np.mean(values), len(values))
    return values + noise


def generate_cylinder(r, h_min, h_max, n_points=50, noise_level=0.02):
    """
    Generate data for a simple cylinder.

    Parameters:
    -----------
    r : float
        Radius in mm
    h_min, h_max : float
        Height range in mm
    n_points : int
        Number of measurement points
    noise_level : float
        Measurement noise as fraction of signal

    Returns:
    --------
    DataFrame with Height_mm and Volume_ml columns
    """
    heights = np.linspace(h_min, h_max, n_points)
    volumes_mm3 = np.pi * r**2 * heights
    volumes_ml = volumes_mm3 / 1000

    # Add noise
    volumes_ml = add_measurement_noise(volumes_ml, noise_level)
    volumes_ml = np.maximum.accumulate(volumes_ml)  # Ensure monotonic

    return pd.DataFrame({
        'Height_mm': heights,
        'Volume_ml': volumes_ml
    })


def generate_cone(r_base, h_total, n_points=50, noise_level=0.02):
    """
    Generate data for a cone (apex at bottom).

    V(h) = (π/3) * h * (r_base * h/H)²
    """
    heights = np.linspace(0.1, h_total, n_points)
    r_at_h = r_base * (heights / h_total)
    volumes_mm3 = (np.pi / 3) * heights * r_at_h**2
    volumes_ml = volumes_mm3 / 1000

    volumes_ml = add_measurement_noise(volumes_ml, noise_level)
    volumes_ml = np.maximum.accumulate(volumes_ml)

    return pd.DataFrame({
        'Height_mm': heights,
        'Volume_ml': volumes_ml
    })


def generate_sphere_cap(R, h_max, n_points=50, noise_level=0.02):
    """
    Generate data for a spherical cap (rounded bottom).

    V(h) = πh²(3R - h)/3
    """
    h_max = min(h_max, 2*R)  # Cap at hemisphere
    heights = np.linspace(0.1, h_max, n_points)
    volumes_mm3 = (np.pi * heights**2 * (3*R - heights)) / 3
    volumes_ml = volumes_mm3 / 1000

    volumes_ml = add_measurement_noise(volumes_ml, noise_level)
    volumes_ml = np.maximum.accumulate(volumes_ml)

    return pd.DataFrame({
        'Height_mm': heights,
        'Volume_ml': volumes_ml
    })


def generate_frustum(r1, r2, h_total, n_points=50, noise_level=0.02):
    """
    Generate data for a frustum (truncated cone).

    Linear taper from r1 (bottom) to r2 (top).
    """
    heights = np.linspace(0, h_total, n_points)
    volumes_mm3 = np.zeros_like(heights)

    for i, h in enumerate(heights):
        if h == 0:
            volumes_mm3[i] = 0
        else:
            r_h = r1 + (r2 - r1) * (h / h_total)
            # Volume of frustum from 0 to h
            volumes_mm3[i] = (np.pi * h / 3) * (r1**2 + r_h**2 + r1 * r_h)

    volumes_ml = volumes_mm3 / 1000
    volumes_ml = add_measurement_noise(volumes_ml, noise_level)
    volumes_ml = np.maximum.accumulate(volumes_ml)

    return pd.DataFrame({
        'Height_mm': heights,
        'Volume_ml': volumes_ml
    })


def generate_composite_sphere_cylinder(R_sphere, r_cyl, h_sphere, h_cyl,
                                       n_points=80, noise_level=0.02):
    """
    Generate data for sphere cap bottom + cylindrical body.
    Common in flasks and vials.
    """
    # Sphere cap portion
    n_sphere = int(n_points * h_sphere / (h_sphere + h_cyl))
    df_sphere = generate_sphere_cap(R_sphere, h_sphere, n_sphere, noise_level=0)

    # Cylinder portion
    n_cyl = n_points - n_sphere
    h_cyl_start = h_sphere
    h_cyl_end = h_sphere + h_cyl
    heights_cyl = np.linspace(h_cyl_start, h_cyl_end, n_cyl)

    # Volume at top of sphere cap
    v_sphere_top = df_sphere['Volume_ml'].iloc[-1]
    v_sphere_top_mm3 = v_sphere_top * 1000

    # Add cylindrical volume
    volumes_cyl_mm3 = v_sphere_top_mm3 + np.pi * r_cyl**2 * (heights_cyl - h_cyl_start)
    volumes_cyl_ml = volumes_cyl_mm3 / 1000

    df_cyl = pd.DataFrame({
        'Height_mm': heights_cyl,
        'Volume_ml': volumes_cyl_ml
    })

    # Combine
    df = pd.concat([df_sphere, df_cyl], ignore_index=True)
    df['Volume_ml'] = add_measurement_noise(df['Volume_ml'].values, noise_level)
    df['Volume_ml'] = np.maximum.accumulate(df['Volume_ml'])

    return df


def generate_composite_cone_cylinder(r_cone, h_cone, r_cyl, h_cyl,
                                     n_points=80, noise_level=0.02):
    """
    Generate data for conical tip + cylindrical body.
    Common in centrifuge tubes and pipette tips.
    """
    # Cone portion
    n_cone = int(n_points * h_cone / (h_cone + h_cyl))
    df_cone = generate_cone(r_cone, h_cone, n_cone, noise_level=0)

    # Cylinder portion
    n_cyl = n_points - n_cone
    h_cyl_start = h_cone
    h_cyl_end = h_cone + h_cyl
    heights_cyl = np.linspace(h_cyl_start, h_cyl_end, n_cyl)

    # Volume at top of cone
    v_cone_top = df_cone['Volume_ml'].iloc[-1]
    v_cone_top_mm3 = v_cone_top * 1000

    # Add cylindrical volume
    volumes_cyl_mm3 = v_cone_top_mm3 + np.pi * r_cyl**2 * (heights_cyl - h_cyl_start)
    volumes_cyl_ml = volumes_cyl_mm3 / 1000

    df_cyl = pd.DataFrame({
        'Height_mm': heights_cyl,
        'Volume_ml': volumes_cyl_ml
    })

    # Combine
    df = pd.concat([df_cone, df_cyl], ignore_index=True)
    df['Volume_ml'] = add_measurement_noise(df['Volume_ml'].values, noise_level)
    df['Volume_ml'] = np.maximum.accumulate(df['Volume_ml'])

    return df


def generate_test_suite():
    """
    Generate comprehensive test suite with various container geometries.

    Returns dictionary of test cases with metadata.
    """
    test_cases = {}

    # ========== SIMPLE CYLINDERS ==========

    # Small diameter cylinder (1ml microcentrifuge tube)
    test_cases['cylinder_small_5mm'] = {
        'data': generate_cylinder(r=2.5, h_min=0, h_max=40, n_points=50),
        'expected_shape': 'cylinder',
        'expected_segments': 1,
        'diameter_mm': 5.0,
        'height_range_mm': (0, 40),
        'volume_range_ml': (0, 0.785),
        'description': 'Small microcentrifuge tube (5mm diameter, 40mm height)'
    }

    # Medium diameter cylinder (15ml tube)
    test_cases['cylinder_medium_17mm'] = {
        'data': generate_cylinder(r=8.5, h_min=0, h_max=120, n_points=60),
        'expected_shape': 'cylinder',
        'expected_segments': 1,
        'diameter_mm': 17.0,
        'height_range_mm': (0, 120),
        'volume_range_ml': (0, 27.2),
        'description': 'Medium falcon tube (17mm diameter, 120mm height)'
    }

    # Large diameter cylinder (beaker)
    test_cases['cylinder_large_60mm'] = {
        'data': generate_cylinder(r=30, h_min=0, h_max=100, n_points=50),
        'expected_shape': 'cylinder',
        'expected_segments': 1,
        'diameter_mm': 60.0,
        'height_range_mm': (0, 100),
        'volume_range_ml': (0, 282.7),
        'description': 'Large beaker (60mm diameter, 100mm height)'
    }

    # ========== CONES ==========

    # Pipette tip (cone)
    test_cases['cone_pipette_tip'] = {
        'data': generate_cone(r_base=3, h_total=50, n_points=50),
        'expected_shape': 'cone',
        'expected_segments': 1,
        'diameter_mm': (0, 6.0),  # Apex to base
        'height_range_mm': (0, 50),
        'volume_range_ml': (0, 0.471),
        'description': 'Pipette tip (cone from 0 to 6mm, 50mm height)'
    }

    # Centrifuge tube tip (cone)
    test_cases['cone_centrifuge_tip'] = {
        'data': generate_cone(r_base=4, h_total=15, n_points=30),
        'expected_shape': 'cone',
        'expected_segments': 1,
        'diameter_mm': (0, 8.0),
        'height_range_mm': (0, 15),
        'volume_range_ml': (0, 0.251),
        'description': 'Centrifuge tube conical tip (8mm base, 15mm height)'
    }

    # ========== SPHERE CAPS ==========

    # Round bottom flask (hemisphere)
    test_cases['sphere_cap_flask_bottom'] = {
        'data': generate_sphere_cap(R=25, h_max=25, n_points=50),
        'expected_shape': 'sphere_cap',
        'expected_segments': 1,
        'diameter_mm': 50.0,
        'height_range_mm': (0, 25),
        'volume_range_ml': (0, 65.4),
        'description': 'Round bottom flask hemisphere (50mm diameter)'
    }

    # Vial rounded bottom (partial sphere cap)
    test_cases['sphere_cap_vial_bottom'] = {
        'data': generate_sphere_cap(R=6, h_max=8, n_points=40),
        'expected_shape': 'sphere_cap',
        'expected_segments': 1,
        'diameter_mm': 12.0,
        'height_range_mm': (0, 8),
        'volume_range_ml': (0, 1.34),
        'description': 'Vial rounded bottom (12mm diameter sphere, 8mm height)'
    }

    # ========== FRUSTUMS ==========

    # Expanding beaker (frustum)
    test_cases['frustum_expanding_beaker'] = {
        'data': generate_frustum(r1=15, r2=25, h_total=80, n_points=50),
        'expected_shape': 'frustum',
        'expected_segments': 1,
        'diameter_mm': (30, 50),  # 30mm bottom to 50mm top
        'height_range_mm': (0, 80),
        'volume_range_ml': (0, 117.8),
        'description': 'Expanding beaker (30mm bottom, 50mm top, 80mm height)'
    }

    # Narrow to wide tube
    test_cases['frustum_narrow_to_wide'] = {
        'data': generate_frustum(r1=5, r2=10, h_total=60, n_points=50),
        'expected_shape': 'frustum',
        'expected_segments': 1,
        'diameter_mm': (10, 20),
        'height_range_mm': (0, 60),
        'volume_range_ml': (0, 21.99),
        'description': 'Frustum tube (10mm to 20mm, 60mm height)'
    }

    # ========== COMPOSITE CONTAINERS ==========

    # Flask: Sphere bottom + Cylinder body
    test_cases['composite_flask_sphere_cylinder'] = {
        'data': generate_composite_sphere_cylinder(
            R_sphere=20, r_cyl=15, h_sphere=15, h_cyl=50, n_points=80
        ),
        'expected_shape': 'sphere_cap+cylinder',
        'expected_segments': 2,
        'diameter_mm': (30, 30),
        'height_range_mm': (0, 65),
        'volume_range_ml': (0, 47.5),
        'description': 'Flask with sphere bottom + cylinder body (15mm sphere, 30mm cyl, 65mm total)'
    }

    # Centrifuge tube: Cone tip + Cylinder body
    test_cases['composite_centrifuge_cone_cylinder'] = {
        'data': generate_composite_cone_cylinder(
            r_cone=5, h_cone=10, r_cyl=5, h_cyl=40, n_points=80
        ),
        'expected_shape': 'cone+cylinder',
        'expected_segments': 2,
        'diameter_mm': 10.0,
        'height_range_mm': (0, 50),
        'volume_range_ml': (0, 4.45),
        'description': 'Centrifuge tube with conical tip (10mm cone + 40mm cylinder)'
    }

    # Eppendorf tube: Cone + Cylinder + slight taper at top
    test_cases['composite_eppendorf_complex'] = {
        'data': pd.concat([
            generate_cone(r_base=4, h_total=8, n_points=20, noise_level=0),
            generate_cylinder(r=4, h_min=8, h_max=35, n_points=40, noise_level=0)
        ], ignore_index=True),
        'expected_shape': 'cone+cylinder',
        'expected_segments': 2,
        'diameter_mm': 8.0,
        'height_range_mm': (0, 35),
        'volume_range_ml': (0, 1.81),
        'description': 'Eppendorf-style tube (8mm cone + cylinder, 35mm total)'
    }

    # Combine volumes properly for eppendorf
    df_eppi = test_cases['composite_eppendorf_complex']['data']
    v_cone_end = df_eppi[df_eppi['Height_mm'] <= 8]['Volume_ml'].iloc[-1]
    df_eppi.loc[df_eppi['Height_mm'] > 8, 'Volume_ml'] += v_cone_end
    df_eppi['Volume_ml'] = add_measurement_noise(df_eppi['Volume_ml'].values, 0.02)
    df_eppi['Volume_ml'] = np.maximum.accumulate(df_eppi['Volume_ml'])

    # ========== NOISY DATA TESTS ==========

    # High noise cylinder (test robustness)
    test_cases['cylinder_high_noise'] = {
        'data': generate_cylinder(r=10, h_min=0, h_max=50, n_points=50, noise_level=0.10),
        'expected_shape': 'cylinder',
        'expected_segments': 1,
        'diameter_mm': 20.0,
        'height_range_mm': (0, 50),
        'volume_range_ml': (0, 15.7),
        'description': 'Cylinder with 10% noise (robustness test)'
    }

    # Very fine sampling (test numerical stability)
    test_cases['cylinder_fine_sampling'] = {
        'data': generate_cylinder(r=5, h_min=0, h_max=30, n_points=200, noise_level=0.01),
        'expected_shape': 'cylinder',
        'expected_segments': 1,
        'diameter_mm': 10.0,
        'height_range_mm': (0, 30),
        'volume_range_ml': (0, 2.36),
        'description': 'Cylinder with very fine sampling (200 points, numerical stability test)'
    }

    # Sparse sampling (test with few points)
    test_cases['cylinder_sparse_sampling'] = {
        'data': generate_cylinder(r=8, h_min=0, h_max=40, n_points=15, noise_level=0.02),
        'expected_shape': 'cylinder',
        'expected_segments': 1,
        'diameter_mm': 16.0,
        'height_range_mm': (0, 40),
        'volume_range_ml': (0, 8.04),
        'description': 'Cylinder with sparse sampling (15 points only)'
    }

    return test_cases


def save_test_suite(output_dir='test_data'):
    """Generate and save all test cases to CSV files."""
    os.makedirs(output_dir, exist_ok=True)

    test_cases = generate_test_suite()

    print(f"Generating {len(test_cases)} test cases...")
    print("=" * 70)

    for name, test_case in test_cases.items():
        filename = os.path.join(output_dir, f"{name}.csv")
        test_case['data'].to_csv(filename, index=False)

        print(f"✅ {name}")
        print(f"   File: {filename}")
        print(f"   Description: {test_case['description']}")
        print(f"   Expected: {test_case['expected_segments']} segment(s), "
              f"shape={test_case['expected_shape']}")
        print()

    # Save test metadata
    import json
    metadata = {
        name: {k: v for k, v in test.items() if k != 'data'}
        for name, test in test_cases.items()
    }

    with open(os.path.join(output_dir, 'test_metadata.json'), 'w') as f:
        json.dump(metadata, f, indent=2)

    print("=" * 70)
    print(f"✅ Generated {len(test_cases)} test cases in '{output_dir}/' directory")
    print(f"📄 Metadata saved to: {output_dir}/test_metadata.json")

    return test_cases


if __name__ == '__main__':
    # Set random seed for reproducibility
    np.random.seed(42)

    print("Container Geometry Analyzer - Test Data Generator")
    print("=" * 70)
    print()

    test_cases = save_test_suite()

    print("\nTest suite includes:")
    print("- 3 simple cylinders (small, medium, large)")
    print("- 2 cones (pipette tip, centrifuge tip)")
    print("- 2 sphere caps (flask, vial)")
    print("- 2 frustums (expanding shapes)")
    print("- 3 composite shapes (flask, centrifuge, eppendorf)")
    print("- 3 robustness tests (high noise, fine sampling, sparse sampling)")
