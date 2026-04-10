import os
import glob
import gzip
import shutil
import csv

from .config import config
from .common import get_logger, run_command, get_ref_path

logger = get_logger(__name__)

_SHIGAPASS_TARGETS = ["escherichia coli", "shigella"]


def _is_shigapass_target(organism_name):
    """Check if organism_name contains a ShigaPass-relevant genus."""
    return any(organism_name.lower().startswith(target) for target in _SHIGAPASS_TARGETS)


def should_run_shigapass(tc_result):
    """Check if ShigaPass should run.

    Requires both conditions:
    1. Any hit in tc_result has an Escherichia/Shigella organism_name.
    2. The status is 'indistinguishable'.
    """
    if not tc_result:
        return False
    if tc_result[0].get("status") != "indistinguishable":
        return False
    return any(_is_shigapass_target(hit.get("organism_name", "")) for hit in tc_result)


def _needs_db_init():
    """Check if ShigaPass BLAST databases need initialization."""
    db_dir = get_ref_path(config.SHIGAPASS_DB_DIR)
    for subdir in ["IPAH", "RFB", "FLIC", "CRISPR", "MLST"]:
        fasta_files = glob.glob(os.path.join(db_dir, subdir, "*.fasta"))
        if fasta_files:
            # Check if corresponding .ndb or .nhr exists
            ndb = fasta_files[0] + ".ndb"
            nhr = fasta_files[0] + ".nhr"
            if not os.path.exists(ndb) and not os.path.exists(nhr):
                return True
    return False


def _prepare_input(input_file, out_dir):
    """Prepare input for ShigaPass: decompress if gzipped, create input list file.

    Returns:
        tuple: (input_list_file, temp_fasta) where temp_fasta is the decompressed
               file path (or None if no decompression was needed).
    """
    temp_fasta = None
    if input_file.endswith(".gz"):
        # Decompress to output directory
        base_name = os.path.basename(input_file).replace(".gz", "")
        temp_fasta = os.path.join(out_dir, base_name)
        with gzip.open(input_file, "rb") as f_in:
            with open(temp_fasta, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)
        fasta_path = temp_fasta
    else:
        fasta_path = os.path.abspath(input_file)

    # Create input list file for ShigaPass
    input_list_file = os.path.join(out_dir, "shigapass_input_list.txt")
    with open(input_list_file, "w") as f:
        f.write(fasta_path + "\n")

    return input_list_file, temp_fasta


_SEROTYPE_PREFIX_TO_ORGANISM = {
    "SB": "Shigella boydii",
    "SD": "Shigella dysenteriae",
    "SF": "Shigella flexneri",
    "SS": "Shigella sonnei",
}


def _derive_organism(predicted_serotype):
    """Derive organism name from the Predicted_Serotype prefix."""
    if predicted_serotype and len(predicted_serotype) >= 2:
        prefix = predicted_serotype[:2]
        if prefix in _SEROTYPE_PREFIX_TO_ORGANISM:
            return _SEROTYPE_PREFIX_TO_ORGANISM[prefix]
    return "Escherichia coli"


def parse_summary(summary_file):
    """Parse the semicolon-delimited ShigaPass_summary.csv into a dict."""
    if not os.path.exists(summary_file):
        logger.warning("ShigaPass summary file not found: %s", summary_file)
        return {}

    with open(summary_file) as f:
        reader = csv.reader(f, delimiter=";")
        header = next(reader, None)
        if header is None:
            return {}
        row = next(reader, None)
        if row is None:
            return {}

    # Header: Name;rfb;rfb_hits,(%);MLST;fliC;CRISPR;ipaH;Predicted_Serotype;Predicted_FlexSerotype;Comments
    csv_keys = ["name", "rfb", "rfb_hits", "MLST", "fliC", "CRISPR", "ipaH",
                "Predicted_Serotype", "Predicted_FlexSerotype", "Comments"]

    values = {}
    for i, key in enumerate(csv_keys):
        values[key] = row[i] if i < len(row) else ""

    # Build result with organism inserted after ipaH
    result = {}
    for key in csv_keys:
        result[key] = values[key]
        if key == "ipaH":
            result["organism"] = _derive_organism(values.get("Predicted_Serotype", ""))
    return result


def parse_flex_summary(flex_summary_file):
    """Parse the ShigaPass_Flex_summary.csv if it exists."""
    if not os.path.exists(flex_summary_file):
        return {}

    with open(flex_summary_file) as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    if not rows:
        return {}

    # Flex summary format: FastaName;phage_genes;FlexSerotype
    row = rows[0]
    return {
        "name": row[0] if len(row) > 0 else "",
        "phage_genes": row[1:-1] if len(row) > 2 else [],
        "flex_serotype": row[-1] if len(row) > 1 else "",
    }


def run():
    """Run ShigaPass analysis.

    Returns:
        dict: ShigaPass result with keys: name, rfb, rfb_hits, mlst, fliC, crispr,
              ipaH, predicted_serotype, predicted_flex_serotype, comments.
    """
    input_file = config.QUERY_GENOME
    out_dir = config.OUT_DIR
    shigapass_out_dir = os.path.join(out_dir, config.SHIGAPASS_OUTPUT_DIR)

    logger.info("===== Start ShigaPass serotype prediction =====")

    # Auto-install ShigaPass if the script is not found
    shigapass_script = get_ref_path(config.SHIGAPASS_SCRIPT)
    if not os.path.exists(shigapass_script):
        logger.info("ShigaPass script not found. Running setup_shigapass to install it.")
        from .admin.setup_shigapass import setup_shigapass
        setup_shigapass()

    # Prepare input
    input_list_file, temp_fasta = _prepare_input(input_file, out_dir)

    # Build command
    cmd = [
        "bash", shigapass_script,
        "-l", input_list_file,
        "-o", shigapass_out_dir,
        "-p", get_ref_path(config.SHIGAPASS_DB_DIR),
        "-t", str(config.NUM_THREADS),
    ]

    # Check if BLAST databases need initialization
    if _needs_db_init():
        logger.info("ShigaPass BLAST databases not found. Initializing with -u flag.")
        cmd.append("-u")

    run_command(cmd, task_name="ShigaPass")

    # Parse results
    summary_file = os.path.join(shigapass_out_dir, config.SHIGAPASS_SUMMARY)
    result = parse_summary(summary_file)

    flex_summary_file = os.path.join(shigapass_out_dir, config.SHIGAPASS_FLEX_SUMMARY)
    flex_result = parse_flex_summary(flex_summary_file)
    if flex_result:
        result["flex_result"] = flex_result

    # Cleanup temp files
    if temp_fasta and os.path.exists(temp_fasta):
        os.remove(temp_fasta)
    if os.path.exists(input_list_file):
        os.remove(input_list_file)

    logger.info("===== ShigaPass serotype prediction completed =====")
    return result
