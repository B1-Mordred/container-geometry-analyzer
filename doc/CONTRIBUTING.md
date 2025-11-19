# Contributing to Container Geometry Analyzer

Thank you for your interest in contributing to the Container Geometry Analyzer! This document provides guidelines and instructions for contributing to this project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/container-geometry-analyzer.git
   cd container-geometry-analyzer
   ```

3. **Add the upstream repository**:
   ```bash
   git remote add upstream https://github.com/ORIGINAL-OWNER/container-geometry-analyzer.git
   ```

## Development Environment Setup

### Prerequisites

- Python 3.7 or higher
- pip package manager
- git

### Installation

1. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

3. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Set up pre-commit hooks** (optional but recommended):
   ```bash
   pre-commit install
   ```

### Verify Installation

Run the test suite to verify everything is working:
```bash
pytest test_transition_detection.py -v
```

## Making Changes

### Creating a Branch

Always create a new branch for your changes:
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b bugfix/issue-description
```

Branch naming conventions:
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/improvements

### Code Guidelines

1. **Follow the existing code style** - The project uses:
   - Black for code formatting (line length: 100)
   - isort for import sorting
   - flake8 for linting

2. **Write clear, descriptive commit messages**:
   ```
   Add: New geometric shape support for ellipsoids
   Fix: STL bottom cap triangulation orientation
   Update: Improve segmentation accuracy for small volumes
   Docs: Add testing guidelines to CLAUDE.md
   ```

3. **Add tests** for new functionality:
   - Unit tests in `test_transition_detection.py`
   - Integration tests for end-to-end functionality
   - Update benchmarks if performance is affected

4. **Update documentation**:
   - Update README.md for user-facing changes
   - Update CLAUDE.md for AI assistant guidance
   - Add docstrings to new functions
   - Update this CONTRIBUTING.md if process changes

## Testing

### Running Tests

Run the full test suite:
```bash
pytest test_transition_detection.py -v
```

Run with coverage:
```bash
pytest test_transition_detection.py --cov=. --cov-report=html
```

Run benchmarks:
```bash
python benchmark_transition_detection.py
```

### Writing Tests

All new features should include tests. Place tests in `test_transition_detection.py` or create new test files following the `test_*.py` naming convention.

Example test structure:
```python
def test_your_feature():
    """Test description."""
    # Arrange
    input_data = prepare_test_data()

    # Act
    result = your_function(input_data)

    # Assert
    assert result == expected_value
```

## Code Style

The project uses automated code formatting and linting:

### Automatic Formatting

Format your code before committing:
```bash
# Format with Black
black --line-length 100 *.py

# Sort imports with isort
isort --profile black --line-length 100 *.py
```

### Linting

Check code quality:
```bash
# Check with flake8
flake8 . --max-line-length=100

# Type check with mypy
mypy container_geometry_analyzer_gui_v3_11_8.py --ignore-missing-imports
```

### Pre-commit Hooks

If you've installed pre-commit hooks, these checks run automatically:
```bash
pre-commit run --all-files
```

## Submitting Changes

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   pytest test_transition_detection.py -v
   ```

2. **Verify code style**:
   ```bash
   black --check --line-length 100 *.py
   isort --check-only --profile black *.py
   flake8 . --max-line-length=100
   ```

3. **Update documentation** if needed

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Creating a Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Select your branch
4. Fill in the PR template with:
   - **Description**: What does this PR do?
   - **Motivation**: Why is this change needed?
   - **Testing**: How was this tested?
   - **Related Issues**: Link any related issues

### PR Review Process

- Maintainers will review your PR
- CI/CD checks must pass (tests, linting, etc.)
- Address any feedback from reviewers
- Once approved, a maintainer will merge your PR

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Environment information**:
   - Python version
   - Operating system
   - Package versions (`pip list`)

2. **Steps to reproduce**:
   - Minimal code example
   - Input data (CSV file if applicable)
   - Expected vs actual behavior

3. **Error messages**:
   - Full error traceback
   - Log output

### Feature Requests

When requesting features:

1. **Describe the problem** you're trying to solve
2. **Propose a solution** (optional)
3. **Provide use cases** and examples
4. **Consider alternatives** you've explored

## Development Workflow

### Typical Workflow

```bash
# 1. Sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# 2. Create feature branch
git checkout -b feature/my-feature

# 3. Make changes and test
# ... edit files ...
pytest test_transition_detection.py -v

# 4. Format and lint
black --line-length 100 *.py
flake8 . --max-line-length=100

# 5. Commit and push
git add .
git commit -m "Add: My awesome feature"
git push origin feature/my-feature

# 6. Create PR on GitHub
```

### Keeping Your Fork Updated

Regularly sync with upstream:
```bash
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Project Structure

Understanding the codebase:

```
container-geometry-analyzer/
├── container_geometry_analyzer_gui_v3_11_8.py  # Main application
├── test_transition_detection.py                # Unit tests
├── benchmark_transition_detection.py           # Benchmarks
├── transition_detection_improvements.py        # Algorithm improvements
├── visualize_algorithm_comparison.py           # Visualizations
├── requirements.txt                            # Production dependencies
├── requirements-dev.txt                        # Development dependencies
├── setup.py                                    # Package setup
├── pyproject.toml                              # Modern Python config
├── README.md                                   # User documentation
├── CLAUDE.md                                   # AI assistant guide
└── CONTRIBUTING.md                             # This file
```

## Key Development Areas

### Adding New Geometric Shapes

1. Add volume calculation function
2. Update `segment_and_fit_optimized()`
3. Update `create_enhanced_profile()`
4. Add tests for the new shape
5. Update PDF report rendering

### Improving Segmentation

1. Modify `find_optimal_transitions_improved()`
2. Adjust `DEFAULT_PARAMS` if needed
3. Test with multiple sample datasets
4. Update benchmarks

### Enhancing Visualizations

1. Add plotting function to `generate_comprehensive_plots()`
2. Integrate into PDF report
3. Test with sample data

## Questions?

If you have questions:

1. Check existing issues on GitHub
2. Read the documentation (README.md, CLAUDE.md)
3. Open a new issue with the "question" label

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what's best for the project
- Show empathy towards other contributors

## License

By contributing to this project, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to Container Geometry Analyzer!
