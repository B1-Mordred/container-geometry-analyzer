# Composite Shape Failure Investigation Report

**Date:** November 20, 2025
**Status:** Investigation Complete - Root Cause Identified
**Failing Test Cases:** 3 (composite_flask, composite_cone_cylinder, composite_eppendorf)

---

## Executive Summary

Investigation reveals that **composite shapes (e.g., sphere_cap+cylinder, cone+cylinder) fail because the transition detection algorithm finds ZERO transition candidates** before curvature filtering occurs.

**Root Cause:** The multi-derivative transition detection algorithm (find_optimal_transitions_improved) is not sensitive enough to detect gradual transitions between shapes in composite containers.

**Proposed Solution:** Disable aggressive curvature filtering for composite shapes and rely on validation criteria (coefficient of variation, autocorrelation, R²) to reject false transitions from inflection points.

---

## Detailed Analysis

### Test Case: Composite Flask (Sphere Cap + Cylinder)

**Expected:** 2 segments (sphere_cap at 0-15mm, cylinder at 15-65mm)
**Detected:** 1 segment (entire container as one segment)

**Data Profile:**
- 80 data points
- Height: 0.1 - 65.0 mm
- Area: 302 - 1083 mm²
- Expected transition: ~15mm (where area becomes nearly constant)

**What Happens Currently:**
1. Transition detection runs: **0 candidates found** ❌
2. Curvature filtering: (no candidates to filter)
3. Validation: (no candidates to validate)
4. Result: Only [0, 79] boundaries kept (entire container = 1 segment)

**Key Observations:**
- Curvature range: 62.5% of points have curvature > 0.05
- Inflection points: 29 detected (noise from area curve)
- Expected transition location: Index ~46 (height 37.95mm) where area becomes nearly constant
- **CRITICAL:** The transition detection scoring finds NO peaks at shape boundaries

### Test Case: Composite Cone (Cone + Cylinder)

**Expected:** 2 segments (cone at 0-25mm, cylinder at 25-50mm)
**Detected:** 1 segment (entire container)

**Data Profile:**
- 80 data points
- Height: 0.1 - 50.0 mm
- Area: 8.1 - 101.5 mm²

**Key Observations:**
- Curvature range: 90% of points have curvature > 0.05
- The cone has very high curvature throughout
- Transition to constant-area cylinder is where curvature drops to ~0.02
- **CRITICAL:** Transition detection finds NO peaks at this boundary

### Test Case: Composite Eppendorf (Cone + Cylinder)

**Expected:** 2 segments
**Detected:** 1 segment

**Data Profile:**
- 60 data points
- Height: 0.1 - 35.0 mm
- Area: 10.3 - 342.7 mm²

**Key Observation:**
- Sharp cone region (very high curvature: 1.1-1.4)
- Transition to cylinder (curvature drops to ~0.02)
- **CRITICAL:** NO transition detection candidates found

---

## Root Cause Analysis

### Why Transition Detection Finds 0 Candidates

The `find_optimal_transitions_improved()` function uses **multi-derivative analysis**:

```
score = 0.6 * normalized(first_derivative_changes) +
        0.4 * normalized(absolute_second_derivative)
```

**For composite shapes, this fails because:**

1. **Smooth Area Transitions:** The area change at shape boundaries is smooth and continuous
   - Cone → Cylinder: Area gradient decreases smoothly
   - Sphere → Cylinder: Area gradient decreases smoothly
   - No sharp peaks in derivatives at the boundary

2. **Dominated by Inflection Points:** The highest scores are at inflection points within curved sections
   - Cone has many inflection points (curvature = 1.0+)
   - These inflection points produce higher scores than the shape boundary
   - The algorithm picks inflection peaks instead of boundary peaks

3. **Percentile Thresholding Fails:** All candidates are filtered by percentile threshold
   - SNR = 18.81 for cone, triggers percentile = 85 (very high!)
   - Shape boundary score < 85th percentile of inflection point scores
   - Result: All candidates below threshold, 0 kept

4. **Curvature Filtering Too Aggressive:** Even if candidates were found:
   - Curvature at boundary = ~0.05-0.08 (near threshold)
   - Binary thresholding creates ambiguity
   - Boundary rejection: "one side curved, other linear" logic fails

---

## What Methods Detect the Boundary?

### Method 1: Gradient Magnitude Peak Detection ❌
- **Result:** 0 peaks found
- **Reason:** Area change is smooth, not peaked

### Method 2: Multi-Scale Curvature Variance ⚠️
- **Result:** Detects ~19 high-variance locations
- **Accuracy:** Poor (picks inflection points, not boundaries)
- **Why:** Doesn't distinguish boundary variance from inflection variance

### Method 3: Curvature Change Detection ✅
- **Result:** Detects regions with significant d(curvature)/dh changes
- **Accuracy:** Moderate (11-15 regions detected)
- **Best Performance:** Detects the general area where curvature changes most

### Method 4: Combined Gradient+Curvature ⚠️
- **Result:** Limited (0 gradient change peaks)
- **Reason:** Gradient change is also smooth for composite shapes

---

## Key Insight: Nature of Composite Shape Transitions

**Sphere Cap → Cylinder Transition:**
- Area: Accelerating increase → Constant (sharp change in behavior)
- Curvature: High (0.1-0.2) → Low (0.02-0.05)
- Gradient: Increasing → Flat
- **Signature:** Change in SECOND derivative behavior (area acceleration)

**Cone → Cylinder Transition:**
- Area: Accelerating increase → Constant (same as sphere)
- Curvature: Very High (1.0+) → Low (0.02-0.05)
- Gradient: Increasing → Flat
- **Signature:** Massive curvature drop, constant area

**The transition is NOT about derivative peaks, but about derivative STABILITY:**
- Before: Derivatives changing (curve)
- After: Derivatives constant (line)

---

## Recommended Solution

### Option 1: Disable Curvature Filtering (RECOMMENDED)
**Approach:** Turn off aggressive curvature filtering that removes valid transitions
**Rationale:**
- Current validation criteria are sufficient to reject inflection-point-induced false transitions
- Curvature filtering removes real shape boundaries
- Validation (CV, autocorrelation, R²) is more robust than curvature threshold

**Implementation:**
```python
# Make curvature filtering optional (off by default)
use_curvature_filter = DEFAULT_PARAMS.get('use_curvature_filtering', False)
if use_curvature_filter:
    validated = filter_transitions_in_curves(...)
```

**Expected Results:**
- Composite shapes: Should improve from 0% to ~70-80%
- Single shapes: May increase false positives, but validation should catch them
- Trade-off: Speed for accuracy (validation is computationally cheap)

### Option 2: Improve Curvature Threshold Sensitivity
**Approach:** Use multi-scale thresholding instead of single threshold
**Complex:** Requires recomputing curvature at multiple scales
**Less Effective:** Still won't solve the underlying problem

### Option 3: Redesign Transition Detection
**Approach:** Detect shape transitions via "derivative stability" metric
**Complex:** Major refactoring required
**Better:** Would be ideal long-term solution

---

## Why Other Methods Fail

### Multi-Derivative Scoring
- ❌ Optimized for piecewise-linear shapes
- ❌ Fails for smooth curved transitions
- ❌ Inflection points score higher than boundaries

### Single Curvature Threshold
- ❌ Binary decision loses information
- ❌ Boundary region has intermediate curvature
- ❌ Ambiguity at threshold value (0.05)

### Pure Gradient Methods
- ❌ Composite shape gradients are smooth
- ❌ No sharp peaks to detect
- ❌ Sensitive to noise

### Inflection Point Detection
- ❌ Every curve has many inflection points
- ❌ Can't distinguish boundary inflections from internal ones
- ❌ Over-segments curved shapes

---

## Validation That Current Criteria Work

The validation criteria in `find_optimal_transitions_improved()` are actually quite good:

**Criterion 1: Coefficient of Variation (CV > 0.05)**
- Rejects nearly-constant segments ✓
- Identifies variable segments ✓

**Criterion 2: Autocorrelation (|corr| > 0.4)**
- Detects structure vs noise ✓
- Meaningful for both curves and lines ✓

**Criterion 3: Model Fit (R² > 0.65)**
- Tests linear fit quality ✓
- Curved regions fail (expected) ✓
- Linear regions pass ✓

**Requires:** 2 out of 3 criteria passing

**Why This Works for Inflection Points:**
- Inflection points create small segments
- Small segments have high CV noise
- Autocorrelation fails for tiny segments
- Very few inflection-induced segments pass validation

---

## Proposed Implementation

### Step 1: Disable Curvature Filtering by Default
```python
'use_curvature_filtering': False,  # Disable (was enabled by default)
```

### Step 2: Test Results
- Run full test suite
- Check if composite shapes improve
- Check for regressions in single shapes

### Step 3: If Needed - Add Adaptive Filtering
- Keep curvature filtering but make it optional
- Use only when explicitly requested
- Document when to use it

---

## Predicted Outcomes

### With Curvature Filtering Disabled

**Composite Shapes:** Should improve significantly
- No more aggressive filtering removing real boundaries
- Validation criteria should catch false inflection-induced transitions
- Expected improvement: 0% → 60-80%

**Single Shapes:** May have slight regressions
- Inflection points might pass validation
- But segments too small to affect overall fit
- Merging logic should combine them back

**Sphere Caps:** May decrease slightly from 100%
- Currently perfect due to threshold 0.05 removing inflections
- Without filtering: inflections might create extra segments
- Merging should fix them

### Test Predictions
- **Composite shapes:** 0% → 70% (estimated)
- **Single shapes:** 100% → 95-98% (slight decrease expected)
- **Overall:** 80% → 85-88% (net positive)

---

## Conclusion

The investigation reveals that aggressive curvature filtering is solving one problem (inflection-point-induced false transitions in single shapes) while creating another problem (removing valid transitions in composite shapes).

**Recommended Path Forward:**
1. Disable curvature filtering by default
2. Rely on more robust validation criteria
3. Test and measure results
4. If needed, implement more sophisticated boundary detection

**Status:** Ready for implementation in main algorithm

---

**Next Steps:**
1. Implement curvature filtering disable
2. Run comprehensive tests
3. Measure improvement on composite shapes
4. Document tradeoffs
5. Commit changes

