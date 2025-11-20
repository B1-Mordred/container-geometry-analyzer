#!/usr/bin/env python3
"""
Comprehensive Assessment Test Runner
====================================

Runs the complete test suite with:
- 56 comprehensive test cases
- 1, 2, and 3 segment combinations
- Ideal and 2% pipetting error scenarios
- Detailed result analysis and reporting
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container_geometry_analyzer_gui_v3_11_8 import (
    load_data_csv,
    compute_areas,
    segment_and_fit_optimized,
)

def run_test(test_file):
    """Run a single test case and return results"""
    try:
        df = load_data_csv(test_file)
        df = compute_areas(df)  # Compute areas before segmentation
        segments = segment_and_fit_optimized(df, verbose=False)

        segment_count = len(segments)
        shapes_detected = [seg[2] for seg in segments]

        return {
            'success': True,
            'segments_detected': segment_count,
            'shapes_detected': shapes_detected,
            'error': None
        }
    except Exception as e:
        return {
            'success': False,
            'segments_detected': 0,
            'shapes_detected': [],
            'error': str(e)
        }

def main():
    """Run comprehensive assessment"""
    print("\n" + "="*80)
    print("COMPREHENSIVE ASSESSMENT TEST RUN")
    print("="*80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    test_dir = Path('test_data_comprehensive')

    if not test_dir.exists():
        print(f"❌ Test data directory not found: {test_dir}")
        print("   Run: python tests/generate_comprehensive_tests.py")
        return

    # Load metadata
    metadata_file = test_dir / 'comprehensive_metadata.json'
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    print(f"\nTest cases to run: {len(metadata['test_cases'])}")

    # Run all tests
    results = []
    print("\nRunning tests...")

    for idx, test_case in enumerate(metadata['test_cases']):
        test_file = test_case['file']
        description = test_case['description']
        expected_segments = test_case['expected_segments']
        expected_shapes = test_case['expected_shapes']

        # Run test
        start = time.time()
        result = run_test(test_file)
        elapsed = time.time() - start

        # Check if passed
        passed = (result['segments_detected'] == expected_segments and
                 result['success'])

        result['test_file'] = test_file
        result['description'] = description
        result['expected_segments'] = expected_segments
        result['expected_shapes'] = expected_shapes
        result['passed'] = passed
        result['elapsed'] = elapsed

        results.append(result)

        # Progress indicator
        status = "✅" if passed else "❌"
        print(f"  {status} [{idx+1:2d}/{len(metadata['test_cases'])}] {Path(test_file).name:<50} "
              f"({result['segments_detected']}/{expected_segments} segs, {elapsed*1000:.0f}ms)")

    # Analysis
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)

    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    pass_rate = 100 * passed_count / total_count

    print(f"\nOverall: {passed_count}/{total_count} passed ({pass_rate:.1f}%)")
    print(f"Total time: {sum(r['elapsed'] for r in results):.2f}s")
    print(f"Avg per test: {np.mean([r['elapsed'] for r in results])*1000:.1f}ms")

    # Breakdown by category
    print("\n" + "-"*80)
    print("RESULTS BY CATEGORY")
    print("-"*80)

    # By segment count
    print("\nBy Segment Count:")
    for seg_count in [1, 2, 3]:
        seg_results = [r for r in results if r['expected_segments'] == seg_count]
        if seg_results:
            seg_passed = sum(1 for r in seg_results if r['passed'])
            seg_rate = 100 * seg_passed / len(seg_results)
            print(f"  {seg_count}-segment: {seg_passed}/{len(seg_results)} ({seg_rate:.1f}%)")

    # By error scenario
    print("\nBy Error Scenario:")
    for scenario in ['ideal', '2_percent_pipetting_error']:
        scenario_results = [r for r in results if scenario in r['test_file']]
        if scenario_results:
            scenario_passed = sum(1 for r in scenario_results if r['passed'])
            scenario_rate = 100 * scenario_passed / len(scenario_results)
            scenario_label = "Ideal data" if scenario == 'ideal' else "2% pipetting error"
            print(f"  {scenario_label}: {scenario_passed}/{len(scenario_results)} ({scenario_rate:.1f}%)")

    # By tube type
    print("\nBy Tube Type:")
    tube_types = {}
    for r in results:
        # Extract tube type from filename
        fname = Path(r['test_file']).stem
        if fname.startswith('composite'):
            tube_type = 'composite'
        else:
            tube_type = fname.split('_')[0]

        if tube_type not in tube_types:
            tube_types[tube_type] = {'passed': 0, 'total': 0}

        tube_types[tube_type]['total'] += 1
        if r['passed']:
            tube_types[tube_type]['passed'] += 1

    for tube_type in sorted(tube_types.keys()):
        stats = tube_types[tube_type]
        rate = 100 * stats['passed'] / stats['total']
        print(f"  {tube_type:<15}: {stats['passed']:2d}/{stats['total']:2d} ({rate:5.1f}%)")

    # By diameter
    print("\nBy Diameter:")
    diameters = {}
    for r in results:
        fname = Path(r['test_file']).stem
        # Extract diameter (e.g., "5mm", "10mm", "15mm")
        if '_5mm' in fname or 'composite_' in fname and fname.split('_')[2].startswith('5'):
            diameter = '5mm'
        elif '_10mm' in fname or 'composite_' in fname and fname.split('_')[2].startswith('10'):
            diameter = '10mm'
        elif '_15mm' in fname or 'composite_' in fname and fname.split('_')[2].startswith('15'):
            diameter = '15mm'
        elif '_8mm' in fname:
            diameter = '8mm'
        else:
            diameter = 'unknown'

        if diameter not in diameters:
            diameters[diameter] = {'passed': 0, 'total': 0}

        diameters[diameter]['total'] += 1
        if r['passed']:
            diameters[diameter]['passed'] += 1

    for diameter in sorted(diameters.keys()):
        stats = diameters[diameter]
        rate = 100 * stats['passed'] / stats['total']
        print(f"  {diameter:<15}: {stats['passed']:2d}/{stats['total']:2d} ({rate:5.1f}%)")

    # Failed tests details
    failed = [r for r in results if not r['passed']]
    if failed:
        print("\n" + "-"*80)
        print(f"FAILED TESTS ({len(failed)})")
        print("-"*80)
        for r in failed[:10]:  # Show first 10
            fname = Path(r['test_file']).name
            print(f"  ❌ {fname:<50} "
                  f"Expected {r['expected_segments']}, got {r['segments_detected']}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")

    # Save detailed results
    results_file = f'assessment_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    results_json = []
    for r in results:
        results_json.append({
            'file': r['test_file'],
            'description': r['description'],
            'expected_segments': r['expected_segments'],
            'expected_shapes': r['expected_shapes'],
            'segments_detected': r['segments_detected'],
            'shapes_detected': r['shapes_detected'],
            'passed': r['passed'],
            'elapsed_ms': round(r['elapsed'] * 1000, 1)
        })

    with open(results_file, 'w') as f:
        json.dump({
            'test_run': datetime.now().isoformat(),
            'total_tests': total_count,
            'passed': passed_count,
            'pass_rate_percent': round(pass_rate, 1),
            'results': results_json
        }, f, indent=2)

    print(f"\n📄 Results saved to: {results_file}")

    print("\n" + "="*80)
    print("END OF TEST RUN")
    print("="*80 + "\n")

    return pass_rate

if __name__ == '__main__':
    pass_rate = main()
    sys.exit(0 if pass_rate >= 70 else 1)
