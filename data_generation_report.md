# Data Generation & Error Analysis Report
**Date:** November 19, 2025
**Subject:** Centrifuge Tube Filling Simulation (1.5 mL)

## 1. Methodology: Geometric Modeling
The relationship between liquid volume and column height was derived from the technical drawing of a standard 1.5 mL centrifuge tube.

### Geometric Primitive
The tube is modeled as a composite shape:
1.  **Conical Bottom:**
    *   **Height:** 18.4 mm
    *   **Top Diameter:** 10.46 mm (matching cylinder)
    *   **Bottom:** Mathematically modeled as a cone tapering to a rounded tip.
    *   **Volume Logic:** \( V_{cone} \propto h^3 \) (cubic relationship in the conical section).
2.  **Cylindrical Body:**
    *   **Height:** 39.5 mm
    *   **Inner Diameter:** 10.46 mm
    *   **Volume Logic:** \( V_{cyl} \propto h \) (linear relationship above 18.4 mm).

### Simulation Process
To simulate the filling process, we calculated the height \( h \) for every accumulated volume \( V \) in **0.02 mL (20 µL)** increments.

---

## 2. Error Simulation Model
Real-world manual pipetting is never perfectly accurate. We applied a **Monte Carlo-style simulation** to introduce realistic noise to the volume additions.

### The Model
Instead of adding exactly 0.0200 mL at every step, the simulated addition \( V_{step} \) is:
\[ V_{step} = V_{nominal} + \epsilon_{systematic} + \epsilon_{random} \]

*   **Systematic Error (Bias):** A constant offset simulating a slightly miscalibrated pipette or consistent user tendency (e.g., consistently stopping at the wrong angle).
*   **Random Error (Precision):** Gaussian noise unique to each step, representing hand steadiness and mechanical variations.

These errors **accumulate**, meaning the final volume/height deviates from the ideal curve over time, mimicking a real laboratory filling sequence.

---

## 3. Justification of Error Rates

We simulated two scenarios: "Typical" and "Doubled" (Conservative). Both fall within reasonable and safe ranges for laboratory contexts.

### Scenario A: Typical Laboratory Error
*   **Parameters:** Systematic Bias: **-0.25%** | Random Error (CV): **1.0%**
*   **Justification:**
    *   **ISO 8655 Standard:** For a standard P20 pipette at 20 µL (nominal volume), the maximum permissible random error is **±0.5%**.
    *   **Human Factor:** Manual pipetting introduces additional variation beyond the mechanical spec. Adding 0.5% for human variance brings the total CV to roughly **1.0%**.
    *   **Verdict:** This represents a skilled technician using calibrated equipment.

### Scenario B: Doubled Error (Conservative / Worst-Case)
*   **Parameters:** Systematic Bias: **-0.50%** | Random Error (CV): **2.0%**
*   **Justification:**
    *   **Equipment Range:** If a larger pipette (e.g., P200) is used to dispense 20 µL (only 10% of its capacity), ISO 8655 permits significantly larger errors (often up to **±2.0-3.0%**).
    *   **Operational Variance:** Factors such as viscous liquids, temperature differences, or technician fatigue can easily double the coefficient of variation (CV).
    *   **Verdict:** A 2% CV is a **safe upper limit** for simulation. It ensures the system is robust enough to handle data from less-than-ideal pipetting runs without being unrealistically broken.

## 4. Summary of Generated Files
1.  **`centrifuge_tube_volume_height.csv`**: Ideal geometric data (no error).
2.  **`centrifuge_tube_simulation_with_error.csv`**: Simulation with Scenario A (Typical 1% CV).
3.  **`centrifuge_tube_simulation_doubled_error.csv`**: Simulation with Scenario B (Conservative 2% CV).
