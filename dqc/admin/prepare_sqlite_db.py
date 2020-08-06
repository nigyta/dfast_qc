import os
from ..common import get_logger, get_ref_path
from ..config import config
from ..models import Reference, init_db, db
from .asm_report_parser import Assembly
from .ani_report_parser import get_filtered_ANI_report
from ..ete3_helper import get_valid_name

logger = get_logger(__name__)

def clean_organism_name(asm_rep):
    organism_name_org = asm_rep.organism_name
    infraspecific_name = asm_rep.infraspecific_name
    taxid = asm_rep.taxid
    valid_taxid, organism_name = get_valid_name(taxid)
    # logger.debug("%s ==> %s", organism_name_org, organism_name)
    return valid_taxid, organism_name_org, organism_name, infraspecific_name

# def clean_organism_name(asm_rep, ani_rep):

#     is_filtered, is_valid = ani_rep.validate()
#     organism_name = asm_rep.organism_name
#     infraspecific_name = asm_rep.infraspecific_name
#     infraspecific_name = infraspecific_name.replace("strain=", "").strip()
#     if ";" in infraspecific_name:
#         infraspecific_name = infraspecific_name.split(";")[0].strip()
#     if "=" in organism_name:
#         organism_name = organism_name.split("=")[0].strip()
#     if organism_name.endswith(infraspecific_name):
#         organism_name = organism_name.replace(infraspecific_name, "").strip(" =")
#         if organism_name.endswith("str."):
#             organism_name = organism_name.replace("str.", "").strip(" =")
#         elif organism_name.endswith("strain"):
#             organism_name = organism_name.replace("strain", "").strip(" =")
#     return organism_name, infraspecific_name, is_filtered, is_valid

def prepare_sqlite_db():
    logger.info("===== Prepare SQLite DB file (references.db) =====")

    asm_report = get_ref_path(config.ASSEMBLY_REPORT_FILE)
    ani_report = get_ref_path(config.ANI_REPORT_FILE)
    type_strain_report = get_ref_path(config.TYPE_STRAIN_REPORT_FILE)


    logger.debug("%s\t%s\t%s", asm_report, ani_report, type_strain_report)

    # check output file (delete and regenerate)
    output_sqlitedb_file = get_ref_path(config.SQLITE_REFERENCE_DB)
    if os.path.exists(output_sqlitedb_file):
        Reference.drop_table()
        db.create_tables([Reference])
        logger.warning("Dropped and re-created 'Reference' table. [%s]", output_sqlitedb_file)
    else:
        init_db()
        logger.info("New SQLite DB is created. [%s]", output_sqlitedb_file)

    target_reports = get_filtered_ANI_report(ani_report)
    cnt = 0
    for asm_rep in Assembly.parse(asm_report):
        if asm_rep.assembly_accession in target_reports:
            ani_rep = target_reports[asm_rep.assembly_accession]
            # organism_name, infraspecific_name, is_filtered, is_valid = clean_organism_name(asm_rep, ani_rep)
            valid_taxid, organism_name_org, organism_name, infraspecific_name = clean_organism_name(asm_rep)
            if organism_name is None:
                logger.warning("Could not determine valid organism name for %s (%s, taxid=%s)", organism_name_org, asm_rep.assembly_accession, asm_rep.taxid)
                continue
                # organism_name = organism_name_org
            is_filtered, is_valid = ani_rep.validate()
            cnt += 1
            Reference.create(
                accession=asm_rep.assembly_accession,
                taxid=valid_taxid,
                species_taxid=ani_rep.species_taxid,
                organism_name=organism_name,
                species_name=ani_rep.species_name,
                infraspecific_name=infraspecific_name,
                relation_to_type_material=ani_rep.assembly_type_category,
                is_valid=is_valid
            )
    logger.info("Inserted %d Reference records.", cnt)

    logger.info("===== Completed preparing SQLite DB file =====")
