# Comprehensive Geometry Detection Evaluation - Algorithm Details

## Algorithm Overview

The Container Geometry Analyzer uses a multi-stage pipeline to detect geometric transitions and fit container shapes to volume-height data.

**Pipeline Stages:**
1. Data preprocessing and area computation
2. Transition detection (improved multi-derivative method)
3. Segment extraction and shape fitting
4. Post-processing and optimization

---

## Stage 1: Data Preprocessing

### Input Data
```
DataFrame with:
  - Height_mm: Array of n height values
  - Volume_mm3: Array of n cumulative volume values
```

### Cross-Sectional Area Computation

**Method:** Local polynomial regression (Savitzky-Golay filtering)

```python
# Smooth volume data
volume_smooth = savgol_filter(volume, window_length=9, polyorder=2)

# Compute area via numerical differentiation
area = np.diff(volume_smooth) / np.diff(height)
```

**Purpose:**
- Reduce noise in volume measurements
- Enable stable derivative computation
- Preserve geometric features

**Parameters:**
- Window length: 9 points (adjustable)
- Polynomial order: 2 (quadratic)
- Result: 1 fewer points than input (differencing)

---

## Stage 2: Transition Detection (Improved Method)

### Overview

Uses **multi-derivative analysis** with adaptive thresholding to detect geometry transitions.

### Key Insight

Different geometric shapes have characteristic derivative patterns:
- **Sphere:** Curved surface → Non-linear area change
- **Frustum:** Linear taper → Linear area change
- **Cylinder:** Constant radius → Constant area (zero 1st derivative)
- **Cone:** Linear taper from apex → Linear area change (different slope)

### Mathematical Foundation

**1st Derivative (Rate of Change):**
```
dA/dh = rate of area change
- Sphere: Non-zero, decreasing
- Frustum: Constant (non-zero)
- Cylinder: Zero
- Cone: Constant but different slope
```

**2nd Derivative (Curvature):**
```
d²A/dh² = change in rate of change
- Sphere: Non-zero (curved)
- Frustum: Zero (linear)
- Cylinder: Zero (constant)
- Cone: Zero (linear)
```

### Transition Detection Algorithm

**Step 1: Compute Derivatives**
```python
heights = df_areas['Height_mm'].values
area = df_areas['Area'].values

# Smooth area to reduce noise
area_smooth = savgol_filter(area, window_length=max(5, min(15, n//10)), polyorder=2)

# Compute 1st and 2nd derivatives
first_deriv = np.gradient(area_smooth, heights)
second_deriv = np.gradient(first_deriv, heights)
```

**Step 2: Compute Transition Score**
```python
# Absolute changes in derivatives
first_deriv_change = np.abs(np.diff(first_deriv))
second_deriv_abs = np.abs(second_deriv[:-1])

# Normalize to [0, 1]
norm_1st = (first_deriv_change - min) / (max - min)
norm_2nd = (second_deriv_abs - min) / (max - min)

# Combine with weighting
# 60% weight on 1st derivative (linear transitions)
# 40% weight on 2nd derivative (curved transitions)
score = 0.6 * norm_1st + 0.4 * norm_2nd
```

**Step 3: Adaptive Thresholding**
```python
# Estimate Signal-to-Noise Ratio (SNR)
area_very_smooth = savgol_filter(area, window_length=window, polyorder=2)
noise = area - area_very_smooth
noise_std = np.std(noise)
signal_range = np.max(area) - np.min(area)
snr = signal_range / (noise_std + 1e-8)

# Adapt percentile based on SNR
if snr > 100:
    percentile = 70  # Very clean → more sensitive
elif snr > 50:
    percentile = 75  # Clean
elif snr > 20:
    percentile = 80  # Moderate noise
elif snr > 10:
    percentile = 85  # Noisy
else:
    percentile = 90  # Very noisy → less sensitive

threshold = np.percentile(score, percentile)
candidates = np.where(score > threshold)[0] + 1
```

**Step 4: Validation**
```python
# Ensure minimum spacing between transitions
min_points = 12
transitions = [0]

for candidate in sorted(candidates):
    if candidate - transitions[-1] >= min_points:
        transitions.append(candidate)

if transitions[-1] != n - 1:
    transitions.append(n - 1)

# Validate segments
validated = [0]
for i in range(len(transitions) - 1):
    segment = area[transitions[i]:transitions[i+1]]

    # Check: coefficient of variation
    cv = np.std(segment) / (np.mean(segment) + 1e-8)
    has_variation = cv > 0.05

    # Check: structure (autocorrelation)
    if len(segment) > 3:
        correlation = np.corrcoef(segment[:-1], segment[1:])[0, 1]
        has_structure = abs(correlation) > 0.4
    else:
        has_structure = True

    # Check: fit quality
    z = np.arange(len(segment))
    if len(z) > 2:
        coeffs = np.polyfit(z, segment, 1)
        predicted = np.polyval(coeffs, z)
        r_squared = 1 - (np.sum((segment - predicted)**2) /
                        (np.sum((segment - np.mean(segment))**2) + 1e-8))
        fits_model = r_squared > 0.65
    else:
        fits_model = True

    passed = sum([has_variation, has_structure, fits_model])
    if passed >= 2 or i in [0, len(transitions)-2]:
        validated.append(transitions[i+1])

return sorted(list(set(validated)))
```

### Transition Detection Parameters

| Parameter | Value | Rationale |
|---|---|---|
| **Percentile (base)** | 90 | Use 90th percentile of transition score |
| **SNR threshold 1** | 100 | Indicates very clean data |
| **SNR threshold 2** | 50 | Indicates clean data |
| **SNR threshold 3** | 20 | Indicates moderate noise |
| **SNR threshold 4** | 10 | Indicates noisy data |
| **Adaptive percentile range** | 70-90 | Adjust sensitivity based on data quality |
| **Min points between transitions** | 12 | Ensure segments have minimum data |
| **CV threshold** | 0.05 | Detect variation in segment |
| **Autocorrelation threshold** | 0.4 | Detect structure vs noise |
| **R² threshold** | 0.65 | Accept segments fitting polynomial model |

---

## Stage 3: Segmentation & Shape Fitting

### Segment Extraction

For each detected transition pair (start_idx, end_idx):
```python
x = heights[start_idx:end_idx+1]
y = volumes[start_idx:end_idx+1]

# Guessed radius from mean area
mean_area = np.median(area[start_idx:end_idx+1])
guess_r = np.sqrt(mean_area / np.pi)
```

### Shape Fitting Methods

**A. Cylinder Fit**
```
Model: V(h) = π × r² × (h - h₀)

Parameters: [r]
Bounds: [0.5*guess_r, 3.0*guess_r]

Error metric: MAE (mean absolute error)
```

**B. Frustum Fit**
```
Model: V(h) = π × (h - h₀) / 3 × (r1² + r1×r2 + r2²)

Parameters: [r1, r2, h]
Bounds:
  - r1: [0.5*r1_guess, 3.0*r1_guess]
  - r2: [0.5*r2_guess, 3.0*r2_guess]
  - h: [0.8*height_span, 1.2*height_span]

Error metric: MAE
```

**C. Cone Fit**
```
Model: V(h) = π × h / 3 × r² (apex at origin)

Parameters: [r_base, h]
Bounds:
  - r_base: [0.1*guess_r, 5*guess_r]
  - h: [0.5*height_span, 2*height_span]

Error metric: MAE
```

**D. Sphere Cap Fit**
```
Model: V(h) = π × h² / 3 × (3R - h)

Parameters: [R] (sphere radius)
Bounds: [0.5*R_guess, 10*R_guess]
where R_guess = 1.5 * max_radius_in_segment

Error metric: MAE
```

### Shape Selection Logic

```python
# Compute error for each shape
fit_results = []
for shape_fit in [cylinder_fit, frustum_fit, cone_fit, sphere_fit]:
    error_pct = compute_error_percentage(shape_fit)
    fit_results.append((shape_name, params, error_pct))

# Apply complexity penalty (prefer simpler models)
adjusted_results = []
for shape_name, params, error_pct in fit_results:
    adjusted_error = error_pct

    if shape_name == 'frustum' and error_pct < 3.0:
        adjusted_error += 0.5  # Penalize 3-parameter model
    elif shape_name == 'cone' and error_pct < 3.0:
        adjusted_error += 0.2  # Penalize 2-parameter model
    # cylinder and sphere_cap: no penalty

    adjusted_results.append((shape_name, params, error_pct, adjusted_error))

# Select best (lowest adjusted error)
best_shape = min(adjusted_results, key=lambda x: x[3])

# Special case: if frustum is near-cylindrical, prefer cylinder
if best_shape == 'frustum' and len(best_params) >= 2:
    r1, r2 = best_params[0], best_params[1]
    rel_diff = abs(r2 - r1) / max(r1, r2)

    if rel_diff < 0.05:  # < 5% difference
        cyl_fit = [next((f for f in fit_results if f[0]=='cylinder'))]
        if cyl_fit and cyl_fit[0][2] <= best_error * 1.2:
            best_shape = 'cylinder'
```

---

## Stage 4: Post-Processing - Intelligent Merging

### Purpose

Reduce over-segmentation by merging adjacent segments of the same shape if they are geometrically continuous.

### Merge Validation Rules

**For Frustums:**
```python
r2_current = current_segment.params[1]
r1_next = next_segment.params[0]
radius_diff = abs(r2_current - r1_next) / max(r2_current, r1_next)

if radius_diff < 0.10:  # < 10% difference
    merge_segments()
```

**For Cylinders:**
```python
r_current = current_segment.params[0]
r_next = next_segment.params[0]
radius_diff = abs(r_current - r_next) / max(r_current, r_next)

if radius_diff < 0.05:  # < 5% difference
    merge_segments()
```

**For Cones:**
```python
r_current = current_segment.params[0]
r_next = next_segment.params[0]
radius_diff = abs(r_current - r_next) / max(r_current, r_next)

if radius_diff < 0.10:  # < 10% difference
    merge_segments()
```

**Special Cases:**
```python
# Never merge sphere_cap with other shapes
if current_shape == 'sphere_cap' or next_shape == 'sphere_cap':
    skip_merge()

# Only merge if adjacent and same shape
if next_shape != current_shape or next_start > current_end + 1:
    skip_merge()
```

### Merge Algorithm

```python
merged_segments = []
skip_indices = set()

for i in range(len(segments)):
    if i in skip_indices:
        continue

    current = segments[i]
    merged = False

    while i + 1 < len(segments):
        next_seg = segments[i + 1]

        # Check shape, adjacency
        if next_seg.shape != current.shape or next_seg.start > current.end + 1:
            break

        # Special: never merge sphere_cap
        if current.shape == 'sphere_cap':
            break

        # Check geometric continuity
        if validate_continuity(current, next_seg):
            # Merge
            current.end = next_seg.end
            if current.shape == 'frustum':
                current.params = [current.r1, next_seg.r2, current.end - current.start]
            skip_indices.add(i + 1)
            merged = True
            i += 1
        else:
            break

    merged_segments.append(current)

return merged_segments
```

---

## Configuration & Optimization

### Current Optimal Parameters

Based on 16-test evaluation:

```python
DEFAULT_PARAMS = {
    'percentile': 96,              # Higher for less sensitivity
    'variance_threshold': 0.14,    # CV threshold for validation
    'merge_threshold': 0.12,       # Adjacent segment merge tolerance
    'transition_detection_method': 'improved',  # Multi-derivative method
    'use_adaptive_threshold': True,  # SNR-based percentile
    'use_local_regression': True,  # Savitzky-Goyal area computation
    'debug_transitions': False,    # Verbose output
}
```

### Tuning Rationale

**Percentile: 96**
- Reduced from 90 to decrease false positives in smooth regions
- Higher value → less sensitive to noise
- Balance: Catches real transitions while avoiding noise artifacts

**Merge Threshold: 0.12**
- Tolerates up to 12% radius variation
- Merges adjacent frustum segments with continuous taper
- Prevents over-segmentation in linear regions

---

## Performance Characteristics

### Computational Complexity

| Stage | Complexity | Time |
|---|---|---|
| Area computation | O(n) | <1 ms |
| Transition detection | O(n) | 10-50 ms |
| Shape fitting | O(k×n) | 100-500 ms |
| Post-processing | O(k²) | 1-10 ms |
| **Total** | **O(n + k×n)** | **~200 ms** |

where n = number of points (~120), k = number of segments (~3-4)

### Memory Usage

- Input data: ~2 KB (120 points × 16 bytes)
- Intermediate arrays: ~10 KB (area, derivatives, scores)
- Fitting results: <1 KB
- **Total: ~15 KB** (negligible)

---

## Known Limitations

1. **Smooth Curves:** Difficulty distinguishing smooth sphere cap curves from noise
2. **Linear Segments:** Frustum and cone both show linear area changes; differentiating requires careful threshold tuning
3. **Small Segments:** Segments with <12 points rejected; may miss small geometric features
4. **Noise Sensitivity:** SNR estimation may be inaccurate with bimodal noise distributions

---

## Validation Metrics

Algorithm evaluated on:
- **Scenario coverage:** 4 distinct geometry combinations
- **Size range:** 10-16 mm diameter cylinders
- **Data quality:** 120 points per container, 0.5% noise
- **Ground truth:** Exact mathematical formulas

See `results/` directory for detailed evaluation results.
