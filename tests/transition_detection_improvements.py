"""
Improved Transition Detection Algorithms for Container Geometry Analyzer
=========================================================================

This module contains multiple approaches to improve transition detection
between geometric segments (cylinder/frustum boundaries).

Author: Analysis by Claude
Date: 2025-11-19
"""

import numpy as np
import pandas as pd
from scipy.signal import savgol_filter, find_peaks, argrelextrema
from scipy.ndimage import gaussian_filter1d
from scipy.stats import zscore
from typing import List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


# ==============================================================================
# ISSUE 1: Current method only uses FIRST DERIVATIVE
# ==============================================================================

def detect_transitions_multi_derivative(
    area: np.ndarray,
    heights: np.ndarray,
    min_points: int = 12,
    verbose: bool = False
) -> List[int]:
    """
    Improved transition detection using MULTIPLE derivatives.

    Current method (line 309): Only uses abs(diff(area_smooth))
    Problem: Misses gradual transitions with low first derivative

    Solution: Combine first AND second derivatives (curvature)

    Physics intuition:
    - Cylinder → Frustum: Area changes from constant to linear
      * First derivative: 0 → constant
      * Second derivative: 0 → 0 (but first deriv changes!)
    - Frustum → Cylinder: Area changes from linear to constant
      * First derivative: constant → 0
      * Second derivative: 0 → 0 (but first deriv changes!)
    - Cylinder → Sphere: Area changes from constant to curved
      * First derivative: 0 → increasing
      * Second derivative: 0 → positive (acceleration!)
    """
    n = len(area)

    if n < 2 * min_points:
        return [0, n - 1]

    # Smooth the area data (same as current)
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1

    try:
        area_smooth = savgol_filter(area, window_length=window, polyorder=2)
    except:
        area_smooth = gaussian_filter1d(area, sigma=2.0)

    # === NEW: Compute multiple derivatives ===

    # First derivative: rate of change
    # For cylinders: ~0, for frustums: constant, for spheres: varying
    first_deriv = np.gradient(area_smooth, heights)

    # Second derivative: curvature (rate of change of rate of change)
    # Detects when slope CHANGES (cylinder→frustum transition)
    second_deriv = np.gradient(first_deriv, heights)

    # Third derivative: jerk (for very smooth transitions)
    third_deriv = np.gradient(second_deriv, heights)

    # === Detect transitions in each derivative ===

    # Method 1: First derivative magnitude changes
    first_deriv_change = np.abs(np.diff(first_deriv))
    first_deriv_score = first_deriv_change / (np.std(first_deriv_change) + 1e-8)

    # Method 2: Second derivative peaks (curvature maxima)
    second_deriv_abs = np.abs(second_deriv)
    second_deriv_score = second_deriv_abs / (np.std(second_deriv_abs) + 1e-8)

    # Method 3: Third derivative for subtle transitions
    third_deriv_abs = np.abs(third_deriv)
    third_deriv_score = third_deriv_abs / (np.std(third_deriv_abs) + 1e-8)

    # === Combine scores with weights ===
    # Pad to match lengths
    score = np.zeros(n)
    score[1:] += 0.5 * normalize_score(first_deriv_score)
    score[:-1] += 0.3 * normalize_score(second_deriv_score[:-1])
    score[:-1] += 0.2 * normalize_score(third_deriv_score[:-1])

    # Find peaks in combined score
    threshold = np.percentile(score[min_points:-min_points], 85)
    candidates = find_peaks(score, height=threshold, distance=min_points)[0]

    if verbose:
        logger.info(f"🔍 Multi-derivative detection: {len(candidates)} candidates")
        logger.info(f"   First deriv contribution: {np.max(first_deriv_score):.3f}")
        logger.info(f"   Second deriv contribution: {np.max(second_deriv_score):.3f}")

    transitions = [0] + list(candidates) + [n - 1]
    return sorted(list(set(transitions)))


# ==============================================================================
# ISSUE 2: Fixed percentile threshold (80%) doesn't adapt to data
# ==============================================================================

def detect_transitions_adaptive_threshold(
    area: np.ndarray,
    heights: np.ndarray,
    min_points: int = 12,
    verbose: bool = False
) -> List[int]:
    """
    Adaptive threshold based on data characteristics.

    Current method: threshold = np.percentile(diff, 80)
    Problem: 80% is arbitrary - noisy data needs higher, clean data needs lower

    Solution: Adapt threshold based on signal-to-noise ratio
    """
    n = len(area)

    if n < 2 * min_points:
        return [0, n - 1]

    # Smooth the data
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1
    area_smooth = savgol_filter(area, window_length=window, polyorder=2)

    # Compute first derivative
    diff = np.abs(np.diff(area_smooth))

    # === Estimate signal-to-noise ratio ===

    # 1. Estimate noise level from high-frequency components
    # Assume noise is in residuals after heavy smoothing
    area_very_smooth = savgol_filter(area, window_length=min(21, n//5 if n//5 % 2 == 1 else n//5+1), polyorder=2)
    noise = area - area_very_smooth
    noise_std = np.std(noise)

    # 2. Estimate signal level from range of area
    signal_range = np.max(area) - np.min(area)

    # 3. SNR ratio
    snr = signal_range / (noise_std + 1e-8)

    # === Adaptive percentile based on SNR ===
    if snr > 100:  # Very clean data
        percentile = 70  # More sensitive, detect subtle transitions
    elif snr > 50:  # Clean data
        percentile = 75
    elif snr > 20:  # Moderate noise
        percentile = 80  # Current default
    elif snr > 10:  # Noisy data
        percentile = 85
    else:  # Very noisy
        percentile = 90  # Less sensitive, avoid false positives

    threshold = np.percentile(diff, percentile)
    candidates = np.where(diff > threshold)[0] + 1

    # Enforce minimum spacing
    transitions = [0]
    for cand in candidates:
        if cand - transitions[-1] >= min_points:
            transitions.append(cand)
    transitions.append(n - 1)

    if verbose:
        logger.info(f"🔍 Adaptive threshold detection:")
        logger.info(f"   SNR: {snr:.2f}")
        logger.info(f"   Adaptive percentile: {percentile}")
        logger.info(f"   Threshold: {threshold:.6f}")
        logger.info(f"   Candidates: {len(candidates)}")

    return sorted(list(set(transitions)))


# ==============================================================================
# ISSUE 3: No consideration of measurement vs real transitions
# ==============================================================================

def detect_transitions_statistical_test(
    area: np.ndarray,
    heights: np.ndarray,
    min_points: int = 12,
    alpha: float = 0.05,
    verbose: bool = False
) -> List[int]:
    """
    Statistical change-point detection using hypothesis testing.

    Current method: Uses arbitrary thresholds
    Problem: Can't distinguish measurement noise from real transitions

    Solution: Use statistical tests (CUSUM, Mann-Kendall) to detect
              significant changes in distribution

    Reference: Page's CUSUM test for change detection
    """
    n = len(area)

    if n < 2 * min_points:
        return [0, n - 1]

    # Smooth the data
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1
    area_smooth = savgol_filter(area, window_length=window, polyorder=2)

    # === CUSUM (Cumulative Sum) Test ===
    # Detects shifts in mean

    # Normalize the data
    area_norm = (area_smooth - np.mean(area_smooth)) / (np.std(area_smooth) + 1e-8)

    # Compute CUSUM
    cusum_pos = np.zeros(n)
    cusum_neg = np.zeros(n)

    h = 5  # Threshold (5 standard deviations)
    k = 0.5  # Slack parameter (0.5 std devs)

    for i in range(1, n):
        cusum_pos[i] = max(0, cusum_pos[i-1] + area_norm[i] - k)
        cusum_neg[i] = min(0, cusum_neg[i-1] + area_norm[i] + k)

    # Detect where CUSUM exceeds threshold
    cusum_combined = np.abs(cusum_pos) + np.abs(cusum_neg)

    # Find peaks in CUSUM (these are change points)
    # Use derivative to find rapid changes
    cusum_deriv = np.abs(np.diff(cusum_combined))
    threshold = np.mean(cusum_deriv) + 2 * np.std(cusum_deriv)

    candidates = np.where(cusum_deriv > threshold)[0] + 1

    # === Mann-Kendall Test for trend changes ===
    # Detects changes in slope (useful for cylinder→frustum)

    mk_scores = []
    for i in range(min_points, n - min_points):
        # Test if slope changes significantly at position i
        before = area_smooth[i-min_points:i]
        after = area_smooth[i:i+min_points]

        # Compute slopes
        z_before = np.arange(len(before))
        z_after = np.arange(len(after))

        slope_before = np.polyfit(z_before, before, 1)[0]
        slope_after = np.polyfit(z_after, after, 1)[0]

        # Slope change magnitude
        slope_change = abs(slope_after - slope_before)
        mk_scores.append((i, slope_change))

    if mk_scores:
        mk_scores = np.array(mk_scores)
        mk_threshold = np.percentile(mk_scores[:, 1], 85)
        mk_candidates = mk_scores[mk_scores[:, 1] > mk_threshold, 0].astype(int)
    else:
        mk_candidates = np.array([])

    # Combine both methods
    all_candidates = np.unique(np.concatenate([candidates, mk_candidates]))

    # Enforce minimum spacing
    transitions = [0]
    for cand in sorted(all_candidates):
        if cand - transitions[-1] >= min_points:
            transitions.append(int(cand))
    transitions.append(n - 1)

    if verbose:
        logger.info(f"🔍 Statistical test detection:")
        logger.info(f"   CUSUM candidates: {len(candidates)}")
        logger.info(f"   Mann-Kendall candidates: {len(mk_candidates)}")
        logger.info(f"   Combined: {len(transitions) - 2}")

    return sorted(list(set(transitions)))


# ==============================================================================
# ISSUE 4: No multi-scale analysis
# ==============================================================================

def detect_transitions_multiscale(
    area: np.ndarray,
    heights: np.ndarray,
    min_points: int = 12,
    scales: List[int] = None,
    verbose: bool = False
) -> List[int]:
    """
    Multi-scale transition detection.

    Current method: Single scale (fixed window)
    Problem: May miss small features or create false positives from noise

    Solution: Analyze at multiple scales and combine results

    Intuition:
    - Small scale: Detects fine transitions, but sensitive to noise
    - Large scale: Detects major transitions, robust to noise
    - Combine: Get both precision and robustness
    """
    n = len(area)

    if n < 2 * min_points:
        return [0, n - 1]

    if scales is None:
        # Automatic scale selection
        scales = [
            max(5, n // 20),   # Fine scale (small features)
            max(9, n // 10),   # Medium scale (current default)
            max(13, n // 5),   # Coarse scale (major features)
        ]

    # Ensure odd windows
    scales = [s if s % 2 == 1 else s + 1 for s in scales]
    scales = [min(s, n - 2) for s in scales]  # Can't exceed data length

    all_transitions = set([0, n - 1])
    scale_votes = {}  # Track how many scales vote for each transition

    for scale_idx, window in enumerate(scales):
        if window < 5:
            continue

        try:
            # Smooth at this scale
            area_smooth = savgol_filter(area, window_length=window, polyorder=2)

            # Detect transitions at this scale
            diff = np.abs(np.diff(area_smooth))

            # Use stricter threshold for finer scales (more noise)
            if scale_idx == 0:  # Fine scale
                percentile = 85
            elif scale_idx == 1:  # Medium scale
                percentile = 80
            else:  # Coarse scale
                percentile = 75

            threshold = np.percentile(diff, percentile)
            candidates = np.where(diff > threshold)[0] + 1

            # Vote for each candidate
            for cand in candidates:
                scale_votes[cand] = scale_votes.get(cand, 0) + 1

            if verbose:
                logger.info(f"   Scale {window}: {len(candidates)} candidates")

        except Exception as e:
            logger.debug(f"Scale {window} failed: {e}")
            continue

    # Consensus: Keep transitions that appear in multiple scales
    # Or strong transitions that appear in coarse scale (definitely real)
    n_scales = len(scales)

    for pos, votes in scale_votes.items():
        # Keep if voted by multiple scales OR if in coarse scale
        if votes >= 2 or votes >= n_scales / 2:
            all_transitions.add(pos)

    # Enforce minimum spacing
    transitions = sorted(list(all_transitions))
    filtered = [transitions[0]]

    for trans in transitions[1:]:
        if trans - filtered[-1] >= min_points:
            filtered.append(trans)

    if filtered[-1] != n - 1:
        filtered[-1] = n - 1

    if verbose:
        logger.info(f"🔍 Multi-scale detection:")
        logger.info(f"   Scales: {scales}")
        logger.info(f"   Total candidates: {len(scale_votes)}")
        logger.info(f"   Consensus transitions: {len(filtered) - 2}")

    return filtered


# ==============================================================================
# ISSUE 5: Variance validation is crude (line 328)
# ==============================================================================

def validate_segments_advanced(
    area: np.ndarray,
    heights: np.ndarray,
    transitions: List[int],
    min_points: int = 12,
    verbose: bool = False
) -> List[int]:
    """
    Advanced segment validation using multiple criteria.

    Current method: seg_var > variance_threshold (line 328)
    Problem: Single threshold doesn't work for all segment types

    Solution: Use shape-aware validation
    """
    validated = [transitions[0]]

    for i in range(len(transitions) - 1):
        seg_start = transitions[i]
        seg_end = transitions[i + 1]

        if seg_end - seg_start + 1 < min_points:
            continue

        seg_area = area[seg_start:seg_end + 1]
        seg_heights = heights[seg_start:seg_end + 1]

        # === Criterion 1: Sufficient variation (original) ===
        cv = np.std(seg_area) / (np.mean(seg_area) + 1e-8)
        has_variation = cv > 0.05  # Lower threshold

        # === Criterion 2: Non-random pattern ===
        # Real segments have structure, noise is random
        # Use autocorrelation: real segments have high autocorrelation
        if len(seg_area) > 3:
            # Lag-1 autocorrelation
            area_shifted = seg_area[1:]
            area_orig = seg_area[:-1]
            correlation = np.corrcoef(area_orig, area_shifted)[0, 1]
            has_structure = abs(correlation) > 0.5
        else:
            has_structure = True

        # === Criterion 3: Monotonic or constant behavior ===
        # Real segments are either:
        # - Constant (cylinder): low variance
        # - Monotonic (frustum): consistent trend
        # - Curved (sphere): smooth curvature

        # Check if monotonic
        diffs = np.diff(seg_area)
        n_increases = np.sum(diffs > 0)
        n_decreases = np.sum(diffs < 0)
        monotonic_ratio = max(n_increases, n_decreases) / (len(diffs) + 1e-8)
        is_monotonic = monotonic_ratio > 0.7

        # Check if nearly constant
        is_constant = cv < 0.10

        # === Criterion 4: Fits a simple model ===
        # Try linear fit
        z = np.arange(len(seg_area))
        if len(z) > 2:
            coeffs = np.polyfit(z, seg_area, 1)
            area_predicted = np.polyval(coeffs, z)
            r_squared = 1 - (np.sum((seg_area - area_predicted)**2) /
                           np.sum((seg_area - np.mean(seg_area))**2))
            fits_model = r_squared > 0.7
        else:
            fits_model = True

        # === Decision: Keep segment if it passes validation ===
        reasons = []
        if has_variation:
            reasons.append("variation")
        if has_structure:
            reasons.append("structure")
        if is_monotonic or is_constant:
            reasons.append("shape")
        if fits_model:
            reasons.append("model")

        # Keep if passes at least 2 criteria, or first/last segment
        is_boundary = i in [0, len(transitions) - 2]
        should_keep = len(reasons) >= 2 or is_boundary

        if should_keep:
            validated.append(seg_end)
            if verbose:
                logger.info(f"   Segment {i}: VALID ({', '.join(reasons)})")
        else:
            if verbose:
                logger.info(f"   Segment {i}: REJECTED (only {', '.join(reasons)})")

    # Ensure endpoints
    if not validated or validated[-1] != transitions[-1]:
        validated.append(transitions[-1])

    return sorted(list(set(validated)))


# ==============================================================================
# ISSUE 6: No visualization of detection process
# ==============================================================================

def visualize_transition_detection(
    area: np.ndarray,
    heights: np.ndarray,
    transitions: List[int],
    save_path: str = None
) -> None:
    """
    Visualize the transition detection process for debugging.

    Shows:
    1. Raw area data with detected transitions
    2. First derivative with threshold
    3. Second derivative (curvature)
    4. CUSUM statistic
    """
    import matplotlib.pyplot as plt

    n = len(area)
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1

    area_smooth = savgol_filter(area, window_length=window, polyorder=2)
    first_deriv = np.gradient(area_smooth, heights)
    second_deriv = np.gradient(first_deriv, heights)

    # CUSUM
    area_norm = (area_smooth - np.mean(area_smooth)) / (np.std(area_smooth) + 1e-8)
    cusum = np.cumsum(area_norm)

    fig, axes = plt.subplots(4, 1, figsize=(12, 10))

    # Plot 1: Area with transitions
    axes[0].plot(heights, area, 'o-', alpha=0.5, label='Raw', markersize=3)
    axes[0].plot(heights, area_smooth, 'b-', linewidth=2, label='Smoothed')
    for trans in transitions:
        if 0 < trans < n - 1:
            axes[0].axvline(heights[trans], color='red', linestyle='--', alpha=0.7)
    axes[0].set_ylabel('Area (mm²)')
    axes[0].set_title('Area Profile with Detected Transitions')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Plot 2: First derivative
    axes[1].plot(heights, first_deriv, 'g-', linewidth=2)
    axes[1].axhline(0, color='black', linestyle='--', alpha=0.3)
    for trans in transitions:
        if 0 < trans < n - 1:
            axes[1].axvline(heights[trans], color='red', linestyle='--', alpha=0.7)
    axes[1].set_ylabel('dA/dh (mm²/mm)')
    axes[1].set_title('First Derivative (Rate of Change)')
    axes[1].grid(True, alpha=0.3)

    # Plot 3: Second derivative
    axes[2].plot(heights, second_deriv, 'm-', linewidth=2)
    axes[2].axhline(0, color='black', linestyle='--', alpha=0.3)
    for trans in transitions:
        if 0 < trans < n - 1:
            axes[2].axvline(heights[trans], color='red', linestyle='--', alpha=0.7)
    axes[2].set_ylabel('d²A/dh² (mm²/mm²)')
    axes[2].set_title('Second Derivative (Curvature)')
    axes[2].grid(True, alpha=0.3)

    # Plot 4: CUSUM
    axes[3].plot(heights, cusum, 'orange', linewidth=2)
    axes[3].axhline(0, color='black', linestyle='--', alpha=0.3)
    for trans in transitions:
        if 0 < trans < n - 1:
            axes[3].axvline(heights[trans], color='red', linestyle='--', alpha=0.7)
    axes[3].set_ylabel('CUSUM')
    axes[3].set_xlabel('Height (mm)')
    axes[3].set_title('Cumulative Sum (Change Detection)')
    axes[3].grid(True, alpha=0.3)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        logger.info(f"📊 Visualization saved: {save_path}")
    else:
        plt.show()

    plt.close()


# ==============================================================================
# UNIFIED BEST APPROACH: Combine all improvements
# ==============================================================================

def find_optimal_transitions_v2(
    area: np.ndarray,
    heights: np.ndarray = None,
    min_points: int = 12,
    method: str = 'ensemble',
    verbose: bool = False,
    visualize: bool = False,
    viz_path: str = None
) -> List[int]:
    """
    Next-generation transition detection combining all improvements.

    Parameters:
    -----------
    area : np.ndarray
        Cross-sectional areas
    heights : np.ndarray, optional
        Height values (if None, uses indices)
    min_points : int
        Minimum points per segment
    method : str
        Detection method:
        - 'ensemble': Combine all methods (recommended)
        - 'multi_derivative': Use multiple derivatives
        - 'adaptive': Adaptive thresholding
        - 'statistical': Statistical tests
        - 'multiscale': Multi-scale analysis
    verbose : bool
        Print detailed information
    visualize : bool
        Generate diagnostic plots
    viz_path : str
        Path to save visualization

    Returns:
    --------
    List[int] : Indices of transition points (including 0 and n-1)
    """
    n = len(area)

    if heights is None:
        heights = np.arange(n)

    if n < 2 * min_points:
        if verbose:
            logger.warning(f"⚠️  Too few points for segmentation ({n} < {2*min_points})")
        return [0, n - 1]

    # Select detection method
    if method == 'multi_derivative':
        transitions = detect_transitions_multi_derivative(area, heights, min_points, verbose)

    elif method == 'adaptive':
        transitions = detect_transitions_adaptive_threshold(area, heights, min_points, verbose)

    elif method == 'statistical':
        transitions = detect_transitions_statistical_test(area, heights, min_points, verbose)

    elif method == 'multiscale':
        transitions = detect_transitions_multiscale(area, heights, min_points, verbose=verbose)

    elif method == 'ensemble':
        # Combine multiple methods
        if verbose:
            logger.info("🔍 Ensemble detection: combining multiple methods")

        trans_multi = detect_transitions_multi_derivative(area, heights, min_points, False)
        trans_adaptive = detect_transitions_adaptive_threshold(area, heights, min_points, False)
        trans_statistical = detect_transitions_statistical_test(area, heights, min_points, False)
        trans_multiscale = detect_transitions_multiscale(area, heights, min_points, False)

        # Voting: keep transitions that appear in at least 2 methods
        all_trans = set()
        vote_counts = {}

        for trans_list in [trans_multi, trans_adaptive, trans_statistical, trans_multiscale]:
            for trans in trans_list:
                vote_counts[trans] = vote_counts.get(trans, 0) + 1

        # Keep transitions with >= 2 votes
        for trans, votes in vote_counts.items():
            if votes >= 2 or trans in [0, n-1]:  # Always keep endpoints
                all_trans.add(trans)

        transitions = sorted(list(all_trans))

        # Enforce minimum spacing
        filtered = [transitions[0]]
        for trans in transitions[1:]:
            if trans - filtered[-1] >= min_points:
                filtered.append(trans)
        if filtered[-1] != n - 1:
            filtered.append(n - 1)

        transitions = filtered

        if verbose:
            logger.info(f"   Multi-derivative: {len(trans_multi) - 2} transitions")
            logger.info(f"   Adaptive: {len(trans_adaptive) - 2} transitions")
            logger.info(f"   Statistical: {len(trans_statistical) - 2} transitions")
            logger.info(f"   Multiscale: {len(trans_multiscale) - 2} transitions")
            logger.info(f"   Ensemble consensus: {len(transitions) - 2} transitions")

    else:
        raise ValueError(f"Unknown method: {method}")

    # Advanced validation
    transitions = validate_segments_advanced(area, heights, transitions, min_points, verbose)

    if verbose:
        logger.info(f"✅ Final transitions: {len(transitions) - 2} segments")

    # Optional visualization
    if visualize:
        visualize_transition_detection(area, heights, transitions, viz_path)

    return transitions


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def normalize_score(arr: np.ndarray) -> np.ndarray:
    """Normalize array to [0, 1] range."""
    arr_min, arr_max = np.min(arr), np.max(arr)
    if arr_max - arr_min < 1e-10:
        return np.zeros_like(arr)
    return (arr - arr_min) / (arr_max - arr_min)


def compare_detection_methods(
    area: np.ndarray,
    heights: np.ndarray = None,
    min_points: int = 12
) -> Dict:
    """
    Compare all detection methods and return results.

    Useful for benchmarking and method selection.
    """
    if heights is None:
        heights = np.arange(len(area))

    results = {}

    methods = ['multi_derivative', 'adaptive', 'statistical', 'multiscale', 'ensemble']

    for method in methods:
        try:
            transitions = find_optimal_transitions_v2(area, heights, min_points, method, verbose=False)
            results[method] = {
                'transitions': transitions,
                'n_segments': len(transitions) - 1
            }
        except Exception as e:
            results[method] = {
                'transitions': [0, len(area) - 1],
                'n_segments': 1,
                'error': str(e)
            }

    return results


if __name__ == "__main__":
    """Example usage and testing."""

    # Generate synthetic data with known transitions
    np.random.seed(42)

    # Segment 1: Cylinder (constant area)
    seg1_area = np.ones(30) * 100 + np.random.normal(0, 2, 30)

    # Segment 2: Frustum (linear area change)
    seg2_area = np.linspace(100, 150, 25) + np.random.normal(0, 2, 25)

    # Segment 3: Cylinder (constant area)
    seg3_area = np.ones(20) * 150 + np.random.normal(0, 2, 20)

    area = np.concatenate([seg1_area, seg2_area, seg3_area])
    heights = np.arange(len(area)) * 0.5

    print("=" * 80)
    print("Testing Transition Detection Improvements")
    print("=" * 80)
    print(f"\nSynthetic data: 3 segments (cylinder-frustum-cylinder)")
    print(f"True transitions at indices: 0, 30, 55, {len(area)-1}")
    print()

    # Compare all methods
    results = compare_detection_methods(area, heights, min_points=12)

    print("\nMethod Comparison:")
    print("-" * 80)
    for method, result in results.items():
        if 'error' in result:
            print(f"{method:20s}: ERROR - {result['error']}")
        else:
            print(f"{method:20s}: {result['n_segments']} segments, transitions at {result['transitions']}")

    # Best method with visualization
    print("\n" + "=" * 80)
    print("Running Ensemble Method with Visualization")
    print("=" * 80)

    transitions = find_optimal_transitions_v2(
        area, heights,
        method='ensemble',
        verbose=True,
        visualize=True,
        viz_path='transition_detection_debug.png'
    )

    print(f"\nFinal result: {len(transitions) - 1} segments")
    print(f"Transitions at indices: {transitions}")
    print(f"Transitions at heights: {[heights[t] for t in transitions]}")
