import os
from ..common import get_logger, get_ref_path
from ..config import config
from ..models import Reference, init_db, db
from .asm_report_parser import Assembly
from .ani_report_parser import get_filtered_ANI_report
from ..ete3_helper import get_valid_name, get_rank

logger = get_logger(__name__)



def dump_sqlite_db():
    logger.info("===== Dump SQLite DB file =====")

    asm_report = get_ref_path(config.ASSEMBLY_REPORT_FILE)
    ani_report = get_ref_path(config.ANI_REPORT_FILE)
    type_strain_report = get_ref_path(config.TYPE_STRAIN_REPORT_FILE)
    reference_genome_tsv = get_ref_path(config.REFERENCE_GENOMES_TSV)
    

    logger.debug("%s\t%s\t%s", asm_report, ani_report, type_strain_report)

    # check output file (delete and regenerate)
    sqlitedb_file = get_ref_path(config.SQLITE_REFERENCE_DB)
    if not os.path.exists(sqlitedb_file):
        logger.error("SQLiteDB file does not exist. [%s]", sqlitedb_file)

    references = Reference.select()
    dict_species = {}
    for reference in references:
        dict_species.setdefault(reference.species_taxid, []).append(reference)

    logger.info("Number of reference genomes: %s (%s species)", len(references), len(dict_species))

    logger.info("Dumping reference genome list to %s", reference_genome_tsv)

    with open(reference_genome_tsv, "w") as f:
        header = ["accession", "taxid", "species_taxid", "organism_name", "strain", "category_of_type", "validated", "rank"]
        f.write("\t".join(header) + "\n")
        for species_tax_id, list_reference in dict_species.items():
            for reference in list_reference:
                rank = get_rank(reference.taxid)
                f.write("\t".join(reference.to_table() + [rank]) + "\n")

    logger.info("===== Completed dumping SQLite DB file =====")

if __name__ == "__main__":
    dump_sqlite_db()