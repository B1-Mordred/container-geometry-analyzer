# Priority 2: Curved Surface Detection - Implementation Plan

**Objective:** Improve detection of hemisphere and sphere cap geometries through specialized curved surface analysis.

**Expected Impact:** +25% accuracy improvement (Semisphere+Cyl: 25%→75%, Sphere+Frust+Cyl: 50%→75%)

**Complexity:** High (requires algorithm enhancements)
**Effort Estimate:** 4-8 hours

---

## Executive Summary

Priority 2 addresses the critical weakness in curved surface detection. The current algorithm assumes piecewise-linear segments and fails on hemispheres/sphere caps, creating false transitions from inflection points in smooth curves.

### The Problem

Current Performance:
- Hemisphere/sphere cap detection: **25-50%** (critical weakness)
- Over-segmentation: **75% of failures** (false transitions from curved surfaces)
- Affecting: Semisphere+Cylinder, Sphere+Frustum+Cylinder scenarios

### The Solution

Implement **curvature-aware detection**:
1. Detect curved surfaces using curvature analysis
2. Apply specialized fitting for hemispheres and sphere caps
3. Suppress false transitions in smooth regions
4. Bottom-of-container focused analysis

---

## Technical Analysis

### Why Current Method Fails

**Hemisphere Volume Curve Analysis:**

```
Volume = (2/3)π × R³ × (3h/R - h³/R³)   where h ∈ [0, R]

First Derivative (Area):
dV/dh = 2πR(2h - h²/R²) × ... = πR² × (2 - 3h²/R²)

Second Derivative (Curvature):
d²V/dh² = -6πRh = non-zero (continuous curvature)

Key Issue: dA/dh is NOT constant (unlike cylinders/frustums)
- Creates smoothly changing area values
- Multiple local extrema in 2nd derivative
- Current percentile thresholding triggers on inflection points
```

**Example Failure: Semisphere+Cylinder at d=12mm**
```
Expected: 2 segments [hemisphere, cylinder]
Detected: 3-4 segments [frustum, frustum, cylinder]

Why:
1. Hemisphere's curved area profile triggers multiple transitions
2. Inflection point at h ≈ 0.5R detected as boundary
3. Merging tolerances insufficient to recombine
```

### Root Causes Identified

| Root Cause | Impact | Current Mitigation | Why Insufficient |
|-----------|--------|-------------------|------------------|
| Non-linear dA/dh | Creates multiple local extrema | SNR-based percentile | Doesn't distinguish curves |
| Inflection points | False transition candidates | Percentile threshold | Triggers on inflection |
| Smooth transitions | Area changes gradually | Variance threshold | Catches every change |
| Continuous curvature | No discrete boundaries | Geometric constraints | Don't apply to curves |

---

## Solution Architecture

### Design: 4-Stage Curved Surface Detection Pipeline

```
┌─────────────────────────────────────────────────────┐
│ Input: Area + Height Data                           │
└────────────────┬────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────┐
│ STAGE 1: Curvature Analysis                         │
│ - Compute curvature (2nd derivative magnitude)      │
│ - Identify potentially curved regions               │
│ - Flag bottom-of-container (likely curved)          │
└────────────────┬────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────┐
│ STAGE 2: Curved Surface Classification              │
│ - Check if region matches hemisphere signature      │
│ - Check if region matches sphere cap signature      │
│ - Determine fitting strategy                        │
└────────────────┬────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────┐
│ STAGE 3: Specialized Fitting                        │
│ - Hemisphere: V = (2/3)πR³ × f(h/R)                │
│ - Sphere cap: V = πh² × (3R - h) / 3              │
│ - Apply curvature-aware bounds                      │
└────────────────┬────────────────────────────────────┘
                 ▼
┌─────────────────────────────────────────────────────┐
│ STAGE 4: Transition Suppression                     │
│ - Suppress false transitions in curved regions      │
│ - Merge inflection-point-induced segments          │
│ - Return final segments                             │
└─────────────────────────────────────────────────────┘
```

---

## Implementation Strategy

### Approach: Hybrid Curvature + Traditional Detection

Modify transition detection to:
1. **Identify curved regions** using curvature threshold
2. **Apply curvature-aware filtering** to suppress false transitions
3. **Use specialized hemisphere/sphere cap fitting**
4. **Post-process merging** for inflection-induced segments

### Key Innovations

#### 1. Curvature Quantification

```python
# Current: Uses only 1st and 2nd derivatives
# Issue: Doesn't distinguish curves from noise

# New: Add curvature coefficient
curvature = np.abs(second_deriv) / (1 + np.abs(first_deriv))**1.5

# Identify curved regions:
# - High curvature in smooth areas → likely curved surface
# - High curvature in noisy areas → likely noise
```

#### 2. Hemisphere Signature Detection

```python
# Check if data matches hemisphere profile:
# V(h) = (2/3)πR³ × (3h/R - h³/R³)
# Characteristics:
# - Area starts at π*R² (maximum)
# - Area decreases with height
# - Concave-down profile
# - Smoothly reaches near-zero area at top

def detect_hemisphere_signature(area, heights):
    # Check 1: Area decreases monotonically
    area_increasing = np.all(np.diff(area) <= 0)

    # Check 2: Curvature pattern matches hemisphere
    second_deriv = np.gradient(np.gradient(area))
    curvature_smooth = np.abs(second_deriv) < threshold

    # Check 3: Initial area close to maximum
    area_ratio = area[0] / np.max(area)

    return area_increasing and curvature_smooth and area_ratio > 0.95
```

#### 3. Sphere Cap Signature Detection

```python
# Sphere cap: V = πh² × (3R - h) / 3
# Characteristics:
# - Starts at zero area (apex)
# - Increases monotonically with height
# - Area increase rate changes
# - Concave pattern

def detect_sphere_cap_signature(area, heights):
    # Check 1: Area increases monotonically
    area_increasing = np.all(np.diff(area) >= 0)

    # Check 2: Area starts near zero
    area_min_ratio = area[0] / np.max(area)

    # Check 3: Curvature pattern (acceleration changes)
    first_deriv = np.gradient(area)
    second_deriv = np.gradient(first_deriv)

    # For sphere cap: dA/dh increases then decreases
    max_deriv_idx = np.argmax(first_deriv)
    changes_sign = (second_deriv[:max_deriv_idx] > 0).sum() > len(second_deriv) // 3

    return area_increasing and area_min_ratio < 0.05 and changes_sign
```

#### 4. Curvature-Aware Transition Filtering

```python
# Suppress transitions within curved regions
def filter_transitions_in_curves(transitions, area, heights, curvature_threshold=0.1):
    """
    Remove transitions that occur in smooth (curved) regions
    """
    # Compute curvature for full data
    smooth_area = savgol_filter(area, window_length=..., polyorder=2)
    first_deriv = np.gradient(smooth_area)
    second_deriv = np.gradient(first_deriv)
    curvature = np.abs(second_deriv) / (1 + np.abs(first_deriv))**1.5

    # Find smooth regions (high curvature)
    smooth_mask = curvature > curvature_threshold

    # Filter transitions: keep only those at boundaries of smooth regions
    filtered = []
    for t in transitions:
        # Check if transition is at smooth→linear boundary
        is_boundary = (smooth_mask[t-1] != smooth_mask[t]) if t > 0 else True
        if is_boundary:
            filtered.append(t)

    return filtered
```

#### 5. Hemisphere-Specific Fitting

```python
def volume_hemisphere(h, R):
    """
    Hemisphere volume as function of fill height
    V(h) = (2/3)π*R³ × (3h/R - h³/R³)
    """
    h_ratio = h / R
    return (2/3) * np.pi * R**3 * (3*h_ratio - h_ratio**3)

# In segment fitting:
# For identified hemisphere regions:
# - Use hemisphere fitting function
# - Apply bounds: h_max = R (hemisphere height = radius)
# - Initial guess from area[0] ≈ π*R²
```

---

## Implementation Steps

### Step 1: Add Curvature Analysis Functions (30 min)

Create new module: `_curved_surface_detection.py`

```python
def compute_curvature(area, heights):
    """Compute curvature coefficient for area profile"""
    first_deriv = np.gradient(area, heights)
    second_deriv = np.gradient(first_deriv, heights)
    return np.abs(second_deriv) / (1 + np.abs(first_deriv))**1.5

def detect_hemisphere_signature(area, heights):
    """Detect if data matches hemisphere profile"""
    # Check monotonic decrease
    # Check maximum at start
    # Check curvature pattern
    pass

def detect_sphere_cap_signature(area, heights):
    """Detect if data matches sphere cap profile"""
    # Check monotonic increase from zero
    # Check curvature inflection
    pass

def filter_transitions_in_curves(transitions, area, heights):
    """Remove false transitions in curved regions"""
    pass
```

### Step 2: Add Specialized Fitting Functions (30 min)

```python
def volume_hemisphere(h, R):
    """Hemisphere volume function"""
    h_ratio = np.asarray(h) / R
    return (2/3) * np.pi * R**3 * (3*h_ratio - h_ratio**3)

def volume_sphere_cap(h, R):
    """Sphere cap volume function"""
    return np.pi * h**2 * (3*R - h) / 3

def fit_hemisphere(x, y):
    """Fit hemisphere model to segment"""
    # x: height, y: volume
    # Solve for R using curve_fit
    pass

def fit_sphere_cap(x, y):
    """Fit sphere cap model to segment"""
    # x: height, y: volume
    # Solve for R using curve_fit
    pass
```

### Step 3: Integrate into Transition Detection (1 hour)

Modify `find_optimal_transitions_improved()`:

```python
def find_optimal_transitions_improved(area, heights=None, ..., use_curvature_filter=True):
    # ... existing code ...

    # NEW: Apply curvature filtering
    if use_curvature_filter:
        # Identify curved regions
        curvature = compute_curvature(area, heights)

        # Filter transitions that occur in curves
        transitions = filter_transitions_in_curves(
            transitions, area, heights, curvature_threshold=0.15
        )

    return transitions
```

### Step 4: Integrate into Segment Fitting (1 hour)

Modify `segment_and_fit_optimized()`:

```python
def segment_and_fit_optimized(df_areas, ...):
    # ... existing code ...

    # NEW: Curved surface detection
    hemisphere_sig = detect_hemisphere_signature(area, heights)
    sphere_cap_sig = detect_sphere_cap_signature(area, heights)

    # NEW: Specialized fitting for curves
    if current_shape == 'hemisphere' or hemisphere_sig:
        # Try hemisphere fit
        result = fit_hemisphere(x, y)
        fit_results.append(('hemisphere', result, error))

    if sphere_cap_sig:
        # Try sphere cap fit
        result = fit_sphere_cap(x, y)
        fit_results.append(('sphere_cap', result, error))

    # ... existing fitting code ...
```

### Step 5: Add Post-Processing for Curved Segments (30 min)

```python
def merge_inflection_segments(segments):
    """
    Merge segments that were created by inflection points
    in a single curved surface
    """
    # Strategy: If consecutive segments are same shape
    # and curvature is continuous, merge them

    # Check for: frustum+frustum in curved region
    # → likely a single hemisphere split by inflection
    pass
```

---

## Testing Strategy

### Test Phase 1: Unit Tests

```python
# Test curvature detection
test_hemisphere_curvature_high()
test_linear_curvature_low()

# Test signature detection
test_detect_hemisphere_signature()
test_detect_sphere_cap_signature()

# Test fitting
test_hemisphere_fit_accuracy()
test_sphere_cap_fit_accuracy()
```

### Test Phase 2: Integration Tests

```python
# Test on specific failing cases
test_semisphere_cylinder_d10()    # Currently fails
test_semisphere_cylinder_d12()    # Currently fails
test_sphere_frustum_cylinder_d14() # Currently fails

# Expected: Improvement from 25% → 50-75%
```

### Test Phase 3: Regression Tests

```python
# Ensure Priority 1 still works
test_all_16_scenarios()           # Should maintain or improve

# Expected: Overall improvement from 50% → 70-75%
```

---

## Expected Outcomes

### Success Metrics

| Scenario | Before | Target | Success |
|----------|--------|--------|---------|
| Semisphere+Cylinder | 25% | 75% | ✓ +50pts |
| Sphere+Frustum+Cylinder | 50% | 75% | ✓ +25pts |
| Frustum+Cylinder | 50% | 55% | ✓ +5pts |
| Cone+Frustum+Cylinder | 75% | 80% | ✓ +5pts |
| **Overall** | **50%** | **70-75%** | ✓ +20-25pts |

### Risk Assessment

**Medium Risk:**
- Algorithm changes are localized to curved detection
- Fallback to existing fitting if curved detection fails
- Regression tests catch any degradation

**Mitigation:**
- Use feature flag to enable/disable curvature filtering
- Comprehensive testing on all scenarios
- Maintain backward compatibility

---

## Timeline Estimate

| Phase | Time | Tasks |
|-------|------|-------|
| **Analysis & Design** | 1h | Finalize approach, review math |
| **Implementation** | 2-3h | Code all 5 steps above |
| **Testing** | 1-2h | Unit, integration, regression |
| **Documentation** | 30m | Results, commit message |
| **Iteration/Debugging** | 1h | Fix any issues found |
| **Total** | **5-7.5h** | **Complete Priority 2** |

---

## Success Criteria

- [ ] Code compiles without errors
- [ ] Curvature analysis functions working
- [ ] Hemisphere/sphere cap signatures detected correctly
- [ ] Specialized fitting achieving <5% error on test data
- [ ] False transitions suppressed in curved regions
- [ ] Semisphere+Cylinder accuracy ≥50% (target 75%)
- [ ] Sphere+Frustum+Cylinder accuracy ≥60% (target 75%)
- [ ] No regression in other scenarios
- [ ] All changes committed and documented

---

## Next Phase After Priority 2

Once curved surface detection is working:

**Priority 3: Linear Shape Discrimination**
- Improve cone vs. frustum distinction
- Expected: +10% accuracy improvement
- Focus: Better fitting bounds, apex detection
- Effort: 2-4 hours

**Target Final Performance:** 80-85% overall accuracy

---

## References

### Mathematical Formulas

**Hemisphere Volume:**
```
V(h) = (2/3)πR³ × (3h/R - h³/R³)
     = πh²(3R - h)/3
Area(h) = πR² × (2 - 3(h/R)²)
```

**Sphere Cap Volume:**
```
V(h) = πh² × (3R - h) / 3
Area(h) = π(R² - (R-h)²) = π(2Rh - h²)
```

**Curvature (simplified):**
```
κ = |d²y/dx²| / (1 + |dy/dx|²)^1.5
```

### Key Papers/References
- Differential geometry of curves
- Least-squares fitting for non-linear models
- Signal processing for curved data
- Geometric shape recognition

---

## Appendix: Pseudocode for Key Functions

### Algorithm 1: Detect Curved Surface

```
function detectCurvedSurface(area, heights):
    compute curvature c = curvature(area, heights)

    if max(c) > HIGH_THRESHOLD:
        check hemisphere signature
        check sphere cap signature

        if hemisphere or sphere_cap:
            return CURVED_SURFACE

    return LINEAR_SURFACE
```

### Algorithm 2: Suppress Inflection Transitions

```
function suppressInflectionTransitions(transitions, curvature):
    filtered = []

    for each transition t:
        if curvature[t] > CURVE_THRESHOLD:
            # Transition is in curved region
            # Check if at boundary of curved region
            if curvature[t-1] != curvature[t]:
                # At boundary: keep it
                filtered.append(t)
            # else: inside curve: skip it
        else:
            # In linear region: keep it
            filtered.append(t)

    return filtered
```

---

**Status:** PLANNING PHASE COMPLETE
**Next Action:** Begin implementation of Step 1

