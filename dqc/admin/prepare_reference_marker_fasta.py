import os
import sys
import glob
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from more_itertools import chunked

from ..config import config
from ..common import get_logger, run_command, get_ref_path, get_ref_genome_fasta, get_existing_gtdb_genomes
from ..prepare_marker_fasta import main as prepare_marker_fasta
from .download_all_reference_genomes import get_existing_genomes
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

def concat_result_files(marker_dir, for_gtdb=False):
    def cat_files(file_list, out_file_name, chunk_no=None):
        cmd = ["cat", " ".join(file_list), ">", out_file_name]
        if chunk_no is not None:
            logger.debug("Concatenating %d files for chunk %d [%s]", len(file_list), chunk_no, out_file_name)
        else:
            logger.debug("Concatenating %d tempolary files to generate final result. [%s]", len(file_list), out_file_name)

        p = subprocess.run(" ".join(cmd), shell=True, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if p.returncode != 0:
            logger.error("Command failed. Aborted. [%s]", cmd)
            logger.error("Stdout: \n%s", p.stdout)
            exit(1)

    def cat_files_wih_multi_threads(file_list_all, out_file_name, chunk_size=1000):
        threads = config.NUM_THREADS
        tmp_output_files = []
        futures = []
        with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
            for i, chunked_file_list in enumerate(chunked(file_list_all, chunk_size)):
                tmp_output_file_name = out_file_name + f".chunk{i}"
                f = executor.submit(cat_files, chunked_file_list, tmp_output_file_name, chunk_no=i)
                tmp_output_files.append(tmp_output_file_name)
                futures.append(f)
        [f.result() for f in as_completed(futures)]  # wait until all the jobs finish
        cat_files(tmp_output_files, out_file_name)
        rm_cmd = ["rm"] + tmp_output_files
        subprocess.run(rm_cmd, shell=False, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)        

    # concatenate reference marker FASTA
    if for_gtdb:
        out_fasta = get_ref_path(config.GTDB_REFERENCE_MARKERS_FASTA) # reference_markers.fasta
    else:
        out_fasta = get_ref_path(config.REFERENCE_MARKERS_FASTA) # reference_markers.fasta
    fasta_file_list = glob.glob(f"{marker_dir}/*/markers.fasta")
    cat_files_wih_multi_threads(fasta_file_list, out_fasta)
    logger.info("Reference marker FASTA was written to %s", out_fasta)

    # concatenate reference summary
    if for_gtdb:
        out_summary = get_ref_path(config.GTDB_REFERENCE_SUMMARY_TSV) # reference_markers.fasta
    else:
        out_summary = get_ref_path(config.REFERENCE_SUMMARY_TSV) # reference_markers.fasta

    summary_file_list = glob.glob(f"{marker_dir}/*/marker.summary.tsv")
    cat_files_wih_multi_threads(summary_file_list, out_summary)
    logger.info("Reference marker summary was written to %s", out_summary)

    format_reference_fasta(out_fasta)

def format_reference_fasta(reference_fasta):
    logger.info("Will prepare BLAST database for %s", reference_fasta)
    cmd = ["makeblastdb", "-in", reference_fasta, "-dbtype nucl", "-hash_index"]
    run_command(cmd, "makeblastdb", shell=True)

def prepare_reference_marker_fasta(delete_existing=False, for_gtdb=False):
    
    threads = config.NUM_THREADS
    if for_gtdb:
        ref_genome_dir = get_ref_path(config.GTDB_GENOME_DIR)
        ref_marker_dir = get_ref_path(config.GTDB_REFERENCE_MARKER_DIR)
        logger.info("===== Prepare reference marker FASTA for GTDB (%s) =====", config.GTDB_REFERENCE_MARKERS_FASTA)
    else:
        ref_genome_dir = get_ref_path(config.REFERENCE_GENOME_DIR)
        ref_marker_dir = get_ref_path(config.REFERENCE_MARKER_DIR)
        logger.info("===== Prepare reference marker FASTA (%s) =====", config.REFERENCE_MARKERS_FASTA)

    # check reference genome dir.
    if not os.path.exists(ref_genome_dir):
        logger.error("Reference genome directory does not exist. [%s]", ref_genome_dir)
        exit(1)
    if for_gtdb:
        existing_genomes = set(get_existing_gtdb_genomes())
    else:
        existing_genomes = set(get_existing_genomes(ref_genome_dir))
    logger.info("Number of existing genomes : %d (%s)", len(existing_genomes), ref_genome_dir)

    # check reference marker dir.
    # Deleted if 'delete_existing == True'
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

        futures = []
        with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        # with ProcessPoolExecutor(max_workers=num_parallel_workers) as executor:
            for accession in new_markers:
                input_file_name = get_ref_genome_fasta(accession, for_gtdb=for_gtdb)
                marker_out_dir = os.path.join(ref_marker_dir, accession)
                prefix = accession
                f = executor.submit(prepare_marker_fasta, input_file_name, marker_out_dir, prefix)
                futures.append(f)
        [f.result() for f in as_completed(futures)]  # wait until all the jobs finish

        logger.info("Created %d markers.", len(new_markers))

    # delete unwanted markers
    if unwanted_markers:
        logger.info("Start deleting unwanted markers.")
        unwanted_markers = sorted(unwanted_markers)
        delete_unwanted_markers(unwanted_markers, ref_marker_dir)
        logger.info("Deleted %d markers.", len(unwanted_markers))

    concat_result_files(ref_marker_dir, for_gtdb=for_gtdb)
    
    logger.info("===== Completed preparing reference marker FASTA =====")


if __name__ == "__main__":
    pass
    
    # for test run: python -m dqc.admin.prepare_reference_marker_fasta
    # ref_marker_dir = "dqc_reference/markers"
    # concat_result_files(ref_marker_dir)    
    # prepare_reference_marker_fasta_GTDB()
    # config.NUM_THREADS = 6
    prepare_reference_marker_fasta(delete_existing=False, for_gtdb=True)