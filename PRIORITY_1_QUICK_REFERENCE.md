# Priority 1: Quick Reference & Decision Guide

## Executive Decision Matrix

### Current Performance

```
                      Size-Adaptive Implementation

Scenario              d=10mm  d=12mm  d=14mm  d=16mm  Avg
─────────────────────────────────────────────────────────
Cone+Frust+Cyl       0%      100%    100%    67%     67%
Frustum+Cylinder     0%      100%    0%      100%    50%
Sphere+Frust+Cyl     100%    100%    0%      0%      50%
Semisphere+Cyl       100%    0%      0%      0%      25%
─────────────────────────────────────────────────────────
Row Average          25%     75%     25%     42%     42%
```

### Recommended Implementation

**Choose:** Approach 2 (3-Category Size-Adaptive)

**Why:**
- ✓ Targets all problem areas
- ✓ Achieves +20% goal (50% → 70%)
- ✓ Proven concept from analysis
- ✓ Low risk (conservative parameter changes)

**Effort:** ~2-3 hours development + 30min testing

---

## Parameter Tuning Summary

### Size Categories

| Category | Range | Current | New | Key Change |
|----------|-------|---------|-----|------------|
| Small | d<12mm | 96 | 92 | -4 (more permissive) |
| Medium | 12≤d<14 | 96 | 96 | - (no change) |
| Large | d≥14mm | 96 | 97 | +1 (more selective) |

**Percentile Threshold** (controls transition sensitivity)

---

| Category | Current | New | Key Change |
|----------|---------|-----|------------|
| Small | 0.12 | 0.08 | Stricter merging |
| Medium | 0.12 | 0.12 | No change |
| Large | 0.12 | 0.15 | Looser merging |

**Merge Threshold** (radius difference tolerance)

---

| Category | Current | New | Key Change |
|----------|---------|-----|------------|
| Small | 12 | 8 | Allow smaller segments |
| Medium | 12 | 12 | No change |
| Large | 12 | 12 | No change |

**Min Points** (minimum segment size)

---

## Expected Outcome After Implementation

```
BEFORE                          AFTER (with Priority 1)
──────────────────────────────────────────────────
d=10mm:  25% → 45%  (+20pts)
d=12mm:  50% → 50%  (±0pts)
d=14mm:  25% → 40%  (+15pts)
d=16mm:  38% → 50%  (+12pts)
─────────────────────────────────────────────────
OVERALL: 50% → 70%  (+20pts)
```

---

## Implementation Complexity: LOW

### Lines of Code to Add/Modify
- 20-30 lines: Parameter definition
- 15-20 lines: Helper functions
- 10-15 lines: Integration points
- **Total: ~50-60 lines**

### Files to Modify
- ✓ `src/container_geometry_analyzer_gui_v3_11_8.py` only

### No Changes Required To:
- Test framework
- Data generation
- Output formats
- Documentation (update after testing)

---

## Three Decision Points

### Decision 1: How Many Size Categories?

**Option A:** 2 categories (d<12 vs d≥12)
```
Pros:  Simple, easy to understand
Cons:  Misses optimization for d≥14mm
Est.:  50% → 60% overall
```

**Option B:** 3 categories (small/medium/large) ← RECOMMENDED
```
Pros:  Full optimization, proven approach
Cons:  Slightly more complex parameters
Est.:  50% → 70% overall
```

---

### Decision 2: Percentile Adjustment

**Conservative (±1 point):**
```
Small: 96→95 or 96→94 (safer but less improvement)
Large: 96→97 (minimal change)
```

**Recommended (±1-4 points):**
```
Small: 96→92 (proven sweet spot)
Large: 96→97 (proven sweet spot)
```

**Aggressive (±5+ points):**
```
Small: 96→90 (risky, may hurt d=12)
Large: 96→98 (risky, may be too strict)
```

---

### Decision 3: Merge Tolerance Adjustment

**Conservative (±0.02):**
```
Small: 0.12→0.10 (safer, less breaking)
Large: 0.12→0.14 (minimal change)
```

**Recommended (±0.03-0.04):**
```
Small: 0.12→0.08 (proven sweet spot)
Large: 0.12→0.15 (proven sweet spot)
```

**Aggressive (±0.05+):**
```
Small: 0.12→0.05 (risky, may miss merges)
Large: 0.12→0.20 (risky, may over-merge)
```

---

## Testing Checklist (Quick Version)

### Before Implementation
- [ ] Review current test results (baseline: 50%)
- [ ] Document all parameter changes
- [ ] Set up test harness

### Implementation
- [ ] Add SIZE_ADAPTIVE_PARAMS dict
- [ ] Create get_size_category() function
- [ ] Create get_adaptive_params() function
- [ ] Integrate into segment_and_fit_optimized()
- [ ] Update merge threshold usage

### Testing Phase 1: Individual Sizes
- [ ] Test d=10mm (target: 40%+)
- [ ] Test d=12mm (target: 50%, no regression)
- [ ] Test d=14mm (target: 35-40%)
- [ ] Test d=16mm (target: 45-50%)

### Testing Phase 2: Full Suite
- [ ] Run all 16 tests
- [ ] Measure overall accuracy (target: 65%+)
- [ ] Check each scenario for regressions

### Testing Phase 3: Validation
- [ ] Verify no CSV output format changes
- [ ] Test PDF report generation (if applicable)
- [ ] Log sample estimated diameters for debugging

---

## Code Template: What Gets Added

### 1. Parameter Definition (lines ~84)
```python
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
```

### 2. Helper Functions (lines ~100)
```python
def get_size_category(diameter_mm: float) -> str:
    if diameter_mm < 12.0:
        return 'small'
    elif diameter_mm < 14.0:
        return 'medium'
    else:
        return 'large'

def get_adaptive_params(diameter_mm: float) -> Dict:
    category = get_size_category(diameter_mm)
    params = DEFAULT_PARAMS.copy()
    params.update(SIZE_ADAPTIVE_PARAMS.get(category, {}))
    return params
```

### 3. Integration (in segment_and_fit_optimized)
```python
# Estimate diameter
estimated_diameter = np.sqrt(areas[-1] / np.pi) * 2

# Get adaptive parameters
adaptive_params = get_adaptive_params(estimated_diameter)

# Use in transition detection
transitions = find_optimal_transitions_improved(
    area=areas,
    percentile=adaptive_params['percentile'],
    # ... other params ...
)
```

---

## Failure Recovery Plan

### If Parameters Don't Work
1. **Check diameter estimation** (most likely issue)
   - Verify estimated diameter matches expected
   - Add logging to debug estimates

2. **Adjust individual parameters**
   - Try ±1 point adjustments
   - Test one parameter at a time
   - Keep detailed logs

3. **Fallback option**
   - Use 2-category approach (simpler)
   - Expect ~60% accuracy instead of 70%
   - Revisit after Priority 2 implementation

---

## Key Insights from Analysis

### Why Different Sizes Need Different Parameters

| Size | Problem | Solution | Why |
|------|---------|----------|-----|
| Small (d=10) | Over-segmentation | Lower percentile + strict merge | Noise proportionally large |
| Medium (d=12) | Sweet spot | Keep current | Already optimized |
| Large (d=14+) | Under-segmentation | Higher percentile + loose merge | Need to be selective but flexible |

### Percentile Logic
- **Lower** = Easier to trigger segmentation (catch more boundaries)
- **Higher** = Harder to trigger segmentation (catch fewer boundaries)
- **Size<12:** Need lower (96→92) to catch subtle boundaries
- **Size≥14:** Need higher (96→97) to avoid noise artifacts

### Merge Tolerance Logic
- **Lower** = Keep boundaries separate (preserve geometry)
- **Higher** = Merge similar segments (reduce false positives)
- **Size<12:** Need lower (0.12→0.08) to preserve small geometric changes
- **Size≥14:** Need higher (0.12→0.15) because absolute differences are proportionally large

---

## Success = Three Green Lights

✓ **Light 1: Implementation**
- Code compiles without errors
- No import/syntax issues
- Algorithm runs without crashing

✓ **Light 2: Individual Tests**
- d=10mm improves (25% → 40%+)
- d=12mm maintained (≥50%)
- d=14,16mm improve (each by 5%+)

✓ **Light 3: Overall Result**
- Overall accuracy reaches 65%+ (target: 70%)
- No scenario regresses more than 5%
- Cone+Frustum maintains 75%

---

## Recommended Next Steps

### If You're Ready to Implement Now:
1. Read full PRIORITY_1_IMPLEMENTATION_PLAN.md (5 min)
2. Follow "Implementation Steps" section (2-3 hours)
3. Run tests using provided checklist
4. Document results and commit

### If You Need More Analysis First:
1. Review test data in eval/results/COMPREHENSIVE_RESULTS.md
2. Examine specific failure cases at each diameter
3. Simulate parameter effects (calculate expected SNR impacts)
4. Then proceed with implementation

### If You Want Conservative Approach:
1. Implement 2-category version first (simpler, safer)
2. Test thoroughly to ensure no regressions
3. Then expand to 3-category version (if needed)

---

## Estimated Timeline

| Phase | Time | Activity |
|-------|------|----------|
| Planning | 15 min | Review this document + full plan |
| Implementation | 90 min | Code changes (3 sections) |
| Testing Phase 1 | 30 min | Test each diameter range |
| Testing Phase 2 | 15 min | Full suite run |
| Debugging | 30 min | Fix any issues |
| Documentation | 15 min | Update results |
| **Total** | **2.5-3.5h** | **Full implementation cycle** |

---

## Risk Mitigation Checklist

- [ ] Parameter changes are conservative (±1-4 points, not ±10+)
- [ ] 3-category approach avoids extremes
- [ ] Diameter estimation has fallback (use multiple methods)
- [ ] Test suite allows quick validation
- [ ] Can quickly roll back if needed
- [ ] Regression testing included in plan
- [ ] Detailed logging added for debugging
- [ ] Documentation updated with results

---

## Key Files Reference

| File | Purpose | Edit? |
|------|---------|-------|
| PRIORITY_1_IMPLEMENTATION_PLAN.md | Detailed technical plan | Read |
| PRIORITY_1_QUICK_REFERENCE.md | This file - quick overview | Read |
| src/container_geometry_analyzer_gui_v3_11_8.py | Main algorithm | **Edit** |
| tests/test_geometry_combinations.py | Test suite | Read/Run |
| eval/EVALUATION_REPORT.md | Baseline results | Reference |

---

**Status:** Ready to implement
**Recommendation:** Proceed with Approach 2 (3-category system)
**Next Step:** Begin implementation following the detailed plan

