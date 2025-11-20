#!/usr/bin/env python3
"""
Composite Shape Failure Analysis
=================================

Analyzes why transitions aren't detected between composite shapes
by examining curvature, area profiles, and transition detection.
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container_geometry_analyzer_gui_v3_11_8 import (
    load_data_csv,
    compute_areas,
    compute_curvature,
    find_optimal_transitions_improved,
    DEFAULT_PARAMS
)

# Composite test cases that are failing
FAILING_CASES = {
    'composite_flask_sphere_cylinder': {
        'file': 'test_data/composite_flask_sphere_cylinder.csv',
        'expected_segments': 2,
        'expected_shapes': 'sphere_cap + cylinder',
        'description': 'Flask with sphere bottom + cylinder body'
    },
    'composite_centrifuge_cone_cylinder': {
        'file': 'test_data/composite_centrifuge_cone_cylinder.csv',
        'expected_segments': 2,
        'expected_shapes': 'cone + cylinder',
        'description': 'Centrifuge tube with conical tip'
    },
    'composite_eppendorf_complex': {
        'file': 'test_data/composite_eppendorf_complex.csv',
        'expected_segments': 2,
        'expected_shapes': 'cone + cylinder',
        'description': 'Eppendorf-style tube'
    },
}


def analyze_composite_shape(name, case_info):
    """Analyze a composite shape failure in detail."""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {name}")
    print(f"{'='*80}")
    print(f"Description: {case_info['description']}")
    print(f"Expected: {case_info['expected_segments']} segments ({case_info['expected_shapes']})")

    # Load data
    df = load_data_csv(case_info['file'])
    print(f"Data points: {len(df)}")

    # Compute areas
    df_with_areas = compute_areas(df)
    area = df_with_areas['Area'].values
    heights = df_with_areas['Height_mm'].values

    print(f"Height range: {heights[0]:.2f} - {heights[-1]:.2f} mm")
    print(f"Area range: {area[0]:.2f} - {np.max(area):.2f} mm²")

    # Compute curvature
    curvature = compute_curvature(area, heights)

    # Find transitions with current algorithm
    transitions = find_optimal_transitions_improved(
        area, heights=heights, min_points=12, verbose=True
    )
    print(f"\nDetected transitions: {transitions}")
    print(f"Number of segments detected: {len(transitions) - 1}")

    # Analyze curvature profile
    print(f"\n{'─'*80}")
    print("CURVATURE ANALYSIS")
    print(f"{'─'*80}")
    print(f"Curvature range: {np.min(curvature):.6f} - {np.max(curvature):.6f}")
    print(f"Mean curvature: {np.mean(curvature):.6f}")
    print(f"Median curvature: {np.median(curvature):.6f}")

    # Find high-curvature regions (> 0.05)
    high_curv = np.where(curvature > 0.05)[0]
    low_curv = np.where(curvature <= 0.05)[0]

    print(f"\nHigh curvature points (>0.05): {len(high_curv)} ({100*len(high_curv)/len(curvature):.1f}%)")
    if len(high_curv) > 0:
        print(f"  Range: indices {high_curv[0]}-{high_curv[-1]}")
        print(f"  Height range: {heights[high_curv[0]]:.2f}-{heights[high_curv[-1]]:.2f} mm")

    print(f"Low curvature points (≤0.05): {len(low_curv)} ({100*len(low_curv)/len(curvature):.1f}%)")
    if len(low_curv) > 0:
        print(f"  Range: indices {low_curv[0]}-{low_curv[-1]}")
        print(f"  Height range: {heights[low_curv[0]]:.2f}-{heights[low_curv[-1]]:.2f} mm")

    # Analyze area gradient (first derivative)
    first_deriv = np.gradient(area, heights)
    print(f"\n{'─'*80}")
    print("AREA GRADIENT ANALYSIS (dA/dh)")
    print(f"{'─'*80}")
    print(f"Gradient range: {np.min(first_deriv):.4f} - {np.max(first_deriv):.4f}")
    print(f"Mean gradient: {np.mean(first_deriv):.4f}")
    print(f"Median gradient: {np.median(first_deriv):.4f}")

    # Find gradient changes (second derivative)
    second_deriv = np.gradient(first_deriv, heights)
    print(f"\n{'─'*80}")
    print("AREA CURVATURE ANALYSIS (d²A/dh²)")
    print(f"{'─'*80}")
    print(f"Second deriv range: {np.min(second_deriv):.6f} - {np.max(second_deriv):.6f}")
    print(f"Mean second deriv: {np.mean(second_deriv):.6f}")

    # Find inflection points (where second derivative changes sign)
    sign_changes = np.where(np.diff(np.sign(second_deriv)) != 0)[0]
    print(f"\nInflection points (sign changes): {len(sign_changes)}")
    if len(sign_changes) > 0:
        print("Inflection point locations (first 5):")
        for i in sign_changes[:5]:
            print(f"  Index {i}: height {heights[i]:.2f}mm, area {area[i]:.2f}mm², "
                  f"curvature {curvature[i]:.6f}")

    # Analyze expected transition location
    print(f"\n{'─'*80}")
    print("EXPECTED TRANSITION ANALYSIS")
    print(f"{'─'*80}")

    if 'sphere' in case_info['expected_shapes'].lower():
        # For sphere+cylinder, expect transition when area becomes constant
        print("Expected transition: Where sphere cap ends and cylinder begins")
        print("  Indicator: Area becomes nearly constant (low gradient)")
        # Find where gradient stabilizes
        gradient_threshold = 0.1
        stable_gradient_indices = np.where(np.abs(first_deriv) < gradient_threshold)[0]
        if len(stable_gradient_indices) > 0:
            print(f"  Points with |dA/dh| < {gradient_threshold}: {len(stable_gradient_indices)}")
            first_stable = stable_gradient_indices[0]
            print(f"  First stable point: index {first_stable}, height {heights[first_stable]:.2f}mm")

    elif 'cone' in case_info['expected_shapes'].lower():
        # For cone+cylinder, expect transition when area gradient changes significantly
        print("Expected transition: Where cone ends and cylinder begins")
        print("  Indicator: Sudden change in area gradient (from accelerating to constant)")

        # Analyze gradient magnitude
        grad_magnitude = np.abs(first_deriv)
        # Find significant changes
        grad_changes = np.abs(np.diff(grad_magnitude))
        largest_changes = np.argsort(grad_changes)[-5:][::-1]
        print(f"  Top 5 gradient magnitude changes:")
        for idx in largest_changes:
            print(f"    Index {idx}: {grad_changes[idx]:.4f} at height {heights[idx]:.2f}mm")

    # Create visualization
    print(f"\n{'─'*80}")
    print("Generating diagnostic plots...")
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))

    # Plot 1: Area profile with detected transitions
    ax = axes[0]
    ax.plot(heights, area, 'b-', linewidth=2, label='Area profile')
    for t in transitions:
        if 0 <= t < len(heights):
            ax.axvline(heights[t], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.set_xlabel('Height (mm)')
    ax.set_ylabel('Area (mm²)')
    ax.set_title(f'{name} - Area Profile with Detected Transitions')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 2: Curvature profile
    ax = axes[1]
    ax.plot(heights, curvature, 'g-', linewidth=2, label='Curvature coefficient')
    ax.axhline(0.05, color='orange', linestyle='--', linewidth=1, label='Threshold (0.05)')
    for t in transitions:
        if 0 <= t < len(heights):
            ax.axvline(heights[t], color='red', linestyle='--', linewidth=2, alpha=0.7)
    ax.set_xlabel('Height (mm)')
    ax.set_ylabel('Curvature')
    ax.set_title(f'{name} - Curvature Profile')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: First and second derivatives
    ax = axes[2]
    ax.plot(heights, first_deriv, 'b-', linewidth=2, label='First derivative (dA/dh)')
    ax2 = ax.twinx()
    ax2.plot(heights, second_deriv, 'r-', linewidth=2, label='Second derivative (d²A/dh²)')
    for t in transitions:
        if 0 <= t < len(heights):
            ax.axvline(heights[t], color='gray', linestyle='--', linewidth=1, alpha=0.5)
    ax.set_xlabel('Height (mm)')
    ax.set_ylabel('First Derivative', color='b')
    ax2.set_ylabel('Second Derivative', color='r')
    ax.set_title(f'{name} - Area Derivatives')
    ax.tick_params(axis='y', labelcolor='b')
    ax2.tick_params(axis='y', labelcolor='r')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plot_file = f'composite_analysis_{name}.png'
    plt.savefig(plot_file, dpi=150, bbox_inches='tight')
    print(f"Saved plot: {plot_file}")
    plt.close()

    return {
        'name': name,
        'detected_segments': len(transitions) - 1,
        'expected_segments': case_info['expected_segments'],
        'match': len(transitions) - 1 == case_info['expected_segments'],
        'curvature_stats': {
            'min': np.min(curvature),
            'max': np.max(curvature),
            'mean': np.mean(curvature),
            'high_curv_pct': 100 * len(high_curv) / len(curvature)
        }
    }


def main():
    """Main analysis function."""
    print("\n" + "=" * 80)
    print("COMPOSITE SHAPE FAILURE INVESTIGATION")
    print("=" * 80)
    print(f"Analyzing {len(FAILING_CASES)} failing composite shapes")
    print(f"Curvature threshold: {DEFAULT_PARAMS['curvature_threshold']}")

    results = []
    for name, case_info in FAILING_CASES.items():
        result = analyze_composite_shape(name, case_info)
        results.append(result)

    # Summary
    print("\n\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for result in results:
        status = "✅" if result['match'] else "❌"
        print(f"{status} {result['name']:<40} "
              f"Detected: {result['detected_segments']}, Expected: {result['expected_segments']}")

    print("\nCurvature Statistics:")
    for result in results:
        stats = result['curvature_stats']
        print(f"  {result['name']:<40} "
              f"Max: {stats['max']:.6f}, High%: {stats['high_curv_pct']:.1f}%")

    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("""
The failing composite shapes all share a pattern:
1. Curved section (sphere cap or cone) in the lower part
2. Linear section (cylinder) in the upper part
3. Transition between them is subtle

Possible reasons for detection failure:
1. Curvature filtering is suppressing the transition boundary
2. Transition detection algorithm not sensitive enough at boundaries
3. The transition region has gradual change, not sharp discontinuity
4. Current algorithm confuses boundary with inflection point

Recommended next steps:
1. Test multi-scale curvature analysis
2. Implement gradient-based boundary detection
3. Use inflection point + curvature change detection
4. Apply second-derivative peak detection
""")

    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
