import os
import glob
from ..common import run_command, get_ref_path 
from ..config import config
from logging import getLogger

logger = getLogger(__name__)

def gtdb_sketching():
    logger.info("===== Starting the sketch for GTDB genomes  =====") 
    # Setting the paths for GTDB genome dir & MASH sketch file.
    gtdb_paths_file = os.path.join(config.DQC_REFERENCE_DIR, "gtdb_genome_files_paths.txt")
    gtdb_genome_dir = get_ref_path(config.GTDB_GENOME_DIR)

    # Use glob to find files matching the pattern
    gtdb_genome_paths = glob.glob(os.path.join(gtdb_genome_dir, '**', f'*.fna.gz'), recursive = True)
    logger.info(f"Found {len(gtdb_genome_paths)} genomes in {gtdb_genome_dir}")

    # Write the list of genome file paths to a file
    with open(gtdb_paths_file, "w") as file:
        file.write("\n".join(gtdb_genome_paths))

    # Define the command for running mash sketch with the specified parameters
    gtdb_mash_sketch_file = get_ref_path(config.GTDB_MASH_SKETCH_FILE)
    cmd_gtdb_sketch = ["mash", "sketch", "-l", gtdb_paths_file, "-o", gtdb_mash_sketch_file, "-p", str(config.NUM_THREADS)]
    run_command(cmd_gtdb_sketch, task_name="mash sketching GTDB genomes")
    
    logger.info("===== Sketching GTDB genomes is done =====") 
    os.remove(gtdb_paths_file)  # Remove the temporary file used to store genome file paths

if __name__ == "__main__":
    gtdb_sketching()