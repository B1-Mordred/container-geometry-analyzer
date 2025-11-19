#!/usr/bin/env python3
"""
Curvature Threshold Tuning Script
==================================

Systematically tests different curvature thresholds to find optimal balance
between composite shape detection and inflection point filtering.

Tests thresholds: 0.05, 0.08, 0.10, 0.12, 0.15, 0.20
"""

import os
import sys
import json
import subprocess
import re
from datetime import datetime

THRESHOLDS_TO_TEST = [0.05, 0.08, 0.10, 0.12, 0.15, 0.20]


def modify_threshold_in_source(threshold_value):
    """Modify the curvature threshold in the source file."""
    source_file = 'src/container_geometry_analyzer_gui_v3_11_8.py'

    with open(source_file, 'r') as f:
        content = f.read()

    pattern = r"'curvature_threshold': 0\.\d+"
    replacement = f"'curvature_threshold': {threshold_value}"
    new_content = re.sub(pattern, replacement, content)

    with open(source_file, 'w') as f:
        f.write(new_content)

    return new_content != content


def run_test_suite():
    """Run the comprehensive test suite and capture results."""
    result = subprocess.run(
        ['python', 'tests/run_comprehensive_tests.py'],
        env={**os.environ, 'PYTHONPATH': 'src:' + os.environ.get('PYTHONPATH', '')},
        capture_output=True,
        text=True,
        timeout=180
    )

    output = result.stdout + result.stderr

    pass_match = re.search(r'Total tests:\s+(\d+)', output)
    passed_match = re.search(r'Passed:\s+(\d+)', output)

    if pass_match and passed_match:
        total = int(pass_match.group(1))
        passed = int(passed_match.group(1))
        return {
            'total': total,
            'passed': passed,
            'pass_rate': (passed / total * 100) if total > 0 else 0,
            'output': output
        }

    return None


def extract_category_results(output):
    """Extract pass/fail by category from test output."""
    categories = {}
    lines = output.split('\n')
    current_category = None

    for line in lines:
        if line.startswith('Simple Cylinders:'):
            current_category = 'simple_cylinders'
        elif line.startswith('Cones:'):
            current_category = 'cones'
        elif line.startswith('Sphere Caps:'):
            current_category = 'sphere_caps'
        elif line.startswith('Frustums:'):
            current_category = 'frustums'
        elif line.startswith('Composite Shapes:'):
            current_category = 'composite_shapes'
        elif line.startswith('Robustness Tests:'):
            current_category = 'robustness'

        if current_category and ('✅' in line or '❌' in line):
            if current_category not in categories:
                categories[current_category] = {'passed': 0, 'failed': 0}

            if '✅' in line:
                categories[current_category]['passed'] += 1
            elif '❌' in line:
                categories[current_category]['failed'] += 1

    for cat in categories:
        total = categories[cat]['passed'] + categories[cat]['failed']
        categories[cat]['total'] = total
        categories[cat]['pass_rate'] = (
            categories[cat]['passed'] / total * 100 if total > 0 else 0
        )

    return categories


def main():
    """Main threshold tuning function."""
    print("\n" + "=" * 80)
    print("PRIORITY 2: CURVATURE THRESHOLD TUNING")
    print("=" * 80)
    print(f"Testing {len(THRESHOLDS_TO_TEST)} threshold values")

    results_by_threshold = []

    for threshold in THRESHOLDS_TO_TEST:
        print(f"\n{'─' * 80}")
        print(f"Testing Threshold: {threshold}")
        print(f"{'─' * 80}")

        if not modify_threshold_in_source(threshold):
            print(f"❌ Failed to modify threshold in source")
            continue

        print("Running test suite...")
        test_result = run_test_suite()

        if test_result:
            print(f"✅ Results: {test_result['passed']}/{test_result['total']} passed "
                  f"({test_result['pass_rate']:.1f}%)")

            category_results = extract_category_results(test_result['output'])

            print("\nResults by Category:")
            for cat in ['simple_cylinders', 'cones', 'sphere_caps', 'frustums',
                       'composite_shapes', 'robustness']:
                if cat in category_results:
                    stats = category_results[cat]
                    print(f"  {cat:<20} {stats['passed']}/{stats['total']:<3} "
                          f"({stats['pass_rate']:.1f}%)")

            results_by_threshold.append({
                'threshold': threshold,
                'total': test_result['total'],
                'passed': test_result['passed'],
                'pass_rate': test_result['pass_rate'],
                'by_category': category_results
            })
        else:
            print(f"❌ Failed to extract results from test output")

    # Summary
    print("\n\n" + "=" * 80)
    print("THRESHOLD TUNING SUMMARY")
    print("=" * 80)

    print(f"\n{'Threshold':<12} {'Pass Rate':<15} {'Passed':<15}")
    print("-" * 80)

    best_threshold = None
    best_pass_rate = 0

    for result in results_by_threshold:
        threshold = result['threshold']
        pass_rate = result['pass_rate']
        passed = result['passed']

        marker = " ← BEST" if pass_rate > best_pass_rate else ""
        print(f"{threshold:<12.2f} {pass_rate:<14.1f}% {passed}/{result['total']:<12}{marker}")

        if pass_rate > best_pass_rate:
            best_pass_rate = pass_rate
            best_threshold = threshold

    # Best threshold analysis
    print("\n\n" + "=" * 80)
    print(f"BEST THRESHOLD: {best_threshold} ({best_pass_rate:.1f}%)")
    print("=" * 80)

    best_result = next(r for r in results_by_threshold if r['threshold'] == best_threshold)

    print(f"\nOverall: {best_result['passed']}/{best_result['total']} passed")
    print("\nBy Category:")
    for cat in ['simple_cylinders', 'cones', 'sphere_caps', 'frustums',
               'composite_shapes', 'robustness']:
        if cat in best_result['by_category']:
            stats = best_result['by_category'][cat]
            status = "✅" if stats['pass_rate'] == 100 else "❌" if stats['pass_rate'] == 0 else "⚠️"
            print(f"  {status} {cat:<20} {stats['passed']}/{stats['total']:<3} "
                  f"({stats['pass_rate']:.1f}%)")

    # Save results
    results_file = f'threshold_tuning_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(results_file, 'w') as f:
        json_results = [
            {
                'threshold': r['threshold'],
                'pass_rate': r['pass_rate'],
                'total_passed': r['passed'],
                'total_tests': r['total'],
                'by_category': {
                    cat: {
                        'passed': stats['passed'],
                        'total': stats['total'],
                        'pass_rate': stats['pass_rate']
                    }
                    for cat, stats in r['by_category'].items()
                }
            }
            for r in results_by_threshold
        ]
        json.dump(json_results, f, indent=2)

    print(f"\n📄 Results saved to: {results_file}")
    print("=" * 80 + "\n")

    return best_threshold


if __name__ == '__main__':
    try:
        best = main()
        print(f"✅ Best threshold: {best}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
