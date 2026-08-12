# Use a minimal, official Debian stable baseline
FROM debian:stable-slim

# Prevent interactive prompts during package configuration passes
ENV DEBIAN_FRONTEND=noninteractive

# Install complete Debian build suite and static analysis linters
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    devscripts \
    debhelper \
    fakeroot \
    lintian \
    && rm -rf /var/lib/apt/lists/*

# Set up a clean working directory inside the container
WORKDIR /workspace

# By default, run debuild with flags optimized for automated workflows:
# -b: Binary-only package compilation (no source .dsc generation)
# -uc -us: Unsigned changelog and unsigned source (bypasses local GPG key requirements)
ENTRYPOINT ["debuild", "-b", "-uc", "-us"]
