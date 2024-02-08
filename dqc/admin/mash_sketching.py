import os
import glob
from ..common import run_command, get_ref_path 
from ..config import config
from logging import getLogger

logger = getLogger(__name__)

def sketching():
    logger.info("===== Starting the sketch for referance genomes  =====") 
    # Setting the paths for refereance genome dir & MASH sketch file.
    paths_file = os.path.join(config.DQC_REFERENCE_DIR, "genome_files_paths.txt")

    #test = os.path.join(config.DQC_ROOT_DIR,"test_genomes")
    # Use glob to find files matching the pattern
    genome_files_paths = glob.glob(os.path.join(config.REFERENCE_GENOME_DIR,"*.fna.gz"))
    
    # Write the list of genome file paths to a file
    with open(paths_file, "w") as file:
        file.write("\n".join(genome_files_paths))

    # Define the command for running mash sketch with the specified parameters
    cmd_sketch = ["mash", "sketch", "-l", paths_file, "-o", config.MASH_SKETCH_FILE]
    run_command(cmd_sketch, task_name="mash sketching reference genomes")
    
    logger.info("===== Sketching referance genomes is done =====") 
    os.remove(paths_file)  # Remove the temporary file used to store genome file paths

if __name__ == "__main__":
    sketching()
