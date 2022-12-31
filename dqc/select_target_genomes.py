import sys
import os
from .common import get_logger, run_command, get_ref_path, get_ref_genome_fasta
from argparse import ArgumentError, ArgumentParser
from logging import StreamHandler, Formatter, INFO, DEBUG, getLogger


logger = get_logger(__name__)
from .config import config


def check_blast_db(db_path):
    if not os.path.exists(db_path):
        logger.error("Reference marker FASTA does not exist. (%s)", db_path)
        exit(1)
    else:
        if not os.path.exists(db_path + ".nhr"):
            logger.warn("Database file is not indexed. Try to create BLAST database.")
            cmd = ["makeblastdb", "-in", db_path, "-dbtype nucl", "-hash_index"]
            run_command(cmd, "makeblastdb", shell=True)

def run_blastn(input_file, output_file, for_gtdb=False):
    if for_gtdb:
        db_file = get_ref_path(config.GTDB_REFERENCE_MARKERS_FASTA)
    else:
        db_file = get_ref_path(config.REFERENCE_MARKERS_FASTA)
    blast_options = config.BLAST_OPTIONS
    check_blast_db(db_file)
    cmd = ["blastn", "-query", input_file, "-db", db_file, "-out", output_file, blast_options]
    run_command(cmd, task_name="Blastn", shell=True)
    return output_file

def print_selected_genomes(str_result):
    logger.debug("\n%s\n%s%s", "-"*80, str_result, "-"*80)


def main(query_markers_fasta, out_dir, for_gtdb=False):
    """
    Search query_markers_fasta against reference_markers_fasta to select target genomes.
    """
    # genome_dir = get_ref_path(config.REFERENCE_GENOME_DIR)
    blast_result_file = os.path.join(out_dir, config.BLAST_RESULT)
    target_genome_list_file = os.path.join(out_dir, config.TARGET_GENOME_LIST)

    run_blastn(query_markers_fasta, blast_result_file, for_gtdb=for_gtdb)

    target_accessions = set()
    for line in open(blast_result_file):
        cols = line.strip("\n").split("\t")
        accession = "_".join(cols[1].split("_")[0:2])  # example of col2 GCF_001433745.1_rpoD 
        target_accessions.add(accession)
    ret, target_cnt = "", 0
    for accession in target_accessions:
        # target_genome_path = os.path.join(genome_dir, accession + ".fna.gz")
        target_genome_path = get_ref_genome_fasta(accession, for_gtdb=for_gtdb)
        target_cnt += 1
        ret += target_genome_path + "\n"
    with open(target_genome_list_file, "w") as f:
        f.write(ret)
    if not config.DEBUG:
        os.remove(blast_result_file)
    logger.info("Selected %d target genomes.", target_cnt)
    logger.info("Target genome list was writen to %s", target_genome_list_file)
    print_selected_genomes(ret)
    return target_genome_list_file

if __name__ == '__main__':

    def parse_args():
        parser = ArgumentParser()
        parser.add_argument(
            "-i",
            "--input",
            type=str,
            required=True,
            help="Query marker FASTA file [required]",
            metavar="PATH"
        )
        parser.add_argument(
            "-o",
            "--out_dir",
            default=".",
            type=str,
            help="Output directory (default: .)",
            metavar="PATH"
        )
        parser.add_argument(
            '--for_gtdb',
            action='store_true',
            help='Search against GTDB.'
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Debug mode'
        )
        args = parser.parse_args()
        return args

    args = parse_args()
    if args.debug:
        config.DEBUG = True

    main(args.input, args.out_dir, args.for_gtdb)  

