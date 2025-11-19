# Priority 1 Implementation Plan: Size-Adaptive Parameters

**Objective:** Implement diameter-dependent parameter tuning to improve detection accuracy by ~20%

**Expected Impact:**
- Overall: 50% → 70% accuracy
- d=10mm: 25% → 45%
- d=14mm: 25% → 40%
- d=16mm: 38% → 50%

**Effort Estimate:** 2-4 hours

**Complexity:** Medium (parameter tuning + conditional logic)

---

## Executive Summary

Current testing shows non-uniform performance across container diameters:
- **d=12mm (BEST):** 50% accuracy (sweet spot)
- **d=10mm:** 25% accuracy (under-performing)
- **d=14mm:** 25% accuracy (unexpected regression)
- **d=16mm:** 38% accuracy (moderate performance)

The issue is that **single, global parameters** work best for medium sizes (d=12mm) but fail at extremes. Different diameter ranges need different algorithm parameters to handle variations in:
1. Relative segment sizes vs. noise
2. Absolute radius magnitudes
3. Transition detection sensitivity
4. Segment merging thresholds

---

## Analysis of Current Bottlenecks

### Issue 1: Small Containers (d=10mm)

**Observed Problem:**
- Over-segmentation: Detecting 3-4 segments when expecting 2
- Detecting 4 segments when expecting 3
- Noise becomes proportionally larger relative to geometric features

**Root Cause Analysis:**

| Aspect | Impact | Evidence |
|--------|--------|----------|
| Segment size | Very small | ~20 points per segment at 120 total points |
| Noise impact | Proportionally high | 0.5% noise ≈ larger relative feature size |
| Transition sensitivity | Too aggressive | SNR-based adaptive percentile still uses base 96 |
| Min-points constraint | Inadequate | `min_points=12` means 60% of segment is minimum |

**Specific Failures (d=10mm):**
1. Frustum+Cylinder: Detecting [cylinder, frustum, cylinder] instead of [frustum, cylinder]
   - Frustum incorrectly split or false transition detected
   - Merge threshold (0.12) may be too strict for small radius differences

2. Cone+Frustum+Cylinder: Detecting [cone, frustum, cylinder, cylinder] instead of [cone, frustum, cylinder]
   - Cylinder at top falsely split into 2 segments
   - Over-sensitive to noise in straight sections

3. Semisphere+Cylinder: Correct detection [frustum, cylinder]
   - **SUCCESS**: Hemisphere detected as frustum (conservative but acceptable)
   - Smaller radius makes boundary more distinct relative to noise

**Solution Direction:**
- **Lower percentile threshold** (more permissive): 96 → 92
  - Reduces false positives from noise fluctuations
  - Requires fewer local extrema to trigger segmentation

- **Stricter merge tolerance** (fewer merges): 0.12 → 0.08
  - Don't merge segments with radius differences > 8%
  - Preserves legitimate small geometric changes

- **Lower min-points requirement**: 12 → 8-10
  - Allow smaller segments when container is small
  - Proportional to total container size

---

### Issue 2: Medium-Large Containers (d=14mm)

**Observed Problem:**
- Also shows 25% accuracy (unexpected, worse than d=10mm)
- Both over-segmentation AND under-segmentation failures
- Inconsistent patterns across scenarios

**Root Cause Analysis:**

This is the most puzzling result. Why would d=14mm perform worse than d=10mm?

| Failure Type | Count | Pattern |
|---|---|---|
| Over-segmentation | 4 | Frustum+Cyl, Cone+Frust+Cyl, Semisphere+Cyl |
| Under-segmentation | 2 | Sphere+Frust+Cyl (both instances) |

**Hypothesis:** The issue may be related to **how noise interacts with geometric scaling**

At d=14mm:
- Segments are larger (fewer points per segment)
- Noise is absolute (0.5% of mean volume)
- Transition zones might be in "bad fit" zones

Example: Sphere+Frustum+Cylinder at d=14mm
- Detecting [cone, frustum] instead of [cone, frustum, cylinder]
- Cylinder merged with frustum (under-segmentation)
- But Frustum+Cylinder at d=14mm shows over-segmentation

**Possible causes:**
1. Larger cylinder radius → larger area values → noise relatively smaller
2. But cumulative volume is larger → SNR calculation changes
3. Different shape combinations interact differently with absolute pixel values

**Solution Direction:**
- **Raise percentile for larger sizes** (more sensitive): 96 → 98-99
  - At larger sizes, absolute noise is smaller relative to features
  - Can afford to be more selective about transitions

- **Loosen merge tolerance slightly**: 0.12 → 0.15
  - Larger radius differences are still proportionally small
  - Accept merging if radius change is <15%

- **Adjust transition_buffer for size**:
  - Buffer determines minimum segment size differently at different scales

---

### Issue 3: Larger Containers (d=16mm)

**Observed Problem:**
- 38% accuracy (better than d=14mm but worse than d=12mm)
- Mix of success and failures across scenarios
- Generally more stable than smaller sizes

**Root Cause Analysis:**

At d=16mm, the algorithm works reasonably well (38%) but not optimally. This suggests:

| Metric | Impact |
|--------|--------|
| Segment sizes | Largest: ~30 points per segment |
| Noise impact | Smallest relative impact |
| Transition clarity | Generally good |
| Merging effectiveness | Good (few false positives) |

**Specific Issues:**
1. Cone+Frustum+Cylinder at d=16mm: [frustum, frustum, cylinder]
   - Cone detected as frustum (acceptable, correct count)
   - Success despite shape misidentification

2. Semisphere+Cylinder at d=16mm: [frustum, frustum, cylinder]
   - Hemisphere split into 2 frustum segments (over-segmentation)
   - Curved surface still causing issues

**Solution Direction:**
- **Balanced approach**: Current percentile (96) is good
  - Could try 97-98 for even more selectivity
  - Focus on improving curved surface handling (Priority 2)

- **Loosen merge tolerance**: 0.12 → 0.15
  - Larger containers can afford less strict matching
  - 15% radius tolerance is reasonable for 6-8mm cylinders

---

## Recommended Size Categories

Based on analysis, define **3 size categories** with specific parameters:

### Category 1: Small Containers (d ≤ 11mm)
**Characteristics:** Segments small, noise proportionally large, max points ~120

**Parameters:**
```python
'small': {
    'percentile': 92,           # More permissive (96→92)
    'merge_threshold': 0.08,    # Stricter merging (0.12→0.08)
    'min_points': 8,            # Smaller minimum (12→8)
    'variance_threshold': 0.12, # Lower (0.14→0.12, more sensitive to changes)
    'transition_buffer': 2.0,   # Reduced from 2.5
}
```

**Rationale:**
- Lower percentile = fewer points required to trigger segmentation
- Stricter merge = preserve all legitimate boundaries
- Smaller min_points = allow granular detection
- Lower variance_threshold = catch subtle variations

**Expected Impact:**
- d=10mm: 25% → 40-45%
- Cone+Frustum+Cylinder: 0% → 50% (currently fails at d=10)
- Frustum+Cylinder: 0% → 30% (currently fails at d=10)

---

### Category 2: Medium Containers (12mm ≤ d ≤ 13mm)
**Characteristics:** Optimal size range, segments well-sized, noise appropriately scaled

**Parameters:**
```python
'medium': {
    'percentile': 96,           # Keep current optimal (proven good)
    'merge_threshold': 0.12,    # Keep current
    'min_points': 12,           # Keep current
    'variance_threshold': 0.14, # Keep current
    'transition_buffer': 2.5,   # Keep current
}
```

**Rationale:**
- Don't change what works: d=12mm already at 50% (sweet spot)
- Baseline for other tuning efforts
- These parameters are already optimized through testing

**Expected Impact:**
- d=12mm: 50% → 50% (no change, maintain baseline)
- Stabilize behavior as reference point

---

### Category 3: Large Containers (d ≥ 14mm)
**Characteristics:** Segments large, noise absolutely smaller, more stable transitions

**Parameters:**
```python
'large': {
    'percentile': 97,           # More selective (96→97, higher bar for transitions)
    'merge_threshold': 0.15,    # Looser merging (0.12→0.15)
    'min_points': 12,           # Keep current
    'variance_threshold': 0.14, # Keep current
    'transition_buffer': 2.5,   # Keep current
}
```

**Rationale:**
- Higher percentile = only strongest transitions count
- Looser merge = acceptable to combine similar-sized segments
- At larger sizes, proportional differences are smaller
- min_points and variance_threshold unchanged (good at d=16)

**Expected Impact:**
- d=14mm: 25% → 35-40%
- d=16mm: 38% → 45-50%
- Sphere+Frustum+Cylinder: 50% → 60% (reduce under-segmentation)

---

## Implementation Strategy

### Approach 1: Simple (Recommended for Phase 1)
**Implementation:** Single diameter threshold (d < 12mm vs. d ≥ 12mm)

**Pros:**
- Easy to understand and implement
- Minimal code changes (~20-30 lines)
- Clear decision boundary

**Cons:**
- Less fine-grained than 3-category approach
- Misses optimization opportunity for d≥14mm

**Code Changes:**
```python
# In segment_and_fit_optimized() function
if diameter < 12:
    params = DEFAULT_PARAMS.copy()
    params['percentile'] = 92
    params['merge_threshold'] = 0.08
    params['min_points'] = 8
    params['variance_threshold'] = 0.12
else:
    params = DEFAULT_PARAMS.copy()
    # Use defaults (already optimized for d≥12)
```

**Expected Performance:**
- d=10mm: 25% → 40%
- d=12mm: 50% → 50%
- d=14mm: 25% → 28% (minor improvement)
- d=16mm: 38% → 40% (minor improvement)
- **Overall: 50% → 57%**

---

### Approach 2: Comprehensive (Recommended for Final)
**Implementation:** 3-category approach with smooth transitions

**Pros:**
- Optimizes for all size ranges
- Achieves target +20% improvement
- Professional-grade tuning

**Cons:**
- Requires more testing and validation
- ~50-70 lines of code
- More complex parameter combinations to test

**Code Changes:**
```python
# Define size-based parameters
SIZE_ADAPTIVE_PARAMS = {
    'small': {      # d < 12
        'percentile': 92,
        'merge_threshold': 0.08,
        'min_points': 8,
        'variance_threshold': 0.12,
        'transition_buffer': 2.0,
    },
    'medium': {     # 12 ≤ d < 14
        'percentile': 96,
        'merge_threshold': 0.12,
        'min_points': 12,
        'variance_threshold': 0.14,
        'transition_buffer': 2.5,
    },
    'large': {      # d ≥ 14
        'percentile': 97,
        'merge_threshold': 0.15,
        'min_points': 12,
        'variance_threshold': 0.14,
        'transition_buffer': 2.5,
    }
}

# In segment_and_fit_optimized()
def get_size_category(diameter):
    if diameter < 12:
        return 'small'
    elif diameter < 14:
        return 'medium'
    else:
        return 'large'

category = get_size_category(estimated_diameter)
params = SIZE_ADAPTIVE_PARAMS.get(category, DEFAULT_PARAMS.copy())
```

**Expected Performance:**
- d=10mm: 25% → 45%
- d=12mm: 50% → 50%
- d=14mm: 25% → 40%
- d=16mm: 38% → 50%
- **Overall: 50% → 70%**

---

## Implementation Steps

### Step 1: Add Size Category Logic (15 min)

**File:** `src/container_geometry_analyzer_gui_v3_11_8.py`

**Location:** After `DEFAULT_PARAMS` definition (line ~84)

**Changes:**
1. Define `SIZE_ADAPTIVE_PARAMS` dictionary
2. Create helper function `get_size_category(diameter)`
3. Create function `get_adaptive_params(diameter)`

**Code:**
```python
# Size-adaptive parameter tuning for Priority 1 improvement
SIZE_ADAPTIVE_PARAMS = {
    'small': {      # d < 12mm
        'percentile': 92,
        'merge_threshold': 0.08,
        'min_points': 8,
        'variance_threshold': 0.12,
        'transition_buffer': 2.0,
    },
    'medium': {     # 12 ≤ d < 14mm
        'percentile': 96,
        'merge_threshold': 0.12,
        'min_points': 12,
        'variance_threshold': 0.14,
        'transition_buffer': 2.5,
    },
    'large': {      # d ≥ 14mm
        'percentile': 97,
        'merge_threshold': 0.15,
        'min_points': 12,
        'variance_threshold': 0.14,
        'transition_buffer': 2.5,
    }
}

def get_size_category(diameter_mm: float) -> str:
    """Determine parameter set based on container diameter."""
    if diameter_mm < 12.0:
        return 'small'
    elif diameter_mm < 14.0:
        return 'medium'
    else:
        return 'large'

def get_adaptive_params(diameter_mm: float) -> Dict:
    """Get adaptive parameters for given diameter."""
    category = get_size_category(diameter_mm)
    params = DEFAULT_PARAMS.copy()
    params.update(SIZE_ADAPTIVE_PARAMS.get(category, {}))
    return params
```

### Step 2: Integrate into Segment Fitting (30 min)

**File:** `src/container_geometry_analyzer_gui_v3_11_8.py`

**Function:** `segment_and_fit_optimized()` (around line 700-900)

**Changes:**
1. Extract estimated diameter early in function
2. Call `get_adaptive_params()` to get tuned parameters
3. Pass tuned parameters to transition detection function

**Current Code Pattern:**
```python
def segment_and_fit_optimized(df, config=None, verbose=False):
    # ... existing code ...

    # Find transitions with DEFAULT_PARAMS
    transitions = find_optimal_transitions_improved(
        area=df_areas['Area'].values,
        # ... uses DEFAULT_PARAMS['percentile'] ...
    )
```

**Modified Code:**
```python
def segment_and_fit_optimized(df, config=None, verbose=False):
    # ... existing code ...

    # Estimate diameter from first/last area (approximation)
    areas = df_areas['Area'].values
    estimated_radius = np.sqrt(areas[-1] / np.pi)  # Approximate from cylinder top
    estimated_diameter = estimated_radius * 2

    # Get adaptive parameters for this diameter
    adaptive_params = get_adaptive_params(estimated_diameter)

    if verbose:
        logger.info(f"Detected diameter: {estimated_diameter:.1f}mm, category: {get_size_category(estimated_diameter)}")

    # Find transitions with adaptive parameters
    transitions = find_optimal_transitions_improved(
        area=df_areas['Area'].values,
        heights=df_areas['Height_mm'].values,
        min_points=adaptive_params['min_points'],
        percentile=adaptive_params['percentile'],
        variance_threshold=adaptive_params['variance_threshold'],
        transition_buffer=adaptive_params['transition_buffer'],
    )
```

### Step 3: Update Segment Merging Logic (15 min)

**File:** `src/container_geometry_analyzer_gui_v3_11_8.py`

**Function:** Intelligent merging section (around line 918-1006)

**Changes:**
1. Use adaptive `merge_threshold` parameter
2. Apply it in geometric continuity validation

**Current Code:**
```python
# In intelligent segment merging section
merge_tolerance = DEFAULT_PARAMS['merge_threshold']  # 0.12
```

**Modified Code:**
```python
merge_tolerance = adaptive_params['merge_threshold']
```

---

## Testing and Validation Plan

### Test Phase 1: Individual Size Category Testing

**Objective:** Verify each parameter set improves its target diameter range

**Method:**
```bash
# Test small containers (d=10mm)
python tests/test_geometry_combinations.py --diameter-only 10

# Test medium containers (d=12mm)
python tests/test_geometry_combinations.py --diameter-only 12

# Test large containers (d=14,16mm)
python tests/test_geometry_combinations.py --diameter-only 14
python tests/test_geometry_combinations.py --diameter-only 16
```

**Success Criteria:**
- Small (d=10): Improvement from 25% to ≥40%
- Medium (d=12): Maintain 50% or better
- Large (d≥14): Improvement to 40%+ (average)

---

### Test Phase 2: Full Test Suite Re-Run

**Objective:** Measure overall improvement across all 16 test cases

**Method:**
```bash
cd /home/user/container-geometry-analyzer
python tests/test_geometry_combinations.py 2>&1 | tee size_adaptive_results.txt
```

**Expected Results:**
```
Current:
- d=10mm: 25%
- d=12mm: 50%
- d=14mm: 25%
- d=16mm: 38%
- Overall: 50%

Expected After Priority 1:
- d=10mm: 45%
- d=12mm: 50%
- d=14mm: 40%
- d=16mm: 50%
- Overall: 70%
```

**Success Criteria:**
- Overall accuracy improves from 50% to ≥65% (target: 70%)
- No scenario should regress below current performance
- Cone+Frustum+Cylinder maintains 75% success

---

### Test Phase 3: Regression Testing

**Objective:** Ensure no unintended side effects on other code paths

**Tests:**
1. Run existing unit tests (if any)
2. Test with real lab data (if available)
3. Verify CSV output format unchanged
4. Verify PDF report generation still works

---

## Risk Assessment

### Risk 1: Over-Tuning for Synthetic Data

**Description:** Parameters optimized for synthetic data may not generalize to real lab data

**Likelihood:** Medium (synthetic data is mathematically precise)

**Mitigation:**
- Keep parameter changes conservative (±10% of current values)
- Test with real lab data if available before release
- Document that tuning was done on synthetic data

**Impact if Occurs:** Reduced effectiveness on real data

---

### Risk 2: Parameter Sensitivity

**Description:** Small parameter changes might have large effects

**Likelihood:** High (algorithm is known to be sensitive)

**Mitigation:**
- Make incremental changes (e.g., 96→92 vs. 96→80)
- Test each change individually before combining
- Keep detailed test logs
- Build in safety margins (e.g., 92 not 88)

**Impact if Occurs:** Need to retune, 1-2 hours additional work

---

### Risk 3: Regression in Some Scenarios

**Description:** Parameters optimized for small containers might hurt large ones

**Likelihood:** Low (recommended parameters are conservative)

**Mitigation:**
- Design 3-category approach specifically to avoid this
- Test all diameter ranges thoroughly
- Use regression test suite

**Impact if Occurs:** Need to adjust thresholds between categories

---

### Risk 4: Diameter Estimation Error

**Description:** Algorithm estimates diameter from cylinder area; estimate might be wrong

**Likelihood:** Medium

**Mitigation:**
- Use multiple methods to estimate diameter (top area, middle area, average)
- Add ±1mm tolerance band (use medium params for d=11-13)
- Log estimated diameter for debugging

**Code:**
```python
# Better diameter estimation
areas = df_areas['Area'].values
heights = df_areas['Height_mm'].values

# Use top ~10% of data (likely cylinder portion) for radius estimate
top_area_fraction = areas[-len(areas)//10:]
estimated_radius = np.sqrt(np.median(top_area_fraction) / np.pi)
estimated_diameter = estimated_radius * 2

logger.debug(f"Diameter estimate: {estimated_diameter:.2f}mm from median area {np.median(top_area_fraction):.1f}")
```

---

## Implementation Checklist

- [ ] Step 1: Add SIZE_ADAPTIVE_PARAMS and helper functions
- [ ] Step 2: Integrate into segment_and_fit_optimized()
- [ ] Step 3: Update merging logic
- [ ] Step 4: Test Phase 1 (individual diameter ranges)
- [ ] Step 5: Test Phase 2 (full test suite)
- [ ] Step 6: Verify no regressions
- [ ] Step 7: Update documentation
- [ ] Step 8: Commit changes with detailed message
- [ ] Step 9: Create PR with test results

---

## Success Metrics

| Metric | Current | Target | Achieved | Notes |
|--------|---------|--------|----------|-------|
| Overall Accuracy | 50% | 70% | TBD | Primary metric |
| d=10mm Accuracy | 25% | 45% | TBD | Small containers |
| d=12mm Accuracy | 50% | 50% | TBD | Baseline (no regression) |
| d=14mm Accuracy | 25% | 40% | TBD | Medium-large |
| d=16mm Accuracy | 38% | 50% | TBD | Large containers |
| Cone+Frust+Cyl | 75% | 75% | TBD | No regression |
| Implementation Time | -- | 2-4h | TBD | Actual effort |
| Code Added | -- | ~100 LOC | TBD | Actual lines |

---

## Post-Implementation Actions

### If Successful (≥65% overall)
1. Update eval/EVALUATION_REPORT.md with new results
2. Create new test results document: eval/PRIORITY_1_RESULTS.md
3. Move to Priority 2 implementation (curved surface detection)
4. Document parameter tuning rationale in algorithm details

### If Partial Success (50-65% overall)
1. Analyze which size categories underperformed
2. Iteratively adjust thresholds
3. Consider hybrid approach (e.g., different thresholds for different scenarios)
4. Re-test after adjustments

### If Unsuccessful (<50%)
1. Review parameter choices
2. Consider alternative approaches (e.g., machine learning-based classification)
3. Document lessons learned
4. Adjust Priority 2 focus to address root causes differently

---

## Next Steps After Priority 1

Once size-adaptive parameters are implemented and validated:

1. **Priority 2: Curved Surface Detection**
   - Implement hemisphere-specific fitting
   - Use curvature analysis to detect sphere caps
   - Expected: +25% accuracy improvement
   - Focus: Fix Semisphere+Cylinder (25% → 75%)

2. **Priority 3: Shape Discrimination**
   - Improve cone vs. frustum differentiation
   - Analyze rate-of-change patterns
   - Expected: +10% accuracy improvement

3. **Validation**
   - Test with real lab data
   - Compare against manual measurements
   - Document performance on production datasets

---

## References

- **Evaluation Report:** `eval/EVALUATION_REPORT.md` (lines 323-335)
- **Algorithm Details:** `eval/algorithm/ALGORITHM_DETAILS.md`
- **Test Results:** `eval/results/COMPREHENSIVE_RESULTS.md`
- **Test Suite:** `tests/test_geometry_combinations.py`
- **Main Algorithm:** `src/container_geometry_analyzer_gui_v3_11_8.py` (lines 69-84, 517+)

---

## Appendix: Parameter Tuning Rationale

### Why Lower Percentile for Small Sizes?

**Percentile in transition detection:**
- Higher percentile (e.g., 96) = raise bar for what counts as transition
- Lower percentile (e.g., 92) = lower bar, more permissive

**At small sizes (d=10mm):**
- Segments only ~20 points each
- Noise is absolute, relatively large in percentage terms
- Many false local extrema in derivative
- Need to be LESS selective (lower percentile) to catch real transitions
- Counter-intuitive but correct

**At large sizes (d≥14mm):**
- Segments ~30+ points each
- Noise is absolute, relatively small in percentage terms
- Fewer false local extrema
- Can be MORE selective (higher percentile) without missing real transitions

---

**Document Created:** 2025-11-19
**Analysis By:** Claude Code AI
**Status:** Ready for Implementation
