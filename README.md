# APT Repository Configuration Packages

This project manages a collection of personal Debian configuration packages
(.deb) that automatically add custom software repositories and cryptographic
keyrings to target systems.

The repository is structured as a monorepo containing abstract configuration
manifests, a shared template directory, and the generated package source trees.

## Project Structure

* `config.yaml` - Global configuration settings for package maintainer and
copyright metadata.
* `manifests/` - Individual YAML files defining the parameters for each
software repository.
* `template/debian/` - The universal skeleton configuration files used to
generate the Debian layouts.
* `dpkg-sources/` - The fully expanded, human-readable Debian source configurations
generated from the manifests. This directory is committed to version control
for auditing and security verification.

## Development Setup

The generation tool is written in Python and runs across Linux, macOS, and Windows.

1. Initialize a Python virtual environment:

   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   * Linux/macOS: `source .venv/bin/activate`
   * Windows (PowerShell): `.venv\Scripts\Activate.ps1`

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Building Packages

To process the manifests and populate the `sources/` directory, run the build command:

```bash
python generate.py build
```

To see detailed step-by-step execution logs during generation, append the
debug flag:

```bash
python generate.py build --debug
```

### Running Tests

This project includes automated unit and functional integration tests powered
by pytest. Run the test suite using:

```bash
pytest -v
```
