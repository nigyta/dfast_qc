FROM --platform=linux/amd64 continuumio/miniconda3:23.10.0-1 AS build

LABEL maintainer=nigyta

RUN cd / && \
	mkdir /work && chmod 777 /work && \
	pip install checkm-genome --no-cache-dir && \
	conda install -y -c bioconda -c conda-forge mash skani gsl==2.6 hmmer prodigal blast && \
	conda clean --all -y

RUN pip install ete3 more-itertools peewee --no-cache-dir

# Security: CVE-2026-111497, an out-of-bounds write in the Brotli decoder. The conda base
# env ships brotli-python, which urllib3 uses to decode "Content-Encoding: br".
RUN conda install -y "brotli-python>=1.2.1" && \
	conda clean --all -y && \
	conda list brotli-python

# Source version to build. Docker has no inline comments, so this must stay on its own
# line: anything after "=" would otherwise become part of VERSION.
# Keep in step with dqc/__init__.py, and tag the repository before building.
ARG VERSION=1.1.2
RUN	git clone --branch ${VERSION} --depth 1 https://github.com/nigyta/dfast_qc.git

FROM --platform=linux/amd64 debian:bookworm-slim

COPY --from=build /opt/conda/. /opt/conda/
COPY --from=build /dfast_qc /dfast_qc

# definition of environmental variables
ENV PATH /opt/conda/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DQC_ENV docker
ENV CHECKM_DATA_PATH /dqc_reference/checkm_data

# Security: CVE-2026-111497. libbrotli1 comes from the base image, so it needs an
# explicit upgrade. Debian 12 (bookworm) fixes it in 1.0.9-2+deb12u1 (DLA-4855-1).
RUN apt-get update && \
	apt-get install -y --only-upgrade libbrotli1 && \
	rm -rf /var/lib/apt/lists/* && \
	dpkg -l libbrotli1 | tail -1

RUN ln -s /dfast_qc/dfast_qc /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_admin_tools.py /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_initial_setup.sh /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_ref_manager.py  /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_multi  /usr/local/bin/ && \
	mkdir -p /dqc_reference/checkm_data && \
	checkm data setRoot /dqc_reference/checkm_data

WORKDIR /work
CMD bash
