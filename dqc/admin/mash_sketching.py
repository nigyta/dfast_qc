import os
import glob
from ..common import run_command, get_ref_path, get_logger
from ..config import config

logger = get_logger(__name__)

def sketching():
    logger.info("===== Starting the sketch for referance genomes  =====") 
    # Setting the paths for refereance genome dir & MASH sketch file.
    paths_file = os.path.join(config.DQC_REFERENCE_DIR, "genome_files_paths.txt")
    reference_genome_dir = get_ref_path(config.REFERENCE_GENOME_DIR)

    # Use glob to find files matching the pattern
    genome_files_paths = glob.glob(os.path.join(reference_genome_dir, "*.fna.gz"))
    logger.info(f"Found {len(genome_files_paths)} genomes in {reference_genome_dir}")
    
    # Write the list of genome file paths to a file
    with open(paths_file, "w") as file:
        file.write("\n".join(genome_files_paths))

    # Define the command for running mash sketch with the specified parameters
    mash_sketch_file = get_ref_path(config.MASH_SKETCH_FILE)
    cmd_sketch = ["mash", "sketch", "-l", paths_file, "-o", mash_sketch_file, "-p", str(config.NUM_THREADS)]
    run_command(cmd_sketch, task_name="mash sketching reference genomes")
    
    logger.info("===== Sketching reference genomes is done =====")
    os.remove(paths_file)  # Remove the temporary file used to store genome file paths

if __name__ == "__main__":
    sketching()
