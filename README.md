# `apt` Repository Configuration Package Generator

This project reads YAML files that describe a `apt` package repository and turns
them into installable Debian (`.deb`) packages. You can use it to automatically
generate repository configuration files and signing keyrings.

---

## What It Does

1. **Reads Manifests**: It looks inside a directory for `.yaml` files that
   describe the software packages, where their code is hosted, and what operating
   systems they support.
2. **Maintains a Changelog**: It updates a timeline file (`changelog`) that
   lists everything that changed between versions. If you edit a file but forget
   to change the version number, the tool will notice and ask if you want to
   automatically raise it.
3. **Builds Source Folders**: It generates standard Debian configuration files
   (like `control` and `rules`) and places them into an output directory.
4. **Cleans Up**: It can safely delete temporary files and folders to keep the
   workspace tidy.

---

## How OS Mappings Work

The `os_mappings` section in the manifest files solves a common problem:
different Linux distributions use different names and codebases, even when they
are based on the same underlying software.

This defines those relationships in plain text, and it translates them into
automated installation choices inside the packages.

### 1. Linking Different Systems

Inside the manifest, you can list a specific hardware device or distribution
name and map it directly to its mainstream Linux ancestor. For example:

```yaml
os_mappings:
  raspbian:
    distro: debian
    codename: ${DEBIAN_CODENAME}
  pop|linuxmint:
    distro: ubuntu
    codename: ${UBUNTU_CODENAME}
```

This tells the package system that if a user is running **Raspbian**, the tool
needs to use repositories meant for **Debian**. If they are running
**Pop!_OS** or **Linux Mint**, it uses repositories meant for **Ubuntu**.

### 2. Handling Multiple Names at Once

The pipe symbol (`|`) in `pop|linuxmint` is read as an "OR" statement. You don't
have to write duplicate configuration blocks for separate operating systems that
share the exact same foundation.

### 3. Turning Settings into Code

When the script processes these fields it loops through the mappings and
automatically compiles them into a section of the package's `postinst` file.

When a user installs a finished `.deb` package, that script runs instantly. It
detects their specific operating system flavor, cross-references it against the
mappings list, and adds the correct repository automatically.

---

## How the Changelog Generator Works

The changelog generator is the most powerful part of this tool. Instead of making
you type out updates manually, it acts like an automated investigator. It reads
the package history line-by-line and reverse-engineers the timeline of the
project completely on its own.

### 1. Reconstructing the Past

Every time you build the packages, the tool opens the existing `changelog`
file. It parses the text blocks and recreates a running timeline of the exact
historical settings—like old descriptions, previous repository links, or which
operating systems were supported in version 1.0.0 vs version 1.0.1.

### 2. Smart Order Tracking

People arrange settings in different ways. The tool tracks the exact layout
order of the files chronologically from oldest to newest. It remembers the
custom order you used for the operating system listings, ensuring that
re-generated files look exactly like the original documents instead of getting
scrambled alphabetically.

### 3. Automatic Difference Detection

The tool compares the current YAML file settings against the history it rebuilt
from the text file. It specifically checks for:

* Changed package descriptions or copyright dates.
* Swapped repository URLs or components.
* Added or removed operating system support fields.

If it finds a difference, it automatically writes a clean bullet-point list
detailing the modifications.

### 4. Idempotency (Skipping Duplicates)

If you run a build without changing any settings, the generator notices that
the files are identical. It safely stops and returns the existing file
completely untouched. This keeps you from accidentally printing duplicate
version headers or cluttering the project history with empty updates.

### 5. Safety Guard Rails

If the generator detects that you modified a settings file but forgot to raise
the version number, it blows a fuse to protect the history. It will halt the
build and ask you inside the terminal if you want to automatically raise the
version number (e.g., from `1.0.0` to `1.0.1`). If you choose yes, it will use
the template to safely rewrite the manifest file for you, keeping the history
perfectly synchronized.

---

## Getting Started

### 1. Requirements

You must have Python 3.11 or newer installed on your computer.

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

To read the configuration files and create the Debian source directories, run:

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
python generate.py clean --sources-dir dpkg-sources
```

---

## Creating the Final .deb Files

Because building a `.deb` package requires a Linux environment with specific
compiling tools, a `docker-compose.yml` file is included to handle this part
inside a container.

Once the source files are generated inside the `dpkg-sources` folder, run:

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
