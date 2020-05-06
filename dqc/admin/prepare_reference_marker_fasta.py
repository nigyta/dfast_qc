import os
import sys
import glob
import shutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from ..config import config
from ..common import get_logger, run_command
from ..prepare_marker_fasta import main as prepare_marker_fasta
from .download_all_reference_fasta import get_existing_genomes

logger = get_logger(__name__)

def delete_unwanted_markers(unwanted_markers, marker_dir):
    for accession in unwanted_markers:
        target_dir = os.path.join(marker_dir, accession)
        assert os.path.exists(target_dir)
        shutil.rmtree(target_dir)
        logger.info("Deleted %s", target_dir)

def get_existing_markers(marker_dir):
    marker_file_basename = config.QUERY_MARKERS_FASTA
    existing_markers = []
    for accession in os.listdir(marker_dir):
        fasta_file = os.path.join(marker_dir, accession, marker_file_basename)
        if os.path.exists(fasta_file):
            existing_markers.append(accession)
    return existing_markers

def concat_result_files(out_dir, marker_dir):
    ref_marker_fasta_base = os.path.basename(config.REFERENCE_MARKERS_FASTA)  # reference_markers.fasta
    ref_summary_tsv_base = os.path.basename(config.REFERENCE_SUMMARY_TSV)  # reference_summary.tsv
    
    out_fasta = os.path.join(out_dir, ref_marker_fasta_base)
    out_summary = os.path.join(out_dir, ref_summary_tsv_base)
    cmd1 = ["cat", f"{marker_dir}/*/*markers.fasta", ">", out_fasta]
    run_command(cmd1, "concat-fasta", shell=True)
    logger.info("Reference marker FASTA was written to %s", out_fasta)
    cmd2 = ["cat", f"{marker_dir}/*/*.summary.tsv", ">", out_summary]
    run_command(cmd2, "concat-summary", shell=True)
    logger.info("Reference marker summary was written to %s", out_summary)
    format_reference_fasta(out_fasta)

def format_reference_fasta(reference_fasta):
    logger.info("Will prepare BLAST database for %s", reference_fasta)
    cmd = ["makeblastdb", "-in", reference_fasta, "-dbtype nucl", "-hash_index"]
    run_command(cmd, "makeblastdb", shell=True)

def prepare_reference_marker_fasta(out_dir=None, threads=1, delete_existing=False):
    logger.info("===== Prepare reference marker FASTA (reference_markers.fasta) =====")
    ref_genome_dir_base = os.path.basename(config.REFERENCE_GENOME_DIR)  # genomes 
    ref_marker_dir_base = os.path.basename(config.REFERENCE_MARKER_DIR)  # markers 

    # check out_dir (default: DQC_REFERENCE_DIR)
    if out_dir is None:
        out_dir = config.DQC_REFERENCE_DIR
    os.makedirs(out_dir, exist_ok=True)

    # check reference genome dir. (default: genomes)
    ref_genome_dir = os.path.join(out_dir, ref_genome_dir_base)
    if not os.path.exists(ref_genome_dir):
        logger.error("Reference genome directory does not exist. [%s]", ref_genome_dir)
        exit(1)
    existing_genomes = set(get_existing_genomes(ref_genome_dir))
    logger.info("Number of existing genomes : %d (%s)", len(existing_genomes), ref_genome_dir)

    # check reference marker dir. (default: markers)
    # Deleted if 'delete_existing == True'
    ref_marker_dir = os.path.join(out_dir, ref_marker_dir_base)
    if delete_existing and os.path.exists(ref_marker_dir):
        shutil.rmtree(ref_marker_dir)
        logger.warning("Deleted existing markers: %s", ref_marker_dir)
    os.makedirs(ref_marker_dir, exist_ok=True)
    existing_markers = set(get_existing_markers(ref_marker_dir))
    logger.info("Number of existing markers: %d (%s)", len(existing_markers), ref_marker_dir)

    new_markers = list(existing_genomes - existing_markers)
    unwanted_markers = list(existing_markers - existing_genomes)
    logger.info("Number of new markers to be created: %d", len(new_markers))    
    logger.info("Number of unwanted markers to be deleted: %d", len(unwanted_markers))    

    # add new markers
    if new_markers:
        new_markers = sorted(new_markers)
        logger.info("Start preparing new markers.")

        with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        # with ProcessPoolExecutor(max_workers=num_parallel_workers) as executor:
            for accession in new_markers:
                input_file_name = os.path.join(ref_genome_dir, accession + ".fna.gz")
                marker_out_dir = os.path.join(ref_marker_dir, accession)
                prefix = accession
                executor.submit(prepare_marker_fasta, input_file_name, marker_out_dir, prefix)

        logger.info("Created %d markers.", len(new_markers))


    if unwanted_markers:
        logger.info("Start deleting unwanted markers.")
        unwanted_markers = sorted(unwanted_markers)
        delete_unwanted_markers(unwanted_markers, ref_marker_dir)
        logger.info("Deleted %d markers.", len(unwanted_markers))

    concat_result_files(out_dir, ref_marker_dir)
    
    logger.info("===== Completed preparing reference marker FASTA =====")
