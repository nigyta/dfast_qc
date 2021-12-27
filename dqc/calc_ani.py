import sys
import os
from .common import get_logger, run_command
from argparse import ArgumentError, ArgumentParser
from .models import Reference
from .config import config
from .download_files import download_genomes_parallel
from .classify_tc_hits import classify_tc_hits

logger = get_logger(__name__)

ani_threshold = config.ANI_THRESHOLD

def check_fasta_existence(reference_list_file):
    """
    Check if reference genomes exist. If not, missing genomes will be downloaded from AssemblyDB.
    """
    reference_files = open(reference_list_file).readlines()
    reference_files = [fn.strip() for fn in reference_files]
    missing_genomes = []
    existing_genomes = []
    for file_name in reference_files:
        if not os.path.exists(file_name):
            base_name = os.path.basename(file_name)
            accession = base_name.replace(".fna.gz", "")
            logger.warning("%s does not exist.", base_name)
            missing_genomes.append(accession)
        else:
            existing_genomes.append(file_name)
    num_threads = config.NUM_THREADS
    if not missing_genomes:
        return
    if config.AUTO_DOWNLOAD:
        logger.info("Will try to download missing genomes.")
        download_genomes_parallel(missing_genomes, threads=num_threads)
    else:
        # Remove missing target genomes
        missing_genomes = ",".join(missing_genomes)
        logger.info(f"Remove missing genomes from the reference list. [{missing_genomes}]")
        with open(reference_list_file, "w") as f:
            f.write("\n".join(existing_genomes))

def run_fastani(input_file, reference_list_file, output_file):
    num_threads = config.NUM_THREADS
    cmd = ["fastANI", "--query", input_file, "--refList", reference_list_file, "--output", output_file, "--threads", str(num_threads)]
    run_command(cmd, task_name="fastANI")

def add_organism_info_to_fastani_result(fastani_result_file, output_file):
    # parse fastANI result and add organism info
    # also, result dict will be generated
    header = ["organism_name", "strain", "accession", "taxid", "species_taxid", "relation_to_type", "validated", "ani", "matched_fragments", "total_fragments", "status"]
    ret = "\t".join(header) + "\n"
    hit_cnt, hit_cnt_above_cutoff = 0, 0
    tc_result = []
    for line in open(fastani_result_file):
        cols = line.strip("\n").split("\t")
        target_file, ani_value, matched_frag, total_frag = cols[1], float(cols[2]), int(cols[3]), int(cols[4])
        accession = os.path.basename(target_file).replace(".fna.gz", "")
        ref = Reference.get_or_none(Reference.accession==accession)
        if ref:
            organism_name, strain, relation_to_type_material = ref.organism_name, ref.infraspecific_name, ref.relation_to_type_material
            taxid, species_taxid, validated = ref.taxid, ref.species_taxid, ref.is_valid
        else:
            organism_name, strain, relation_to_type_material = accession, "-", "-"
            taxid, species_taxid, validated = "-", "-", "-"
        hit_cnt += 1
        if ani_value > ani_threshold:
            hit_cnt_above_cutoff += 1
        result_row = [organism_name, strain, accession, taxid, species_taxid, relation_to_type_material, validated, ani_value, matched_frag, total_frag, ""]
        ret_dict = {key: value for key, value in zip(header, result_row)}
        tc_result.append(ret_dict)
    status = classify_tc_hits(tc_result)
    logger.info("Found %d fastANI hits (%d hits with ANI > %d%%)", hit_cnt, hit_cnt_above_cutoff, ani_threshold)
    logger.info("The taxonomy check result is classified as '%s'.", status)
    for result in tc_result:
        ret += "\t".join([str(result[key]) for key in header]) + "\n"
    logger.info("DFAST Taxonomy check final result\n%s\n%s%s", "-"*80, ret, "-"*80)
    with open(output_file, "w") as f:
        f.write(ret)
    logger.info("DFAST Taxonomy check result was written to %s", output_file)
    return tc_result    

def main(query_fasta, reference_list, out_dir):
    fastani_result_file = os.path.join(out_dir, config.FASTANI_RESULT)
    dqc_result_file = os.path.join(out_dir, config.TC_RESULT)

    check_fasta_existence(reference_list)
    run_fastani(query_fasta, reference_list, fastani_result_file)
    tc_result = add_organism_info_to_fastani_result(fastani_result_file, dqc_result_file)
    if not config.DEBUG:
        os.remove(fastani_result_file)
    return tc_result

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

