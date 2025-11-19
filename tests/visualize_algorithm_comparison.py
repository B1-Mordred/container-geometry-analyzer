"""
Visualization of Transition Detection Algorithm Improvements
=============================================================

Generate comparison plots showing why the improved method is better.

Author: Container Geometry Analyzer Team
Date: 2025-11-19
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Import from main file
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from container_geometry_analyzer_gui_v3_11_8 import (
    find_optimal_transitions,
    find_optimal_transitions_improved
)

from scipy.signal import savgol_filter


def visualize_derivative_comparison(area, heights, save_path='derivative_comparison.png'):
    """
    Visualize why second derivative helps detect transitions.

    Shows:
    1. Original area data
    2. First derivative (what legacy uses)
    3. Second derivative (what improved adds)
    4. Combined score
    """

    n = len(area)

    # Smooth the data
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1

    area_smooth = savgol_filter(area, window_length=window, polyorder=2)

    # Compute derivatives
    first_deriv = np.gradient(area_smooth, heights)
    second_deriv = np.gradient(first_deriv, heights)

    # Run both detection methods
    trans_legacy = find_optimal_transitions(area, verbose=False)
    trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)

    # Create figure
    fig, axes = plt.subplots(4, 1, figsize=(14, 12))
    fig.suptitle('Why Multi-Derivative Detection Works Better', fontsize=16, fontweight='bold')

    # Plot 1: Area data with transitions
    ax = axes[0]
    ax.plot(heights, area, 'o-', alpha=0.5, markersize=3, label='Raw data', color='gray')
    ax.plot(heights, area_smooth, 'b-', linewidth=2, label='Smoothed')

    for trans in trans_legacy:
        if 0 < trans < n - 1:
            ax.axvline(heights[trans], color='red', linestyle='--', alpha=0.7, linewidth=2, label='Legacy' if trans == trans_legacy[1] else '')

    for trans in trans_improved:
        if 0 < trans < n - 1:
            ax.axvline(heights[trans], color='green', linestyle='-', alpha=0.7, linewidth=2, label='Improved' if trans == trans_improved[1] else '')

    ax.set_ylabel('Area (mm²)', fontweight='bold')
    ax.set_title('Area Profile with Detected Transitions')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    # Plot 2: First derivative (what legacy uses)
    ax = axes[1]
    ax.plot(heights, first_deriv, 'orange', linewidth=2)
    ax.axhline(0, color='black', linestyle='--', alpha=0.3)

    # Show threshold used by legacy
    first_deriv_change = np.abs(np.diff(first_deriv))
    threshold_legacy = np.percentile(first_deriv_change, 80)
    ax.axhline(threshold_legacy, color='red', linestyle=':', linewidth=2, alpha=0.7, label=f'Legacy threshold (80%)')
    ax.axhline(-threshold_legacy, color='red', linestyle=':', linewidth=2, alpha=0.7)

    ax.set_ylabel('dA/dh (mm²/mm)', fontweight='bold')
    ax.set_title('First Derivative (Rate of Change) - Legacy Method Uses This')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 3: Second derivative (what improved adds)
    ax = axes[2]
    ax.plot(heights, second_deriv, 'm-', linewidth=2)
    ax.axhline(0, color='black', linestyle='--', alpha=0.3)

    # Highlight where second derivative is high (transitions!)
    second_deriv_abs = np.abs(second_deriv)
    threshold_second = np.percentile(second_deriv_abs, 80)
    ax.axhline(threshold_second, color='green', linestyle=':', linewidth=2, alpha=0.7, label=f'Detection threshold')
    ax.axhline(-threshold_second, color='green', linestyle=':', linewidth=2, alpha=0.7)

    # Mark transitions
    for trans in trans_improved:
        if 0 < trans < n - 1:
            ax.axvline(heights[trans], color='green', linestyle='-', alpha=0.5)

    ax.set_ylabel('d²A/dh² (mm²/mm²)', fontweight='bold')
    ax.set_title('Second Derivative (Curvature) - Improved Method Adds This')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Plot 4: Combined score used by improved method
    ax = axes[3]

    # Compute the combined score
    first_deriv_change = np.abs(np.diff(first_deriv))
    second_deriv_abs_trimmed = np.abs(second_deriv[:-1])

    def normalize_score(arr):
        arr_min, arr_max = np.min(arr), np.max(arr)
        if arr_max - arr_min < 1e-10:
            return np.zeros_like(arr)
        return (arr - arr_min) / (arr_max - arr_min)

    score = (0.6 * normalize_score(first_deriv_change) +
             0.4 * normalize_score(second_deriv_abs_trimmed))

    ax.plot(heights[1:], score, 'purple', linewidth=2, label='Combined score (60% 1st + 40% 2nd)')
    threshold_combined = np.percentile(score, 80)
    ax.axhline(threshold_combined, color='green', linestyle='--', linewidth=2, alpha=0.7, label='Adaptive threshold')

    # Mark detected transitions
    for trans in trans_improved:
        if 0 < trans < n - 1:
            ax.axvline(heights[trans], color='green', linestyle='-', alpha=0.5)

    ax.set_ylabel('Detection Score', fontweight='bold')
    ax.set_xlabel('Height (mm)', fontweight='bold')
    ax.set_title('Combined Score - Improved Method Uses This for Detection')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"📊 Saved derivative comparison: {save_path}")
    plt.close()


def visualize_adaptive_threshold(save_path='adaptive_threshold_comparison.png'):
    """
    Show how adaptive threshold helps with different noise levels.
    """

    np.random.seed(42)

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle('Adaptive Threshold: Adjusting to Data Quality', fontsize=16, fontweight='bold')

    noise_levels = [
        (0.5, 'Very Clean (SNR>100)'),
        (5, 'Moderate Noise (SNR≈20)'),
        (20, 'Very Noisy (SNR<10)')
    ]

    for idx, (noise_std, noise_label) in enumerate(noise_levels):
        # Generate data: cylinder with step change
        seg1 = np.ones(30) * 100.0
        seg2 = np.ones(30) * 200.0
        area = np.concatenate([seg1, seg2]) + np.random.normal(0, noise_std, 60)
        heights = np.arange(60) * 0.5

        # Left plot: Fixed threshold
        ax = axes[idx, 0]
        trans_fixed = find_optimal_transitions_improved(area, heights, use_adaptive=False, verbose=False)

        ax.plot(heights, area, 'o-', alpha=0.6, markersize=3)
        for trans in trans_fixed:
            if 0 < trans < len(area) - 1:
                ax.axvline(heights[trans], color='red', linestyle='--', linewidth=2)

        ax.set_ylabel('Area (mm²)', fontweight='bold')
        ax.set_title(f'{noise_label} - Fixed Threshold (80%)')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, f'Detected: {len(trans_fixed)-1} segments',
                transform=ax.transAxes, va='top', bbox=dict(boxstyle='round', facecolor='wheat'))

        # Right plot: Adaptive threshold
        ax = axes[idx, 1]
        trans_adaptive = find_optimal_transitions_improved(area, heights, use_adaptive=True, verbose=False)

        ax.plot(heights, area, 'o-', alpha=0.6, markersize=3)
        for trans in trans_adaptive:
            if 0 < trans < len(area) - 1:
                ax.axvline(heights[trans], color='green', linestyle='-', linewidth=2)

        ax.set_ylabel('Area (mm²)', fontweight='bold')
        ax.set_title(f'{noise_label} - Adaptive Threshold')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, f'Detected: {len(trans_adaptive)-1} segments\n(Correct: 2 segments)',
                transform=ax.transAxes, va='top', bbox=dict(boxstyle='round', facecolor='lightgreen'))

    axes[-1, 0].set_xlabel('Height (mm)', fontweight='bold')
    axes[-1, 1].set_xlabel('Height (mm)', fontweight='bold')

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"📊 Saved adaptive threshold comparison: {save_path}")
    plt.close()


def visualize_legacy_vs_improved(save_path='legacy_vs_improved_comparison.png'):
    """
    Side-by-side comparison of legacy vs improved on different test cases.
    """

    np.random.seed(42)

    # Generate test cases
    test_cases = []

    # Test 1: Gentle frustum (hard to detect)
    area1 = np.linspace(100, 120, 50) + np.random.normal(0, 1, 50)
    heights1 = np.arange(50) * 0.5
    test_cases.append(('Gentle Cone', area1, heights1, 1))

    # Test 2: Noisy cylinder (should NOT split)
    area2 = np.ones(50) * 100.0 + np.random.normal(0, 5, 50)
    heights2 = np.arange(50) * 0.5
    test_cases.append(('Noisy Cylinder', area2, heights2, 1))

    # Test 3: Multi-segment
    seg1 = np.ones(20) * 100 + np.random.normal(0, 1, 20)
    seg2 = np.linspace(100, 200, 20) + np.random.normal(0, 1, 20)
    seg3 = np.ones(20) * 200 + np.random.normal(0, 1, 20)
    area3 = np.concatenate([seg1, seg2, seg3])
    heights3 = np.arange(60) * 0.5
    test_cases.append(('Complex (3 segments)', area3, heights3, 3))

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle('Legacy vs Improved: Side-by-Side Comparison', fontsize=16, fontweight='bold')

    for idx, (test_name, area, heights, expected_segs) in enumerate(test_cases):
        # Legacy method
        ax = axes[idx, 0]
        trans_legacy = find_optimal_transitions(area, verbose=False)

        ax.plot(heights, area, 'o-', alpha=0.6, markersize=3, color='skyblue')
        for trans in trans_legacy:
            if 0 < trans < len(area) - 1:
                ax.axvline(heights[trans], color='red', linestyle='--', linewidth=2, alpha=0.7)

        n_legacy = len(trans_legacy) - 1
        is_correct = n_legacy == expected_segs

        ax.set_ylabel('Area (mm²)', fontweight='bold')
        ax.set_title(f'{test_name} - Legacy Method')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, f'Detected: {n_legacy} segments\nExpected: {expected_segs}\n{"✅ Correct" if is_correct else "❌ Incorrect"}',
                transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='lightcoral' if not is_correct else 'lightgreen'))

        # Improved method
        ax = axes[idx, 1]
        trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)

        ax.plot(heights, area, 'o-', alpha=0.6, markersize=3, color='skyblue')
        for trans in trans_improved:
            if 0 < trans < len(area) - 1:
                ax.axvline(heights[trans], color='green', linestyle='-', linewidth=2, alpha=0.7)

        n_improved = len(trans_improved) - 1
        is_correct_imp = n_improved == expected_segs

        ax.set_ylabel('Area (mm²)', fontweight='bold')
        ax.set_title(f'{test_name} - Improved Method')
        ax.grid(True, alpha=0.3)
        ax.text(0.02, 0.98, f'Detected: {n_improved} segments\nExpected: {expected_segs}\n{"✅ Correct" if is_correct_imp else "❌ Incorrect"}',
                transform=ax.transAxes, va='top',
                bbox=dict(boxstyle='round', facecolor='lightcoral' if not is_correct_imp else 'lightgreen'))

    axes[-1, 0].set_xlabel('Height (mm)', fontweight='bold')
    axes[-1, 1].set_xlabel('Height (mm)', fontweight='bold')

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches='tight')
    print(f"📊 Saved legacy vs improved comparison: {save_path}")
    plt.close()


def create_all_visualizations():
    """Generate all comparison visualizations."""

    print("="*70)
    print("GENERATING ALGORITHM COMPARISON VISUALIZATIONS")
    print("="*70)

    # Test case: Cylinder-Frustum-Cylinder
    np.random.seed(42)
    seg1 = np.ones(30) * 314.16 + np.random.normal(0, 2, 30)
    seg2 = np.linspace(314.16, 706.86, 25) + np.random.normal(0, 2, 25)
    seg3 = np.ones(20) * 706.86 + np.random.normal(0, 2, 20)
    area = np.concatenate([seg1, seg2, seg3])
    heights = np.arange(len(area)) * 0.5

    print("\n1. Generating derivative comparison plot...")
    visualize_derivative_comparison(area, heights)

    print("\n2. Generating adaptive threshold comparison...")
    visualize_adaptive_threshold()

    print("\n3. Generating legacy vs improved comparison...")
    visualize_legacy_vs_improved()

    print("\n" + "="*70)
    print("✅ All visualizations generated!")
    print("="*70)
    print("\nFiles created:")
    print("  - derivative_comparison.png")
    print("  - adaptive_threshold_comparison.png")
    print("  - legacy_vs_improved_comparison.png")
    print("\n")


if __name__ == "__main__":
    create_all_visualizations()
