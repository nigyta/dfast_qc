# ---------------------------------------------------------------------------
# SECURITY PATCH RELEASE ONLY --- this is not the normal build.
#
# This branch/tag exists to ship CVE-2026-111497 (out-of-bounds write in the
# Brotli decoder) without changing anything else. It layers on the published
# 1.1.1 image instead of rebuilding from source, because the normal Dockerfile
# installs its conda/pip dependencies unpinned: the 1.1.1 image was built in
# April 2026, so a rebuild picks up seven months of drift. A rebuild attempt
# (released as 1.1.3) moved skani 0.3.1 -> 0.4.0, peewee 4.0.4 -> 4.5.3,
# entrez-direct 24.0 -> 26.0, dendropy, pysam, numpy and matplotlib. skani is
# the ANI engine, so that is a scientific change, not a security patch.
#
# The real fix is to pin those dependencies on master. Until then, security
# patches for 1.1.x should be built this way.
# ---------------------------------------------------------------------------
FROM --platform=linux/amd64 nigyta/dfast_qc:1.1.1

# conda-side Brotli: urllib3 advertises "Accept-Encoding: ...,br" whenever
# brotli-python is present, so this is the decoder that actually runs on the
# reference-data downloads. --freeze-installed keeps the rest of the env where
# 1.1.1 left it rather than letting the solver drift it forward.
RUN conda install -y --freeze-installed "brotli-python>=1.2.1" && \
	conda clean --all -y && \
	conda list brotli-python

# System libbrotli1, which came in with git/libcurl in 1.1.1.
# Debian 12 (bookworm) fixes it in 1.0.9-2+deb12u1 (DLA-4855-1).
RUN apt-get update && \
	apt-get install -y --only-upgrade libbrotli1 && \
	rm -rf /var/lib/apt/lists/* && \
	dpkg -l libbrotli1 | tail -1

# The source in the image is 1.1.1; report the version this image is tagged as.
RUN sed -i 's/dqc_version = "1.1.1"/dqc_version = "1.1.4"/' /dfast_qc/dqc/__init__.py && \
	python3 -c 'import sys; sys.path.insert(0,"/dfast_qc"); import dqc; print("dqc_version:", dqc.dqc_version)'
