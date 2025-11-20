#!/usr/bin/env python3
"""
Phase 2 Comprehensive Assessment Test Runner
=============================================

Runs the complete test suite with Phase 2 selective routing ENABLED
to evaluate the conservative integration strategy.

Compares:
- Phase 1-3 baseline (use_selective_detection = False)
- Phase 2 selective routing (use_selective_detection = True)
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
    DEFAULT_PARAMS,
)


def run_test_baseline(test_file):
    """Run a single test case using baseline (Phase 1-3)"""
    try:
        # Ensure Phase 2 is disabled
        DEFAULT_PARAMS['use_selective_detection'] = False

        df = load_data_csv(test_file)
        df = compute_areas(df)
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


def run_test_phase2(test_file):
    """Run a single test case using Phase 2 selective routing"""
    try:
        # Enable Phase 2
        DEFAULT_PARAMS['use_selective_detection'] = True
        DEFAULT_PARAMS['selective_confidence_threshold'] = 'high'

        df = load_data_csv(test_file)
        df = compute_areas(df)
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
    finally:
        # Always reset to baseline for safety
        DEFAULT_PARAMS['use_selective_detection'] = False


def main():
    """Run comprehensive assessment with Phase 2"""
    print("\n" + "="*80)
    print("PHASE 2 SELECTIVE ROUTING - COMPREHENSIVE ASSESSMENT")
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
    print("\nRunning with TWO CONFIGURATIONS:")
    print("  1. Baseline (Phase 1-3): use_selective_detection = False")
    print("  2. Phase 2: use_selective_detection = True (high confidence)")

    # Run all tests with both configurations
    results = []
    print("\nRunning tests...\n")

    for idx, test_case in enumerate(metadata['test_cases'], 1):
        test_file = test_case['file']
        description = test_case['description']
        expected_segments = test_case['expected_segments']
        expected_shapes = test_case['expected_shapes']

        # Run baseline
        start = time.time()
        result_baseline = run_test_baseline(test_file)
        elapsed_baseline = time.time() - start

        # Run Phase 2
        start = time.time()
        result_phase2 = run_test_phase2(test_file)
        elapsed_phase2 = time.time() - start

        # Check if passed
        passed_baseline = (result_baseline['segments_detected'] == expected_segments and
                          result_baseline['success'])
        passed_phase2 = (result_phase2['segments_detected'] == expected_segments and
                        result_phase2['success'])

        result = {
            'test_file': test_file,
            'description': description,
            'expected_segments': expected_segments,
            'expected_shapes': expected_shapes,
            'baseline': {
                **result_baseline,
                'passed': passed_baseline,
                'elapsed': elapsed_baseline
            },
            'phase2': {
                **result_phase2,
                'passed': passed_phase2,
                'elapsed': elapsed_phase2
            },
            'improved': passed_phase2 and not passed_baseline,
            'regressed': not passed_phase2 and passed_baseline,
        }

        results.append(result)

        # Show progress
        status_baseline = "✅" if passed_baseline else "❌"
        status_phase2 = "✅" if passed_phase2 else "❌"
        change = ""
        if result['improved']:
            change = " 📈 IMPROVED"
        elif result['regressed']:
            change = " 📉 REGRESSED"

        print(f"[{idx:2d}/{len(metadata['test_cases'])}] {status_baseline} → {status_phase2} {description}{change}")

    # Analyze results
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)

    baseline_passed = sum(1 for r in results if r['baseline']['passed'])
    phase2_passed = sum(1 for r in results if r['phase2']['passed'])
    improved = sum(1 for r in results if r['improved'])
    regressed = sum(1 for r in results if r['regressed'])

    print(f"\nOVERALL ACCURACY:")
    print(f"  Baseline (Phase 1-3): {baseline_passed}/{len(results)} ({100*baseline_passed/len(results):.1f}%)")
    print(f"  Phase 2 Selective:    {phase2_passed}/{len(results)} ({100*phase2_passed/len(results):.1f}%)")
    print(f"  Change: {phase2_passed - baseline_passed:+d} ({(phase2_passed - baseline_passed)*100/len(results):+.1f}%)")

    print(f"\nPERFORMANCE CHANGES:")
    print(f"  Improved: {improved} tests")
    print(f"  Regressed: {regressed} tests")
    print(f"  Unchanged: {len(results) - improved - regressed} tests")

    # Analyze by segment count
    print(f"\nBY SEGMENT COUNT:")
    for seg_count in sorted(set(r['expected_segments'] for r in results)):
        seg_results = [r for r in results if r['expected_segments'] == seg_count]
        baseline_acc = sum(1 for r in seg_results if r['baseline']['passed']) / len(seg_results)
        phase2_acc = sum(1 for r in seg_results if r['phase2']['passed']) / len(seg_results)
        change = phase2_acc - baseline_acc
        print(f"  {seg_count}-segment: {baseline_acc*100:.1f}% → {phase2_acc*100:.1f}% ({change:+.1f}%)")

    # Analyze by diameter
    print(f"\nBY DIAMETER:")
    for test_case in metadata['test_cases']:
        # Extract diameter from description if available
        pass

    # Performance metrics
    baseline_times = [r['baseline']['elapsed'] for r in results]
    phase2_times = [r['phase2']['elapsed'] for r in results]
    print(f"\nPERFORMANCE METRICS:")
    print(f"  Baseline avg: {np.mean(baseline_times)*1000:.1f}ms ± {np.std(baseline_times)*1000:.1f}ms")
    print(f"  Phase 2 avg:  {np.mean(phase2_times)*1000:.1f}ms ± {np.std(phase2_times)*1000:.1f}ms")
    print(f"  Overhead: {(np.mean(phase2_times) - np.mean(baseline_times))*1000:+.1f}ms")

    # Save detailed results
    output_file = f"assessment_results_phase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'baseline': 'Phase 1-3 (use_selective_detection=False)',
                'phase2': 'Phase 2 (use_selective_detection=True, confidence=high)'
            },
            'summary': {
                'total_tests': len(results),
                'baseline_passed': baseline_passed,
                'phase2_passed': phase2_passed,
                'improved': improved,
                'regressed': regressed,
                'baseline_accuracy': f"{100*baseline_passed/len(results):.1f}%",
                'phase2_accuracy': f"{100*phase2_passed/len(results):.1f}%",
            },
            'results': results
        }, f, indent=2)

    print(f"\n✅ Detailed results saved to: {output_file}")

    # Decision
    print("\n" + "="*80)
    print("DECISION GATE - STAGE 2 COMPLETION")
    print("="*80)

    if regressed > 0:
        print(f"⚠️  WARNING: {regressed} regressions detected")
        print("   Recommendation: Fix regressions before proceeding to parameter tuning")
        return False
    elif improved > 0:
        print(f"✅ PASS: {improved} improvements detected, no regressions")
        print("   Recommendation: Proceed to Stage 3 parameter tuning")
        return True
    else:
        print(f"✅ PASS: No regressions, behavior consistent with baseline")
        print("   Recommendation: Proceed to Stage 3 (or maintain current configuration)")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
