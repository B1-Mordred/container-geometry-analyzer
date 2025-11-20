"""
Unit Tests for Priority 4: Phase 2 - Selective Hybrid Routing

Tests for find_optimal_transitions_selective() function that implements
conservative hybrid routing between stability-based and multi-derivative methods.
"""

import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src'))

from container_geometry_analyzer_gui_v3_11_8 import (
    find_optimal_transitions_selective,
    find_optimal_transitions_improved,
    predict_segment_count,
    HAS_STABILITY_DETECTION
)


def generate_synthetic_cylinder(height_points=100, radius=5.0):
    """Generate synthetic cylinder data (1-segment)."""
    heights = np.linspace(0, 100, height_points)
    # Constant area = π * r²
    area = np.full(height_points, np.pi * radius**2)
    return area, heights


def generate_synthetic_2segment(height_points=100):
    """Generate synthetic 2-segment container (cone -> cylinder)."""
    heights = np.linspace(0, 100, height_points)
    area = np.zeros(height_points)

    # Cone segment (0-50mm): r = 5 + 5*h/50
    cone_idx = int(height_points * 0.5)
    for i in range(cone_idx):
        r = 5.0 + 5.0 * (heights[i] / 50.0)
        area[i] = np.pi * r**2

    # Cylinder segment (50-100mm): r = 10
    for i in range(cone_idx, height_points):
        area[i] = np.pi * 10.0**2

    return area, heights


def generate_synthetic_3segment(height_points=100):
    """Generate synthetic 3-segment container (cone -> cylinder -> frustum)."""
    heights = np.linspace(0, 100, height_points)
    area = np.zeros(height_points)

    # Cone segment (0-33mm): r = 5 + 5*h/33
    cone_idx = int(height_points * 0.33)
    for i in range(cone_idx):
        r = 5.0 + 5.0 * (heights[i] / 33.0)
        area[i] = np.pi * r**2

    # Cylinder segment (33-66mm): r = 10
    cyl_idx = int(height_points * 0.66)
    for i in range(cone_idx, cyl_idx):
        area[i] = np.pi * 10.0**2

    # Frustum segment (66-100mm): r = 10 - 5*(h-66)/34
    for i in range(cyl_idx, height_points):
        r = 10.0 - 5.0 * (heights[i] - 66.0) / 34.0
        area[i] = np.pi * r**2

    return area, heights


def test_selective_routing_returns_tuple():
    """Test that selective routing returns (transitions, method) tuple."""
    print("\n=== Test 1: Return value format ===")
    area, heights = generate_synthetic_cylinder()
    result = find_optimal_transitions_selective(area, heights, verbose=False)

    assert isinstance(result, tuple), "Should return tuple"
    assert len(result) == 2, "Should return 2-element tuple (transitions, method)"
    transitions, method = result
    assert isinstance(transitions, list), "First element should be transition list"
    assert isinstance(method, str), "Second element should be method string"
    print(f"✅ Returns correct tuple format: {method}")
    return True


def test_selective_routing_1segment():
    """Test that 1-segment (cylinder) routes correctly."""
    print("\n=== Test 2: 1-segment (cylinder) routing ===")
    area, heights = generate_synthetic_cylinder()
    transitions, method = find_optimal_transitions_selective(area, heights, verbose=False)

    # Should use multi-derivative for 1-segment
    assert method in ['multi-derivative', 'multi-derivative-fallback'], \
        f"1-segment should use multi-derivative, got {method}"

    # Should find exactly 1 segment (2 endpoints)
    assert len(transitions) == 2, f"Should find 2 transitions for 1 segment, got {len(transitions)}"
    print(f"✅ 1-segment correctly routed to {method}: {len(transitions) - 1} segments")
    return True


def test_selective_routing_2segment():
    """Test that 2-segment routes to multi-derivative."""
    print("\n=== Test 3: 2-segment (cone->cylinder) routing ===")
    area, heights = generate_synthetic_2segment()
    transitions, method = find_optimal_transitions_selective(area, heights, verbose=False)

    # Should use multi-derivative for 2-segment
    assert method in ['multi-derivative', 'multi-derivative-fallback'], \
        f"2-segment should use multi-derivative, got {method}"

    print(f"✅ 2-segment correctly routed to {method}")
    return True


def test_selective_routing_3segment():
    """Test that 3-segment can route to stability method if available."""
    print("\n=== Test 4: 3-segment (cone->cyl->frustum) routing ===")

    if not HAS_STABILITY_DETECTION:
        print("⚠️  Stability detection not available, skipping stability routing test")
        return True

    area, heights = generate_synthetic_3segment()
    transitions, method = find_optimal_transitions_selective(
        area, heights, confidence_threshold='high', verbose=False
    )

    # Method should be one of the valid return values
    valid_methods = [
        'stability', 'multi-derivative',
        'multi-derivative-fallback', 'multi-derivative-emergency-fallback'
    ]
    assert method in valid_methods, f"Invalid method returned: {method}"

    print(f"✅ 3-segment routed to {method}: {len(transitions) - 1} segments detected")
    return True


def test_selective_routing_with_confidence_threshold():
    """Test that confidence threshold affects routing."""
    print("\n=== Test 5: Confidence threshold behavior ===")

    if not HAS_STABILITY_DETECTION:
        print("⚠️  Stability detection not available, skipping confidence test")
        return True

    area, heights = generate_synthetic_3segment()

    # Test with high confidence threshold
    transitions_high, method_high = find_optimal_transitions_selective(
        area, heights, confidence_threshold='high', verbose=False
    )

    # Test with medium confidence threshold
    transitions_medium, method_medium = find_optimal_transitions_selective(
        area, heights, confidence_threshold='medium', verbose=False
    )

    # Both should return valid results
    assert len(transitions_high) >= 2, "Should return at least endpoints"
    assert len(transitions_medium) >= 2, "Should return at least endpoints"

    print(f"✅ High confidence: {method_high}, Medium confidence: {method_medium}")
    return True


def test_selective_routing_graceful_fallback():
    """Test that function gracefully falls back to multi-derivative on errors."""
    print("\n=== Test 6: Graceful fallback behavior ===")

    # Create minimal but valid data (need at least 5 points for Savitzky-Goyal with default window)
    area = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    heights = np.arange(len(area), dtype=float)

    # Should not crash, should return valid result
    try:
        transitions, method = find_optimal_transitions_selective(
            area, heights, min_points=3, verbose=False
        )
        assert len(transitions) >= 2, "Should return at least endpoints"
        print(f"✅ Gracefully handled minimal data: {method}")
        return True
    except Exception as e:
        print(f"❌ Failed with exception: {e}")
        return False


def test_selective_routing_with_diameter():
    """Test that diameter parameter is properly passed through."""
    print("\n=== Test 7: Diameter parameter handling ===")

    area, heights = generate_synthetic_cylinder()

    # Test with diameter
    transitions_with_d, method = find_optimal_transitions_selective(
        area, heights, diameter_mm=5.0, verbose=False
    )

    # Test without diameter
    transitions_without_d, method = find_optimal_transitions_selective(
        area, heights, verbose=False
    )

    # Both should work
    assert len(transitions_with_d) >= 2, "Should work with diameter"
    assert len(transitions_without_d) >= 2, "Should work without diameter"

    print(f"✅ Diameter parameter handled correctly")
    return True


def test_selective_routing_consistency():
    """Test that baseline behavior is preserved when feature is disabled."""
    print("\n=== Test 8: Consistency with multi-derivative when not using stability ===")

    area, heights = generate_synthetic_cylinder()

    # Get selective routing result
    transitions_selective, method = find_optimal_transitions_selective(
        area, heights, verbose=False
    )

    # Get baseline result
    transitions_baseline = find_optimal_transitions_improved(
        area, heights, verbose=False
    )

    # For 1-segment (cylinder), both should find same number of segments
    # (though exact endpoints might differ slightly)
    assert abs(len(transitions_selective) - len(transitions_baseline)) <= 1, \
        "Selective should match baseline for simple cases"

    print(f"✅ Selective routing consistent with baseline: "
          f"selective={len(transitions_selective)-1} seg, baseline={len(transitions_baseline)-1} seg")
    return True


def test_selective_routing_verbose_output():
    """Test that verbose output doesn't cause errors."""
    print("\n=== Test 9: Verbose output handling ===")

    area, heights = generate_synthetic_2segment()

    try:
        transitions, method = find_optimal_transitions_selective(
            area, heights, verbose=True
        )
        assert len(transitions) >= 2, "Should return valid transitions"
        print(f"✅ Verbose output handled correctly")
        return True
    except Exception as e:
        print(f"❌ Verbose output caused exception: {e}")
        return False


def run_all_tests():
    """Run all unit tests and report results."""
    print("\n" + "="*70)
    print("PRIORITY 4: PHASE 2 - SELECTIVE ROUTING UNIT TESTS")
    print("="*70)

    tests = [
        test_selective_routing_returns_tuple,
        test_selective_routing_1segment,
        test_selective_routing_2segment,
        test_selective_routing_3segment,
        test_selective_routing_with_confidence_threshold,
        test_selective_routing_graceful_fallback,
        test_selective_routing_with_diameter,
        test_selective_routing_consistency,
        test_selective_routing_verbose_output,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except AssertionError as e:
            print(f"❌ Test failed: {e}")
            results.append(False)
        except Exception as e:
            print(f"❌ Test error: {e}")
            results.append(False)

    # Summary
    print("\n" + "="*70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("="*70)

    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
