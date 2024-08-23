FROM --platform=linux/amd64 continuumio/miniconda3:23.10.0-1 AS build

LABEL maintainer=nigyta

RUN cd / && \
	mkdir /work && chmod 777 /work && \
	pip install checkm-genome --no-cache-dir && \
	conda install -y -c bioconda -c conda-forge mash skani gsl==2.6 hmmer prodigal && \
	conda clean --all -y

RUN pip install ete3 more-itertools peewee --no-cache-dir

ARG VERSION=1.0.3-1  # Increment this when the source code is updated (to disable cache)
RUN	git clone https://github.com/nigyta/dfast_qc.git

FROM debian:bookworm-slim

COPY --from=build /opt/conda/. /opt/conda/
COPY --from=build /dfast_qc /dfast_qc

# definition of environmental variables
ENV PATH /opt/conda/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DQC_ENV docker
ENV CHECKM_DATA_PATH /dqc_reference/checkm_data

RUN ln -s /dfast_qc/dfast_qc /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_admin_tools.py /usr/local/bin/ && \
	ln -s /dfast_qc/initial_setup.sh /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_ref_manager.py  /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_multi  /usr/local/bin/ && \
	mkdir -p /dqc_reference/checkm_data && \
	checkm data setRoot /dqc_reference/checkm_data

WORKDIR /work
CMD bash
