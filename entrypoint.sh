#!/bin/bash
set -e

SOURCES_DIR="/workspace/dpkg-sources"
DIST_DIR="/workspace/dist"

echo "=== Initializing Containerized Debian Packaging Pipeline ==="

# Ensure our distribution output container folder physically exists
mkdir -p "${DIST_DIR}"

# Verify that the input sources tree contains actual data before scanning
if [ ! -d "${SOURCES_DIR}" ] || [ -z "$(ls -A "${SOURCES_DIR}")" ]; then
    echo "ERROR: dpkg-sources directory is missing or completely empty."
    exit 1
fi

# Loop chronologically through each individual package subdirectory source layout
for pkg_dir in "${SOURCES_DIR}"/*; do
    if [ -d "${pkg_dir}" ]; then
        pkg_name=$(basename "${pkg_dir}")
        echo "--------------------------------------------------------"
        echo "Processing target package folder layout: [${pkg_name}]"
        echo "--------------------------------------------------------"

        # 1. Navigate directly into the package workspace context row
        cd "${pkg_dir}"

        # 2. Sanitize the Windows volume mount permission artifacts natively inside Linux
        echo "Sanitizing file permissions inside debian/ layout folder..."
        find debian/ -type f -exec chmod 644 {} +

        # Expressly restore the required executable flag strictly to the rules file asset
        if [ -f "debian/rules" ]; then
            chmod +x debian/rules
        fi

        # 3. Compile the package into a binary archive without requiring GPG signatures (-us -uc)
        # using fakeroot to mock file permission access attributes cleanly
        if debuild -us -uc -b; then
            echo "Successfully compiled binary artifacts for [${pkg_name}]."

            # 4. Copy the compiled .deb file out to our mounted host dist/ directory
            # debuild flushes generated packages one level ABOVE the source tree folder
            cd ..
            find . -maxdepth 1 -name "${pkg_name}*.deb" -exec cp {} "${DIST_DIR}/" \;

            # 5. Navigate back into the package folder track and run an official purge pass
            # This completely sweeps out the .debhelper folders, build-stamps, and substvars caches!
            echo "Executing official packaging system purge pass across layout..."
            cd "${pkg_dir}"
            if [ -f "debian/rules" ]; then
                fakeroot debian/rules clean || true
            fi

            # 6. Navigate back up to sweep away loose tracking logs/metadata outside the folder
            cd ..
            echo "Sweeping loose metadata file crumbs..."
            find . -maxdepth 1 -name "${pkg_name}*" ! -name "*.yaml" ! -name "*.yml" -type f -delete
        else
            echo "ERROR: Compilation pass collapsed for package folder: [${pkg_name}]"
            exit 1
        fi
    fi
done

echo "========================================================"
echo "Package compilation pass finalized. Binary files ready inside ./dist/"
echo "Shutting down compilation container cleanly..."
exit 0
