# DFAST_qc: DFAST Qauality Control

DFAST_qc conducts taxonomy and completeness check of the assembled genome.  

- Taxonomy check  
DFAST_qc evaluates taxonomic identity of the genome by querying against 13,000 reference genomes from type strains. To shorten the runtime, it first inspects  universally-conserved housekeeping genes, such as _dnaB_ and _rpsA_ in the query genome, and they are searched against refernce nucleotide databases to narrow down the number of reference genomes used in the downstream process. Then, average nucleotide identity is calculated against the selected reference genomes.  
DFAST_qc uses HMMer and NCBI Blast for the former process and [FastANI](https://doi.org/10.1038/s41467-018-07641-9) for the latter process.

- Completeness check  
DFAST_qc employs [CheckM](https://genome.cshlp.org/content/25/7/1043) to calculate comleteness and contamination values of the genome. DFAST_qc automatically determines the reference marker set for CheckM based on the result of taxonomy check. Alternatively, users can arbitrarily specify thr marker set.

## Installation
1. Source code
    ```
    $ git clone https://github.com/nigyta/dfast_qc.git
    ```
2. Install dependency
    ```
    $ cd dfast_qc
    $ pip install -r requirements.txt
    ```

## Initial setup
Reference data of DFAST_qc is stored in a directory called `DQC_REFERENCE`. By default, it is located in the directory where DFAST_qc is installed (`PATH/TO/dfast_qc/dqc_reference`), or in `/dqc_reference` when the docker version is used.  
In general, you do not need to change this, but you can specify it in the config file or by using `-r` option.

To prepare reference data, reference data must be prepared as following:  

1. Download master files  
    ```
    $ dqc_admin_tools.py download_master_files --targets asm ani tsr hmm
    ```
    This will download "Assembly report", "ANI report", and "Type strain report" from the NCBI FTP server and HMMer profile for TIGR.  

2. Download/Update NCBI taxdump data
    ```
    $ dqc_admin_tools.py update_taxdump
    ```
3. Download reference genomes
    ```
    $ dqc_admin_tools.py download_genomes
    ```
    This will download reference genomic FASTA files from the NCBI Assembly database. As it attempts to download large number of genomes, it is recommended to enable parallel downloadin option (e.g. `--num_threads 4`)
4. Prepare reference profile HMM
    ```
    $ dqc_admin_tools.py prepare_reference_hmm
    ```
    This will generate a reference HMM file `DQC_REFERENCE/reference_markers.hmm`
5. Prepare reference marker FASTA file
    ```
    $ dqc_admin_tools.py prepare_reference_fasta
    ```
    This will generate a reference FASTA file `DQC_REFERENCE/reference_markers.fasta`
    it is recommended to enable parallel processing option (e.g. `--num_threads 4`)
6. Prepare SQLite database file
    ```
    $ dqc_admin_tools.py prepare_sqlite_db
    ```
    This will generate a reference file `DQC_REFERENCE/references.db`, which contains metadata for reference genomes.
7. Prepare CheckM data
    ```
    $ dqc_admin_tools.py prepare_checkm
    ```
    CheckM reference data will be downloaded and configured.
8. Update database for CheckM
    ```
    $ dqc_admin_tools.py update_checkm_db
    ```
    Will insert auxiliary data for CheckM into `DQC_REFERENCE/references.db`
