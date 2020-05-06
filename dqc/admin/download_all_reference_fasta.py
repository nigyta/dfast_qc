import os
from argparse import ArgumentParser
from ..common import get_logger
from .ani_report_parser import ANIreport, get_filtered_ANI_report
from .asm_report_parser import Assembly
from ..config import config
from ..download_files import download_genomes_parallel

logger = get_logger(__name__)

def delete_unwanted_genomes(accessions, genome_dir):
    for accession in accessions:
        target_file = os.path.join(genome_dir, accession + ".fna.gz")
        assert os.path.exists(target_file)
        os.remove(target_file)
        logger.info("Deleted %s", target_file)

def get_existing_genomes(genome_dir):
    # Todo: check eof, broken file
    existing_genomes = []
    for file_name in os.listdir(genome_dir):
        if os.path.getsize(os.path.join(genome_dir, file_name)) > 0:
            existing_genomes.append(file_name.replace(".fna.gz", ""))
    return existing_genomes

def download_all_genomes(asm_report=None, ani_report=None, type_strain_report=None, out_dir=None, threads=1):

    if asm_report is None:
        asm_report = config.ASSEMBLY_REPORT_FILE
    if ani_report is None:
        ani_report = config.ANI_REPORT_FILE
    if type_strain_report is None:
        type_strain_report = config.TYPE_STRAIN_REPORT_FILE
    if out_dir is None:
        out_dir = config.REFERENCE_GENOME_DIR
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    logger.info("===== Download reference genomes from Assembly DB =====")
    logger.info("Reference genome FASTA will be downloaded to %s", out_dir)

    selected_reports_by_ANI = get_filtered_ANI_report(ani_report)
    selected_reports_by_ANI = set(selected_reports_by_ANI.keys())
    target_genomes = set()
    for asm in Assembly.parse(asm_report):
        if asm.assembly_accession in selected_reports_by_ANI:
            # Todo: add extra filtering condition
            target_genomes.add(asm.assembly_accession)
    logger.info("Parsed Assembly report. Number of target genomes: %d", len(target_genomes))
    existing_genomes = get_existing_genomes(out_dir)
    existing_genomes = set(existing_genomes)
    logger.info("Number of existing genomes in output direcotry: %d", len(existing_genomes))    
    new_genomes = list(target_genomes - existing_genomes)
    unwanted_genomes = list(existing_genomes - target_genomes)
    logger.info("Number of new genomes to be downloaded: %d", len(new_genomes))    
    logger.info("Number of unwanted genomes to be deleted: %d", len(unwanted_genomes))    

    if new_genomes:
        new_genomes = sorted(new_genomes)
        logger.info("Start downloading new genomes.")
        download_genomes_parallel(new_genomes, out_dir=out_dir, threads=threads)    
        logger.info("Retrieved %d genomes.", len(new_genomes))
    if unwanted_genomes:
        logger.info("Start deleting unwanted genomes.")
        unwanted_genomes = sorted(unwanted_genomes)
        delete_unwanted_genomes(unwanted_genomes, out_dir)
        logger.info("Deleted %d genomes.", len(unwanted_genomes))
    logger.info("===== Completed downloading reference genomes =====")


if __name__ == '__main__':

    def parse_args():
        parser = ArgumentParser()
        parser.add_argument(
            "--asm", type=str, required=True, metavar="PATH",
            help="Assembly report file [required]"
        )
        parser.add_argument(
            "--ani", type=str, required=True, metavar="PATH",
            help="ANI report file [required]"
        )
        parser.add_argument(
            "--ts", type=str, required=False, metavar="PATH",
            help="Type strain report"
        )
        parser.add_argument(
            "-o", "--out_dir", default=None, type=str, metavar="PATH",
            help="Output directory (default: REFERENCE_GENOME_DIR)"
        )
        args = parser.parse_args()
        return args

    args = parse_args()
    download_all_genomes(asm_report=args.asm, ani_report=args.ani, type_strain_report=args.ts, out_dir=args.out_dir)
    "dev/asm_report_300.txt"