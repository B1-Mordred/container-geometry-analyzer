# IFU Update Guide

## Overview

The **IFU (Instructions For Use)** document provides reliability specifications, performance metrics, and usage guidelines based on comprehensive test validation. This guide explains how to keep the IFU synchronized with algorithm improvements.

---

## Quick Start

### After Running Tests

```bash
# 1. Generate test data
python generate_test_data.py

# 2. Run comprehensive tests
python run_comprehensive_tests.py

# 3. Update IFU with latest metrics
python update_ifu_metrics.py

# 4. Review changes
git diff IFU.md

# 5. Commit
git add IFU.md test_results.json
git commit -m "Update IFU metrics for v3.11.9"
```

---

## The IFU Document

### Purpose

IFU.md serves as:
- **Reliability specifications** by container properties (diameter, height, geometry)
- **Performance benchmarks** (pass rates, fit errors, processing speed)
- **Quality metrics** and acceptance criteria
- **Known limitations** and edge cases
- **Usage guidelines** and best practices
- **Validation evidence** for production deployment

### Structure

| Section | Content | Update Frequency |
|---------|---------|-----------------|
| 1. Intended Use | Scope and target users | Rarely (major changes only) |
| 2. Performance Specifications | Overall pass rate, fit errors | **Every test run** |
| 3. Reliability by Container Properties | Geometry, diameter, height, complexity | **Every test run** |
| 4. Operating Requirements | Software dependencies, data format | When requirements change |
| 5. Quality Metrics | Fit quality indicators | Rarely (methodology changes) |
| 6. Known Limitations | Edge cases, unsupported features | When new limitations discovered |
| 7. Usage Guidelines | Best practices, workflows | When practices refined |
| 8. Interpreting Results | How to read outputs | When output format changes |
| 9. Troubleshooting | Common errors and solutions | When new issues found |
| 10. Validation Summary | Test results by category | **Every test run** |
| 11. Version History | Release notes | **Every release** |

---

## Automated Updates

### The `update_ifu_metrics.py` Script

This script automatically updates IFU sections based on `test_results.json`:

**What it updates:**
- ✅ Overall performance metrics (pass rate, fit errors, processing time)
- ✅ Reliability by geometry type table
- ✅ Validation results by category table
- ✅ Last updated timestamp

**What it doesn't update (manual review required):**
- Known limitations (Section 6)
- Usage guidelines (Section 7)
- Troubleshooting (Section 9)
- Version history (Section 11)

### Usage

```bash
# Standard update (modifies IFU.md)
python update_ifu_metrics.py

# Dry run (preview changes without modifying)
python update_ifu_metrics.py --dry-run

# Specify custom test results file
python update_ifu_metrics.py --test-results my_results.json

# Specify software version
python update_ifu_metrics.py --version v3.12.0
```

### Output Example

```
Loading test results from test_results.json...
Calculating metrics...

======================================================================
Test Results Summary
======================================================================
Pass Rate: 73.3%
Average Fit Error: 2.05%
Max Fit Error: 6.70%
Average Processing Time: 21.5 ms
======================================================================

Category Breakdown:
  Cylinders: 83% (5/6)
  Composite: 67% (2/3)
  Frustums: 100% (2/2)
  Cones: 50% (1/2)
  Sphere_Caps: 50% (1/2)

Reading IFU.md...
Updating Performance Specifications section...
Updating Reliability by Geometry Type table...
Updating Validation Results table...
Updating timestamp to 2025-11-19...
✅ IFU.md updated successfully!

Next steps:
  1. Review changes: git diff IFU.md
  2. Commit: git add IFU.md && git commit -m 'Update IFU metrics for v3.11.9'
```

---

## Manual Update Workflow

### When to Update Manually

Update IFU.md manually when:
1. **New algorithm features** are added (update Section 1: Intended Use)
2. **New limitations** are discovered (update Section 6: Known Limitations)
3. **Best practices** change (update Section 7: Usage Guidelines)
4. **New troubleshooting** tips identified (update Section 9: Troubleshooting)
5. **Major/minor version release** (update Section 11: Version History)

### Manual Update Checklist

- [ ] Run full test suite: `python run_comprehensive_tests.py`
- [ ] Automated update: `python update_ifu_metrics.py`
- [ ] Review EDGE_CASES_ANALYSIS.md for new limitations
- [ ] Update Section 6 (Known Limitations) if needed
- [ ] Update Section 7 (Usage Guidelines) if best practices changed
- [ ] Add version entry to Section 11 (Version History)
- [ ] Update version number in header if releasing
- [ ] Review all changes: `git diff IFU.md`
- [ ] Commit with descriptive message

---

## Version History Updates

### Adding a New Version Entry

When releasing a new version, manually add an entry to Section 11:

```markdown
### v3.12.0 (2025-11-25) - Current Version

**Major Improvements:**
- ✅ [List key improvements]
- ✅ [Algorithm changes]

**Performance:**
- Test pass rate: X% → Y% (improvement)
- Average fit error: X.XX%

**New Capabilities:**
- [New features]

**Validated Test Suite:**
- [Test coverage details]

**Known Limitations:**
- [Updated limitations]

**Recommendation**: ✅/⚠️ [Production status]
```

---

## Reliability Specifications

### Understanding Reliability Tables

**Section 3.1: By Geometry Type**

| Reliability | Meaning | Icon |
|-------------|---------|------|
| 95-100% | Fully validated, production ready | ✅ |
| 80-94% | High confidence, recommended | ✅ |
| 60-79% | Medium confidence, verification recommended | ⚠️ |
| < 60% | Low confidence, manual review required | ❌ |

**Typical Fit Error Ranges:**

| Error Range | Quality Rating | Usage |
|-------------|----------------|-------|
| < 1% | Excellent | All applications |
| 1-2% | Very Good | Most applications |
| 2-4% | Good | General use |
| 4-7% | Acceptable | Non-critical applications |
| > 7% | Poor | Manual review required |

---

## Testing Requirements

### For IFU Updates

To generate valid reliability specifications, ensure:

1. **Comprehensive test suite** covering:
   - ✅ Simple geometries (cylinders, frustums, cones, sphere caps)
   - ✅ Composite shapes (2-3 segments)
   - ✅ Diameter range: 5-100 mm
   - ✅ Height range: 8-200 mm
   - ✅ Robustness tests (noise, sampling density)

2. **Test metadata** includes:
   - `expected_shape`: Geometry type
   - `expected_segments`: Number of segments
   - `diameter_mm`: Container diameter(s)
   - `height_range_mm`: [min, max] height
   - `description`: Human-readable description

3. **Test results** format:
   - JSON file with `summary` and `results` sections
   - Pass/fail status for each test
   - Fit errors per segment
   - Processing time

### Minimum Test Coverage

For reliable IFU specifications:
- **Minimum**: 10 test cases (limited reliability data)
- **Recommended**: 15-20 test cases (good coverage)
- **Comprehensive**: 25+ test cases (high confidence)

Current test suite: **15 test cases** (recommended level)

---

## CI/CD Integration

### Automated IFU Updates in CI

Add to `.github/workflows/tests.yml`:

```yaml
- name: Update IFU Metrics
  run: |
    python update_ifu_metrics.py
    git diff IFU.md > ifu_changes.txt

- name: Upload IFU Changes
  uses: actions/upload-artifact@v3
  with:
    name: ifu-updates
    path: ifu_changes.txt
```

### Pre-Release Checklist

Before tagging a release:

```bash
# 1. Run full test suite
python run_comprehensive_tests.py

# 2. Update IFU
python update_ifu_metrics.py

# 3. Manual review
git diff IFU.md

# 4. Update version history
# (manually add entry to Section 11)

# 5. Commit
git add IFU.md test_results.json
git commit -m "Release v3.12.0: Update IFU and test results"

# 6. Tag release
git tag -a v3.12.0 -m "Release v3.12.0"

# 7. Push
git push && git push --tags
```

---

## Examples

### Example 1: After Algorithm Improvement

```bash
# You've improved transition detection
# Pass rate improved from 73% to 85%

# 1. Generate new test data (if needed)
python generate_test_data.py

# 2. Run tests
python run_comprehensive_tests.py

# Output shows:
# Pass Rate: 85%
# Average Fit Error: 1.8%

# 3. Update IFU
python update_ifu_metrics.py

# 4. Review changes
git diff IFU.md

# Shows updated pass rates and reliability tables

# 5. Update version history manually
# Add entry for v3.12.0 in Section 11

# 6. Commit
git add IFU.md test_results.json
git commit -m "v3.12.0: Improve transition detection, pass rate 73%→85%"
```

### Example 2: After Discovering New Limitation

```bash
# You discovered that containers with threads don't work

# 1. Document in IFU.md Section 6
# Add to "Not Supported" list:
# - ❌ Internal threads or screw caps

# 2. Update troubleshooting in Section 9
# Add error case and solution

# 3. No test run needed (limitation, not algorithm change)

# 4. Commit
git add IFU.md
git commit -m "IFU: Document limitation with threaded containers"
```

### Example 3: Weekly Test Run

```bash
# Regular validation run (no code changes)

# 1. Run tests
python run_comprehensive_tests.py

# 2. If pass rate unchanged, no IFU update needed
# If pass rate changed, investigate why

# 3. If legitimate change (test environment, etc.):
python update_ifu_metrics.py
git commit -am "IFU: Weekly validation run"

# 4. If unexpected change:
# - Review test logs
# - Check for regressions
# - File issue if needed
```

---

## Best Practices

### DO ✅

- ✅ Update IFU after every major/minor release
- ✅ Run full test suite before updating IFU
- ✅ Use dry-run mode to preview changes
- ✅ Commit test_results.json with IFU updates
- ✅ Add descriptive commit messages explaining changes
- ✅ Review all automated updates manually
- ✅ Keep version history up to date

### DON'T ❌

- ❌ Update IFU without running tests first
- ❌ Manually edit auto-updated sections (use script instead)
- ❌ Commit IFU changes without reviewing diff
- ❌ Skip version history updates on releases
- ❌ Cherry-pick test results (run full suite)
- ❌ Update reliability claims without test evidence

---

## Troubleshooting

### Script Errors

**Error: `test_results.json not found`**
```bash
# Run tests first:
python run_comprehensive_tests.py
```

**Error: `KeyError in calculate_metrics`**
```bash
# Ensure test_results.json has correct format
# Check that run_comprehensive_tests.py completed successfully
```

**Warning: `test_metadata.json not found`**
```bash
# Generate test data:
python generate_test_data.py
# This creates test_data/test_metadata.json
```

### Review Failed

**IFU changes don't match expectations**
```bash
# Use dry-run to debug:
python update_ifu_metrics.py --dry-run

# Check test results manually:
cat test_results.json | python -m json.tool

# Verify test metadata:
cat test_data/test_metadata.json | python -m json.tool
```

---

## Contact

For questions about IFU updates:
- Review CLAUDE.md (AI assistant guide)
- Review TEST_SUITE_DOCUMENTATION.md (test details)
- Check GitHub issues

---

**Last Updated**: 2025-11-19
**Document Version**: 1.0
**Maintained By**: Development Team
