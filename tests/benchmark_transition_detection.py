"""
Performance Benchmarks for Transition Detection
================================================

Compare legacy vs improved transition detection on sample data and synthetic tests.

Author: Container Geometry Analyzer Team
Date: 2025-11-19
"""

import numpy as np
import pandas as pd
import time
import sys
import os

# Import from main file
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from container_geometry_analyzer_gui_v3_11_8 import (
    find_optimal_transitions,
    find_optimal_transitions_improved,
    load_data_csv,
    compute_areas
)


def benchmark_single_test(area, heights, test_name, verbose=True):
    """Benchmark both methods on a single test case."""

    results = {
        'test_name': test_name,
        'n_points': len(area),
    }

    # Test Legacy Method
    start_time = time.time()
    trans_legacy = find_optimal_transitions(area, verbose=False)
    legacy_time = time.time() - start_time

    results['legacy_time_ms'] = legacy_time * 1000
    results['legacy_segments'] = len(trans_legacy) - 1
    results['legacy_transitions'] = trans_legacy

    # Test Improved Method
    start_time = time.time()
    trans_improved = find_optimal_transitions_improved(area, heights, verbose=False)
    improved_time = time.time() - start_time

    results['improved_time_ms'] = improved_time * 1000
    results['improved_segments'] = len(trans_improved) - 1
    results['improved_transitions'] = trans_improved

    # Compare
    results['speedup_ratio'] = legacy_time / improved_time if improved_time > 0 else 0
    results['segments_diff'] = abs(results['legacy_segments'] - results['improved_segments'])

    if verbose:
        print(f"\n{'='*70}")
        print(f"Test: {test_name}")
        print(f"{'='*70}")
        print(f"Data points: {results['n_points']}")
        print(f"\nLegacy Method:")
        print(f"  Time: {results['legacy_time_ms']:.2f} ms")
        print(f"  Segments detected: {results['legacy_segments']}")
        print(f"  Transitions at: {trans_legacy}")
        print(f"\nImproved Method:")
        print(f"  Time: {results['improved_time_ms']:.2f} ms")
        print(f"  Segments detected: {results['improved_segments']}")
        print(f"  Transitions at: {trans_improved}")
        print(f"\nComparison:")
        print(f"  Speed ratio: {results['speedup_ratio']:.2f}x")
        print(f"  Segment count difference: {results['segments_diff']}")

        if results['improved_time_ms'] < results['legacy_time_ms']:
            print(f"  ✅ Improved method is FASTER by {((legacy_time - improved_time)/legacy_time)*100:.1f}%")
        else:
            print(f"  ⚠️  Improved method is slower by {((improved_time - legacy_time)/legacy_time)*100:.1f}%")

    return results


def generate_synthetic_testcases():
    """Generate synthetic test cases with known properties."""

    np.random.seed(42)
    test_cases = []

    # Test 1: Single perfect cylinder
    n = 50
    area = np.ones(n) * 100.0
    heights = np.arange(n) * 0.5
    test_cases.append(('Perfect Cylinder', area, heights, {'expected_segments': 1}))

    # Test 2: Single noisy cylinder
    area = np.ones(50) * 100.0 + np.random.normal(0, 2, 50)
    heights = np.arange(50) * 0.5
    test_cases.append(('Noisy Cylinder', area, heights, {'expected_segments': 1}))

    # Test 3: Two distinct cylinders (step change)
    seg1 = np.ones(30) * 100.0
    seg2 = np.ones(30) * 200.0
    area = np.concatenate([seg1, seg2])
    heights = np.arange(60) * 0.5
    test_cases.append(('Step Change (2 Cylinders)', area, heights, {'expected_segments': 2}))

    # Test 4: Cylinder-Frustum-Cylinder
    seg1 = np.ones(30) * 314.16 + np.random.normal(0, 1, 30)
    seg2 = np.linspace(314.16, 706.86, 25) + np.random.normal(0, 1, 25)
    seg3 = np.ones(20) * 706.86 + np.random.normal(0, 1, 20)
    area = np.concatenate([seg1, seg2, seg3])
    heights = np.arange(len(area)) * 0.5
    test_cases.append(('Cyl-Frustum-Cyl', area, heights, {'expected_segments': 3}))

    # Test 5: Gentle frustum (hard to detect)
    area = np.linspace(314.16, 380.13, 60) + np.random.normal(0, 2, 60)
    heights = np.arange(60) * 0.5
    test_cases.append(('Gentle Frustum', area, heights, {'expected_segments': 1}))

    # Test 6: Very noisy data
    area = np.ones(50) * 100.0 + np.random.normal(0, 30, 50)
    heights = np.arange(50) * 0.5
    test_cases.append(('High Noise (SNR<5)', area, heights, {'expected_segments': 1}))

    # Test 7: Complex multi-segment (4 segments)
    seg1 = np.ones(20) * 100 + np.random.normal(0, 1, 20)
    seg2 = np.linspace(100, 200, 20) + np.random.normal(0, 1, 20)
    seg3 = np.ones(20) * 200 + np.random.normal(0, 1, 20)
    seg4 = np.linspace(200, 150, 20) + np.random.normal(0, 1, 20)
    area = np.concatenate([seg1, seg2, seg3, seg4])
    heights = np.arange(len(area)) * 0.5
    test_cases.append(('Complex (4 segments)', area, heights, {'expected_segments': 4}))

    # Test 8: Large dataset (performance test)
    n = 200
    seg1 = np.ones(100) * 100 + np.random.normal(0, 2, 100)
    seg2 = np.linspace(100, 200, 100) + np.random.normal(0, 2, 100)
    area = np.concatenate([seg1, seg2])
    heights = np.arange(n) * 0.5
    test_cases.append(('Large Dataset (200 pts)', area, heights, {'expected_segments': 2}))

    return test_cases


def benchmark_real_data():
    """Benchmark on real sample CSV files."""

    print("\n" + "="*70)
    print("BENCHMARKING ON REAL SAMPLE DATA")
    print("="*70)

    results = []

    # Try to load sample files
    sample_files = [
        'sample_2ml_tube_geometry_corrected.csv',
        'simulated_container_eppi_50uL.csv'
    ]

    for filename in sample_files:
        if not os.path.exists(filename):
            print(f"\n⚠️  Sample file not found: {filename}")
            continue

        print(f"\nLoading: {filename}")

        try:
            # Load and prepare data
            df = load_data_csv(filename, verbose=False)
            df_areas = compute_areas(df, verbose=False)

            area = df_areas['Area'].values
            heights = df_areas['Height_mm'].values

            # Run benchmark
            result = benchmark_single_test(area, heights, filename, verbose=True)
            results.append(result)

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    return results


def benchmark_synthetic_data():
    """Benchmark on synthetic test cases."""

    print("\n" + "="*70)
    print("BENCHMARKING ON SYNTHETIC TEST CASES")
    print("="*70)

    test_cases = generate_synthetic_testcases()
    results = []

    for test_name, area, heights, metadata in test_cases:
        result = benchmark_single_test(area, heights, test_name, verbose=True)
        result['expected_segments'] = metadata.get('expected_segments', None)

        # Check accuracy
        if result['expected_segments']:
            legacy_accurate = result['legacy_segments'] == result['expected_segments']
            improved_accurate = result['improved_segments'] == result['expected_segments']

            result['legacy_accurate'] = legacy_accurate
            result['improved_accurate'] = improved_accurate

            print(f"\nAccuracy:")
            print(f"  Expected segments: {result['expected_segments']}")
            print(f"  Legacy correct: {'✅' if legacy_accurate else '❌'}")
            print(f"  Improved correct: {'✅' if improved_accurate else '❌'}")

        results.append(result)

    return results


def print_summary(results):
    """Print overall summary statistics."""

    print("\n" + "="*70)
    print("OVERALL BENCHMARK SUMMARY")
    print("="*70)

    if not results:
        print("No results to summarize.")
        return

    # Aggregate statistics
    total_tests = len(results)

    legacy_times = [r['legacy_time_ms'] for r in results]
    improved_times = [r['improved_time_ms'] for r in results]

    legacy_correct = sum(1 for r in results if r.get('legacy_accurate', False))
    improved_correct = sum(1 for r in results if r.get('improved_accurate', False))
    accuracy_tests = sum(1 for r in results if 'legacy_accurate' in r)

    print(f"\nTests run: {total_tests}")
    print(f"Tests with known ground truth: {accuracy_tests}")

    print(f"\nPerformance:")
    print(f"  Legacy avg time: {np.mean(legacy_times):.2f} ms")
    print(f"  Improved avg time: {np.mean(improved_times):.2f} ms")
    print(f"  Average speedup: {np.mean(legacy_times)/np.mean(improved_times):.2f}x")

    if accuracy_tests > 0:
        print(f"\nAccuracy:")
        print(f"  Legacy accuracy: {legacy_correct}/{accuracy_tests} ({100*legacy_correct/accuracy_tests:.1f}%)")
        print(f"  Improved accuracy: {improved_correct}/{accuracy_tests} ({100*improved_correct/accuracy_tests:.1f}%)")
        print(f"  Improvement: {((improved_correct - legacy_correct)/accuracy_tests)*100:+.1f}%")

    # Segment count statistics
    legacy_segments = [r['legacy_segments'] for r in results]
    improved_segments = [r['improved_segments'] for r in results]

    print(f"\nSegment Detection:")
    print(f"  Legacy avg segments: {np.mean(legacy_segments):.2f}")
    print(f"  Improved avg segments: {np.mean(improved_segments):.2f}")

    # Create results table
    print(f"\nDetailed Results:")
    print(f"{'Test Name':<30} {'Legacy':<10} {'Improved':<10} {'Diff':<10} {'Time Ratio':<12}")
    print("-" * 72)

    for r in results:
        test_name = r['test_name'][:28]
        legacy_seg = f"{r['legacy_segments']} segs"
        improved_seg = f"{r['improved_segments']} segs"
        diff = f"{r['segments_diff']:+d}"
        time_ratio = f"{r['speedup_ratio']:.2f}x"

        print(f"{test_name:<30} {legacy_seg:<10} {improved_seg:<10} {diff:<10} {time_ratio:<12}")

    print("="*70)


def export_results_csv(results, filename='benchmark_results.csv'):
    """Export benchmark results to CSV."""

    if not results:
        print("No results to export.")
        return

    # Convert to DataFrame
    df = pd.DataFrame(results)

    # Select relevant columns
    columns = [
        'test_name', 'n_points',
        'legacy_time_ms', 'legacy_segments',
        'improved_time_ms', 'improved_segments',
        'speedup_ratio', 'segments_diff'
    ]

    # Add accuracy columns if available
    if 'legacy_accurate' in df.columns:
        columns.extend(['expected_segments', 'legacy_accurate', 'improved_accurate'])

    df_export = df[columns]

    # Save
    df_export.to_csv(filename, index=False)
    print(f"\n💾 Results exported to: {filename}")


def main():
    """Run all benchmarks."""

    print("="*70)
    print("TRANSITION DETECTION ALGORITHM BENCHMARKS")
    print("="*70)
    print("\nComparing:")
    print("  - Legacy method: First derivative + fixed threshold")
    print("  - Improved method: Multi-derivative + adaptive threshold")
    print("="*70)

    all_results = []

    # Run synthetic benchmarks
    synthetic_results = benchmark_synthetic_data()
    all_results.extend(synthetic_results)

    # Run real data benchmarks
    real_results = benchmark_real_data()
    all_results.extend(real_results)

    # Print summary
    print_summary(all_results)

    # Export results
    export_results_csv(all_results)

    print("\n✅ Benchmarks complete!\n")

    return all_results


if __name__ == "__main__":
    results = main()
