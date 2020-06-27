FROM continuumio/miniconda3:4.8.2 

MAINTAINER nigyta

# definition of environmental variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DQC_ENV docker

RUN cd / && \
	mkdir /work && \
	conda install -y -c bioconda fastani blast  hmmer prodigal && \
	git clone https://github.com/nigyta/dfast_qc.git && \
	pip install -r /dfast_qc/requirements.txt && \
	ln -s /dfast_qc/dfast_qc /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_admin_tools.py /usr/local/bin/ && \
	mkdir -p /dqc_reference/checkm_data && \
	checkm data setRoot /dqc_reference/checkm_data && \
	conda clean --all -y

WORKDIR /work
CMD bash
