# DFAST_qc: DFAST Qauality Control

DFAST_qc conducts taxonomy and completeness check of the assembled genome.  

- Taxonomy check  
DFAST_qc evaluates taxonomic identity of the genome by querying against 13,000 reference genomes from type strains. To shorten the runtime, it first inspects  universally-conserved housekeeping genes, such as _dnaB_ and _rpsA_ in the query genome, and they are searched against refernce nucleotide databases to narrow down the number of reference genomes used in the downstream process. Then, average nucleotide identity is calculated against the selected reference genomes.  
DFAST_qc uses HMMer and NCBI Blast for the former process and [FastANI](https://doi.org/10.1038/s41467-018-07641-9) for the latter process.

- Completeness check  
DFAST_qc employs [CheckM](https://genome.cshlp.org/content/25/7/1043) to calculate comleteness and contamination values of the genome. DFAST_qc automatically determines the reference marker set for CheckM based on the result of taxonomy check. Alternatively, users can arbitrarily specify the marker set.

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

## Initial set up
Reference data of DFAST_qc is stored in a directory called `DQC_REFERENCE`. By default, it is located in the directory where DFAST_qc is installed (`PATH/TO/dfast_qc/dqc_reference`), or in `/dqc_reference` when the docker version is used.  
In general, you do not need to change this, but you can specify it in the config file or by using `-r` option.

To prepare reference data, reference data must be prepared as following. Run `dqc_admin_tools.py -h` or `dqc_admin_tools.py subcommand -h` to show help.
  

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


Once, reference data has been prepared, it can be updated by running command:
```
$ dqc_admin_tools.py update_all
```

## Usage
- Minimum  
    ```
    $ dfast_qc -i /path/to/input_genome.fasta
    ```
- Basic  
    ```
    $ dfast_qc -i /path/to/input_genome.fasta -o /path/to/output --num_threads 2
    ```

```
usage: dfast_qc [-h] [-i PATH] [-o PATH] [-t INT] [-r PATH] [-p STR] [-n INT]
                [--disable_tc | --disable_cc] [--force] [--debug]
                [--show_taxon]

DFAST_QC: Taxonomy and completeness check

optional arguments:
  -h, --help            show this help message and exit
  -i PATH, --input_fasta PATH
                        Input FASTA file (raw or gzipped) [required]
  -o PATH, --out_dir PATH
                        Output directory (default: OUT)
  -t INT, --taxid INT   NCBI taxid for completeness check. Use '--show_taxon'
                        for available taxids. (Default: Automatically inferred
                        from taxonomy check)
  -r PATH, --ref_dir PATH
                        DQC reference directory (default: DQC_REFERENCE_DIR)
  -p STR, --prefix STR  Prefix for output (for debugging use, default: None)
  -n INT, --num_threads INT
                        Number of threads for parallel processing (default: 1)
  --disable_tc          Disable taxonomy check using ANI
  --disable_cc          Disable completeness check using CheckM
  --force               Force overwriting result
  --debug               Debug mode
  --show_taxon          Show available taxa for competeness check
  ```

# Example of Result
- `tc_result.tsv`: Taxonomy check result
- `cc_result.tsv`: Completeness check result
- `dqc_result.json`: DFAST_qc result in a json format as show below:
    ```
    {
        "tc_result": [
            {
                "organism_name": "Lactobacillus parakefiri",
                "strain": "strain=JCM 8573",
                "accession": "GCA_002157585.1",
                "taxid": 152332,
                "species_taxid": 152332,
                "relation_to_type": "type",
                "validated": true,
                "ani": 99.9803,
                "matched_fragments": 770,
                "total_fragments": 778
            },
            {
                "organism_name": "Lactobacillus parakefiri",
                "strain": "strain=DSM 10551",
                "accession": "GCA_004354625.1",
                ...
                "matched_fragments": 172,
                "total_fragments": 778
            }
        ],
        "cc_result": {
            "completeness": 98.71,
            "contamination": 0.81,
            "strain_heterogeneity": 0.0
        }
    }
    ```