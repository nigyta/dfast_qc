### v. 1.1.1 (2026.04.14)
Bug fix for Mash. Mash may fail when running with multiple threads. If you got an error like 'ERROR: Did not find fasta records...', please try running DFAST_QC with a single thread by setting --num_threads to 1."

### v. 1.1.0 (2026.04.10)
- Supported Python version: We recommend using Python 3.11, because some of the module may not work on other versions.
- Dropped macOS support: DFAST_QC previously supported macOS, but as of version 1.1.0, official macOS support has been dropped. It may still work on macOS, but the tool is mainly developed and tested on Linux.
- ShigaPass integration: When the taxonomy check identifies the query genome as *Escherichia coli*/*Shigella* (status: "indistinguishable"), [ShigaPass](https://github.com/imanyass/ShigaPass) is automatically run to predict the *Shigella* serotype. ShigaPass can be disabled with `--disable_shigapass`.
- If ShigaPass is not installed and the query genome is identified as *E. coli*/*Shigella*, ShigaPass and its reference databases are automatically installed at runtime. They can also be manually installed via `dqc_admin_tools.py setup_shigapass`.
- ShigaPass is installed under $DQC_REFERENCE/shigapass
- The ShigaPass result is added to `dqc_result.json` as `shigapass_result`, e.g.:
  ```json
  "shigapass_result": {
      "name": "GCA_000012025",
      "rfb": "C4",
      "rfb_hits": "130,(100.0%)",
      "MLST": "ST1130",
      "fliC": "ShH15(ShH3cplx)",
      "CRISPR": "A-var2",
      "ipaH": "ipaH+",
      "organism": "Shigella boydii",
      "Predicted_Serotype": "SB4",
      "Predicted_FlexSerotype": "",
      "Comments": ""
  }
  ```

### v. 1.0.7 (2025.04.30)
- Minor change. Updated to use GTDB_r226  
- The reference data for GTDB has been changed (config.py)  
  `GTDB_GENOME_DIR = "gtdb_genomes_reps_r226/database"`
  to
  `GTDB_GENOME_DIR = "gtdb_genomes_reps/database"`  
  Creating a sym link is recommended:  
  `ln -s gtdb_genomes_reps_r226 gtdb_genomes_reps`

### v. 1.0.6 (2025.02.04)
- Minor change. Scripts for managing reference data updated.

### v. 1.0.3
- dqc_multi added for batch execution

### v. 1.0.0
- Mash and skani pipeline

### v. 0.5.8
- Final version based on homology search and fastANI

### v. 0.5.7
- Minor bug fix for `dqc_ref_manager.py`

### v. 0.5.6
- `DQC_REFERENCE_COMPACT` has become available. Use `dqc_ref_manager.py` to download the reference data.

### v. 0.5.5_2
- Species specific ANI implemented

### v. 0.5.5
- Implemented ANI calculation against GTDB representative genomes  
- Removed Biopython from dependencies  
- Use the CHECKM_DATA_PATH environmental variable for the checkm data directory  


