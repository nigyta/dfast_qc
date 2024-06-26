import sys
import os
from .common import get_logger, run_command, get_ref_path
from argparse import ArgumentError, ArgumentParser
from .models import Reference, GTDB_Reference
from .config import config
from .download_files import download_genomes_parallel
from .classify_tc_hits import classify_tc_hits , classify_tc_hits_GTDB
import shutil

logger = get_logger(__name__)

default_ani_threshold = config.ANI_THRESHOLD

def check_fasta_existence(reference_list_file, for_gtdb=False):
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
            accession = base_name.replace(".fna.gz", "").replace("_genomic", "")  # Trimming "_genomic" for GTDB genomes.
            logger.warning("%s does not exist.", base_name)
            missing_genomes.append(accession)
        else:
            existing_genomes.append(file_name)
    num_threads = config.NUM_THREADS
    if not missing_genomes:
        return
    if config.AUTO_DOWNLOAD:
        logger.info("Will try to download missing genomes.")
        download_genomes_parallel(missing_genomes, threads=num_threads, for_gtdb=for_gtdb)
    else:
        # Remove missing target genomes
        missing_genomes = ",".join(missing_genomes)
        logger.info(f"Remove missing genomes from the reference list. [{missing_genomes}]")
        with open(reference_list_file, "w") as f:
            f.write("\n".join(existing_genomes))

def get_species_specific_threshold():
    ani_species_specific_threshold_file = get_ref_path(config.SPECIES_SPECIFIC_THRESHOLD)
    logger.info("Loading species specific ANI threshold from %s", ani_species_specific_threshold_file)
    D = {}
    if not os.path.exists(ani_species_specific_threshold_file):
        logger.warning("Species-specific ANI threshold file not found. Will use the default threshold for all species. [%s]", ani_species_specific_threshold_file)
        return D
    for line in open(ani_species_specific_threshold_file):
        if line.startswith("#"):
            continue
        cols = line.strip("\n").split("\t")
        species_taxid = int(cols[0])
        ani_threshold = float(cols[2])
        D[species_taxid] = ani_threshold
    return D

def run_skani(input_file, reference_list_file,skani_result_file,skani_database):
    num_threads = config.NUM_THREADS
    cmd_sketch = ["skani", "sketch", "-l",reference_list_file,"-o",skani_database,"-t",str(num_threads)]
    cmd_skani = ["skani", "search", input_file, "-d",skani_database,"-o",skani_result_file,"-t",str(num_threads)]
    run_command(cmd_sketch, task_name="skani_sketch")
    run_command(cmd_skani, task_name="skani_search")

def add_organism_info_to_skani_result(skani_result_file, output_file):

    # Read the content of the original file, skipping the first line
    with open(skani_result_file, 'r') as original_file:
        lines = original_file.readlines()[1:]

    # Write the modified content to the new file
    with open(skani_result_file, 'w') as new_file:
        new_file.writelines(lines)
    
    # parse Skani result and add organism info
    # also, result dict will be generated

    dict_species_specific_threthold = get_species_specific_threshold()

    header = ["organism_name", "strain", "accession", "taxid", "species_taxid", "relation_to_type", "validated", "ani", "align_fraction_ref", "align_fraction_query", "ani_threshold", "status"]
    ret = "\t".join(header) + "\n"
    hit_cnt, hit_cnt_above_cutoff = 0, 0
    tc_result = []
    for line in open(skani_result_file):
        cols = line.strip("\n").split("\t")
        target_file, ani_value, align_fraction_ref, align_fraction_query  = cols[0], float(cols[2]), float(cols[3]), float(cols[4])
        accession = os.path.basename(target_file).replace(".fna.gz", "")
        ref = Reference.get_or_none(Reference.accession==accession)
        if ref:
            organism_name, strain, relation_to_type_material = ref.organism_name, ref.infraspecific_name, ref.relation_to_type_material
            taxid, species_taxid, validated = ref.taxid, ref.species_taxid, ref.is_valid
        else:
            organism_name, strain, relation_to_type_material = accession, "-", "-"
            taxid, species_taxid, validated = "-", "-", "-"
        hit_cnt += 1
        ani_threshold = dict_species_specific_threthold.get(species_taxid, default_ani_threshold)
        if ani_value > ani_threshold:
            hit_cnt_above_cutoff += 1
        result_row = [organism_name, strain, accession, taxid, species_taxid, relation_to_type_material, validated, ani_value, align_fraction_ref, align_fraction_query, ani_threshold, ""]
        ret_dict = {key: value for key, value in zip(header, result_row)}
        tc_result.append(ret_dict)
    status = classify_tc_hits(tc_result)
    logger.info("Found %d ANI hits (%d hits with ANI > threshold)", hit_cnt, hit_cnt_above_cutoff)
    logger.info("The taxonomy check result is classified as '%s'.", status)
    for result in tc_result:
        ret += "\t".join([str(result[key]) for key in header]) + "\n"
    logger.info("DFAST Taxonomy check final result\n%s\n%s%s", "-"*80, ret, "-"*80)
    with open(output_file, "w") as f:
        f.write(ret)
    logger.info("DFAST Taxonomy check result was written to %s", output_file)
    return tc_result    

def add_organism_info_to_skani_result_for_gtdb(skani_result_file, output_file):

    # Read the content of the original file, skipping the first line
    with open(skani_result_file, 'r') as original_file:
        lines = original_file.readlines()[1:]

    # Write the modified content to the new file
    with open(skani_result_file, 'w') as new_file:
        new_file.writelines(lines)
    
    # parse Skani result and add organism info
    # also, result dict will be generated
    header = ["accession", "gtdb_species", "ani", "align_fraction_ref", "align_fraction_query", 
        "gtdb_taxonomy", "ani_circumscription_radius", "mean_intra_species_ani", "min_intra_species_ani",
        "mean_intra_species_af", "min_intra_species_af", "num_clustered_genomes", "status"]
    ret = "\t".join(header) + "\n"
    hit_cnt, hit_cnt_above_cutoff = 0, 0
    gtdb_result = []
    for line in open(skani_result_file):
        cols = line.strip("\n").split("\t")
        target_file, ani_value, align_fraction_ref, align_fraction_query  = cols[0], float(cols[2]), float(cols[3]), float(cols[4])
        accession = os.path.basename(target_file).replace("_genomic.fna.gz", "")
        ref = GTDB_Reference.get_or_none(GTDB_Reference.accession==accession)
        if ref:
            gtdb_species, gtdb_taxonomy, ani_circumscription_radius = ref.gtdb_species, ref.gtdb_taxonomy, ref.ani_circumscription_radius
            mean_intra_species_ani, min_intra_species_ani, mean_intra_species_af = ref.mean_intra_species_ani, ref.min_intra_species_ani, ref.mean_intra_species_af
            min_intra_species_af, num_clustered_genomes, status = ref.min_intra_species_af, ref.num_clustered_genomes, "-" # ref.clustered_genomes
        else:
            gtdb_species, gtdb_taxonomy, ani_circumscription_radius = "-", "-", "-"
            mean_intra_species_ani, min_intra_species_ani, mean_intra_species_af = "-", "-", "-"
            min_intra_species_af, num_clustered_genomes, status = "-", "-", "-"
        hit_cnt += 1
        if ani_value > ani_circumscription_radius:
            hit_cnt_above_cutoff += 1
        result_row = [accession, gtdb_species, ani_value, align_fraction_ref, align_fraction_query,
            gtdb_taxonomy, ani_circumscription_radius, mean_intra_species_ani, min_intra_species_ani,
            mean_intra_species_af, min_intra_species_af, num_clustered_genomes, status]
        ret_dict = {key: value for key, value in zip(header, result_row)}
        gtdb_result.append(ret_dict)
    status = classify_tc_hits_GTDB(gtdb_result)
    logger.info("Found %d ANI hits (%d hits with ANI > circumscription radius)", hit_cnt, hit_cnt_above_cutoff)
    # logger.info("The taxonomy check result is classified as '%s'.", status)
    for result in gtdb_result:
        ret += "\t".join([str(result[key]) for key in header]) + "\n"
    logger.info("GTDB search result\n%s\n%s%s", "-"*80, ret, "-"*80)
    with open(output_file, "w") as f:
        f.write(ret)
    logger.info("GTDB search result was written to %s", output_file)
    return gtdb_result

def main(query_fasta, reference_list, out_dir, for_gtdb=False):
    if for_gtdb:
        skani_result_file = os.path.join(out_dir, config.GTDB_SKANI_RESULT)
        result_file = os.path.join(out_dir, config.GTDB_RESULT)
        skani_database = os.path.join(out_dir, config.SKANI_DATABASE_GTDB)
    else:
        skani_result_file = os.path.join(out_dir, config.SKANI_RESULT)
        result_file = os.path.join(out_dir, config.TC_RESULT)
        skani_database = os.path.join(out_dir, config.SKANI_DATABASE_REF)

    check_fasta_existence(reference_list, for_gtdb=for_gtdb)
    run_skani(query_fasta, reference_list,skani_result_file,skani_database)
    if for_gtdb:
        tc_result = add_organism_info_to_skani_result_for_gtdb(skani_result_file, result_file)
    else:
        tc_result = add_organism_info_to_skani_result(skani_result_file, result_file)
    if not config.DEBUG:
        os.remove(skani_result_file)
        shutil.rmtree(skani_database)
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
    main(args.input, args.reference_list, args.out_dir, for_gtdb=args.for_gtdb)

