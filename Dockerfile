FROM continuumio/miniconda3:4.8.2 

LABEL maintainer=nigyta

# definition of environmental variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DQC_ENV docker

RUN cd / && \
	mkdir /work && chmod 777 /work && \
	conda install -y -c bioconda biopython fastani blast checkm-genome
	# conda install -y -c bioconda fastani blast hmmer prodigal


#	pip install -r /dfast_qc/requirements.txt && \
#	pip install ete3==3.1.2 more-itertools==8.2.0 peewee==3.14.4 && \
RUN	git clone https://github.com/nigyta/dfast_qc.git && \
	pip install ete3 more-itertools peewee && \
	ln -s /dfast_qc/dfast_qc /usr/local/bin/ && \
	ln -s /dfast_qc/dqc_admin_tools.py /usr/local/bin/ && \
	mkdir -p /dqc_reference/checkm_data && \
	checkm data setRoot /dqc_reference/checkm_data && \
	conda clean --all -y

ENV DQC_VERSION 0.5.1


WORKDIR /work
CMD bash
