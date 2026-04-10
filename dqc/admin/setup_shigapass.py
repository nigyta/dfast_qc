import os
import shutil
import tempfile
from ..common import get_logger, run_command
from ..config import config

logger = get_logger(__name__)

SHIGAPASS_REPO_URL = "https://github.com/imanyass/ShigaPass.git"
SHIGAPASS_LICENSE_URL = "https://raw.githubusercontent.com/imanyass/ShigaPass/main/LICENSE"


def setup_shigapass():
    out_dir = os.path.join(config.DQC_REFERENCE_DIR, "shigapass")
    script_dest = os.path.join(config.DQC_REFERENCE_DIR, config.SHIGAPASS_SCRIPT)
    db_dest = os.path.join(config.DQC_REFERENCE_DIR, config.SHIGAPASS_DB_DIR)

    logger.info("===== Setup ShigaPass =====")
    logger.info("ShigaPass will be installed to: %s", out_dir)

    os.makedirs(out_dir, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        clone_dir = os.path.join(tmpdir, "ShigaPass")
        logger.info("Cloning ShigaPass repository from %s", SHIGAPASS_REPO_URL)
        run_command(["git", "clone", SHIGAPASS_REPO_URL, clone_dir])

        # Copy ShigaPass.sh
        src_script = os.path.join(clone_dir, "SCRIPT", "ShigaPass.sh")
        logger.info("Copying ShigaPass.sh to %s", script_dest)
        shutil.copy2(src_script, script_dest)
        os.chmod(script_dest, 0o755)

        # Copy ShigaPass_DataBases
        src_db = os.path.join(clone_dir, "SCRIPT", "ShigaPass_DataBases")
        if os.path.exists(db_dest):
            logger.info("Removing existing ShigaPass_DataBases directory: %s", db_dest)
            shutil.rmtree(db_dest)
        logger.info("Copying ShigaPass_DataBases to %s", db_dest)
        shutil.copytree(src_db, db_dest)

        # Copy LICENSE file for redistribution
        src_license = os.path.join(clone_dir, "LICENSE")
        dest_license = os.path.join(out_dir, "LICENSE")
        if os.path.exists(src_license):
            logger.info("Copying LICENSE to %s", dest_license)
            shutil.copy2(src_license, dest_license)
        else:
            logger.warning("LICENSE file not found in the repository.")

    logger.info("===== ShigaPass setup complete =====")
