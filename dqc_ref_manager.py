#!/usr/bin/env python
import os
import sys
import glob
import shutil
import json
import subprocess
from datetime import datetime
from argparse import ArgumentParser
from dqc.config import config
from dqc.common import get_logger, get_ref_inf, get_ref_path

# logger = None

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
    print("download. To be implemented")


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
