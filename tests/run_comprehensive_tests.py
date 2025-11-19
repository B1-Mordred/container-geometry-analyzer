"""
Comprehensive Test Runner for Container Geometry Analyzer
==========================================================

Runs the analyzer on all generated test cases and validates results.

Usage:
    python run_comprehensive_tests.py

Requirements:
    - All dependencies installed (numpy, pandas, scipy, etc.)
    - Test data generated (python generate_test_data.py)

Author: Container Geometry Analyzer Team
Date: 2025-11-19
"""

import os
import sys
import json
import time
from datetime import datetime
import pandas as pd

# Import the main analyzer module
try:
    from container_geometry_analyzer_gui_v3_11_8 import (
        load_data_csv,
        compute_areas,
        segment_and_fit_optimized,
        create_enhanced_profile,
        AnalysisJob,
        DEFAULT_PARAMS
    )
    ANALYZER_AVAILABLE = True
except ImportError as e:
    print(f"❌ Error importing analyzer: {e}")
    print("Please install dependencies: pip install -r requirements.txt")
    ANALYZER_AVAILABLE = False


class TestResult:
    """Container for test results."""

    def __init__(self, test_name):
        self.test_name = test_name
        self.passed = False
        self.duration_ms = 0
        self.segments_detected = 0
        self.shapes_detected = []
        self.fit_errors = []
        self.avg_fit_error = 0
        self.area_method = 'unknown'
        self.transition_method = 'unknown'
        self.errors = []
        self.warnings = []

    def to_dict(self):
        """Convert to dictionary for JSON export."""
        return {
            'test_name': self.test_name,
            'passed': self.passed,
            'duration_ms': self.duration_ms,
            'segments_detected': self.segments_detected,
            'shapes_detected': self.shapes_detected,
            'fit_errors': self.fit_errors,
            'avg_fit_error': self.avg_fit_error,
            'area_method': self.area_method,
            'transition_method': self.transition_method,
            'errors': self.errors,
            'warnings': self.warnings
        }


def run_single_test(test_file, metadata, verbose=False):
    """
    Run analyzer on a single test case.

    Parameters:
    -----------
    test_file : str
        Path to CSV test file
    metadata : dict
        Test case metadata with expected results
    verbose : bool
        Print detailed information

    Returns:
    --------
    TestResult object
    """
    test_name = os.path.basename(test_file).replace('.csv', '')
    result = TestResult(test_name)

    if verbose:
        print(f"\n{'='*70}")
        print(f"Testing: {test_name}")
        print(f"Description: {metadata.get('description', 'N/A')}")
        print(f"Expected: {metadata.get('expected_segments')} segment(s), "
              f"{metadata.get('expected_shape')}")
        print(f"{'='*70}")

    try:
        start_time = time.time()

        # Create job tracker
        job = AnalysisJob(test_file)

        # Step 1: Load data
        df = load_data_csv(test_file, job=job, verbose=verbose)

        # Step 2: Compute areas (with improvements)
        df_areas = compute_areas(df, job=job, verbose=verbose,
                                 use_local_regression=DEFAULT_PARAMS['use_local_regression'])

        # Step 3: Segment and fit
        segments = segment_and_fit_optimized(df_areas, job=job, verbose=verbose)

        # Step 4: Generate profile
        z_profile, r_profile = create_enhanced_profile(
            segments, df_areas, job=job, verbose=verbose
        )

        # Record results
        result.duration_ms = (time.time() - start_time) * 1000
        result.segments_detected = len(segments)
        result.shapes_detected = [seg[2] for seg in segments]
        result.fit_errors = job.statistics.get('fit_errors', [])
        result.avg_fit_error = job.statistics.get('avg_fit_error', 0)
        result.area_method = job.statistics.get('area_method', 'unknown')
        result.transition_method = DEFAULT_PARAMS.get('transition_detection_method', 'unknown')

        # Validation
        expected_segments = metadata.get('expected_segments', None)
        if expected_segments is not None:
            if result.segments_detected == expected_segments:
                result.passed = True
            else:
                result.errors.append(
                    f"Segment count mismatch: expected {expected_segments}, got {result.segments_detected}"
                )

        # Check if expected shape was detected
        expected_shape = metadata.get('expected_shape', '')
        if expected_shape and '+' not in expected_shape:
            if expected_shape in result.shapes_detected:
                # Expected shape found
                pass
            else:
                result.warnings.append(
                    f"Expected shape '{expected_shape}' not found. Detected: {result.shapes_detected}"
                )

        # Report
        if verbose:
            print(f"\n📊 Results:")
            print(f"   Duration: {result.duration_ms:.2f} ms")
            print(f"   Segments: {result.segments_detected}")
            print(f"   Shapes: {result.shapes_detected}")
            print(f"   Fit errors: {[f'{e:.2f}%' for e in result.fit_errors]}")
            print(f"   Avg error: {result.avg_fit_error:.2f}%")
            print(f"   Area method: {result.area_method}")
            print(f"   Transition method: {result.transition_method}")

            if result.passed:
                print(f"   ✅ PASS")
            else:
                print(f"   ⚠️  PARTIAL PASS (see warnings)")

            if result.errors:
                print(f"   ❌ Errors: {result.errors}")
            if result.warnings:
                print(f"   ⚠️  Warnings: {result.warnings}")

    except Exception as e:
        result.errors.append(str(e))
        if verbose:
            print(f"   ❌ FAIL: {e}")
            import traceback
            traceback.print_exc()

    return result


def run_test_suite(test_dir='test_data', verbose=False):
    """
    Run all tests in the test directory.

    Returns:
    --------
    List of TestResult objects
    """
    # Load metadata
    metadata_file = os.path.join(test_dir, 'test_metadata.json')
    if not os.path.exists(metadata_file):
        print(f"❌ Metadata file not found: {metadata_file}")
        print("Run: python generate_test_data.py first")
        return []

    with open(metadata_file, 'r') as f:
        all_metadata = json.load(f)

    # Find all test CSV files
    test_files = sorted([
        os.path.join(test_dir, f)
        for f in os.listdir(test_dir)
        if f.endswith('.csv')
    ])

    if not test_files:
        print(f"❌ No test files found in {test_dir}/")
        return []

    print(f"\n{'='*70}")
    print(f"CONTAINER GEOMETRY ANALYZER - COMPREHENSIVE TEST SUITE")
    print(f"{'='*70}")
    print(f"Test directory: {test_dir}")
    print(f"Test cases: {len(test_files)}")
    print(f"Configuration:")
    print(f"  - Area method: {'local_regression' if DEFAULT_PARAMS['use_local_regression'] else 'legacy'}")
    print(f"  - Transition detection: {DEFAULT_PARAMS['transition_detection_method']}")
    print(f"  - Adaptive threshold: {DEFAULT_PARAMS['use_adaptive_threshold']}")
    print(f"{'='*70}\n")

    # Run tests
    results = []
    for test_file in test_files:
        test_name = os.path.basename(test_file).replace('.csv', '')
        metadata = all_metadata.get(test_name, {})

        result = run_single_test(test_file, metadata, verbose=verbose)
        results.append(result)

    return results


def generate_report(results, output_file='test_results.json'):
    """Generate comprehensive test report."""

    if not results:
        print("No results to report")
        return

    # Summary statistics
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r.passed and not r.errors)
    failed_tests = sum(1 for r in results if r.errors)
    warning_tests = sum(1 for r in results if r.warnings and not r.errors)

    total_duration = sum(r.duration_ms for r in results)
    avg_duration = total_duration / total_tests if total_tests > 0 else 0

    all_fit_errors = [e for r in results for e in r.fit_errors if r.fit_errors]
    avg_fit_error = sum(all_fit_errors) / len(all_fit_errors) if all_fit_errors else 0
    max_fit_error = max(all_fit_errors) if all_fit_errors else 0

    # Shape detection statistics
    shape_counts = {}
    for r in results:
        for shape in r.shapes_detected:
            shape_counts[shape] = shape_counts.get(shape, 0) + 1

    # Print summary
    print(f"\n{'='*70}")
    print(f"TEST RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"Total tests:     {total_tests}")
    print(f"Passed:          {passed_tests} ({100*passed_tests/total_tests:.1f}%)")
    print(f"With warnings:   {warning_tests} ({100*warning_tests/total_tests:.1f}%)")
    print(f"Failed:          {failed_tests} ({100*failed_tests/total_tests:.1f}%)")
    print()
    print(f"Performance:")
    print(f"  Total time:    {total_duration:.2f} ms")
    print(f"  Avg per test:  {avg_duration:.2f} ms")
    print()
    print(f"Fit Quality:")
    print(f"  Avg fit error: {avg_fit_error:.2f}%")
    print(f"  Max fit error: {max_fit_error:.2f}%")
    print()
    print(f"Shape Detection:")
    for shape, count in sorted(shape_counts.items()):
        print(f"  {shape:15s}: {count} occurrences")
    print(f"{'='*70}\n")

    # Detailed results by category
    categories = {
        'Simple Cylinders': [],
        'Cones': [],
        'Sphere Caps': [],
        'Frustums': [],
        'Composite Shapes': [],
        'Robustness Tests': []
    }

    for r in results:
        if 'cylinder' in r.test_name and 'composite' not in r.test_name:
            if 'noise' in r.test_name or 'sampling' in r.test_name:
                categories['Robustness Tests'].append(r)
            else:
                categories['Simple Cylinders'].append(r)
        elif 'cone' in r.test_name and 'composite' not in r.test_name:
            categories['Cones'].append(r)
        elif 'sphere' in r.test_name and 'composite' not in r.test_name:
            categories['Sphere Caps'].append(r)
        elif 'frustum' in r.test_name:
            categories['Frustums'].append(r)
        elif 'composite' in r.test_name:
            categories['Composite Shapes'].append(r)

    print("DETAILED RESULTS BY CATEGORY")
    print("=" * 70)

    for category, tests in categories.items():
        if not tests:
            continue

        print(f"\n{category}:")
        print("-" * 70)

        for r in tests:
            status = "✅" if r.passed and not r.errors else "⚠️ " if r.warnings else "❌"
            print(f"{status} {r.test_name:40s} | {r.segments_detected} seg | "
                  f"{r.avg_fit_error:5.2f}% err | {r.duration_ms:6.2f} ms")
            if r.errors:
                for err in r.errors:
                    print(f"      Error: {err}")
            if r.warnings:
                for warn in r.warnings:
                    print(f"      Warning: {warn}")

    # Save JSON report
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'configuration': {
            'area_method': 'local_regression' if DEFAULT_PARAMS['use_local_regression'] else 'legacy',
            'transition_detection': DEFAULT_PARAMS['transition_detection_method'],
            'adaptive_threshold': DEFAULT_PARAMS['use_adaptive_threshold']
        },
        'summary': {
            'total_tests': total_tests,
            'passed': passed_tests,
            'with_warnings': warning_tests,
            'failed': failed_tests,
            'pass_rate': 100 * passed_tests / total_tests if total_tests > 0 else 0,
            'total_duration_ms': total_duration,
            'avg_duration_ms': avg_duration,
            'avg_fit_error_pct': avg_fit_error,
            'max_fit_error_pct': max_fit_error,
            'shape_counts': shape_counts
        },
        'results': [r.to_dict() for r in results]
    }

    with open(output_file, 'w') as f:
        json.dump(report_data, f, indent=2)

    print(f"\n📄 Detailed report saved to: {output_file}")
    print(f"{'='*70}\n")

    return report_data


if __name__ == '__main__':
    if not ANALYZER_AVAILABLE:
        sys.exit(1)

    import argparse

    parser = argparse.ArgumentParser(description='Run comprehensive tests for Container Geometry Analyzer')
    parser.add_argument('--test-dir', default='test_data', help='Directory containing test CSV files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print detailed output')
    parser.add_argument('--output', '-o', default='test_results.json', help='Output JSON file')

    args = parser.parse_args()

    # Check if test data exists
    if not os.path.exists(args.test_dir):
        print(f"❌ Test directory not found: {args.test_dir}")
        print("\nGenerate test data first:")
        print("  python generate_test_data.py")
        sys.exit(1)

    # Run tests
    results = run_test_suite(args.test_dir, verbose=args.verbose)

    if results:
        # Generate report
        generate_report(results, args.output)

        # Exit code
        failed = sum(1 for r in results if r.errors)
        sys.exit(0 if failed == 0 else 1)
    else:
        print("❌ No tests were run")
        sys.exit(1)
