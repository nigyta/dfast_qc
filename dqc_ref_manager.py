#!/usr/bin/env python
import os
import sys
import glob
import shutil
import json
import subprocess
from datetime import datetime
from argparse import ArgumentParser
from urllib.request import urlretrieve
from urllib.error import HTTPError, URLError
from dqc.config import config
from dqc.common import get_logger, get_ref_inf, get_ref_path, safe_tar_extraction

# logger = None

# DQC_REF_URL = "http://localhost:8000/"  # for debug
DQC_REF_URL = "https://dfast.ddbj.nig.ac.jp/static/" #  dqc_reference_compact_latest.tar.gz"

def dump_dqc_reference(args):
    """
    Prepare DQC_REFERENCE_COMPACT data.
    """

    # metadata
    now = datetime.now()
    if args.date:
        if len(args.date) != 8:
            logger.error("Invalid format. Specify date in 'YYYYMMDD'. Aborted.")
            exit(1)
        try:
            dt = datetime.strptime(args.date, "%Y%m%d")
        except ValueError as e:
            logger.error(f"Failed to parse date '{args.date}'. Aborted.")
            exit(1)
    else:
        dt = datetime.now()
    time_stamp = dt.strftime("%Y-%m-%d") 
    ref_type = "compact"
    ref_inf = {"version": time_stamp, "type": ref_type}

    # temporaly output directorey
    tmp_out_dir = "dqc_reference_compact"
    if os.path.exists(tmp_out_dir):
        logger.error(f"'{tmp_out_dir}' already exists. Aborted.")
        exit(1)
    else:
        os.makedirs(tmp_out_dir)

    logger.info("Dumping reference files.")
    ref_file_list = ["INDISTINGUISHABLE_GROUPS_PROKARYOTE", "SPECIES_SPECIFIC_THRESHOLD", 
    "SQLITE_REFERENCE_DB", "ETE3_SQLITE_DB", "REFERENCE_MARKERS_HMM", "GTDB_SPECIES_LIST"]
    # Reference files
    for name in ref_file_list:
        ref_file = get_ref_path(getattr(config, name))
        logger.debug("Copying %s into %s", ref_file, tmp_out_dir)
        shutil.copy(ref_file, tmp_out_dir)

    # Blast DB files
    logger.info("Dumping Blast database files.")
    blast_db_list = ["REFERENCE_MARKERS_FASTA", "GTDB_REFERENCE_MARKERS_FASTA"]
    for name in blast_db_list:
        for db_file_name in glob.glob(get_ref_path(getattr(config, name)) + ".n*"):  # append .n?? for BLAST-DB
            logger.debug("Copying %s into %s", db_file_name, tmp_out_dir)
            shutil.copy(db_file_name, tmp_out_dir)

    # CheckM files
    logger.info("Dumping CheckM reference data.")
    checkm_data_root = get_ref_path(config.CHECKM_DATA_ROOT)
    dest_dir = os.path.join(tmp_out_dir, config.CHECKM_DATA_ROOT)
    logger.debug("Copying %s to %s", checkm_data_root, dest_dir)
    shutil.copytree(checkm_data_root, dest_dir)

    # Writing inf.json file
    out_json_file = os.path.join(tmp_out_dir, config.REFERENCE_INF)
    logger.info("Writing reference info. [version=%s, type=%s]", ref_inf["version"], ref_inf["type"])
    with open(out_json_file, "w") as f:
        json.dump(ref_inf, f)

    # Making tarball
    if args.output:
        # clean args.output and then append .tar.gz
        out_tar_name = args.output.replace(".tar", "").replace(".gz", "") + ".tar.gz"
    else:
        out_tar_name = "dqc_reference_compact.tar.gz"
    logger.info(f"Archiving the reference data into {out_tar_name}")
    subprocess.run(f"tar cfz {out_tar_name} {tmp_out_dir}", shell=True)
    logger.debug("Deleting temporary directory '%s'", tmp_out_dir)
    shutil.rmtree(tmp_out_dir)
    logger.info(f"Done.")

def download_dqc_reference(args):

    # Check input string
    if args.date:
        if len(args.date) != 8:
            logger.error("Invalid format. Specify date in 'YYYYMMDD'. Aborted.")
            exit(1)
        base_name = f"dqc_reference_compact_{args.date}.tar.gz"
    else:
        base_name = "dqc_reference_compact_latest.tar.gz"

    # Check existing data    
    dqc_reference_dir = config.DQC_REFERENCE_DIR
    if os.path.exists(dqc_reference_dir):
    
        ref_inf = get_ref_inf()
        ref_version = ref_inf.get("version", "n.a.")
        ref_type = ref_inf.get("type", "n.a.")
        if ref_type != "compact":
            logger.info("Current version=%s, DB_Type=%s", ref_version, ref_type)
            logger.error("You cannot update '%s' with this script! Please delete the existing directory or specify '--ref_dir' option.", dqc_reference_dir)
            exit(1)
        else:
            logger.info("Try to update existing data '%s'.", dqc_reference_dir)
            logger.info("Current version=%s, DB_Type=%s", ref_version, ref_type)
    else:
        logger.info("Try to download DQC_REFERENCE_COMPACT into a new directory '%s'.", dqc_reference_dir)

    url = DQC_REF_URL + base_name
    tmp_work_dir = "tmp_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    logger.debug("Creating temporary working directory '%s'", tmp_work_dir)
    os.makedirs(tmp_work_dir)
    logger.info("Downloading DQC_REFERENCE_COMPACT from %s", url)
    dest_path = os.path.join(tmp_work_dir, base_name)
    try:
        urlretrieve(url, dest_path)
    except HTTPError as e:
        logger.error("HTTPError. Failed to download resources from %s", url)
        if args.date:
            logger.error("Please check the database version you specified. [%s]", args.date)
        if os.path.exists(tmp_work_dir):
            shutil.rmtree(tmp_work_dir)
        exit(1)
    except URLError as e:
        logger.error("URLError. Failed to download resources from %s", url)
        exit(1)

    logger.info(f"Downloaded {base_name}. Extracting...")
    safe_tar_extraction(dest_path, tmp_work_dir)
    extracted_dir = os.path.join(tmp_work_dir, "dqc_reference_compact")

    if not os.path.exists(dqc_reference_dir):
        logger.info("Creating directory %s", dqc_reference_dir)
        os.makedirs(dqc_reference_dir)

    # copy files
    for file_name in os.listdir(extracted_dir):
        src = os.path.join(extracted_dir, file_name)
        dst = os.path.join(dqc_reference_dir, file_name)
        logger.debug("Moving '%s' to '%s'", src, dst)
        if os.path.exists(dst) and os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.move(src, dst)
    shutil.rmtree(tmp_work_dir)
    ref_inf = get_ref_inf()
    ref_version = ref_inf.get("version", "n.a.")
    ref_type = ref_inf.get("type", "n.a.")
    logger.info("Data retrieved into %s, [version=%s, type=%s]", dqc_reference_dir, ref_version, ref_type)
    logger.info("Please run this script again to update the reference.")

def parse_args():
    parser = ArgumentParser(description="DFAST_QC utility tools for admin.")
    subparsers = parser.add_subparsers(help="")

    # common parser
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument('--debug', action='store_true', help='Debug mode')
    common_parser.add_argument("-r", "--ref_dir", default=None, type=str, metavar="PATH",
        help="DQC reference directory (default: DQC_REFERENCE_DIR)")

    # subparser for dump reference data
    parser_dump = subparsers.add_parser('dump', help="Dump reference data for DQC_REFERENCE_COMPACT into '.tar.gz' file).", parents=[common_parser])
    parser_dump.add_argument("-o", "--output", default=None, type=str, metavar="PATH",
        help="Output file name. ('.tar.gz' will be appended.)")
    parser_dump.add_argument("-d", "--date", default=None, type=str, metavar="YYYYMMDD",
        help="Time stamp for reference data. (default=TODAY)")
    parser_dump.set_defaults(func=dump_dqc_reference)

    # subparser for dump reference data
    parser_download = subparsers.add_parser('download', help='Download/update reference data for DQC_REFERENCE_COMPACT (.tar.gz file).', parents=[common_parser])
    parser_download.add_argument("-v", "--date", default=None, type=str, metavar="YYYYMMDD",
        help="Time stamp of reference data to be downloaded. (default=latest)")
    parser_download.set_defaults(func=download_dqc_reference)


    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        exit()
    return args

if __name__ == "__main__":
    pass
    args = parse_args()
    if args.debug:
        config.DEBUG = True
    if args.ref_dir:
        config.DQC_REFERENCE_DIR = args.ref_dir
    logger = get_logger(__name__)

    args.func(args)
