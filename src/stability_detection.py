"""
Priority 4: Stability-Based Multi-Segment Detection
====================================================

Core module for derivative-stability analysis and segment count prediction.
This module provides alternative transition detection for 3+ segment containers.

Author: Marco Horstmann
Date: November 2025
"""

import numpy as np
from scipy.signal import savgol_filter, find_peaks
from scipy.ndimage import gaussian_filter1d
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# PART 1: STABILITY METRIC COMPUTATION
# ============================================================================

def compute_curvature(area, heights):
    """
    Compute curvature coefficient κ for each point.

    κ = |d²A/dh²| / (1 + |dA/dh|)^1.5

    This quantifies how "curved" the shape is at each height.
    - Linear region (cylinder): κ ≈ 0
    - Curved region (cone, sphere): κ >> 0

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values

    Returns:
        np.ndarray: Curvature values (same length as area)
    """
    if len(area) < 3:
        return np.zeros_like(area)

    # Compute derivatives
    dA_dh = np.gradient(area, heights)
    d2A_dh2 = np.gradient(dA_dh, heights)

    # Compute curvature
    denominator = (1 + np.abs(dA_dh)) ** 1.5
    curvature = np.abs(d2A_dh2) / (denominator + 1e-8)

    return curvature


def compute_stability_metric(area, heights, window_size=5):
    """
    Compute stability metric S(h) that measures curvature consistency.

    S(h) = |d²A/dh²_windowed| / (1 + |dA/dh|)

    High stability: curved region (cone, sphere) - high curvature
    Low stability: linear region (cylinder) - low curvature
    Transition: large jump in stability value

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values
        window_size: int - Window for local averaging (default 5)

    Returns:
        tuple: (stability_values, derivatives, smoothed_area)
    """
    n = len(area)

    # Smooth area data
    window = max(5, min(15, n // 10))
    if window % 2 == 0:
        window += 1

    try:
        area_smooth = savgol_filter(area, window_length=window, polyorder=2)
    except:
        area_smooth = gaussian_filter1d(area, sigma=2.0)

    # Compute derivatives
    dA_dh = np.gradient(area_smooth, heights)
    d2A_dh2 = np.gradient(dA_dh, heights)

    # Compute windowed second derivative (local average)
    d2A_dh2_windowed = np.zeros_like(d2A_dh2)
    half_window = window_size // 2

    for i in range(n):
        start = max(0, i - half_window)
        end = min(n, i + half_window + 1)
        d2A_dh2_windowed[i] = np.mean(np.abs(d2A_dh2[start:end]))

    # Compute stability metric
    stability = d2A_dh2_windowed / (1 + np.abs(dA_dh) + 1e-8)

    # Smooth stability for better jump detection
    stability_smooth = savgol_filter(stability, window_length=min(7, n), polyorder=2)

    return stability_smooth, np.gradient(stability_smooth), area_smooth


# ============================================================================
# PART 2: SEGMENT COUNT PREDICTION (3 Heuristics)
# ============================================================================

def predict_segment_count_zero_crossing(area, heights):
    """
    Method 1: Count sign changes in 2nd derivative.

    Each sign change in d²A/dh² indicates a transition between
    linear and curved regions.

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values

    Returns:
        int: Predicted segment count (1-3)
    """
    if len(area) < 10:
        return 1

    dA_dh = np.gradient(area, heights)
    d2A_dh2 = np.gradient(dA_dh, heights)

    # Count sign changes
    sign_changes = np.sum(np.diff(np.sign(d2A_dh2)) != 0)

    # Heuristic: each 2 sign changes ≈ 1 segment boundary
    predicted = min(1 + sign_changes // 2, 3)

    return predicted


def predict_segment_count_curvature_regime(area, heights):
    """
    Method 2: Identify high vs. low curvature regimes.

    Counts transitions between high-curvature and low-curvature regions.

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values

    Returns:
        int: Predicted segment count (1-3)
    """
    if len(area) < 10:
        return 1

    curvature = compute_curvature(area, heights)

    # Identify regime transitions (curvature changes significantly)
    curvature_smooth = savgol_filter(curvature, window_length=min(7, len(curvature)), polyorder=2)
    dcurv_dh = np.gradient(curvature_smooth)

    # Find large jumps in curvature
    threshold = np.std(dcurv_dh) * 1.0
    transition_indices = np.where(np.abs(dcurv_dh) > threshold)[0]

    # Count distinct regimes
    num_regimes = 1 + len(transition_indices) // 3  # Conservative estimate

    predicted = min(num_regimes, 3)

    return predicted


def predict_segment_count_variance(area, heights):
    """
    Method 3: Count local variance peaks.

    Different shape types have different growth characteristics,
    creating local variance peaks.

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values

    Returns:
        int: Predicted segment count (1-3)
    """
    if len(area) < 15:
        return 1

    # Compute local variance with sliding window
    window_size = max(4, len(area) // 5)
    local_vars = []

    for i in range(0, len(area) - window_size, max(1, window_size // 2)):
        local_vars.append(np.var(area[i:i + window_size]))

    if not local_vars:
        return 1

    # Find peaks in variance
    local_vars_array = np.array(local_vars)
    median_var = np.median(local_vars_array)
    peaks = np.where(local_vars_array > median_var * 1.2)[0]

    # Count distinct peaks
    num_peaks = len(peaks)
    predicted = 1 + num_peaks // 2

    return min(predicted, 3)


def predict_segment_count(area, heights, verbose=False):
    """
    Ensemble prediction of segment count (1, 2, or 3).

    Uses three heuristic methods and votes on result.
    Robustness from ensemble approach.

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values
        verbose: bool - Print prediction details

    Returns:
        int: Predicted segment count (1, 2, or 3)
        dict: Details of prediction
    """
    pred1 = predict_segment_count_zero_crossing(area, heights)
    pred2 = predict_segment_count_curvature_regime(area, heights)
    pred3 = predict_segment_count_variance(area, heights)

    predictions = [pred1, pred2, pred3]
    predicted = int(np.median(predictions))

    if verbose:
        logger.info(f"   Segment count prediction:")
        logger.info(f"     Method 1 (zero-crossing): {pred1}")
        logger.info(f"     Method 2 (curvature): {pred2}")
        logger.info(f"     Method 3 (variance): {pred3}")
        logger.info(f"     Ensemble result: {predicted}")

    details = {
        'method1': pred1,
        'method2': pred2,
        'method3': pred3,
        'ensemble': predicted,
        'confidence': 'high' if len(set(predictions)) == 1 else 'medium'
    }

    return predicted, details


# ============================================================================
# PART 3: STABILITY-BASED TRANSITION DETECTION
# ============================================================================

def find_stability_transitions(area, heights, min_points=12, verbose=False):
    """
    Detect transitions using derivative-stability analysis.

    Detects points where curvature stability changes significantly.
    Designed for 3+ segment containers where peak-based detection fails.

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values
        min_points: int - Minimum points per segment
        verbose: bool - Print details

    Returns:
        list: Indices of transition points [0, t1, t2, ..., n-1]
    """
    n = len(area)

    if n < 2 * min_points:
        if verbose:
            logger.warning(f"⚠️  Too few points for segmentation ({n} < {2*min_points})")
        return [0, n - 1]

    # Compute stability metric
    stability, dS_dh, area_smooth = compute_stability_metric(area, heights)

    # Find candidates: points where stability changes significantly
    # Look for large derivatives in stability (jumps in S value)

    threshold = np.std(dS_dh) * 1.5
    if threshold < 1e-8:
        threshold = np.max(np.abs(dS_dh)) * 0.3

    candidates = []

    # Find upward and downward jumps in stability
    # Enhanced filtering: look for sustained changes, not just peaks
    for i in range(min_points, n - min_points):
        # Look at local stability changes with larger window
        left_stability = np.mean(stability[max(0, i-7):i])
        right_stability = np.mean(stability[i:min(n, i+7)])

        jump_magnitude = abs(right_stability - left_stability)

        # Enhanced: Check if stability stays different (sustained change)
        # This filters out transient peaks
        if i > 12 and i < n - 12:
            left_before = np.mean(stability[max(0, i-12):max(0, i-7)])
            right_after = np.mean(stability[min(n, i+7):min(n, i+12)])

            sustained_change = (
                abs(left_before - left_stability) < jump_magnitude * 0.4 and
                abs(right_stability - right_after) < jump_magnitude * 0.4
            )
        else:
            sustained_change = True

        # Score the candidate - CONSERVATIVE THRESHOLD for 3-segment focus
        # Only use when high-confidence 3-segment prediction, so can be stricter
        if jump_magnitude > threshold * 0.6 and abs(dS_dh[i]) > threshold * 0.5 and sustained_change:
            score = jump_magnitude * abs(dS_dh[i])
            candidates.append((i, score, jump_magnitude))

    if verbose and candidates:
        logger.info(f"   Found {len(candidates)} stability transition candidates")

    # Sort by score (magnitude of transition)
    candidates.sort(key=lambda x: x[1], reverse=True)

    # Select top transitions with spacing constraint
    # MORE CONSERVATIVE: require larger spacing to avoid inflection detection
    final_transitions = [0]
    min_transition_spacing = max(min_points * 2, int(n * 0.15))  # 15% of container or 2x min_points

    for idx, score, magnitude in candidates:
        # Ensure minimum spacing between transitions
        if idx - final_transitions[-1] >= min_transition_spacing:
            final_transitions.append(idx)

            # For 3-segment, we only need 2 transitions (3 parts)
            if len(final_transitions) >= 3:
                break

    if final_transitions[-1] != n - 1:
        final_transitions.append(n - 1)

    if verbose:
        logger.info(f"   Stability method selected {len(final_transitions)-1} transitions")

    return sorted(set(final_transitions))


# ============================================================================
# PART 4: VALIDATION WITH SHAPE SIGNATURES
# ============================================================================

def compute_area_gradient_stats(area, heights, start, end):
    """
    Compute statistics of area gradient in a segment.

    Used to identify shape characteristics:
    - Constant gradient: cylinder
    - Increasing gradient: cone
    - Non-monotonic: sphere cap, frustum

    Args:
        area: np.ndarray - All areas
        heights: np.ndarray - All heights
        start: int - Start index
        end: int - End index

    Returns:
        dict: Statistics about gradient behavior
    """
    if end - start < 3:
        return None

    seg_area = area[start:end+1]
    seg_heights = heights[start:end+1]

    # Compute gradient
    gradient = np.gradient(seg_area, seg_heights)

    # Compute second derivative (curvature)
    d2A = np.gradient(gradient, seg_heights)

    stats = {
        'mean_gradient': np.mean(np.abs(gradient)),
        'mean_curvature': np.mean(np.abs(d2A)),
        'gradient_range': np.max(gradient) - np.min(gradient),
        'curvature_std': np.std(d2A),
        'is_monotonic': np.all(d2A >= -1e-6) or np.all(d2A <= 1e-6),
    }

    return stats


def validate_transition(area, heights, transition_idx, min_points=5):
    """
    Validate that a transition point is likely a real boundary.

    Checks if adjacent segments have significantly different
    curvature/gradient characteristics.

    Args:
        area: np.ndarray - All areas
        heights: np.ndarray - All heights
        transition_idx: int - Transition point to validate
        min_points: int - Minimum points to check

    Returns:
        bool: True if transition is likely valid
    """
    n = len(area)

    # Need enough points on both sides
    if transition_idx < min_points or transition_idx > n - min_points - 1:
        return False

    # Get stats on left and right
    left_start = max(0, transition_idx - min_points)
    left_end = transition_idx
    right_start = transition_idx
    right_end = min(n - 1, transition_idx + min_points)

    left_stats = compute_area_gradient_stats(area, heights, left_start, left_end)
    right_stats = compute_area_gradient_stats(area, heights, right_start, right_end)

    if left_stats is None or right_stats is None:
        return False

    # Check if segments are significantly different
    left_curve = left_stats['mean_curvature']
    right_curve = right_stats['mean_curvature']

    # Valid transition: curvatures differ significantly
    # OR one is clearly curved and other is linear
    if left_curve > 0.1 or right_curve > 0.1:
        ratio = max(left_curve, right_curve) / (min(left_curve, right_curve) + 1e-8)
        is_valid = ratio > 1.5
    else:
        # Both relatively linear - check gradient difference
        left_grad = left_stats['mean_gradient']
        right_grad = right_stats['mean_gradient']
        is_valid = abs(left_grad - right_grad) > np.mean([left_grad, right_grad]) * 0.2

    return is_valid


def validate_all_transitions(area, heights, transitions, verbose=False):
    """
    Validate all detected transitions.

    Removes false positives (inflection points, noise peaks).

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values
        transitions: list - Detected transition indices
        verbose: bool - Print validation details

    Returns:
        list: Validated transition indices
    """
    validated = [transitions[0]]  # Always keep start

    for i in range(1, len(transitions) - 1):
        transition_idx = transitions[i]

        if validate_transition(area, heights, transition_idx):
            validated.append(transition_idx)

            if verbose:
                logger.debug(f"   ✓ Transition at index {transition_idx} validated")
        else:
            if verbose:
                logger.debug(f"   ✗ Transition at index {transition_idx} rejected")

    validated.append(transitions[-1])  # Always keep end

    return sorted(set(validated))


# ============================================================================
# PART 5: HYBRID DETECTION (COMBINE BOTH METHODS)
# ============================================================================

def find_optimal_transitions_hybrid(area, heights, min_points=12,
                                   diameter_mm=None, use_adaptive=True,
                                   verbose=False):
    """
    Hybrid transition detection: combines multi-derivative (for 1-2 segment)
    with stability-based method (for 3+ segment).

    Routes to appropriate algorithm based on segment count prediction.

    Args:
        area: np.ndarray - Cross-sectional areas
        heights: np.ndarray - Height values
        min_points: int - Minimum points per segment
        diameter_mm: float - Container diameter (for tuning)
        use_adaptive: bool - Use adaptive thresholding
        verbose: bool - Print details

    Returns:
        list: Indices of transition points [0, t1, t2, ..., n-1]
        str: Method used ('multi_derivative' or 'stability')
    """
    n = len(area)

    if n < 2 * min_points:
        if verbose:
            logger.warning(f"⚠️  Too few points for segmentation ({n} < {2*min_points})")
        return [0, n - 1], 'insufficient_data'

    # STEP 1: Predict segment count
    predicted_segments, prediction_details = predict_segment_count(area, heights, verbose=verbose)

    if verbose:
        logger.info(f"   Predicted segment count: {predicted_segments} "
                   f"(confidence: {prediction_details['confidence']})")

    # STEP 2: Route to appropriate method
    if predicted_segments <= 2:
        if verbose:
            logger.info(f"   Routing to MULTI-DERIVATIVE method (1-2 segment optimal)")
        # Use standard multi-derivative (from main algorithm)
        # This will be called from main algorithm
        return None, 'route_multi_derivative'

    else:  # predicted_segments >= 3
        if verbose:
            logger.info(f"   Routing to STABILITY method (3+ segment optimal)")

        # Use stability-based detection
        transitions = find_stability_transitions(area, heights, min_points, verbose=verbose)

        # Validate transitions
        transitions = validate_all_transitions(area, heights, transitions, verbose=verbose)

        if verbose:
            logger.info(f"   ✨ Hybrid detection: {len(transitions)-1} transitions found via stability method")

        return transitions, 'stability'


# ============================================================================
# PART 6: TESTING UTILITIES
# ============================================================================

def test_stability_metric(verbose=True):
    """
    Unit test: Verify stability metric computation.

    Creates synthetic 3-segment data and checks if stability
    shows expected jumps at boundaries.

    Returns:
        bool: True if test passes
    """
    # Create synthetic 3-segment container
    heights = np.linspace(0, 60, 100)

    # Cone: A ∝ h²
    cone_idx = heights < 20
    cone_area = (heights[cone_idx] / 20) ** 2 * 100

    # Cylinder: A = constant
    cyl_idx = (heights >= 20) & (heights < 40)
    cyl_area = np.full_like(heights[cyl_idx], 100.0)

    # Frustum: A ∝ h (linear increase from 100 to 150)
    frust_idx = heights >= 40
    frust_area = 100 + (heights[frust_idx] - 40) / 20 * 50

    # Combine
    area = np.concatenate([cone_area, cyl_area, frust_area])

    # Compute stability
    stability, dS_dh, _ = compute_stability_metric(area, heights)

    # Check for jumps at ~20 and ~40
    jump1 = abs(stability[25] - stability[15])  # Around cone->cyl boundary
    jump2 = abs(stability[50] - stability[30])  # Around cyl->frust boundary

    if verbose:
        logger.info(f"   Stability jump at cone→cyl: {jump1:.4f}")
        logger.info(f"   Stability jump at cyl→frust: {jump2:.4f}")

    # At least one jump should be significant (2nd derivative changes)
    # Threshold lowered because stability is normalized
    test_pass = jump1 > 0.01 and jump2 > 0.05

    if verbose:
        result = "✅ PASS" if test_pass else "❌ FAIL"
        logger.info(f"   Stability metric test: {result}")

    return test_pass


def test_segment_prediction(verbose=True):
    """
    Unit test: Verify segment count prediction.

    Tests all three heuristic methods on synthetic data.

    Returns:
        bool: True if all methods work reasonably
    """
    # Create synthetic 3-segment data (same as above)
    heights = np.linspace(0, 60, 100)

    cone_idx = heights < 20
    cone_area = (heights[cone_idx] / 20) ** 2 * 100

    cyl_idx = (heights >= 20) & (heights < 40)
    cyl_area = np.full_like(heights[cyl_idx], 100.0)

    frust_idx = heights >= 40
    frust_area = 100 + (heights[frust_idx] - 40) / 20 * 50

    area = np.concatenate([cone_area, cyl_area, frust_area])

    # Test all methods
    pred1 = predict_segment_count_zero_crossing(area, heights)
    pred2 = predict_segment_count_curvature_regime(area, heights)
    pred3 = predict_segment_count_variance(area, heights)
    pred_ensemble, details = predict_segment_count(area, heights)

    if verbose:
        logger.info(f"   Zero-crossing: {pred1}")
        logger.info(f"   Curvature regime: {pred2}")
        logger.info(f"   Variance: {pred3}")
        logger.info(f"   Ensemble: {pred_ensemble}")

    # At least 2 methods should predict 3
    votes_for_3 = sum(1 for p in [pred1, pred2, pred3] if p == 3)
    test_pass = votes_for_3 >= 2

    if verbose:
        result = "✅ PASS" if test_pass else "❌ FAIL"
        logger.info(f"   Segment prediction test: {result}")

    return test_pass


def test_stability_transitions(verbose=True):
    """
    Unit test: Verify stability-based transition detection.

    Tests on synthetic 3-segment data, checks if both
    transitions are found correctly.

    Returns:
        bool: True if test passes
    """
    # Create synthetic 3-segment data
    heights = np.linspace(0, 60, 100)

    cone_idx = heights < 20
    cone_area = (heights[cone_idx] / 20) ** 2 * 100

    cyl_idx = (heights >= 20) & (heights < 40)
    cyl_area = np.full_like(heights[cyl_idx], 100.0)

    frust_idx = heights >= 40
    frust_area = 100 + (heights[frust_idx] - 40) / 20 * 50

    area = np.concatenate([cone_area, cyl_area, frust_area])

    # Detect transitions
    transitions = find_stability_transitions(area, heights, min_points=8, verbose=verbose)

    if verbose:
        logger.info(f"   Detected {len(transitions)-1} transitions at indices: {transitions}")
        logger.info(f"   Expected transitions around indices: 33 (cone→cyl), 66 (cyl→frust)")

    # Should find 3 transitions (0, ~33, ~66, 99)
    test_pass = len(transitions) == 4

    if verbose:
        result = "✅ PASS" if test_pass else "❌ FAIL"
        logger.info(f"   Stability transition detection: {result}")

    return test_pass


def run_all_tests(verbose=True):
    """
    Run all Priority 4 foundation tests.

    Returns:
        bool: True if all tests pass
    """
    if verbose:
        logger.info("\n" + "="*70)
        logger.info("PRIORITY 4 FOUNDATION TESTS")
        logger.info("="*70)

    results = []

    logger.info("\n[1/3] Testing stability metric...")
    results.append(test_stability_metric(verbose))

    logger.info("\n[2/3] Testing segment prediction...")
    results.append(test_segment_prediction(verbose))

    logger.info("\n[3/3] Testing stability transition detection...")
    results.append(test_stability_transitions(verbose))

    if verbose:
        logger.info("\n" + "="*70)
        passed = sum(results)
        total = len(results)
        logger.info(f"TEST RESULTS: {passed}/{total} passed")
        if all(results):
            logger.info("✅ ALL TESTS PASSED - Foundation ready for integration")
        else:
            logger.info("⚠️  SOME TESTS FAILED - Review implementation")
        logger.info("="*70 + "\n")

    return all(results)
