#!/usr/bin/env python3
"""
Phase 2 Testing with Medium Confidence Threshold
================================================

Tests selective routing with confidence='medium' instead of 'high'
to see if lower routing threshold improves results.
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


def run_test_medium_confidence(test_file):
    """Run test with medium confidence threshold"""
    try:
        DEFAULT_PARAMS['use_selective_detection'] = True
        DEFAULT_PARAMS['selective_confidence_threshold'] = 'medium'

        df = load_data_csv(test_file)
        df = compute_areas(df)
        segments = segment_and_fit_optimized(df, verbose=False)

        return {
            'success': True,
            'segments_detected': len(segments),
            'shapes_detected': [seg[2] for seg in segments],
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
        DEFAULT_PARAMS['use_selective_detection'] = False


def main():
    """Test with medium confidence"""
    print("\n" + "="*80)
    print("PHASE 2 - MEDIUM CONFIDENCE THRESHOLD TEST")
    print("="*80)

    test_dir = Path('test_data_comprehensive')

    if not test_dir.exists():
        print(f"❌ Test data directory not found: {test_dir}")
        return

    metadata_file = test_dir / 'comprehensive_metadata.json'
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)

    # Load baseline results
    baseline_file = Path('assessment_results_phase2_20251120_094123.json')
    with open(baseline_file, 'r') as f:
        baseline_data = json.load(f)

    baseline_results = {r['test_file']: r for r in baseline_data['results']}

    print(f"\nTesting {len(metadata['test_cases'])} cases with confidence='medium'...\n")

    results = []
    improved_count = 0
    regressed_count = 0

    for idx, test_case in enumerate(metadata['test_cases'], 1):
        test_file = test_case['file']
        description = test_case['description']
        expected_segments = test_case['expected_segments']

        # Get baseline result
        baseline_result = baseline_results.get(test_file, {})
        baseline_passed = baseline_result.get('baseline', {}).get('passed', False)
        high_conf_passed = baseline_result.get('phase2', {}).get('passed', False)

        # Run with medium confidence
        result = run_test_medium_confidence(test_file)
        medium_conf_passed = (result['segments_detected'] == expected_segments and
                             result['success'])

        # Compare: medium confidence vs. high confidence
        improvement = "✅ IMPROVED" if (medium_conf_passed and not high_conf_passed) else ""
        regression = "❌ REGRESSED" if (not medium_conf_passed and high_conf_passed) else ""

        if medium_conf_passed and not high_conf_passed:
            improved_count += 1
        if not medium_conf_passed and high_conf_passed:
            regressed_count += 1

        status = "✅" if medium_conf_passed else "❌"
        print(f"[{idx:2d}] {status} {description} {improvement}{regression}")

        results.append({
            'test_file': test_file,
            'expected': expected_segments,
            'medium_conf': result['segments_detected'],
            'medium_passed': medium_conf_passed,
            'high_conf_passed': high_conf_passed,
            'baseline_passed': baseline_passed
        })

    # Summary
    medium_passed = sum(1 for r in results if r['medium_passed'])
    high_passed = sum(1 for r in results if r['high_conf_passed'])

    print("\n" + "="*80)
    print("COMPARISON: High Confidence vs. Medium Confidence")
    print("="*80)
    print(f"High confidence (current):   {high_passed}/{len(results)} ({100*high_passed/len(results):.1f}%)")
    print(f"Medium confidence (test):    {medium_passed}/{len(results)} ({100*medium_passed/len(results):.1f}%)")
    print(f"Baseline (no selective):     {baseline_data['summary']['baseline_passed']}/{len(results)} ({100*baseline_data['summary']['baseline_passed']/len(results):.1f}%)")
    print(f"\nMedium confidence vs. high:")
    print(f"  Improved: {improved_count} tests")
    print(f"  Regressed: {regressed_count} tests")

    return medium_passed


if __name__ == "__main__":
    main()
