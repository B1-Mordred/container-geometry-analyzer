"""
Unit Tests for Transition Detection Algorithms
===============================================

Tests for both legacy and improved transition detection methods.

Author: Container Geometry Analyzer Team
Date: 2025-11-19
"""

import unittest
import numpy as np
import sys
import os

# Add parent directory to path to import the main module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import functions from main file
from container_geometry_analyzer_gui_v3_11_8 import (
    find_optimal_transitions,
    find_optimal_transitions_improved,
    volume_cylinder,
    volume_frustum
)


class TestGeometricFunctions(unittest.TestCase):
    """Test basic geometric volume calculations."""

    def test_volume_cylinder_basic(self):
        """Test cylinder volume calculation."""
        # V = πr²h, r=5mm, h=10mm → V = π*25*10 ≈ 785.4 mm³
        result = volume_cylinder(h=10, r=5)
        expected = np.pi * 25 * 10
        self.assertTrue(np.isclose(result, expected, rtol=0.001))

    def test_volume_cylinder_zero_height(self):
        """Test cylinder with zero height."""
        result = volume_cylinder(h=0, r=5)
        self.assertEqual(result, 0)

    def test_volume_cylinder_array(self):
        """Test cylinder with array inputs."""
        heights = np.array([0, 5, 10, 15])
        r = 3
        results = volume_cylinder(heights, r)
        expected = np.pi * r**2 * heights
        self.assertTrue(np.allclose(results, expected, rtol=0.001))

    def test_volume_frustum_basic(self):
        """Test frustum volume calculation."""
        # Frustum: r1=5, r2=10, H=10, at h=5
        result = volume_frustum(h=5, r1=5, r2=10, H=10)
        # Should be positive and less than full cone
        self.assertGreater(result, 0)
        self.assertLess(result, volume_frustum(h=10, r1=5, r2=10, H=10))

    def test_volume_frustum_zero_height(self):
        """Test frustum with zero H (edge case)."""
        result = volume_frustum(h=5, r1=5, r2=10, H=0)
        self.assertEqual(result, 0)


class TestSyntheticData(unittest.TestCase):
    """Test transition detection on synthetic data with known transitions."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)

    def test_single_cylinder_legacy(self):
        """Legacy method should detect 1 segment for perfect cylinder."""
        n = 50
        area = np.ones(n) * 100.0  # Constant area = 100 mm²
        transitions = find_optimal_transitions(area, verbose=False)
        n_segments = len(transitions) - 1

        # Should detect exactly 1 segment (no false splits)
        self.assertEqual(n_segments, 1, f"Expected 1 segment, got {n_segments}")

    def test_single_cylinder_improved(self):
        """Improved method should detect 1 segment for perfect cylinder."""
        n = 50
        area = np.ones(n) * 100.0
        heights = np.arange(n) * 0.5
        transitions = find_optimal_transitions_improved(area, heights, verbose=False)
        n_segments = len(transitions) - 1

        self.assertEqual(n_segments, 1, f"Expected 1 segment, got {n_segments}")

    def test_single_cylinder_noisy_improved(self):
        """Improved method should be robust to noise."""
        n = 50
        area = np.ones(n) * 100.0 + np.random.normal(0, 2, n)  # 2% noise
        heights = np.arange(n) * 0.5

        transitions = find_optimal_transitions_improved(
            area, heights, use_adaptive=True, verbose=False
        )
        n_segments = len(transitions) - 1

        # Improved method should handle noise better
        self.assertLessEqual(n_segments, 2, f"Should detect 1-2 segments (noise robust), got {n_segments}")

    def test_multi_segment_detection(self):
        """Test detection on cylinder-frustum-cylinder."""
        # Segment 1: Cylinder
        seg1 = np.ones(30) * 314.16 + np.random.normal(0, 1, 30)
        # Segment 2: Frustum
        seg2 = np.linspace(314.16, 706.86, 25) + np.random.normal(0, 1, 25)
        # Segment 3: Cylinder
        seg3 = np.ones(20) * 706.86 + np.random.normal(0, 1, 20)

        area = np.concatenate([seg1, seg2, seg3])
        heights = np.arange(len(area)) * 0.5

        transitions = find_optimal_transitions_improved(area, heights, verbose=False)
        n_segments = len(transitions) - 1

        # Should detect 2-4 segments
        self.assertGreaterEqual(n_segments, 2, f"Should detect at least 2 segments, got {n_segments}")
        self.assertLessEqual(n_segments, 4, f"Should detect 2-4 segments, got {n_segments}")

    def test_gentle_frustum(self):
        """Test detection of gentle cone transitions."""
        n = 60
        # Very gentle: r1=10mm → r2=11mm (only 10% change)
        area = np.linspace(314.16, 380.13, n) + np.random.normal(0, 2, n)
        heights = np.arange(n) * 0.5

        transitions = find_optimal_transitions_improved(
            area, heights, use_adaptive=True, verbose=False
        )
        n_segments = len(transitions) - 1

        # Should detect this as one segment (it's a single gentle cone)
        self.assertGreaterEqual(n_segments, 1, "Should detect at least 1 segment")
        self.assertLessEqual(n_segments, 2, "Should not over-segment gentle cone")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_too_few_points(self):
        """Test with insufficient data points."""
        area = np.array([100, 105, 110, 115, 120])  # Only 5 points
        heights = np.array([0, 1, 2, 3, 4])

        # Both methods should handle gracefully
        trans_legacy = find_optimal_transitions(area, min_points=12, verbose=False)
        trans_improved = find_optimal_transitions_improved(area, heights, min_points=12, verbose=False)

        # Should return just endpoints
        self.assertEqual(trans_legacy, [0, len(area) - 1])
        self.assertEqual(trans_improved, [0, len(area) - 1])

    def test_constant_area_zero_variance(self):
        """Test with perfectly constant area (zero variance)."""
        area = np.ones(50) * 100.0  # Exactly constant
        heights = np.arange(50) * 0.5

        trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)
        n_segments = len(trans_improved) - 1

        # Should detect as 1 segment
        self.assertEqual(n_segments, 1, "Constant area should be 1 segment")

    def test_step_change(self):
        """Test with abrupt step change (instant transition)."""
        # Two cylinders with different radii, instant transition
        seg1 = np.ones(30) * 100.0
        seg2 = np.ones(30) * 200.0
        area = np.concatenate([seg1, seg2])
        heights = np.arange(60) * 0.5

        trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)
        n_segments = len(trans_improved) - 1

        # Should detect 2 segments
        self.assertGreaterEqual(n_segments, 2, "Should detect step change as 2 segments")

        # Transition should be near index 30
        trans_points = trans_improved[1:-1]
        if len(trans_points) > 0:
            closest_trans = min(trans_points, key=lambda x: abs(x - 30))
            self.assertLess(abs(closest_trans - 30), 5,
                          f"Transition should be near index 30, got {closest_trans}")

    def test_high_noise_low_snr(self):
        """Test with very noisy data (SNR < 5)."""
        np.random.seed(42)
        area = np.ones(50) * 100.0 + np.random.normal(0, 30, 50)  # 30% noise!
        heights = np.arange(50) * 0.5

        trans_improved = find_optimal_transitions_improved(
            area, heights, use_adaptive=True, verbose=False
        )
        n_segments = len(trans_improved) - 1

        # Should be conservative with high noise
        self.assertLessEqual(n_segments, 3,
                           f"Should be conservative with noise, got {n_segments} segments")


class TestAdaptiveThreshold(unittest.TestCase):
    """Test adaptive threshold behavior."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)

    def test_adaptive_vs_fixed_noisy_data(self):
        """Adaptive should be more conservative on noisy data."""
        # Noisy data
        area = np.ones(50) * 100.0 + np.random.normal(0, 10, 50)  # High noise
        heights = np.arange(50) * 0.5

        trans_adaptive = find_optimal_transitions_improved(
            area, heights, use_adaptive=True, verbose=False
        )
        trans_fixed = find_optimal_transitions_improved(
            area, heights, use_adaptive=False, verbose=False
        )

        n_adaptive = len(trans_adaptive) - 1
        n_fixed = len(trans_fixed) - 1

        # Adaptive should not over-segment
        self.assertLessEqual(n_adaptive, n_fixed + 1,
                           "Adaptive should not over-segment noisy data")


class TestRealWorldScenarios(unittest.TestCase):
    """Test scenarios similar to real container data."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)

    def test_2ml_tube_approximation(self):
        """Approximate a 2ml tube: cone tip + cylinder."""
        # Cone tip: r=0 → r=5mm (0-5mm height)
        cone_heights = np.linspace(0, 5, 15)
        cone_radii = np.linspace(0.5, 5, 15)  # Start from small radius
        cone_areas = np.pi * cone_radii**2

        # Main cylinder: r=5mm (5-35mm height)
        cyl_heights = np.linspace(5, 35, 60)
        cyl_areas = np.ones(60) * (np.pi * 5**2)

        area = np.concatenate([cone_areas, cyl_areas]) + np.random.normal(0, 2, 75)
        heights = np.concatenate([cone_heights, cyl_heights])

        trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)
        n_segments = len(trans_improved) - 1

        # Should detect 1-3 segments (cone + cylinder)
        self.assertGreaterEqual(n_segments, 1)
        self.assertLessEqual(n_segments, 3,
                           f"2ml tube should have 1-3 segments, got {n_segments}")

    def test_eppendorf_tube_approximation(self):
        """Approximate Eppendorf tube: cone + cylinder + cap."""
        # Bottom cone
        seg1 = np.linspace(50, 100, 15) + np.random.normal(0, 1, 15)
        # Main cylinder
        seg2 = np.ones(40) * 100 + np.random.normal(0, 1, 40)
        # Cap region (slight increase)
        seg3 = np.linspace(100, 110, 10) + np.random.normal(0, 1, 10)

        area = np.concatenate([seg1, seg2, seg3])
        heights = np.arange(len(area)) * 0.5

        trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)
        n_segments = len(trans_improved) - 1

        # Should detect 2-4 segments
        self.assertGreaterEqual(n_segments, 2)
        self.assertLessEqual(n_segments, 4,
                           f"Eppendorf should have 2-4 segments, got {n_segments}")


class TestComparisonMetrics(unittest.TestCase):
    """Compare legacy vs improved methods quantitatively."""

    def setUp(self):
        """Set up test fixtures."""
        np.random.seed(42)

    def test_detection_consistency(self):
        """Both methods should give consistent results on clear data."""
        # Very clear: two distinct cylinders
        seg1 = np.ones(30) * 100
        seg2 = np.ones(30) * 200
        area = np.concatenate([seg1, seg2])
        heights = np.arange(60) * 0.5

        trans_legacy = find_optimal_transitions(area, verbose=False)
        trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)

        n_legacy = len(trans_legacy) - 1
        n_improved = len(trans_improved) - 1

        # Both should detect at least 2 segments
        self.assertGreaterEqual(n_legacy, 2, "Legacy should detect at least 2 segments")
        self.assertGreaterEqual(n_improved, 2, "Improved should detect at least 2 segments")


# Test runner
def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestGeometricFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestSyntheticData))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveThreshold))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldScenarios))
    suite.addTests(loader.loadTestsFromTestCase(TestComparisonMetrics))

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)

    return result


if __name__ == "__main__":
    run_tests()
