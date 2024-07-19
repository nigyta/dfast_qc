#!/usr/bin/env python

import os
import sys
from argparse import ArgumentParser
from dqc.config import config

config.ADMIN = True

from dqc.common import get_logger, get_ref_inf
logger = get_logger(__name__)

def check_ref_type(args):
    ref_inf = get_ref_inf()
    ref_type = ref_inf.get("type")
    if ref_type == "compact":
        logger.error(f"You cannot update 'dqc_reference_compact' with this script!")
        exit(1)
    # if ref_type == "compact" and not (args.func == prepare_checkm_data or args.func == update_checkm_db):
        # logger.error(f"'{args.func.__name__}' is not allowed for 'dqc_reference_compact'.")
        # exit(1)
    
def download_master_files(args):
    from dqc.admin.download_master_files import download_master_files
    if args.targets is None:
        target_files = ["asm", "ani", "tsr", "igp", "sst"]
    else:
        target_files = args.targets
    download_master_files(target_files)

def update_taxdump(args):
    from dqc.admin.update_taxdump import main as update_taxdump
    update_taxdump()

def download_genomes(args):
    from dqc.admin.download_all_reference_genomes import download_all_genomes
    download_all_genomes()

def mash_ref_sketch(args):
    from dqc.admin.mash_sketching import sketching
    sketching()

def mash_gtdb_sketch(args):
    from dqc.admin.mash_gtdb_sketching import gtdb_sketching
    gtdb_sketching()

def prepare_sqlite_db(args):
    from dqc.admin.prepare_sqlite_db import prepare_sqlite_db, prepare_sqlite_db_for_gtdb
    if args.for_gtdb:
        prepare_sqlite_db_for_gtdb()
    else:
        prepare_sqlite_db()

def prepare_checkm_data(args):
    from dqc.admin.prepare_checkm_data import main as prepare_checkm_data
    prepare_checkm_data(delete_existing_data=args.delete_existing_data)

def update_checkm_db(args):
    from dqc.admin.update_checkm_db import main as update_checkm_db
    update_checkm_db()

def dump_sqlite_db(args):
    from dqc.admin.dump_sqlite_db import dump_sqlite_db
    dump_sqlite_db()

def prepare_genome_size_data(args):
    from dqc.admin.prepare_genome_size_data import prepare_genome_size_data
    prepare_genome_size_data()

def update_all(args):
    from dqc.admin.download_master_files import download_master_files
    download_master_files(target_files=["asm", "ani", "tsr", "igp", "sst"])
    from dqc.admin.update_taxdump import main as update_taxdump
    update_taxdump()
    from dqc.admin.download_all_reference_genomes import download_all_genomes
    download_all_genomes()
    from dqc.admin.prepare_sqlite_db import prepare_sqlite_db
    prepare_sqlite_db()
    from dqc.admin.update_checkm_db import main as update_checkm_db
    update_checkm_db()
    from dqc.admin.mash_sketching import sketching
    sketching()
    from dqc.admin.prepare_genome_size_data import prepare_genome_size_data
    prepare_genome_size_data()

def parse_args():
    parser = ArgumentParser(description="DFAST_QC utility tools for admin.")
    subparsers = parser.add_subparsers(help="")

    # common parser
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument('--debug', action='store_true', help='Debug mode')
    common_parser.add_argument("-r", "--ref_dir", default=None, type=str, metavar="PATH",
        help="DQC reference directory (default: DQC_REFERENCE_DIR)")
    common_parser.add_argument("-n", "--num_threads", default=1, type=int, metavar="INT",
        help="Number of threads for parallel processing (default:1)")

    # subparser for download master files
    parser_master = subparsers.add_parser('download_master_files', help='Download master files.', parents=[common_parser])
    parser_master.add_argument(
        "--targets", type=str, required=False, metavar="STR", 
        choices=['asm', 'ani', 'tsr', "igp", "sst", "egs", "checkm", "taxdump", "gtdb"], nargs="*",
        help="Target(s) for downloading. " + 
             "[asm: Assembly report, ani: ANI report, tsr: Type strain report,igp: indistinguishable groups prokaryotes, sst: ANI species specific threshold, egs: expected genome size, checkm: CheckM reference data, taxdump: NCBI taxdump.tar.gz, gtdb: GTDB representative species list] "
             "(default: asm ani tsr igp)"
    )
    parser_master.set_defaults(func=download_master_files)

    # subparser for update_taxdump
    parser_update_taxdump = subparsers.add_parser('update_taxdump', help='Update NCBI taxdump data', parents=[common_parser])
    parser_update_taxdump.set_defaults(func=update_taxdump)

    # subparser for download reference genomes
    parser_genome = subparsers.add_parser('download_genomes', help='Download reference genomes from Assembly DB.', parents=[common_parser])
    parser_genome.set_defaults(func=download_genomes)

    # subparser for MASH sketching reference genomes
    parser_sketch_ref = subparsers.add_parser('mash_ref_sketch', help='Sketch the reference genomes.', parents=[common_parser])
    parser_sketch_ref.set_defaults(func=mash_ref_sketch)

    # subparser for MASH sketching GTDB genomes
    parser_sketch_gtdb = subparsers.add_parser('mash_gtdb_sketch', help='Sketch the GTDB genomes.', parents=[common_parser])
    parser_sketch_gtdb.set_defaults(func=mash_gtdb_sketch)
    
    # subparser for prepare sqlite DB
    parser_prep_sqlite = subparsers.add_parser('prepare_sqlite_db', help='Prepare SQLite database (references.db).', parents=[common_parser])
    parser_prep_sqlite.add_argument('--for_gtdb', action='store_true', help='Create files for GTDB.')
    parser_prep_sqlite.set_defaults(func=prepare_sqlite_db)

    # subparser for prepare_checkm_data
    parser_prep_checkm = subparsers.add_parser('prepare_checkm', help='Prepare CheckM data root', parents=[common_parser])
    parser_prep_checkm.add_argument('--delete_existing_data', action='store_true', help='Delete existing data directory.')
    parser_prep_checkm.set_defaults(func=prepare_checkm_data)

    # subparser for update_update_checkm_db
    parser_update_checkm_db = subparsers.add_parser('update_checkm_db', help='Update CheckM Taxon DB', parents=[common_parser])
    parser_update_checkm_db.set_defaults(func=update_checkm_db)

    # subparser for prepare_genome_size_data
    parser_genome_size = subparsers.add_parser('prepare_genome_size_data', help='Prepare genome size data', parents=[common_parser])
    parser_genome_size.set_defaults(func=prepare_genome_size_data)

    # subparser for dump_sqlite_db
    parser_dump_sqlite_db = subparsers.add_parser('dump_sqlite_db', help='Dump reference genome info to file.', parents=[common_parser])
    parser_dump_sqlite_db.set_defaults(func=dump_sqlite_db)

    # subparser for update_all
    parser_update_all = subparsers.add_parser('update_all', help='Update all reference data', parents=[common_parser])
    parser_update_all.set_defaults(func=update_all)

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
    if args.num_threads:
        config.NUM_THREADS = args.num_threads
    check_ref_type(args)
    args.func(args)