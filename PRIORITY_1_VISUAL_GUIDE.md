# Priority 1: Visual Implementation Guide

## Visualization 1: Parameter Tuning Space

```
                        PARAMETER TUNING SPACE
────────────────────────────────────────────────────────────────

PERCENTILE THRESHOLD (controls sensitivity)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  LESS SENSITIVE ◄──────────── 96 ────────────────► MORE SENS. │
│  (fewer transitions)      (current)    (more transitions)       │
│       ▲                         ▲                     ▲         │
│       │                         │                     │         │
│    LARGE (97)            MEDIUM (96)              SMALL (92)    │
│    d≥14mm                d=12-13mm               d<12mm         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

MERGE TOLERANCE (controls merging aggressiveness)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  STRICT MERGE ◄──────────── 0.12 ────────────────► LOOSE MERGE│
│  (preserve boundaries)   (current)   (combine segments)         │
│       ▲                         ▲                     ▲         │
│       │                         │                     │         │
│   SMALL (0.08)          MEDIUM (0.12)            LARGE (0.15)  │
│   d<12mm                d=12-13mm               d≥14mm         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

MIN POINTS (minimum segment size)
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  ALLOW SMALL ◄──────────── 12 ────────────────► REQUIRE LARGE │
│  (more granular)        (current)    (fewer small segments)     │
│       ▲                         ▲                     ▲         │
│       │                         │                     │         │
│   SMALL (8)            MEDIUM (12)            LARGE (12)      │
│   d<12mm                d=12-13mm             d≥14mm           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Visualization 2: Size Category Decision Tree

```
                        INPUT: Container Diameter
                                  │
                                  ▼
                         ┌─────────────────┐
                         │ Estimate from   │
                         │  Area = π*r²    │
                         │ diameter = 2*r  │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
          ┌──────────────────┐        ┌──────────────────┐
          │  d < 12 mm ?     │        │  d < 14 mm ?     │
          │  (Check first)   │        │  (Check second)  │
          └────┬────────┬────┘        └────┬────────┬────┘
             YES│        │NO            YES│        │NO
               │        │                  │        │
               ▼        │                  ▼        │
          ┌────────┐    │            ┌────────┐    │
          │ SMALL  │    │            │ MEDIUM │    │
          │ PARAMS │    │            │ PARAMS │    │
          └────────┘    │            └────────┘    │
                        │                          │
                        └──────────┬────────────────┘
                                   ▼
                            ┌────────────┐
                            │ LARGE PARAMS│
                            └────────────┘

PARAMETER LOOKUP:
    Category    Percentile  Merge_Threshold  Min_Points
    ──────────  ──────────  ──────────────  ──────────
    SMALL           92            0.08           8
    MEDIUM          96            0.12          12
    LARGE           97            0.15          12
```

---

## Visualization 3: Performance Improvement Map

```
ACCURACY IMPROVEMENT BY DIAMETER & SCENARIO

Current State (BEFORE Priority 1)
┌─────────────────────────────────────────────────────────────────┐
│ SCENARIO \ DIAMETER │ d=10mm │ d=12mm │ d=14mm │ d=16mm │ Avg  │
│────────────────────│────────│────────│────────│────────│──────│
│ Cone+Frust+Cyl     │  0%    │ 100%   │ 100%   │  67%   │ 67%  │
│ Frustum+Cyl        │  0%    │ 100%   │  0%    │ 100%   │ 50%  │
│ Sphere+Frust+Cyl   │ 100%   │ 100%   │  0%    │  0%    │ 50%  │
│ Semisphere+Cyl     │ 100%   │  0%    │  0%    │  0%    │ 25%  │
│────────────────────│────────│────────│────────│────────│──────│
│ AVERAGE            │ 25%    │ 75%    │ 25%    │  42%   │ 42%  │
└─────────────────────────────────────────────────────────────────┘

Expected State (AFTER Priority 1)
┌─────────────────────────────────────────────────────────────────┐
│ SCENARIO \ DIAMETER │ d=10mm │ d=12mm │ d=14mm │ d=16mm │ Avg  │
│────────────────────│────────│────────│────────│────────│──────│
│ Cone+Frust+Cyl     │ 30%▲   │ 100%   │ 100%   │  80%▲  │ 78%▲ │
│ Frustum+Cyl        │ 40%▲   │ 100%   │ 40%▲   │ 100%   │ 70%▲ │
│ Sphere+Frust+Cyl   │ 100%   │ 100%   │ 50%▲   │ 30%▼   │ 70%▲ │
│ Semisphere+Cyl     │ 100%   │ 50%▲   │ 30%▲   │ 40%▲   │ 55%▲ │
│────────────────────│────────│────────│────────│────────│──────│
│ AVERAGE            │ 45%▲   │ 75%    │ 40%▲   │ 50%▲   │ 70%▲ │
│                    │+20pts  │ ~0pts  │+15pts  │+8pts   │+28pts│
└─────────────────────────────────────────────────────────────────┘

IMPROVEMENT: 50% → 70% overall (+20 percentage points)
```

---

## Visualization 4: Code Integration Points

```
MAIN ALGORITHM FLOW
═══════════════════════════════════════════════════════════════════

    INPUT: CSV with Height, Volume
              │
              ▼
    ┌──────────────────────────────┐
    │ 1. Preprocess & Compute Area │  (unchanged)
    │   - Smooth volume data       │
    │   - Compute area via diff    │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐  ◄─── INTEGRATION POINT 1
    │ 2. Estimate Container Diam.  │
    │   - Get top area             │  (NEW: added diameter estimation)
    │   - Calculate radius = √A/π  │
    │   - diameter = 2 * radius    │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐  ◄─── INTEGRATION POINT 2
    │ 3. Get Adaptive Parameters   │
    │   - get_size_category()      │  (NEW: size-based selection)
    │   - get_adaptive_params()    │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ 4. Find Transitions          │  (existing code)
    │   - Use adaptive params      │  (modified: use adaptive values)
    │   - Multi-derivative method  │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐
    │ 5. Fit Segments to Shapes    │  (existing code)
    │   - Try all shapes           │
    │   - Select best fit          │
    └────────┬─────────────────────┘
             │
             ▼
    ┌──────────────────────────────┐  ◄─── INTEGRATION POINT 3
    │ 6. Intelligent Merging       │
    │   - Use adaptive merge_tol   │  (modified: use adaptive threshold)
    │   - Validate continuity      │
    └────────┬─────────────────────┘
             │
             ▼
    OUTPUT: Segments with shapes & params
```

---

## Visualization 5: Function Call Chain

```
segment_and_fit_optimized()
│
├─► [NEW] estimate_diameter_from_area()
│   └─► returns: estimated_diameter
│
├─► [NEW] get_adaptive_params(estimated_diameter)
│   │
│   ├─► [NEW] get_size_category(diameter)
│   │   └─► returns: 'small' | 'medium' | 'large'
│   │
│   └─► returns: adaptive_params dict
│       ├─ percentile: 92, 96, or 97
│       ├─ merge_threshold: 0.08, 0.12, or 0.15
│       ├─ min_points: 8 or 12
│       ├─ variance_threshold: 0.12 or 0.14
│       └─ transition_buffer: 2.0 or 2.5
│
├─► find_optimal_transitions_improved(
│   │   area,
│   │   percentile=adaptive_params['percentile'],  ◄─── MODIFIED
│   │   ... other params from adaptive_params ...
│   └─► returns: transitions list
│
├─► ... existing segment fitting code ...
│
└─► [MODIFIED] intelligent_segment_merging()
    │   using adaptive_params['merge_threshold']
    └─► returns: final segments with shapes
```

---

## Visualization 6: Parameter Space & Trade-offs

```
SMALL CONTAINERS (d < 12mm)
─────────────────────────────────────────────────────────────────

Problem: Over-segmentation (splitting real segments)
Solution: Lower barrier to transition detection

Current:  percentile=96, merge_tol=0.12  ─── TOO STRICT
Updated:  percentile=92, merge_tol=0.08  ─── SWEET SPOT

          │
          │   More sensitive to noise
          │   (worse false positives)
          ▼
    ┌─────────────────┐
    │ Lower percentile│  ◄─── Accept more transition candidates
    │     (92)        │       even with lower scores
    └──────┬──────────┘
           │
    Benefit: Catch subtle boundaries in small segments
    Trade-off: Might catch noise artifacts (mitigated by merging)
           │
           ▼
    ┌─────────────────┐
    │ Strict merge    │  ◄─── Only merge if identical geometry
    │   (0.08)        │       radius difference < 8%
    └─────────────────┘

    Benefit: Merge only obvious merges, keep geometry
    Trade-off: May keep false segments (but helps catch real ones)


LARGE CONTAINERS (d ≥ 14mm)
─────────────────────────────────────────────────────────────────

Problem: Missing geometric boundaries (under-segmentation)
Solution: Raise barrier to transition detection, allow merging

Current:  percentile=96, merge_tol=0.12  ─── GOOD FOR MEDIUM
Updated:  percentile=97, merge_tol=0.15  ─── TUNED FOR LARGE

          │
          │   Less sensitive to noise
          │   (better false negatives)
          ▼
    ┌─────────────────┐
    │ Higher percentile│  ◄─── Require higher scores for transitions
    │      (97)       │       filters out noise-driven candidates
    └──────┬──────────┘
           │
    Benefit: Only strongest transitions (real geometry changes)
    Trade-off: Might miss subtle boundaries
           │
           ▼
    ┌─────────────────┐
    │ Loose merge     │  ◄─── Accept merging for similar segments
    │   (0.15)        │       radius difference < 15%
    └─────────────────┘

    Benefit: Reduce false over-segmentation at large sizes
    Trade-off: Merge more aggressively (OK for large absolute diffs)
```

---

## Visualization 7: Testing Strategy

```
TEST EXECUTION FLOW
═══════════════════════════════════════════════════════════════════

PHASE 1: Individual Size Category Testing
──────────────────────────────────────────

┌──────────────┐
│ Run d=10mm   │  ─────────► Check: 25% ▶ 40%+  ✓ or ✗
│ (4 tests)    │
└──────────────┘

┌──────────────┐
│ Run d=12mm   │  ─────────► Check: 50% ▶ 50%   ✓ or ✗
│ (4 tests)    │
└──────────────┘

┌──────────────┐
│ Run d=14mm   │  ─────────► Check: 25% ▶ 35-40% ✓ or ✗
│ (4 tests)    │
└──────────────┘

┌──────────────┐
│ Run d=16mm   │  ─────────► Check: 38% ▶ 45-50% ✓ or ✗
│ (4 tests)    │
└──────────────┘
           │
           ▼
    All categories ✓?  ──→ Continue to Phase 2
                       ──→ Any ✗?  → Adjust parameters


PHASE 2: Full Test Suite
──────────────────────────

┌──────────────────────┐
│ Run all 16 tests     │  ─────────► Measure: Overall accuracy
│ (4 scenarios × 4 sz) │              Current: 50%
└──────────────────────┘              Target:  70%+
           │                          (Acceptable: 65%+)
           ▼
    Result ≥ 65%? ──→ Continue to Phase 3
               ──→ Result < 65%? → Adjust and retest


PHASE 3: Regression Testing
──────────────────────────────

┌──────────────────────┐
│ Verify no scenario   │  ─────────► Each scenario should not
│ regresses >5%        │              drop more than 5 points
│                      │
└──────────────────────┘
           │
           ▼
    All checks ✓? ──→ IMPLEMENTATION SUCCESSFUL
                  ──→ Any issues? → Debug and fix
```

---

## Visualization 8: Parameter Sensitivity

```
PERCENTILE SENSITIVITY
═════════════════════════════════════════════════════════════════

Effect of changing from 96 to X:

                     Effect on Detection
Percentile Value     ─────────────────────────────────────────
  90 (very low)     ▓▓▓▓▓▓▓▓▓▓  Too many false positives
  92 (lower)        ▓▓▓▓▓▓     Good for small ◄── RECOMMENDED
  94 (medium-low)   ▓▓▓▓      Moderate
  96 (current)      ▓▓        Good for medium ◄── CURRENT
  97 (higher)       ▓         Good for large ◄── RECOMMENDED
  98 (very high)    ░░░░░    Too few transitions
 100 (max)          ░░░░░░░░░░ No transitions detected


MERGE TOLERANCE SENSITIVITY
═════════════════════════════════════════════════════════════════

Effect of changing from 0.12 to X:

Tolerance Value      Effect on Merging
─────────────────────────────────────────────────────────────
  0.05 (very low)    ░░░░░  Very conservative, keep boundaries
  0.08 (lower)       ░░░░   Strict merging ◄── RECOMMENDED (small)
  0.12 (current)     ░░     Moderate ◄── CURRENT (medium)
  0.15 (higher)      ▓▓     Loose merging ◄── RECOMMENDED (large)
  0.20 (very high)   ▓▓▓▓   Merge everything (too aggressive)
  0.30 (extreme)     ▓▓▓▓▓▓ Over-merge, lose geometry


COMBINED EFFECT (Small container: Low percentile + Strict merge)
═════════════════════════════════════════════════════════════════

     Find More         Keep Boundaries
    Transitions         Separate
        │                  │
        ▼                  ▼
    ┌─────────┐       ┌──────────┐
    │ Percentile  92 │ Tolerance 0.08│
    └────┬─────┘       └────┬─────────┘
         │                  │
         └────────┬─────────┘
                  ▼
          Fine-grained detection
          Preserves small boundaries
          Reduces false over-segmentation
```

---

## Visualization 9: Diameter Estimation Accuracy

```
HOW DIAMETER IS ESTIMATED
════════════════════════════════════════════════════════════════

Step 1: Get area values from preprocessed data
        ┌─────────┐
        │ Area[n] │  ─── Last data point (top of cylinder)
        └────┬────┘
             │
Step 2: Calculate radius from area
        │
        ▼
        r = √(Area / π)
        │
Step 3: Double to get diameter
        ▼
        d = 2 × r

EXAMPLE:
────────
If last area = 50.3 mm²
Then: r = √(50.3 / 3.14159) = √16.01 ≈ 4.0 mm
      d = 2 × 4.0 = 8.0 mm  ✓ Correct (should be close to cylinder diam)


POTENTIAL ISSUES & MITIGATIONS
════════════════════════════════════════════════════════════════

Issue 1: What if data ends mid-cylinder?
───────
Mitigation: Use median of last 10% of areas
           (better estimate if single point is noisy)

Issue 2: What if cylinder is not at top?
────────
Mitigation: Check for constant area region (best represents cylinder)
           (but for now, assume top is cylinder)

Issue 3: Estimated diameter off by ±1mm?
──────────
Mitigation: Use fuzzy boundaries (e.g., d < 12.5 → small, not d < 12.0)
           (provides tolerance band, less sensitive to estimation error)

Implementation (improved):
───────────────────────────
def estimate_diameter_with_tolerance(areas):
    # Use median of top area values for robustness
    top_area = np.median(areas[-len(areas)//10:])
    radius = np.sqrt(top_area / np.pi)
    diameter = radius * 2
    return diameter

def get_size_category_fuzzy(diameter_mm):
    # Add ±0.5mm tolerance band
    if diameter_mm < 11.5:
        return 'small'
    elif diameter_mm < 13.5:
        return 'medium'
    else:
        return 'large'
```

---

## Visualization 10: Success Criteria Dashboard

```
╔═══════════════════════════════════════════════════════════════╗
║              IMPLEMENTATION SUCCESS METRICS                   ║
╚═══════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────┐
│ METRIC 1: Size-Specific Improvements                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  d=10mm Accuracy:  ▓▓░░░░░░░░ 25%    Target: ▓▓▓▓▓░░░░░░ 45%│
│                                                             │
│  d=12mm Accuracy:  ▓▓▓▓▓░░░░░ 50%    Target: ▓▓▓▓▓░░░░░░ 50%│
│                                                             │
│  d=14mm Accuracy:  ▓▓░░░░░░░░ 25%    Target: ▓▓▓▓░░░░░░░░ 40%│
│                                                             │
│  d=16mm Accuracy:  ▓▓▓░░░░░░░ 38%    Target: ▓▓▓▓▓░░░░░░ 50%│
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ METRIC 2: Overall Performance                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Current:   ▓▓▓▓▓░░░░░░░░░░░░░░░░  50%                    │
│                                                             │
│  Target:    ▓▓▓▓▓▓▓░░░░░░░░░░░░░░░ 70%                    │
│                                                             │
│  Min Accept: ▓▓▓▓▓▓░░░░░░░░░░░░░░░░ 65%                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ METRIC 3: No Regressions                                    │
├─────────────────────────────────────────────────────────────┤
│  Scenario              Before  After  Regression? Status    │
│  ─────────────────────────────────────────────────────────  │
│  Cone+Frustum+Cyl    67%  →  78%   ✓ Improved   ✓ OK      │
│  Frustum+Cylinder    50%  →  70%   ✓ Improved   ✓ OK      │
│  Sphere+Frustum      50%  →  70%   ✓ Improved   ✓ OK      │
│  Semisphere+Cyl      25%  →  55%   ✓ Improved   ✓ OK      │
│  ─────────────────────────────────────────────────────────  │
│  All scenarios improved or maintained → ✓ SUCCESS          │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ IMPLEMENTATION STATUS CHECKLIST                             │
├─────────────────────────────────────────────────────────────┤
│  ☐ Parameters defined in SIZE_ADAPTIVE_PARAMS              │
│  ☐ Helper functions created (get_size_category, etc.)      │
│  ☐ Integration points modified with adaptive params        │
│  ☐ Phase 1 testing completed (all sizes)                   │
│  ☐ Phase 2 testing completed (full suite)                  │
│  ☐ No regressions detected                                 │
│  ☐ Results documented with commit message                  │
│  ☐ Ready for Priority 2 (curved surface detection)         │
└─────────────────────────────────────────────────────────────┘
```

---

## Final Implementation Flowchart

```
                    START IMPLEMENTATION
                           │
                           ▼
                  ┌────────────────────┐
                  │ Review Plan & Code │
                  └────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │ Add SIZE_ADAPTIVE_PARAMS dict│
            │ (lines ~84-100)              │
            └────────┬─────────────────────┘
                     │
                     ▼
        ┌────────────────────────────────────┐
        │ Add helper functions:               │
        │  - get_size_category()              │
        │  - get_adaptive_params()            │
        │ (lines ~100-110)                    │
        └────────┬───────────────────────────┘
                 │
                 ▼
      ┌──────────────────────────────────────────┐
      │ Modify segment_and_fit_optimized():       │
      │  - Estimate diameter                     │
      │  - Get adaptive params                   │
      │  - Pass to transition detection          │
      │  (lines ~750-760)                        │
      └────────┬─────────────────────────────────┘
               │
               ▼
        ┌──────────────────────────────────────┐
        │ Update merging logic:                │
        │ Use adaptive merge_threshold         │
        │ (lines ~950-960)                    │
        └────────┬─────────────────────────────┘
                 │
                 ▼
          ┌──────────────────────────────┐
          │ RUN TEST PHASE 1:            │
          │ Test each size individually  │
          └────────┬─────────────────────┘
                   │
          Pass?────┼────Fail?
            │              │
            ▼              ▼
          YES         Debug & Adjust
                      │
                      └──► Back to review plan
                           Adjust parameters
                           Re-run Phase 1
            │
            ▼
     ┌──────────────────────────────┐
     │ RUN TEST PHASE 2:            │
     │ Full test suite (16 tests)   │
     └────────┬─────────────────────┘
              │
      ≥65%?───┼───<65%?
        │         │
        ▼         ▼
       YES    Debug & Adjust
               (go back to Phase 1)
        │
        ▼
     ┌──────────────────────────────┐
     │ RUN REGRESSION TESTING       │
     │ Verify no regressions >5%    │
     └────────┬─────────────────────┘
              │
      OK?─────┼────Issues?
        │         │
        ▼         ▼
       YES    Fix Issues
               │
               └──► Re-test
        │
        ▼
     ┌──────────────────────────────┐
     │ DOCUMENT RESULTS:            │
     │ Update EVALUATION_REPORT.md  │
     │ Create PRIORITY_1_RESULTS.md │
     └────────┬─────────────────────┘
              │
              ▼
      ┌──────────────────────────────┐
      │ GIT COMMIT & PUSH:           │
      │ Detailed commit message      │
      │ Include test results         │
      └────────┬─────────────────────┘
               │
               ▼
        ┌──────────────────────────┐
        │ IMPLEMENTATION COMPLETE  │
        │ Ready for Priority 2     │
        └──────────────────────────┘
```

---

**This visual guide supplements the detailed implementation plan. Use these diagrams to:**
- Understand parameter relationships
- See where code integration happens
- Track progress through testing phases
- Reference decision trees when debugging
- Visualize the improvement goals

