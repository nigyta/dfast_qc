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
    if os.path.exists(ete3_db_file):
        logger.info("Delete existing ETE3 database (%s)", ete3_db_file)
        os.remove(ete3_db_file)
    if not os.path.exists(ete3_db_file):
        open(ete3_db_file, "w")  # create an empty file if not exists
    logger.info("Preparing ETE3 database (%s)", ete3_db_file)
    _ = NCBITaxa(dbfile=ete3_db_file, taxdump_file=ncbi_taxdump_file)
    return ete3_db_file


def main():
    out_dir = config.DQC_REFERENCE_DIR
    logger.info("===== Update NCBI taxdump =====")
    ncbi_taxdump_file = download_taxdump(out_dir)
    update_ete3_db(out_dir, ncbi_taxdump_file)
    logger.info("===== Completed updating NCBI taxdump =====")
