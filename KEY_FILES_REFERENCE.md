# Key Files Reference Guide

## Essential Files for Parameter Tuning

### Configuration & Parameters
| File | Lines | Purpose |
|------|-------|---------|
| `src/container_geometry_analyzer_gui_v3_11_8.py` | 80-101 | `DEFAULT_PARAMS` - Main tunable parameters |
| `src/container_geometry_analyzer_gui_v3_11_8.py` | 104-127 | `SIZE_ADAPTIVE_PARAMS` - Diameter-based tuning |
| `src/container_geometry_analyzer_gui_v3_11_8.py` | 136-167 | `DIAMETER_SPECIFIC_PERCENTILES` - SNR-based ranges |

### Phase 2 Implementation
| File | Lines | Purpose |
|------|-------|---------|
| `src/container_geometry_analyzer_gui_v3_11_8.py` | 1244-1372 | `find_optimal_transitions_selective()` - Phase 2 routing logic |
| `src/container_geometry_analyzer_gui_v3_11_8.py` | 1404-1420 | Integration point in `segment_and_fit_optimized()` |
| `src/stability_detection.py` | ALL | Stability detection foundation (Phase 1) |

### Testing
| File | Purpose |
|------|---------|
| `tests/test_selective_routing.py` | 9 unit tests for Phase 2 |
| `tests/run_comprehensive_medium_confidence.py` | Full 56-test validation with optimal config |
| `tests/run_comprehensive_with_phase2.py` | Phase 2 with high confidence (for comparison) |
| `tests/run_phase2_medium_confidence.py` | Quick validation of medium confidence |

### Documentation
| File | Purpose |
|------|---------|
| `PRIORITY_4_PHASE_2_TESTING_REPORT.md` | Test results & recommendations |
| `PRIORITY_4_PHASE_2_PLAN.md` | Detailed implementation plan |
| `PRIORITY_4_PHASE_1_COMPLETION_REPORT.md` | Stability detection foundation |
| `CODEBASE_EXPLORATION_SUMMARY.md` | Complete technical analysis |
| `PHASE_2_QUICK_START.md` | Quick reference guide |

## Parameter Values Quick Lookup

### Current Baseline Configuration
```
percentile: 96                  (Detection sensitivity)
variance_threshold: 0.14        (Segment validation)
merge_threshold: 0.12           (Segment merging)
curvature_threshold: 0.05       (Curved surface detection)
use_adaptive_threshold: True    (SNR-based adjustment)
use_selective_detection: False  (Phase 2 - currently OFF)
selective_confidence_threshold: 'medium'  (Optimal threshold)
```

### Size Categories
```
Small:  diameter < 12mm
Medium: 12mm <= diameter < 14mm
Large:  diameter >= 14mm
```

### Diameter Categories (for SNR-based percentiles)
```
Small:  diameter < 8mm   (curvature_threshold: 0.04)
Medium: 8-12mm          (curvature_threshold: 0.06)  [Tuned for 10mm]
Large:  diameter >= 12mm (curvature_threshold: 0.05)  [Tuned for 15mm]
```

## Performance Metrics

### Current Baseline (Phase 1-3)
```
Overall: 60.7% (34/56 tests)
By segment:
  - 1-segment: 83.3%
  - 2-segment: 50.0%
  - 3-segment: 25.0%
By diameter:
  - 5mm: 93.8% ⭐
  - 10mm: 45.0%
  - 15mm: 56.2%
```

### Phase 2 Medium Confidence (OPTIMAL)
```
Overall: 69.6% (+8.9%) ✅
By segment:
  - 1-segment: 87.5% (+4.2%)
  - 2-segment: 66.7% (+16.7%) ✅ BIG WIN
  - 3-segment: 25.0% (same)
Performance: 24.5ms average (+0.3ms vs baseline)
```

## How to Make Changes

### To Enable Phase 2
1. File: `src/container_geometry_analyzer_gui_v3_11_8.py`
2. Line: 98
3. Change: `'use_selective_detection': False` → `True`
4. Verify: Run `tests/run_comprehensive_medium_confidence.py`
5. Expected: 69.6% accuracy (39/56 tests)

### To Change Confidence Threshold
1. File: `src/container_geometry_analyzer_gui_v3_11_8.py`
2. Line: 99
3. Options: `'high'` (51.8%) or `'medium'` (69.6%)
4. Currently optimal: `'medium'`

### To Adjust Size-Specific Parameters
1. File: `src/container_geometry_analyzer_gui_v3_11_8.py`
2. Lines: 104-127 (SIZE_ADAPTIVE_PARAMS)
3. Categories: small, medium, large
4. Tunable: percentile, merge_threshold, min_points, variance_threshold

### To Adjust Diameter-Specific Thresholds
1. File: `src/container_geometry_analyzer_gui_v3_11_8.py`
2. Lines: 136-167 (DIAMETER_SPECIFIC_PERCENTILES)
3. Categories: small (SNR ranges), medium, large
4. Tunable: very_clean, clean, moderate, noisy, very_noisy, curvature_threshold

## Testing Workflow

### Quick Test (2 seconds)
```bash
python tests/test_selective_routing.py
```

### Medium Test (5 seconds)
```bash
python tests/run_phase2_medium_confidence.py
```

### Full Test (1-2 minutes)
```bash
python tests/run_comprehensive_medium_confidence.py
```

### Expected Results
- Unit tests: 9/9 passing
- Medium confidence: 39/56 passing (69.6%)
- High confidence: 29/56 passing (51.8%)
- Baseline: 34/56 passing (60.7%)

## Git Workflow

### Current Status
```bash
git log --oneline -5
# Shows: e2c8880, 2fd0d6e, 9235b39, 7e389c3, 396c880

git status
# Should be: working tree clean
```

### To Commit Changes
```bash
# Stage parameter changes
git add src/container_geometry_analyzer_gui_v3_11_8.py

# Commit with descriptive message
git commit -m "Enable Phase 2 selective routing with medium confidence threshold"

# Verify
git log --oneline -1
```

### Branches
- `claude/continue-parameter-tuning-01384wxcpHY3pewktp64y6Sx` - Current
- Based on work from:
  - `e2c8880` - selective routing
  - `2fd0d6e` - Phase 2 testing complete
  - `9235b39` - Phase 2 implementation

## Key Insights

### What Works Well
- Phase 1-3 baseline: 60.7% (proven)
- Single-shape detection: 83.3% (excellent)
- 5mm containers: 93.8% (outstanding)
- Sphere cap detection: 100% (solved in Priority 2)

### What Needs Improvement
- 2-segment composites: 50.0% → 66.7% (Phase 2 medium solves this!)
- 3-segment composites: 25.0% (still needs work)
- 10mm diameter: 45.0% (complex interaction)
- 15mm composites: 56.2% (challenging geometry)

### Phase 2 Impact
- **Overall**: +8.9% improvement
- **2-segment**: +16.7% improvement (primary use case)
- **Risk**: LOW (feature flag for rollback)
- **Performance**: +0.3ms only

## Resource Files

### Historical Documentation
- `PRIORITY_1_COMPLETION_REPORT.md` - Size-adaptive parameters (DEPLOYED)
- `PRIORITY_2_THRESHOLD_TUNING_REPORT.md` - Curved surface detection (DEPLOYED)
- `DIAMETER_SPECIFIC_TUNING_REPORT.md` - Diameter-specific tuning (DEPLOYED)
- `PRIORITY_4_ARCHITECTURAL_REDESIGN_PLAN.md` - Overall redesign strategy

### Data & Results
- `assessment_results_phase2_medium_20251120_094228.json` - Medium confidence test results
- `assessment_results_phase2_20251120_094123.json` - High confidence test results
- `test_data_comprehensive/` - 56 test cases (synthetic containers)

### Configuration Files
- `requirements.txt` - Core dependencies
- `requirements-dev.txt` - Development dependencies
- `setup.py` - Package configuration
- `pyproject.toml` - Modern Python project metadata

## Success Checklist

- [x] Phase 1: Size-adaptive parameters (DEPLOYED)
- [x] Phase 2: Curved surface detection (DEPLOYED)
- [x] Phase 3: Diameter-specific tuning (DEPLOYED)
- [x] Phase 4 Phase 1: Stability detection foundation (IMPLEMENTED)
- [x] Phase 4 Phase 2 Stage 1: Selective routing code (IMPLEMENTED)
- [x] Phase 4 Phase 2 Stage 2: Comprehensive testing (COMPLETE)
- [x] Phase 4 Phase 2 Stage 3: Parameter tuning (COMPLETE - medium confidence optimal)
- [ ] Phase 4 Phase 2 Stage 4: Integration validation (NEXT)
- [ ] Phase 4 Phase 2 Stage 5: Production deployment (FUTURE)

## Next Actions

### Immediate
1. Review Phase 2 test results ✅ (COMPLETE - 69.6% with medium confidence)
2. Approve medium confidence threshold ⏳ (READY FOR APPROVAL)
3. Enable feature flag ⏳ (READY)
4. Run full validation ⏳ (READY)
5. Create PR ⏳ (READY)

### Short-term
6. Deploy to staging
7. Monitor production metrics
8. Gather user feedback
9. Prepare documentation

### Long-term
10. Optimize 3-segment detection (25% → 40%+)
11. Improve 10mm composites (45% → 60%+)
12. Enhance 15mm composites (56% → 70%+)

---

**Summary**: Phase 2 is complete and tested. Medium confidence threshold delivers optimal results (+8.9% overall, +16.7% on 2-segment composites). Ready for deployment.

**Files to Review**:
1. PHASE_2_QUICK_START.md - Start here
2. PRIORITY_4_PHASE_2_TESTING_REPORT.md - Test results
3. src/container_geometry_analyzer_gui_v3_11_8.py - Implementation

**Approval Needed**: Enable Phase 2 with medium confidence threshold
