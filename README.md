# DFAST_QC: DFAST Qauality Control

DFAST_QC conducts taxonomy and completeness check of the assembled genome.  

- Taxonomy check  
DFAST_QC evaluates taxonomic identity of the genome by querying against more than 20,000 reference genomes from type strains. To shorten the runtime , it first run MASH on the query against reference nucleotide databases to narrow down the number of genomes used in the downstream process based on the number of shred hashes. Then, pass it on to Skani against the selected reference genomes to calculate the ANI value.  
DFAST_QC uses [MASH](https://doi.org/10.1186/s13059-016-0997-x) for the former process and [Skani](https://doi.org/10.1038/s41592-023-02018-3) for the latter process.

- Completeness check  
DFAST_QC employs [CheckM](https://genome.cshlp.org/content/25/7/1043) to calculate completeness and contamination values of the query genome. DFAST_QC automatically determines the reference marker set for CheckM based on the result of taxonomy check. Users can also specify the marker set to be used.

- GTDB search  
As of ver. 0.5.0, DFAST_QC can calculate ANI against GTDB representative genomes, thereby enabling species-level identification in the GTDB Taxonomy. Thie employs the same 2-step search as Taxonomy check

---

## System requirements and software dependencies
DFAST_QC runs on Linux / Mac (Intel CPU) with Python ver. 3.7 or later. It requires approximately 4Gbyte of memory. 
The following third party softwares/packages are required.  
- Skani
- Mash  
- HMMer  
- Prodigal  
- CheckM  
- Python packages: peewee, more-itertools, ete3  

## Installation from Bioconda
DFAST_QC is also available from [BioConda](https://bioconda.github.io/recipes/dfast_qc/README.html).
```
conda install -c bioconda -c conda-forge dfast_qc
```
If this did not work, please try [Installation from source code](#installation-from-source-code).  
\* FastANI installed with this might be broken. See below for trouble shooting.


## Installation from source code
1. Source code
    ```
    $ git clone https://github.com/nigyta/dfast_qc.git
    ```

2. Install dependencies  
    We recommend using conda to install dependencies.  
    ```
    $ cd dfast_qc
    $ conda env create -f environment.yml
    ```
    This will create a conda environment named "dfast_qc" and install the above-mentioned dependencies in it.  

    Alternatively, after installing required softwares by yourself, you can install Python packages with the `pip` command.
    ```
    $ pip install -r requirements.txt
    ```

    __[Trouble shoot]__  
    If `fastANI` installed with the `conda` command does not work, please uninstall and re-install it with the commands below.  
    ```
    $ conda remove fastani
    $ conda install -c bioconda -c conda-forge fastani
    ```


Reference data is not included in the conda package. Please install it following the steps below.

## Quick set up (recommended)
Since the full data set of DFAST_QC's reference data (`DQC_REFERENCE_FULL`) is huge (>80GB, including GTDB representative genomes), we have made the pre-built reference data (`DQC_REFERENCE_COMPACT`, <1GB) available for download using 
the `dqc_ref_manager.py` script. 
```
dqc_ref_manager.py download
```
As `DQC_REFERENCE_COMPACT` does not contain reference genomes for ANI calculation, `dfast_qc` will attempt to download the required genomes in an on-the-fly manner during the run (internet connection is required). Therefore, it takes extra time for downloding them (~1min).  
We will update `DQC_REFERENCE_COMPACT` periodically, please update it by running `dqc_ref_manager.py` again.

If you want to prepre `DQC_REFERENCE_FULL`, please follow the procedure [below](#for-power-users).
  
---

## Usage
- Minimum  
    ```
    $ dfast_qc -i /path/to/input_genome.fasta
    ```
- Basic  
    ```
    $ dfast_qc -i /path/to/input_genome.fasta -o /path/to/output --num_threads 2
    ```
    If you are using DQC_REFERENCE_COMPACT, missing genomes will be downloaded in parallel by specifying `--num_threads` value larger than 1. 
- GTDB search (disabled by default)  
    ```
    $ dfast_qc -i /path/to/input_genome.fasta -o /path/to/output --enable_gtdb [--disable_tc] [--disable_cc]
    ```

```
usage: dfast_qc [-h] [--version] [-i PATH] [-o PATH] [-hits INT] [-a INT]
                [-t INT] [-r PATH] [-n INT] [--enable_gtdb] [--disable_tc] 
                [--disable_cc] [--disable_auto_download] [--force] 
                [--debug] [-p STR] [--show_taxon]

DFAST_QC: Taxonomy and completeness check

optional arguments:
options:
  -h, --help            show this help message and exit
  --version             Show program version
  -i PATH, --input_fasta PATH
                        Input FASTA file (raw or gzipped) [required]
  -o PATH, --out_dir PATH
                        Output directory (default: OUT)
  -hits INT, --num_hits INT
                        Number of top hits by MASH (default: 10)
  -a INT, --ani INT     ANI threshold (default: 95%)
  -t INT, --taxid INT   NCBI taxid for completeness check. Use '--show_taxon' for available taxids. (Default: Automatically inferred from taxonomy check)
  -r PATH, --ref_dir PATH
                        DQC reference directory (default: DQC_REFERENCE_DIR)
  -n INT, --num_threads INT
                        Number of threads for parallel processing (default: 1)
  --enable_gtdb         Enable GTDB search
  --disable_tc          Disable taxonomy check using ANI
  --disable_cc          Disable completeness check using CheckM
  --disable_auto_download
                        Disable auto-download for missing reference genomes
  --force               Force overwriting result
  --debug               Debug mode
  -p STR, --prefix STR  Prefix for output (for debugging use, default: None)
  --show_taxon          Show available taxa for competeness check

  ```

## Example of Result
- `tc_result.tsv`: Taxonomy check result
- `cc_result.tsv`: Completeness check result
- `dqc_result.json`: DFAST_QC result in a json format as show below:
    ```
    {
        "tc_result": [
            {
                "organism_name": "Lactobacillus paragasseri",
                "strain": "strain=JCM 5343",
                "accession": "GCA_003307275.1",
                "taxid": 2107999,
                "species_taxid": 2107999,
                "relation_to_type": "type",
                "validated": true,
                "ani": 99.8183,
                "matched_fragments": 629,
                "total_fragments": 667,
                "status": "conclusive"
            },
            ...
            {
                "organism_name": "Lactobacillus gasseri",
                "strain": "strain=ATCC 33323",
                "accession": "GCA_000014425.1",
                ...
                "ani": 93.5813,
                "matched_fragments": 568,
                "total_fragments": 667,
                "status": "below_threshold"
            }
        ],
        "cc_result": {
            "completeness": 98.71,
            "contamination": 0.81,
            "strain_heterogeneity": 0.0
        }
    }
    ```



## List of status in taxonomy check result
- __conclusive__: Effective ANI hit (>=95%) againt only 1 species, hence the species name is conclusively determined.
- __indistinguishable__: The genome belongs to one of the species that are difficult to distinguish using ANI (e.g. E. coli and Shigella spp.) 
- __inconclusive__: ANI hits against more than 2 differenct species. This may result from the comparison between very closely-related species or contamination of 2 different species.
- __below_threhold__: The ANI hit is below the threshold (95%)

Note that DFAST_QC cannot identify clades below species level.

## Run in Docker

Docker image is available at [dockerub](https://hub.docker.com/r/nigyta/dfast_qc).  
The example below shows how to invoke DFAST_QC with an input FASTA file (genome.fa) in the current directory.
```
docker run -it --rm --name dqc -v /path/to/dqc_reference:/dqc_reference -v $PWD:$PWD nigyta/dfast_qc dfast_qc -i $PWD/genome.fa -o $PWD/dfastqc_out
```

---
# For power users

## Prepare reference data 
Reference data of DFAST_QC is stored in a directory called `DQC_REFERENCE`. By default, it is located in the directory where DFAST_QC is installed (`PATH/TO/dfast_qc/dqc_reference`), or in `/dqc_reference` when the docker version is used.  
In general, you do not need to change this, but you can specify it in the config file or by using `-r` option.

__To prepare reference data, run the following command.__
```
$ sh initial_setup.sh [-n int]
```
`-n` denotes the number of threads for parallel processing (default: 1). As data preparation may take time, it is recommended specifying the value 4~8 (or more) for `-n`.

__Once reference data has been prepared, it can be updated by running command__
```
$ dqc_admin_tools.py update_all
```

Instead of running `initial_setup.sh`, you can prepare reference data by manually executing the following commands. Run `dqc_admin_tools.py -h` or `dqc_admin_tools.py subcommand -h` to show help.
  

1. Download master files  
    ```
    $ dqc_admin_tools.py download_master_files --targets asm ani tsr hmm igp
    ```
    This will download "Assembly report", "ANI report", "Type strain report", and "indistinguishable_groups_prokaryotes.txt" from the NCBI FTP server and HMMer profile for TIGR.  

2. Download/Update NCBI taxdump data
    ```
    $ dqc_admin_tools.py update_taxdump
    ```
3. Download reference genomes
    ```
    $ dqc_admin_tools.py download_genomes
    ```
    This will download reference genomic FASTA files from the NCBI Assembly database. As it attempts to download large number of genomes, it is recommended to enable parallel downloading option (e.g. `--num_threads 4`)

4. Sketch reference genomes using MASH
    ```
    $ dqc_admin_tools.py mash_ref_sketch
    ```
5. Prepare SQLite database file
    ```
    $ dqc_admin_tools.py prepare_sqlite_db
    ```
    This will generate a reference file `DQC_REFERENCE/references.db`, which contains metadata for reference genomes.
6. Prepare CheckM data
    ```
    $ dqc_admin_tools.py prepare_checkm
    ```
    CheckM reference data will be downloaded and configured.
7. Update database for CheckM
    ```
    $ dqc_admin_tools.py update_checkm_db
    ```
    Will insert auxiliary data for CheckM into `DQC_REFERENCE/references.db`


## Preparation for the GTDB reference data.
1. Download the representative genomes from GTDB and unarchive it.
    ```
    $ curl -LO https://data.gtdb.ecogenomic.org/releases/latest/genomic_files_reps/gtdb_genomes_reps.tar.gz
    $ tar xfz gtdb_genomes_reps.tar.gz
    ```
2. Place the unarchived folder under `DQC_REFERENCE`.  
Make sure that the folder name is identical to the value `GTDB_GENOME_DIR` specified in [config.py](dqc/config.py).  
    ```
    GTDB_GENOME_DIR = "gtdb_genomes_reps_r214"
    ```
3. Download the species list from GTDB.  
    ```
    curl -LO https://data.gtdb.ecogenomic.org/releases/latest/auxillary_files/sp_clusters.tsv
    ```
    The above command will download [this file](https://data.gtdb.ecogenomic.org/releases/latest/auxillary_files/sp_clusters.tsv) from GTDB.

4. Sketch representative genomes from GTDB using MASH
    ```
    $ dqc_admin_tools.py mash_gtdb_sketch
    ```
    
5. Prepare the SQLite DB file for GTDB  
    ```
    dqc_admin_tools.py prepare_sqlite_db --for_gtdb
    ```

When the newer version of the GTDB representative genomes become available, repeat these steps.