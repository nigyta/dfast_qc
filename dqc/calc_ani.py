import sys
import os
from .common import get_logger, run_command
from argparse import ArgumentError, ArgumentParser
from .models import Reference
from .config import config
from .download_files import download_genomes_parallel

logger = get_logger(__name__)

ani_cutoff = 95

def check_fasta_existence(reference_list_file):
    """
    Check if reference genomes exist. If not, missing genomes will be downloaded from AssemblyDB.
    """
    reference_files = open(reference_list_file).readlines()
    reference_files = [_.strip() for _ in reference_files]
    missing_genomes = []
    for file_name in reference_files:
        if not os.path.exists(file_name):
            base_name = os.path.basename(file_name)
            accession = base_name.replace(".fna.gz", "")
            logger.warning("%s does not exist. Will try to download.", base_name)
            missing_genomes.append(accession)
    num_threads = config.FASTANI_THREADS
    download_genomes_parallel(missing_genomes, threads=num_threads)

def run_fastani(input_file, reference_list_file, output_file):
    num_threads = config.FASTANI_THREADS
    cmd = ["fastANI", "--query", input_file, "--refList", reference_list_file, "--output", output_file, "--threads", str(num_threads)]
    run_command(cmd, task_name="fastANI")

def add_organism_info_to_fastani_result(fastani_result_file, output_file):
    ret, hit_cnt, hit_cnt_above_cutoff = "", 0, 0
    for line in open(fastani_result_file):
        cols = line.strip("\n").split("\t")
        target_file = cols[1]
        accession = os.path.basename(target_file).replace(".fna.gz", "")
        ref = Reference.get_or_none(Reference.accession==accession)
        if ref:
            organism_name, strain, is_type = ref.organism_name, ref.infraspecific_name, ref.relation_to_type_material
            is_valid = "TRUE" if ref.is_valid else "FALSE"
        else:
            organism_name, strain, is_type, is_valid = accession, "-", "-", "FALSE"
        hit_cnt += 1
        ani_value = float(cols[2])
        if ani_value > ani_cutoff:
            hit_cnt_above_cutoff += 1
        ret += "\t".join([organism_name, strain, is_type, is_valid, cols[2], cols[3], cols[4]]) + "\n"
    with open(output_file, "w") as f:
        f.write(ret)
    logger.info("Found %d fastANI hits (%d hits with ANI > %d%%)", hit_cnt, hit_cnt_above_cutoff, ani_cutoff)
    logger.info("DFAST Taxonomy check final result\n%s\n%s%s", "-"*80, ret, "-"*80)
    

def main(query_fasta, reference_list, out_dir):
    fastani_result_file = os.path.join(out_dir, config.FASTANI_RESULT)
    dqc_result_file = os.path.join(out_dir, config.DQC_RESULT)
    dqc_result_file_json = os.path.join(out_dir, config.DQC_RESULT_JSON)

    check_fasta_existence(reference_list)
    run_fastani(query_fasta, reference_list, fastani_result_file)
    add_organism_info_to_fastani_result(fastani_result_file, dqc_result_file)
    if not config.DEBUG:
        os.remove(fastani_result_file)
    logger.info("DFAST Taxonomy check result was written to %s", dqc_result_file)
    logger.info("DFAST Taxonomy check result json was written to %s", dqc_result_file_json)

if __name__ == '__main__':

    def parse_args():
        parser = ArgumentParser()
        parser.add_argument(
            "-i",
            "--input",
            type=str,
            required=True,
            help=f"Input FATA file [required]",
            metavar="PATH"
        )
        parser.add_argument(
            "-rl",
            "--reference_list",
            type=str,
            required=True,
            help="Reference list file [required]",
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
            '--debug',
            action='store_true',
            help='Debug mode'
        )
        args = parser.parse_args()
        return args

    args = parse_args()
    # check_fasta_existence(args.reference_list)
    main(args.input, args.reference_list, args.out_dir)

