# Comprehensive Geometry Detection Evaluation - Scenario Descriptions

## Overview

This evaluation tests the Container Geometry Analyzer algorithm against 4 distinct geometric container combinations across 4 cylinder diameter ranges. Each scenario represents a realistic laboratory container configuration.

## Tested Scenarios

### Scenario 1: Sphere + Frustum + Cylinder (3-segment container)

**Description:** A realistic lab container with hemispherical/curved bottom, tapered middle section, and straight cylindrical neck.

**Real-World Application:**
- Common in flask designs for chemistry labs
- Graduated measuring flasks
- Conical bottom with transition to measurement neck

**Geometric Specification:**
```
1. Sphere/Cap (Bottom)
   - Radius: 5.0 mm (fixed)
   - Height: ~5-7 mm (approximately hemispherical)
   - Volume: Follows sphere cap equation V = πh²/3 * (3R - h)

2. Frustum (Middle)
   - Bottom radius: cylinder_radius + 1.5 mm
   - Top radius: cylinder_radius (linear taper)
   - Height: ~10 mm
   - Volume: Frustum equation with varying radii

3. Cylinder (Top)
   - Radius: 5-8 mm (diameter 10-16 mm)
   - Height: ~8 mm
   - Volume: πr²h
```

**Expected Detection:** 3 distinct segments with clear transitions at:
- Sphere cap to frustum boundary (curvature change to linear)
- Frustum to cylinder boundary (radius changes)

**Challenge:** Detecting the transition from smooth sphere cap curve to linear frustum

---

### Scenario 2: Frustum + Cylinder (2-segment container)

**Description:** Simplified tapered container with straight neck - represents many pipette or burette designs.

**Real-World Application:**
- Burettes and volumetric glassware
- Graduated pipettes
- Simple pourspout containers

**Geometric Specification:**
```
1. Frustum (Bottom)
   - Bottom radius: cylinder_radius + 1.0 mm
   - Top radius: cylinder_radius (linear taper)
   - Height: ~10 mm
   - Volume: Frustum equation

2. Cylinder (Top)
   - Radius: 5-8 mm (diameter 10-16 mm)
   - Height: ~8 mm
   - Volume: πr²h
```

**Expected Detection:** 2 distinct segments with clear boundary where:
- Radius changes discontinuously (linear to constant)
- Area gradient changes significantly

**Challenge:** Avoiding false segmentation within the smooth tapered frustum section

---

### Scenario 3: Cone + Frustum + Cylinder (3-segment container)

**Description:** Container with pointed/conical bottom, tapered middle, and straight top. Represents pointed-bottom flasks.

**Real-World Application:**
- Pointed-bottom centrifuge tubes
- Conical bottom lab vessels
- Specialized chemistry glassware

**Geometric Specification:**
```
1. Cone (Bottom)
   - Apex radius: 3.0 mm (apex at bottom, point)
   - Base radius: 3.0 mm at top of cone
   - Height: ~8 mm
   - Volume: 1/3 * πr²h (cone formula)

2. Frustum (Middle)
   - Bottom radius: 3.0 mm (connects to cone)
   - Top radius: cylinder_radius (linear taper)
   - Height: ~6 mm
   - Volume: Frustum equation

3. Cylinder (Top)
   - Radius: 5-8 mm (diameter 10-16 mm)
   - Height: ~8 mm
   - Volume: πr²h
```

**Expected Detection:** 3 distinct segments with transitions at:
- Cone to frustum (radius stops varying linearly)
- Frustum to cylinder (taper becomes constant)

**Challenge:** Distinguishing cone's linear taper from frustum's different taper rate

---

### Scenario 4: Semisphere + Cylinder (2-segment container - NEW)

**Description:** Container with complete hemispherical bottom and straight cylindrical neck. More practical than partial sphere cap.

**Real-World Application:**
- Some specialized vessels with rounded bottoms
- Biotech culture vessels
- Mixing vessels with hemispherical bottoms

**Geometric Specification:**
```
1. Semisphere (Bottom)
   - Radius: 5-8 mm (matches cylinder radius, diameter 10-16 mm)
   - Height: 5-8 mm (equal to radius for complete hemisphere)
   - Volume: 2/3 * πR³ (hemisphere volume formula)

2. Cylinder (Top)
   - Radius: 5-8 mm (diameter 10-16 mm, matches hemisphere)
   - Height: ~10 mm
   - Volume: πr²h
```

**Expected Detection:** 2 distinct segments with clear boundary where:
- Curvature transitions from spherical to zero (plane surface)
- Area derivative transitions from varying to constant

**Challenge:** Detecting the transition from curved (non-linear area change) to straight (constant area)

---

## Diameter Ranges Tested

All scenarios tested with upper cylinder diameter ranges:

| Diameter (mm) | Radius (mm) | Classification |
|---|---|---|
| 10 | 5.0 | Small vessels |
| 12 | 6.0 | Small-medium vessels |
| 14 | 7.0 | Medium vessels |
| 16 | 8.0 | Medium-large vessels |

**Rationale:** These ranges cover typical laboratory glassware sizes (10-100 mL) where precise volume measurement is critical.

---

## Data Generation Parameters

**Common to All Scenarios:**
- Points per container: 120 (high resolution)
- Height resolution: ~0.3-0.5 mm per point
- Volume units: mL (converted to mm³ for processing)
- Noise addition: Gaussian 0.5% standard deviation
  - Simulates realistic measurement precision
  - Typical for graduated glassware (±0.5-1% accuracy)

**Continuous Geometry:**
- All segment boundaries are geometrically continuous
- Radii match exactly at transitions
- No artificial jumps or discontinuities
- Smooth mathematical representations

---

## Key Evaluation Questions

1. **Transition Detection:** Can the algorithm detect transitions between different geometric shapes?
2. **Shape Identification:** Does it correctly identify the shape types (sphere, frustum, cone, cylinder)?
3. **Segment Count:** Does it detect the correct number of segments?
4. **Robustness:** How does performance vary across different container sizes?
5. **Hemisphere Challenge:** How does the new hemisphere test compare to partial sphere cap detection?

---

## Expected Characteristics by Scenario

### Sphere + Frustum + Cylinder
- **1st Derivative (dA/dh):**
  - Sphere: Non-linear (decreasing rate of change)
  - Frustum: Linear (constant rate of change)
  - Cylinder: Zero (constant area)
- **2nd Derivative (d²A/dh²):**
  - Sphere: Non-zero (curvature)
  - Frustum: Zero (no curvature)
  - Cylinder: Zero (no curvature)

### Frustum + Cylinder
- **1st Derivative:**
  - Frustum: Linear (constant rate)
  - Cylinder: Zero (no change)
- **2nd Derivative:**
  - Frustum: Zero (no curvature)
  - Cylinder: Zero (no curvature)
- **Detection Difficulty:** Moderate - linear frustum might be indistinguishable from noise

### Cone + Frustum + Cylinder
- **1st Derivative:**
  - Cone: Linear with different slope than frustum
  - Frustum: Linear with different slope than cone
  - Cylinder: Zero
- **2nd Derivative:**
  - All zero (all linear in area)
- **Detection Difficulty:** High - must detect rate change in 1st derivative

### Semisphere + Cylinder
- **1st Derivative:**
  - Hemisphere: Non-linear (varies with height)
  - Cylinder: Zero (constant)
- **2nd Derivative:**
  - Hemisphere: Non-zero (curvature)
  - Cylinder: Zero (no curvature)
- **Detection Difficulty:** High (similar to sphere+frustum) - curved bottom with straight top

---

## Measurement Resolution

Each scenario generates exactly 120 data points:

| Height Range | Points | Resolution |
|---|---|---|
| 0-10 mm | ~60 | 0.17 mm per point |
| 10-20 mm | ~60 | 0.17 mm per point |

This provides sufficient resolution for detecting smooth transitions while maintaining realistic measurement noise characteristics.
