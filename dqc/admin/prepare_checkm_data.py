import os
import shutil
from ..common import get_logger, run_command, get_ref_path, safe_tar_extraction
from ..config import config
from .download_master_files import download_file

logger = get_logger(__name__)


def extract_data_file(target_tarfile, data_root, delete_existing_data=False):
    data_manifest = os.path.join(data_root, ".dmanifest")
    if os.path.exists(data_manifest) and not delete_existing_data:
        logger.warning("Data already exists. Data extraction is skipped.")
    else:
        safe_tar_extraction(target_tarfile, data_root)
        logger.info("CheckM data is extracted to %s", data_root)

def download_checkm_data_if_not_exist(out_dir, delete_existing_data=False):
    checkm_data_url = config.URLS["checkm"]
    checkm_data_file_base = os.path.basename(checkm_data_url)
    checkm_data_tarfile = os.path.join(out_dir, checkm_data_file_base)
    if not os.path.exists(checkm_data_tarfile):
        logger.warning("CheckM data file (%s) does not exist. WIll try to download.", checkm_data_file_base)
        download_file(checkm_data_url, out_dir)
    elif delete_existing_data:
        logger.warning("Re-downloading CheckM data file (%s).", checkm_data_file_base)
        download_file(checkm_data_url, out_dir)
    return checkm_data_tarfile

def check_data_directory(out_dir, delete_existing_data=False):
    checkm_data_root = os.path.join(out_dir, config.CHECKM_DATA_ROOT)
    if os.path.exists(checkm_data_root) and delete_existing_data:
        shutil.rmtree(checkm_data_root)
    os.makedirs(checkm_data_root, exist_ok=True)
    return checkm_data_root

def set_root(data_root):
    cmd = ["checkm", "data", "setRoot", data_root]
    run_command(cmd)
    logger.info("Data root is set to %s", data_root)
    
def main(delete_existing_data=False):
    out_dir = config.DQC_REFERENCE_DIR
    logger.info("===== Prepare CheckM data root =====")

    checkm_data_tarfile = download_checkm_data_if_not_exist(out_dir, delete_existing_data=delete_existing_data)
    checkm_data_root = check_data_directory(out_dir, delete_existing_data=delete_existing_data)
    extract_data_file(checkm_data_tarfile, checkm_data_root, delete_existing_data=delete_existing_data)
    set_root(checkm_data_root)
    logger.info("===== Completed preparing CheckM data root =====")
