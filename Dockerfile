FROM --platform=linux/amd64 continuumio/miniconda3:23.10.0-1

LABEL maintainer=nigyta

# definition of environmental variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DQC_ENV docker

RUN cd / && \
	mkdir /work && chmod 777 /work && \
	pip install checkm-genome && \
	conda install -y -c bioconda -c conda-forge biopython mash skani gsl==2.6 hmmer prodigal

RUN pip install ete3 more-itertools peewee

ENV DQC_VERSION 0.6.0

RUN	git clone -b skani https://github.com/nigyta/dfast_qc.git && \
    ln -s /dfast_qc/dfast_qc /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_admin_tools.py /usr/local/bin/ && \
	mkdir -p /dqc_reference/checkm_data && \
	checkm data setRoot /dqc_reference/checkm_data && \
	conda clean --all -y

WORKDIR /work
CMD bash
