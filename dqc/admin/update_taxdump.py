import os
import subprocess
from io import StringIO
from ete3 import NCBITaxa
from ..common import get_logger
from ..config import config
from ..models import Taxon, db
from .download_master_files import download_file

logger = get_logger(__name__)

# def init_ete3_db():
#     ref_dir = config.DQC_REFERENCE_DIR
#     ncbi_taxdump_file = download_taxdump(out_dir)
#     update_ete3_db(ref_dir, ncbi_taxdump_file)

def download_taxdump(out_dir):
    ncbi_taxdump_url = config.URLS["taxdump"]
    ncbi_taxdump_base_name = os.path.basename(ncbi_taxdump_url)
    logger.info("Downloading NCBI taxdump (%s)", ncbi_taxdump_base_name)
    download_file(ncbi_taxdump_url, out_dir)
    ncbi_taxdump_file = os.path.join(out_dir, ncbi_taxdump_base_name)
    return ncbi_taxdump_file

def update_ete3_db(out_dir, ncbi_taxdump_file):
    ete3_db_file = os.path.join(out_dir, config.ETE3_SQLITE_DB)
    logger.info("Updating ETE3 database (%s)", ete3_db_file)
    if not os.path.exists(ete3_db_file):
        open(ete3_db_file, "w")  # create an empty file if not exists
    _ = NCBITaxa(dbfile=ete3_db_file, taxdump_file=ncbi_taxdump_file)
    return ete3_db_file

def update_taxon_table_for_checkM():
    def _run_checkm_taxon_list():
        cmd = ["checkm", "taxon_list"]
        p = subprocess.run(cmd, shell=False, encoding='utf-8', stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if p.returncode != 0:
            logger.error("Error. Cannot get CheckM taxon list.\n%s", p.stdout)
            exit(1)
        return p.stdout

    # To avoid db-not-found error, ete3 is imported here.
    from ..ete3_helper import get_taxid

    # Drop and re-create Taxon table.
    logger.info("Preparing Taxon table for CheckM.")
    Taxon.drop_table()
    db.create_tables([Taxon])

    ret = _run_checkm_taxon_list()
    header_cnt = 0
    f = StringIO(ret)
    while header_cnt < 2:
        line = next(f)
        if line.startswith("---"):
            header_cnt += 1
    taxids = []
    for line in f:
        if line.startswith("---"):
            break
        rank, *taxon, genomes, marker_genes, marker_sets = line.strip().split()
        taxon = " ".join(taxon)
        if rank == "life": # for Prokaryote
            taxid = 0
        else:
            taxid = get_taxid(taxon, rank)
        if not taxid is None:
            logger.debug("Inserting record: <%d: %s (%s)>", taxid, taxon, rank) 
            if taxid in taxids:
                logger.warning("Taxid %d already exists. Skip inserting a record for '%s (%s)'.", taxid, taxon, rank)
            else:
                Taxon.create(taxid=taxid, rank=rank, taxon=taxon, 
                    genomes=int(genomes), marker_genes=int(marker_genes), marker_sets=int(marker_sets))
                taxids.append(taxid)
    logger.info("Inserted %d records.", len(taxids))

def main():
    out_dir = config.DQC_REFERENCE_DIR
    logger.info("===== Update NCBI taxdump =====")
    ncbi_taxdump_file = download_taxdump(out_dir)
    update_ete3_db(out_dir, ncbi_taxdump_file)
    update_taxon_table_for_checkM()
    logger.info("===== Completed updating NCBI taxdump =====")
