import os
import glob
from ..common import run_command, get_ref_path 
from ..config import config
from logging import getLogger

logger = getLogger(__name__)

def gtdb_sketching():
    logger.info("===== Starting the sketch for GTDB genomes  =====") 
    # Setting the paths for refereance genome dir & MASH sketch file.
    gtdb_dir = os.path.join(config.DQC_REFERENCE_DIR,config.GTDB_GENOME_DIR)
    gtdb_paths_file = os.path.join(config.DQC_REFERENCE_DIR, "gtdb_genome_files_paths.txt")

    # Use glob to find files matching the pattern
    gtdb_genome_paths = glob.glob(os.path.join(gtdb_dir, '**', f'*.fna.gz'), recursive = True)
    
    # Write the list of genome file paths to a file
    with open(gtdb_paths_file, "w") as file:
        file.write("\n".join(gtdb_genome_paths))

    # Define the command for running mash sketch with the specified parameters
    cmd_gtdb_sketch = ["mash", "sketch", "-l", gtdb_genome_paths, "-o", config.GTDB_MASH_SKETCH_FILE]
    run_command(cmd_gtdb_sketch, task_name="mash sketching GTDB genomes")
    
    logger.info("===== Sketching GTDB genomes is done =====") 
    os.remove(gtdb_genome_paths)  # Remove the temporary file used to store genome file paths

if __name__ == "__main__":
    gtdb_sketching()