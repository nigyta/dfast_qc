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


