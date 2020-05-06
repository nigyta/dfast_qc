import os
from ..common import get_logger
from ..config import config
from ..models import Reference, init_db
from .asm_report_parser import Assembly
from .ani_report_parser import get_filtered_ANI_report
logger = get_logger(__name__)

def clean_organism_name(asm_rep, ani_rep):

    is_filtered, is_valid = ani_rep.validate()
    organism_name = asm_rep.organism_name
    infraspecific_name = asm_rep.infraspecific_name
    infraspecific_name = infraspecific_name.replace("strain=", "").strip()
    if ";" in infraspecific_name:
        infraspecific_name = infraspecific_name.split(";")[0].strip()
    if "=" in organism_name:
        organism_name = organism_name.split("=")[0].strip()
    if organism_name.endswith(infraspecific_name):
        organism_name = organism_name.replace(infraspecific_name, "").strip(" =")
        if organism_name.endswith("str."):
            organism_name = organism_name.replace("str.", "").strip(" =")
        elif organism_name.endswith("strain"):
            organism_name = organism_name.replace("strain", "").strip(" =")
    return organism_name, infraspecific_name, is_filtered, is_valid

def prepare_sqlite_db(asm_report=None, ani_report=None, type_strain_report=None, out_dir=None):
    logger.info("===== Prepare SQLite DB file (references.db) =====")
    if asm_report is None:
        asm_report = config.ASSEMBLY_REPORT_FILE
    if ani_report is None:
        ani_report = config.ANI_REPORT_FILE
    if type_strain_report is None:
        type_strain_report = config.TYPE_STRAIN_REPORT_FILE
    if out_dir is None:
        out_dir = config.DQC_REFERENCE_DIR
    logger.debug("%s\t%s\t%s\t%s", asm_report, ani_report, type_strain_report, out_dir)

    # check output file (delete and regenerate)
    output_sqlitedb_file = os.path.join(out_dir, os.path.basename(config.SQLITE_REFERENCE_DB))
    if os.path.exists(output_sqlitedb_file):
        os.remove(output_sqlitedb_file)
        logger.warning("Removed existing DB file [%s]", output_sqlitedb_file)

    init_db()
    logger.info("SQLite DB will be created in %s", output_sqlitedb_file)

    target_reports = get_filtered_ANI_report(ani_report)
    cnt = 0
    for asm_rep in Assembly.parse(asm_report):
        if asm_rep.assembly_accession in target_reports:
            ani_rep = target_reports[asm_rep.assembly_accession]
            organism_name, infraspecific_name, is_filtered, is_valid = clean_organism_name(asm_rep, ani_rep)
            cnt += 1
            Reference.create(
                accession=asm_rep.assembly_accession,
                taxid=ani_rep.taxid,
                species_taxid=ani_rep.species_taxid,
                organism_name=organism_name,
                species_name=ani_rep.species_name,
                infraspecific_name=infraspecific_name,
                relation_to_type_material=ani_rep.assembly_type_category,
                is_valid=is_valid
            )
    logger.info("Inserted %d Reference records.", cnt)

    logger.info("===== Completed preparing SQLite DB file =====")
