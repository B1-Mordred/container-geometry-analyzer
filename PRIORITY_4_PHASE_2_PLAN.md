# Priority 4: Phase 2 Implementation Plan
## Conservative Integration Strategy

**Status:** Planning
**Approach:** Option A - Conservative Integration
**Timeline:** 2-3 weeks
**Risk Level:** LOW

---

## Executive Summary

Phase 2 will implement selective integration of the Priority 4 stability detection foundation, using it ONLY for high-confidence 3-segment predictions while maintaining the proven multi-derivative algorithm as the default. This conservative approach minimizes risk of regression while providing targeted improvement for multi-segment containers.

**Expected Outcome:**
- Maintain baseline: 60.7% overall
- Improve 3-segment: 25% → 40-50% (gain 3-6 tests)
- No regression: Single-shape and 2-segment unchanged

---

## Phase 2: Integration Strategy

### Architecture

```
ROUTING LOGIC:
    Predict segment count (ensemble)
         ↓
    IF (predicted_segs >= 3) AND (confidence == 'high'):
    │   ├─ Use stability method
    │   └─ Validate result
    ELSE:
    │   └─ Use multi-derivative (proven baseline)
         ↓
    Return transition points
```

### Implementation Stages

#### Stage 1: Selective Routing (Week 1)
**Goal:** Add routing logic without changing existing behavior

```python
def find_optimal_transitions_selective(area, heights, ...):
    """
    Hybrid transition detection with conservative routing.

    Only uses stability method for high-confidence 3-segment.
    Falls back to multi-derivative for all other cases.
    """
    # Fast segment count prediction
    predicted_segments, confidence = predict_segment_count(area, heights)

    # Conservative routing
    if predicted_segments >= 3 and confidence == 'high':
        # Use stability method
        transitions = find_stability_transitions(area, heights, ...)
        transitions = validate_all_transitions(area, heights, transitions)
        method_used = 'stability'
    else:
        # Use proven multi-derivative
        transitions = find_optimal_transitions_improved(area, heights, ...)
        method_used = 'multi-derivative'

    return transitions, method_used
```

#### Stage 2: Integration into Main Algorithm (Week 1)
**Goal:** Replace current transition detection with selective version

```python
# In segment_and_fit_optimized():

if DEFAULT_PARAMS.get('use_selective_detection', False):
    # Phase 2: Use selective hybrid routing
    transitions, method = find_optimal_transitions_selective(
        area, heights, min_points=..., verbose=verbose
    )
    if verbose:
        logger.info(f"🎯 Used {method} method (predicted: {predicted_segments} seg)")
else:
    # Phase 1-3: Use original improved detection
    transitions = find_optimal_transitions_improved(
        area, heights, ..., diameter_mm=estimated_diameter
    )
```

#### Stage 3: Testing and Validation (Week 2)
**Goal:** Verify routing works correctly and doesn't introduce regressions

Tests to run:
- ✅ Comprehensive suite (56 cases) with Phase 2 enabled
- ✅ Regression testing (ensure 1-2 segment unchanged)
- ✅ 3-segment improvement analysis
- ✅ Performance profiling (<30ms per test)
- ✅ Edge case handling

#### Stage 4: Parameter Tuning (Week 2)
**Goal:** Optimize thresholds for production

Parameters to tune:
- Confidence threshold for routing (currently 'high')
- Stability detection thresholds
- Spacing constraints
- Window sizes

Tuning approach:
- Grid search on key parameters
- Measure accuracy on 3-segment cases
- Verify no regression on others
- Select best combination

#### Stage 5: Documentation and Deployment (Week 3)
**Goal:** Document approach and prepare for rollout

Deliverables:
- ✅ Phase 2 completion report
- ✅ User documentation
- ✅ Deployment guide
- ✅ Rollback procedures
- ✅ Monitoring setup

---

## Phase 2: Success Criteria

### Must-Have (Gate 1: Must Pass)
- [ ] Comprehensive test suite: ≥60% (maintain baseline)
- [ ] 3-segment tests: ≥ 25% (maintain, trying for more)
- [ ] 1-segment tests: ≥ 83% (no regression)
- [ ] 2-segment tests: ≥ 50% (no regression)
- [ ] All unit tests: Passing
- [ ] Performance: <30ms average per test

### Should-Have (Gate 2: Target)
- [ ] 3-segment improvement: 25% → 40%+ (6+ tests)
- [ ] Confidence mechanism: Working correctly
- [ ] Routing logic: Correct method selection
- [ ] Error handling: Graceful fallbacks

### Nice-to-Have (Gate 3: Bonus)
- [ ] 3-segment improvement: 25% → 50%+ (8+ tests)
- [ ] 2-segment improvement: 50% → 55%+ (bonus)
- [ ] Performance optimization: <25ms average
- [ ] Monitoring dashboard: Tracking metrics

---

## Phase 2: Detailed Implementation

### Step 1: Add Configuration Parameter

**File:** `src/container_geometry_analyzer_gui_v3_11_8.py`

```python
DEFAULT_PARAMS = {
    # ... existing params ...
    'use_selective_detection': False,  # NEW: Toggle for Phase 2
    'selective_confidence_threshold': 'high',  # high/medium
    'min_3segment_confidence': 'high',
}
```

### Step 2: Implement Selective Routing Function

**File:** `src/container_geometry_analyzer_gui_v3_11_8.py`

```python
def find_optimal_transitions_selective(area, heights, min_points=12,
                                      diameter_mm=None, use_adaptive=True,
                                      confidence_threshold='high',
                                      verbose=False):
    """
    Selective hybrid transition detection.

    Uses stability method for high-confidence 3-segment,
    falls back to multi-derivative for all other cases.

    Conservative approach: favors stability over risk.
    """
    n = len(area)

    if n < 2 * min_points:
        return [0, n - 1], 'insufficient_data'

    try:
        # Step 1: Predict segment count
        predicted_segs, seg_details = predict_segment_count(
            area, heights, verbose=verbose
        )

        if verbose:
            logger.info(f"🎯 Segment prediction: {predicted_segs} "
                       f"({seg_details['confidence']} confidence)")

        # Step 2: Selective routing
        should_use_stability = (
            predicted_segs >= 3 and
            seg_details['confidence'] == confidence_threshold
        )

        if should_use_stability:
            if verbose:
                logger.info("🔄 High-confidence 3-segment: Using stability method")

            # Use stability detection
            transitions = find_stability_transitions(
                area, heights, min_points=min_points, verbose=verbose
            )

            # Validate to remove false positives
            transitions = validate_all_transitions(
                area, heights, transitions, verbose=verbose
            )

            method_used = 'stability'

        else:
            if verbose:
                reason = "not 3-segment" if predicted_segs < 3 else "low confidence"
                logger.info(f"🔄 Using multi-derivative ({reason})")

            # Use proven multi-derivative
            transitions = find_optimal_transitions_improved(
                area, heights, min_points=min_points,
                use_adaptive=use_adaptive, verbose=verbose,
                diameter_mm=diameter_mm
            )

            method_used = 'multi-derivative'

        return transitions, method_used

    except Exception as e:
        # Fallback to multi-derivative on any error
        logger.warning(f"⚠️  Selective detection error: {e}, using multi-derivative")
        transitions = find_optimal_transitions_improved(
            area, heights, min_points=min_points,
            use_adaptive=use_adaptive, verbose=verbose,
            diameter_mm=diameter_mm
        )
        return transitions, 'multi-derivative-fallback'
```

### Step 3: Integrate into Main Algorithm

**File:** `src/container_geometry_analyzer_gui_v3_11_8.py`

```python
# In segment_and_fit_optimized():

if DEFAULT_PARAMS.get('use_selective_detection', False):
    # Phase 2: Selective hybrid routing
    transitions, method = find_optimal_transitions_selective(
        area,
        heights=heights,
        min_points=adaptive_params['min_points'],
        diameter_mm=estimated_diameter,
        use_adaptive=DEFAULT_PARAMS.get('use_adaptive_threshold', True),
        confidence_threshold=DEFAULT_PARAMS.get('selective_confidence_threshold', 'high'),
        verbose=verbose
    )

    if verbose:
        logger.info(f"✨ Selective detection: {method} method used")

else:
    # Phase 1-3: Original proven method
    transitions = find_optimal_transitions_improved(
        area, heights=heights,
        min_points=adaptive_params['min_points'],
        use_adaptive=DEFAULT_PARAMS.get('use_adaptive_threshold', True),
        verbose=verbose,
        diameter_mm=estimated_diameter
    )

    if verbose:
        logger.info("✨ Using improved transition detection (multi-derivative + diameter-specific tuning)")
```

### Step 4: Test Implementation

**File:** `tests/test_selective_routing.py` (NEW)

```python
"""
Tests for Phase 2 selective hybrid routing.
"""

def test_selective_routing_high_conf_3seg():
    """Test that high-confidence 3-segment uses stability method."""
    # Synthetic 3-segment with perfect prediction confidence
    # Should use stability method
    # Should find 3 transitions
    pass

def test_selective_routing_low_conf_3seg():
    """Test that low-confidence 3-segment falls back to multi-derivative."""
    # Synthetic 3-segment with low prediction confidence
    # Should use multi-derivative
    # Should maintain baseline performance
    pass

def test_selective_routing_2seg():
    """Test that 2-segment uses multi-derivative."""
    # Synthetic 2-segment
    # Should use multi-derivative (proven)
    # Should maintain 50% baseline
    pass

def test_selective_routing_1seg():
    """Test that 1-segment uses multi-derivative."""
    # Synthetic 1-segment
    # Should use multi-derivative
    # Should maintain 100% performance
    pass

def test_no_regression_with_phase2():
    """Test that Phase 2 doesn't regress any performance."""
    # Run comprehensive suite with Phase 2 enabled
    # Verify baseline maintained: 60.7%
    # Verify 3-segment improves (or stays same)
    pass
```

---

## Phase 2: Testing Strategy

### Test Progression

#### Week 1: Unit Tests
- ✅ Selective routing logic
- ✅ Confidence mechanism
- ✅ Method selection
- ✅ Fallback handling

#### Week 2: Integration Tests
- ✅ Comprehensive suite (56 cases) with Phase 2 enabled
- ✅ Regression testing (1-2 segment)
- ✅ 3-segment analysis
- ✅ Edge cases

#### Week 3: Validation
- ✅ Parameter optimization
- ✅ Performance profiling
- ✅ Documentation validation
- ✅ Deployment readiness

### Test Coverage

```
COMPREHENSIVE TESTS (56 cases):
├─ 1-segment (24):     Should stay at 83.3%
├─ 2-segment (24):     Should stay at 50.0%
└─ 3-segment (8):      Should improve to 40%+ (target)

BY DIAMETER:
├─ 5mm:   Should stay at 93.8%
├─ 10mm:  Might improve slightly
└─ 15mm:  Might improve slightly

PERFORMANCE:
└─ Average: <30ms per test (currently 25.8ms)
```

---

## Phase 2: Risk Mitigation

### Risk 1: Selective Routing Breaks Something
**Mitigation:**
- Feature flag: `use_selective_detection` (default: False)
- Can revert instantly by setting to False
- Gradual rollout: enable for small user percentage first
- Monitoring: track method selection in logs

### Risk 2: Confidence Mechanism Unreliable
**Mitigation:**
- Manual testing of confidence threshold
- Tune `selective_confidence_threshold` parameter
- Use 'high' initially, could adjust to 'medium' if needed
- Monitor false positives

### Risk 3: Stability Method Fails on Real Data
**Mitigation:**
- Exception handling with fallback
- Error logging for analysis
- Conservative thresholds reduce false segmentation
- Can disable method entirely if issues found

### Risk 4: Performance Regression
**Mitigation:**
- Performance profiling before/after
- Alert if average test time > 30ms
- Optimize if needed
- Keep performance dashboard

---

## Phase 2: Rollout Plan

### Internal Testing (Week 2)
1. ✅ Enable Phase 2 in test environment
2. ✅ Run comprehensive test suite
3. ✅ Analyze results
4. ✅ Tune parameters
5. ✅ Verify all gates pass

### Beta Rollout (Week 3)
1. ✅ Deploy with feature flag OFF by default
2. ✅ Enable for 10% of users (if live system)
3. ✅ Monitor logs and errors
4. ✅ Collect performance metrics
5. ✅ Verify no issues

### Full Rollout (Week 4+)
1. ✅ Gradually increase to 50% of users
2. ✅ Monitor for 1 week
3. ✅ Full rollout to 100%
4. ✅ Consider making default if stable

---

## Phase 2: Success Metrics

### Primary Metrics
- Overall accuracy: ≥ 60.7% (baseline maintained)
- 3-segment accuracy: ≥ 40% (improvement from 25%)
- Regression: None in 1-seg or 2-seg

### Secondary Metrics
- Confidence mechanism: >90% correct routing
- Error rate: <5% exceptions
- Performance: <30ms average

### Monitoring
- Track method selection (stability vs. multi-deriv)
- Count 3-segment successes
- Monitor error logs
- Performance dashboard

---

## Phase 2: Deliverables

### Code
- [ ] Selective routing function
- [ ] Integration into main algorithm
- [ ] Unit tests
- [ ] Integration tests

### Configuration
- [ ] Phase 2 parameters in DEFAULT_PARAMS
- [ ] Documentation of parameters
- [ ] Examples of configuration

### Documentation
- [ ] Phase 2 completion report
- [ ] Deployment guide
- [ ] User documentation
- [ ] Troubleshooting guide

### Testing
- [ ] Test results (comprehensive suite)
- [ ] Regression analysis
- [ ] 3-segment improvement analysis
- [ ] Performance metrics

---

## Phase 2: Timeline

```
Week 1 (Days 1-5): Implementation
├─ Mon-Tue: Routing logic
├─ Wed-Thu: Integration
└─ Fri: Unit tests

Week 2 (Days 6-10): Testing & Tuning
├─ Mon: Comprehensive tests
├─ Tue: Regression analysis
├─ Wed-Thu: Parameter tuning
└─ Fri: Final validation

Week 3 (Days 11-15): Documentation & Deployment
├─ Mon-Tue: Reports
├─ Wed: Deployment guide
├─ Thu: User documentation
└─ Fri: Ready for rollout
```

---

## Phase 2: Decision Points

### Gate 1: Must Pass (End of Week 2)
**Decision:** Can we proceed to rollout?

**Criteria:**
- Overall: 60.7% maintained
- 1-seg: No regression
- 2-seg: No regression
- 3-seg: At least 25% (no worse than baseline)

**If YES:** Proceed to rollout
**If NO:**
- Investigate issues
- Tune parameters
- Try alternative routing thresholds
- Consider deferring Phase 2

### Gate 2: Ready for Rollout (End of Week 3)
**Decision:** Approve for production deployment?

**Criteria:**
- All tests passing
- Documentation complete
- Deployment guide ready
- Monitoring setup complete

**If YES:** Proceed with beta rollout
**If NO:** Fix issues before rollout

---

## Next Steps

### Immediate (Ready Now)
1. ✅ Approve Phase 2 plan
2. ✅ Create implementation branch
3. ✅ Begin Stage 1 coding

### This Week
1. Implement selective routing (Stage 1-2)
2. Run unit tests (Stage 1-2)
3. Verify integration (Stage 2)

### Next Week
1. Run comprehensive testing (Stage 3)
2. Analyze results (Stage 3)
3. Tune parameters (Stage 4)

### Week 3
1. Create documentation (Stage 5)
2. Deployment guide (Stage 5)
3. Final validation (Stage 5)

---

## Conclusion

Phase 2 implements a conservative integration strategy that:
- ✅ Maintains baseline performance (60.7%)
- ✅ Targets 3-segment improvement (25% → 40%+)
- ✅ Uses feature flag for instant rollback
- ✅ Allows gradual rollout with monitoring
- ✅ Minimizes risk through selective deployment

**Status:** Ready to begin implementation when authorized.

---

**Plan Created:** November 20, 2025
**Approval:** Option A - Conservative Integration
**Ready for:** Implementation kickoff

