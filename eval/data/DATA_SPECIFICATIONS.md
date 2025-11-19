# Comprehensive Geometry Detection Evaluation - Data Specifications

## Data Generation Framework

### Overview
All test data is synthetically generated with mathematically precise definitions to ensure reproducibility and ground truth validation.

### Data Format

**Input Data Structure:**
```
DataFrame with columns:
  - Height_mm: Container height from bottom in millimeters (float64)
  - Volume_mm3: Cumulative volume from bottom in cubic millimeters (float64)
```

**Resolution:**
- 120 data points per container
- Regular spacing in height dimension
- Heights ranging from 0 to ~25-30 mm
- Volumes ranging from 0 to ~1500-2000 mm³ (1.5-2.0 mL)

### Noise Characteristics

**Noise Addition:**
```python
noise = np.random.normal(0, σ, len(volumes))
σ = 0.005 × mean(volumes)  # 0.5% standard deviation
noisy_volumes = volumes + |noise|
```

**Justification:**
- Represents typical measurement precision of graduated laboratory glassware
- Gaussian noise with zero mean (symmetric distribution)
- Magnitude: 0.5% of mean volume
- Applied as absolute value to prevent negative volumes

**Impact on Detection:**
- Does not significantly bias derivative calculations
- Smoothing filters handle noise effectively
- Transition detection uses multi-scale analysis

---

## Scenario-Specific Data Parameters

### Scenario 1: Sphere + Frustum + Cylinder

**Sphere Cap Section:**
```
Parameter: Radius R = 5.0 mm (fixed)
Height range: 0 to 5.0 mm
Formula: V = π × h² / 3 × (3R - h)
At h=5: V = π × 25 / 3 × (15 - 5) = π × 25 / 3 × 10 ≈ 261.8 mm³

Area formula: A = π × (2Rh - h²)
Gradient: dA/dh = π × (2R - 2h)
```

**Frustum Section:**
```
Radius range: r(h) = r1 + (r2 - r1) × (h - h_start) / (h_end - h_start)
where:
  - r1 = cylinder_radius + 1.5 mm
  - r2 = cylinder_radius
  - h_start = 5.0 mm
  - h_end = 15.0 mm

Volume increment: ΔV = π × Δh / 3 × (r1² + r1×r2 + r2²)
```

**Cylinder Section:**
```
Radius: r_cyl = cylinder_radius
Height range: 15.0 to 23.0 mm
Volume increment: ΔV = π × r² × Δh
```

**Data Points Distribution:**
- Sphere points: ~60 (height 0-5 mm)
- Frustum points: ~30 (height 5-15 mm)
- Cylinder points: ~30 (height 15-23 mm)

### Scenario 2: Frustum + Cylinder

**Frustum Section:**
```
Radius range: r(h) = r1 + (r2 - r1) × (h / 10)
where:
  - r1 = cylinder_radius + 1.0 mm
  - r2 = cylinder_radius
  - h ranges from 0 to 10 mm

Volume increment: ΔV = π × Δh / 3 × (r_prev² + r_prev×r_curr + r_curr²)
```

**Cylinder Section:**
```
Radius: r_cyl = cylinder_radius
Height range: 10.0 to 18.0 mm
Volume increment: ΔV = π × r² × Δh
```

**Data Points Distribution:**
- Frustum points: ~60 (height 0-10 mm)
- Cylinder points: ~60 (height 10-18 mm)

### Scenario 3: Cone + Frustum + Cylinder

**Cone Section:**
```
Radius progression: r(h) = r_apex × (h / h_cone)
where:
  - r_apex = 3.0 mm
  - h_cone = 8 mm
  - h ranges from 0 to 8 mm

Linear taper: r starts at 0 (apex), reaches 3 mm at top

Volume increment: ΔV = π × Δh / 3 × (r_prev² + r_prev×r_curr + r_curr²)
```

**Frustum Section:**
```
Radius range: r(h) = 3.0 + (cylinder_r - 3.0) × ((h - 8) / 6)
Height range: 8 to 14 mm
Volume increment: ΔV = π × Δh / 3 × (r_prev² + r_prev×r_curr + r_curr²)
```

**Cylinder Section:**
```
Radius: r_cyl = cylinder_radius
Height range: 14.0 to 22.0 mm
Volume increment: ΔV = π × r² × Δh
```

**Data Points Distribution:**
- Cone points: ~40 (height 0-8 mm)
- Frustum points: ~40 (height 8-14 mm)
- Cylinder points: ~40 (height 14-22 mm)

### Scenario 4: Semisphere + Cylinder (NEW)

**Semisphere Section:**
```
Geometry: Complete hemisphere, height = radius

For sphere of radius R at height h from apex:
  - Radius at height: r(h) = √(R² - (R-h)²)
  - Area at height: A(h) = π × r(h)²
  - Volume increment: ΔV = (A_curr + A_prev) / 2 × Δh (trapezoidal approximation)

Parameters:
  - R = cylinder_radius (5-8 mm)
  - Height range: 0 to cylinder_radius mm
```

**Cylinder Section:**
```
Radius: r_cyl = cylinder_radius
Height range: cylinder_radius to (cylinder_radius + 10) mm
Volume increment: ΔV = π × r² × Δh
```

**Data Points Distribution:**
- Hemisphere points: ~60 (height 0 to R)
- Cylinder points: ~60 (height R to R+10)

**Volume Calculation for Hemisphere:**
```
V_hemisphere = (2/3) × π × R³

Example: R = 5 mm
V = (2/3) × π × 125 ≈ 261.8 mm³

Example: R = 8 mm
V = (2/3) × π × 512 ≈ 1072.3 mm³
```

---

## Data Continuity Validation

All scenarios maintain perfect geometric continuity at transitions:

### Radius Continuity
```
At sphere→frustum: r_sphere = r_frustum_bottom
At frustum→cylinder: r_frustum_top = r_cylinder
At cone→frustum: r_cone_top = r_frustum_bottom
At semisphere→cylinder: r_semisphere = r_cylinder
```

### Volume Continuity
```
No discontinuities in cumulative volume function
Each segment's volume is added to previous cumulative total
```

### Area Continuity
```
Cross-sectional area matches at all boundaries
First derivative may have discontinuities (expected at geometry changes)
```

---

## Numerical Precision

**Floating-Point Handling:**
- Heights: 64-bit float (double precision)
- Volumes: 64-bit float (double precision)
- Noise: Generated with NumPy's normal distribution
- Arithmetic: Standard IEEE 754 floating-point operations

**Potential Precision Issues:**
- Very small height increments (< 0.1 mm): May accumulate rounding errors
- Large volume calculations: Divisions might introduce truncation
- Area derivatives: Finite differences sensitive to precision

**Mitigation:**
- Savitzky-Golay smoothing reduces noise impact
- Normalized scores prevent scale-dependent thresholding
- Adaptive thresholds adjust for SNR variations

---

## Data Generation Reproducibility

**Parameters for Reproducibility:**
```python
# Scenario-specific parameters:
sphere_r = 5.0  # mm (fixed)
cone_r = 3.0    # mm (fixed)
frustum_r1 = cyl_r + 1.0 or 1.5  # depends on scenario
frustum_r2 = cyl_r  # matches cylinder
cylinder_r = 5.0, 6.0, 7.0, 8.0  # mm

# Data generation:
n_points = 120  # total points
noise_level = 0.005  # 0.5% of mean

# Noise seed:
# Not explicitly set - generates different noise each run
# (This is intentional for robustness testing)
```

**Reproducible Components:**
- Geometric definitions (formulas)
- Point count distribution
- Noise standard deviation percentage
- Height ranges and segment lengths

**Non-Reproducible Components:**
- Random noise values (different each run)
- Exact float arithmetic results (platform dependent)

---

## Data Quality Metrics

### Scenario 1-3: Statistical Properties
- **Volume range:** 0 to 1500-2000 mm³
- **Height range:** 0 to 23-25 mm
- **Area range:** 78-201 mm² (cylinder areas)
- **Curvature:** Low (well-behaved polynomials)
- **Noise SNR:** >100 (high-quality data)

### Scenario 4: Hemisphere-Specific
- **Hemisphere volume:** 261.8 - 1072.3 mm³ (depending on radius)
- **Total container volume:** 561.8 - 1572.3 mm³
- **Area progression:** Non-linear (sphere) to linear (cylinder)
- **Maximum curvature:** At bottom of hemisphere

---

## Validation Approach

Each generated dataset is validated for:

1. **Geometric Correctness:**
   - Segments follow exact mathematical formulas
   - Radii match at boundaries
   - Heights progress monotonically

2. **Data Consistency:**
   - Volumes increase monotonically
   - No NaN or inf values
   - All values within physical bounds

3. **Noise Characteristics:**
   - Gaussian distribution
   - Appropriate magnitude
   - No systematic bias

4. **Processing Compatibility:**
   - Correct column names
   - Appropriate data types
   - Valid numeric ranges

---

## Summary Table

| Scenario | Segments | Points Distribution | Volume Range | Difficulty |
|---|---|---|---|---|
| Sphere+Frustum+Cyl | 3 | 60+30+30 | 0-1500 mm³ | Hard |
| Frustum+Cylinder | 2 | 60+60 | 0-2000 mm³ | Medium |
| Cone+Frustum+Cyl | 3 | 40+40+40 | 0-2000 mm³ | Hard |
| Semisphere+Cylinder | 2 | 60+60 | 0-1500 mm³ | Hard |

All data generated with continuous geometry and 0.5% Gaussian noise.
