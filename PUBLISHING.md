# Publishing to PyPI

This document describes how to publish the `fastmvc-middleware` package to PyPI.

## Prerequisites

1. **PyPI Account**: Create accounts on:
   - [PyPI](https://pypi.org/account/register/)
   - [TestPyPI](https://test.pypi.org/account/register/) (for testing)

2. **API Tokens**: Generate API tokens:
   - PyPI: https://pypi.org/manage/account/token/
   - TestPyPI: https://test.pypi.org/manage/account/token/

3. **Install Build Tools**:
   ```bash
   pip install build twine
   ```

## Configuration

### Option 1: Using Environment Variables (Recommended for CI/CD)

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

### Option 2: Using `~/.pypirc` File

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

**Secure the file:**
```bash
chmod 600 ~/.pypirc
```

## Publishing Steps

### 1. Update Version

Update the version in:
- `pyproject.toml` (line: `version = "X.Y.Z"`)
- `fastMiddleware/__init__.py` (line: `__version__ = "X.Y.Z"`)

### 2. Update Changelog

Add release notes to `CHANGELOG.md`

### 3. Run Tests

```bash
make test
# or
pytest --cov=fastMiddleware
```

### 4. Build the Package

```bash
make build
# or
python -m build
```

This creates:
- `dist/fastmvc_middleware-X.Y.Z-py3-none-any.whl` (wheel)
- `dist/fastmvc_middleware-X.Y.Z.tar.gz` (source distribution)

### 5. Verify the Package

```bash
make check
# or
twine check dist/*
```

### 6. Test on TestPyPI (Recommended)

```bash
make publish-test
# or
twine upload --repository testpypi dist/*
```

Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ fastmvc-middleware
```

### 7. Publish to PyPI

```bash
make publish
# or
twine upload dist/*
```

## Post-Publishing

### 1. Create Git Tag

```bash
git tag -a v0.5.0 -m "Release v0.5.0"
git push origin v0.5.0
```

### 2. Create GitHub Release

Go to https://github.com/hyyre/fastmvc-middleware/releases/new and:
- Select the tag
- Add release notes from CHANGELOG.md
- Upload the dist files

### 3. Verify Installation

```bash
pip install fastmvc-middleware
python -c "import fastMiddleware; print(fastMiddleware.__version__)"
```

## Troubleshooting

### "Package already exists"

You cannot overwrite existing versions. Increment the version number.

### "Invalid distribution"

Run `twine check dist/*` to see specific issues.

### "Authentication failed"

- Verify your API token is correct
- Ensure you're using `__token__` as the username
- Check token scope (package-specific vs. all packages)

## Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking API changes
- **MINOR** (0.X.0): New features, backwards compatible
- **PATCH** (0.0.X): Bug fixes, backwards compatible

## Automated Publishing (GitHub Actions)

For automated releases, add this to `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install build
      
      - name: Build package
        run: python -m build
      
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
```

This uses PyPI's trusted publishing (no API token needed).

## Quick Reference

| Command | Description |
|---------|-------------|
| `make build` | Build distribution packages |
| `make check` | Verify packages |
| `make publish-test` | Upload to TestPyPI |
| `make publish` | Upload to PyPI |
| `make clean` | Remove build artifacts |

