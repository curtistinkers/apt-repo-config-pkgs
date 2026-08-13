# Repository Configuration Package Generator

This tool reads simple YAML text files that describe a package repository and turns them into installable Debian (`.deb`) packages. You can use it to automatically generate repository configuration files, signing keyrings, and keep a clean history of your changes.

---

## What It Does

1. **Reads Manifests**: It looks inside a directory for `.yaml` files that
   describe your software packages, where their code is hosted, and what operating
   systems they support.
2. **Maintains a Changelog**: It updates a timeline file (`changelog`) that
   lists everything that changed between versions. If you edit a file but forget
   to change the version number, the tool will notice and ask if you want to
   automatically raise it.
3. **Builds Source Folders**: It generates standard Debian configuration files
   (like `control` and `rules`) and places them into an output directory.
4. **Cleans Up**: It can safely delete temporary files and folders to keep your
   workspace tidy.

---

## Getting Started

### 1. Requirements

YOu must have Python 3.11 or newer installed on your computer.

### 2. Installation

To install the tool along with the packages it needs to run, open your terminal
in the project folder and type:

```bash
pip install .
```

If you plan on running the tests or modifying the source code, install it in
development mode with the extra testing tools instead:

```bash
pip install -e .[dev]
```

---

## How to Use It

The tool uses a command line interface named `generate.py`.

### Build Packages

To read your configuration files and create the Debian source directories, run:

```bash
python generate.py build \
   --project-config config.yaml \
   --manifests-dir manifests \
   --templates-dir templates \
   --sources-dir dpkg-sources
```

Options you can add to the build command:

* `--bump-version`: Automatically accepts version number increases without
   stopping to ask you in the terminal.
* `--debug`: Prints detailed logs to the screen to help you see exactly what the
   tool is doing step-by-step.

### Clean the Workspace

To safely delete the generated source directories and start fresh, run:

```bash
package-generator clean --sources-dir dpkg-sources
```

---

## Creating the Final .deb Files

Because building a `.deb` package requires a Linux environment with specific
compiling tools, a `docker-compose.yml` file is included to handle this part
inside a container.

Once your source files are generated inside the `dpkg-sources` folder, run:

```bash
docker-compose up --build
```

This command will start a temporary Linux container that:

1. Fixes file permissions so the compiler can read them.
2. Runs the standard Debian package builder.
3. Copies the finished `.deb` files into a local folder named `dist`.
4. Cleans up all temporary logs and stamps.
5. Shuts down automatically when finished.

---

## Project Settings Files

### `config.yaml`

This file holds global information about who is making and maintaining the packages:

```yaml
maintainer_name: curtistinkers
maintainer_email: curtistinkers@gmail.com
copyright_holder: curtistinkers
repository_url: https://github.com/curtistinkers/deb-repo-config-packages
package_suffix: -repo-config
```

### Manifest Files (Inside the `manifests/` folder)

Each package has its own YAML file describing its setup:

```yaml
name: curtistinkers
version: 1.0.0
description: My public apt repository.
copyright_year: 2026
dynamic_keyring: false

repo:
  url: https://apt.curtistinkers.com
  suites: stable
  components: main
  key_url: https://apt.curtistinkers.com/curtistinkers-archive-keyring.gpg

os_mappings:
  pop|linuxmint|elementary:
    distro: ubuntu
    codename: ${UBUNTU_CODENAME}
  raspbian:
    distro: debian
    codename: ${DEBIAN_CODENAME}
```

---

## Running Tests

To run the automated tests and verify that the code works correctly, type:

```bash
pytest
```
