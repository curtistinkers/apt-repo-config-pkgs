#!/bin/bash
set -e

SOURCES_DIR="/workspace/dpkg-sources"
DIST_DIR="/workspace/dist"

# Set the maximum number of packages to compile simultaneously
MAX_JOBS="${MAX_JOBS:-2}"

echo "=== Initializing Containerized Parallel Debian Packaging Pipeline ==="
echo "Configured Max Concurrent Jobs: ${MAX_JOBS}"

# Ensure the distribution output container folder physically exists
mkdir -p "${DIST_DIR}"

# Verify that the input sources tree contains actual data before scanning
if [ ! -d "${SOURCES_DIR}" ] || [ -z "$(ls -A "${SOURCES_DIR}")" ]; then
    echo "ERROR: dpkg-sources directory is missing or completely empty."
    exit 1
fi

# Function encapsulating a single isolated package build pass
compile_single_package() {
    local pkg_dir="$1"
    local pkg_name
    pkg_name=$(basename "${pkg_dir}")

    echo "[${pkg_name}] Starting background compilation..."

    # Navigate directly into the package workspace context row
    cd "${pkg_dir}"

    # Sanitize the Windows volume mount permission artifacts natively inside Linux
    find debian/ -type f -exec chmod 644 {} +

    # Expressly restore the required executable flag strictly to the rules file asset
    if [ -f "debian/rules" ]; then
        chmod +x debian/rules
    fi

    # Compile the package into a binary archive without requiring GPG signatures (-us -uc)
    # Redirect outputs to keep the terminal logs from scrambling together
    if debuild -us -uc -b > "${pkg_name}_build.log" 2>&1; then
        echo "[${pkg_name}] Successfully compiled binary artifacts."

        # Copy the compiled .deb file out to the mounted host dist/ directory
        # debuild flushes generated packages one level ABOVE the source tree folder
        cd ..
        find . -maxdepth 1 -name "${pkg_name}*.deb" -exec cp {} "${DIST_DIR}/" \;

        # Navigate back into the package folder track and run an official purge pass
        cd "${pkg_name}"
        if [ -f "debian/rules" ]; then
            fakeroot debian/rules clean > /dev/null 2>&1 || true
        fi

        # Navigate back up to sweep away loose tracking logs and the temporary build log file
        cd ..
        find . -maxdepth 1 -name "${pkg_name}*" ! -name "*.yaml" ! -name "*.yml" -type f -delete
    else
        echo "ERROR: Compilation pass collapsed for package folder: [${pkg_name}]"
        echo "Review log tracks inside: ${pkg_dir}/${pkg_name}_build.log"
        return 1
    fi
}

# Array to keep track of background process IDs
job_pids=()
failure_detected=0

# Loop through each individual package subdirectory source layout
for pkg_dir in "${SOURCES_DIR}"/*; do
    if [ -d "${pkg_dir}" ]; then

        # Throttle loop: If the number of running jobs hits MAX_JOBS, wait for one to finish
        while [ "${#job_pids[@]}" -ge "${MAX_JOBS}" ]; do
            # Filter the array to keep only the PIDs that are still actively running
            still_running=()
            for pid in "${job_pids[@]}"; do
                if kill -0 "${pid}" 2>/dev/null; then
                    still_running+=("${pid}")
                else
                    # A job finished. Check its exit status to see if it failed
                    if ! wait "${pid}"; then
                        failure_detected=1
                    fi
                fi
            done
            job_pids=("${still_running[@]}")

            # Brief sleep to prevent high CPU utilization during polling
            [ "${#job_pids[@]}" -ge "${MAX_JOBS}" ] && sleep 0.5
        done

        # Stop spawning new jobs immediately if a previous concurrent job collapsed
        if [ "${failure_detected}" -ne 0 ]; then
            echo "ERROR: Stopping pipeline execution due to a previous background compilation failure."
            exit 1
        fi

        # Spawn the package compilation task inside an isolated background subshell (&)
        compile_single_package "${pkg_dir}" &
        job_pids+=("$!")
    fi
done

# Wait for all remaining background runners to wrap up completely
echo "Waiting for all running compilation tasks to complete..."
for pid in "${job_pids[@]}"; do
    if ! wait "${pid}"; then
        failure_detected=1
    fi
done

if [ "${failure_detected}" -ne 0 ]; then
    echo "ERROR: One or more background packaging processes failed."
    exit 1
fi

echo "========================================================"
echo "Parallel package compilation pass finalized. Binary files ready inside ./dist/"
echo "Shutting down compilation container cleanly..."
exit 0
