#!/bin/env python

import os
import sys
from argparse import ArgumentParser
from dqc.config import config

config.ADMIN = True

from dqc.common import get_logger
logger = get_logger(__name__)

def download_genomes(args):
    from dqc.admin.download_all_reference_fasta import download_all_genomes
    download_all_genomes(asm_report=args.asm, ani_report=args.ani, type_strain_report=args.tsr, out_dir=args.out_dir, threads=args.threads)

def download_master_files(args):
    from dqc.admin.download_master_files import download_master_files
    if (not hasattr(args, "targets")) or args.targets is None:
        target_files = ["asm", "ani", "tsr"]
    else:
        target_files = args.targets
    download_master_files(target_files, args.out_dir, threads=args.threads)

def prepare_reference_hmm(args):
    from dqc.admin.prepare_reference_hmm import prepare_reference_hmm
    prepare_reference_hmm(master_hmm_file=args.master_hmm_file, out_dir=args.out_dir)

def prepare_reference_marker_fasta(args):
    from dqc.admin.prepare_reference_marker_fasta import prepare_reference_marker_fasta
    prepare_reference_marker_fasta(out_dir=args.out_dir, threads=args.threads, delete_existing=args.delete_existing_marker)

def prepare_sqlite_db(args):
    from dqc.admin.prepare_sqlite_db import prepare_sqlite_db
    prepare_sqlite_db(asm_report=args.asm, ani_report=args.ani, type_strain_report=args.tsr, out_dir=args.out_dir)

def update_all(args):
    pass

def parse_args():
    parser = ArgumentParser(description="DFAST_QC utility tools for admin.")
    subparsers = parser.add_subparsers(help="")

    # common parser
    # todo: outdirではなくて、configの DQC_REFERENCEを書き換えるようにする。
    common_parser = ArgumentParser(add_help=False)
    common_parser.add_argument('--debug', action='store_true', help='Debug mode')
    common_parser.add_argument("-o", "--out_dir", default=None, type=str, metavar="PATH",
        help="Output directory (default: DQC_REFERENCE_DIR)")
    common_parser.add_argument("-t", "--threads", default=1, type=int, metavar="INT",
        help="Number of threads for parallel processing (default:1)")

    # subparser for download master files
    parser_master = subparsers.add_parser('download_master_files', help='Download master files.', parents=[common_parser])
    parser_master.add_argument(
        "--targets", type=str, required=False, metavar="STR", 
        choices=['asm', 'ani', 'tsr', "hmm"], nargs="*",
        help="Target(s) for downloading. " + 
             "[asm: Assembly report, ani: ANI report, tsr: Type strain report, hmm: HMMER profile] "
             "(default: asm ani tsr)"
    )
    parser_master.set_defaults(func=download_master_files)

    # subparser for download reference genomes
    parser_genome = subparsers.add_parser('download_genomes', help='Download reference genomes from AssemblyDB.', parents=[common_parser])
    parser_genome.add_argument("--asm", type=str, required=False, metavar="PATH",
        help="Assembly report file (auto detected if not specified)")
    parser_genome.add_argument("--ani", type=str, required=False, metavar="PATH",
        help="ANI report file (auto detected if not specified)")
    parser_genome.add_argument("--tsr", type=str, required=False, metavar="PATH",
        help="Type strain report (not implemented)")
    parser_genome.set_defaults(func=download_genomes)

    # subparser for prepare_reference_hmm
    parser_prep_ref_hmm = subparsers.add_parser('prepare_reference_hmm', help='Prepare reference profile HMM file　(reference_markers.hmm).', parents=[common_parser])
    parser_prep_ref_hmm.add_argument(
        "--master_hmm_file", type=str, required=False, metavar="PATH", 
        help="Path to profile HMM for TIGRFAMs_15 (raw or gzipped). (Default: auto download)"
    )
    parser_prep_ref_hmm.set_defaults(func=prepare_reference_hmm)

    # subparser for prepare_reference_fasta
    parser_prep_ref_fasta = subparsers.add_parser('prepare_reference_fasta', help='Prepare reference marker FASTA file　(reference_markers.fasta).', parents=[common_parser])
    parser_prep_ref_fasta.add_argument('--delete_existing_marker', action='store_true', help='Delete existing markers and recreate all markers.')
    parser_prep_ref_fasta.set_defaults(func=prepare_reference_marker_fasta)

    # subparser for prepare sqlite DB
    parser_prep_sqlite = subparsers.add_parser('prepare_sqlite_db', help='Prepare SQLite database (references.db).', parents=[common_parser])
    parser_prep_sqlite.add_argument("--asm", type=str, metavar="PATH",
        help="Assembly report file (auto detected if not specified)")
    parser_prep_sqlite.add_argument("--ani", type=str, metavar="PATH",
        help="ANI report file (auto detected if not specified)")
    parser_prep_sqlite.add_argument("--tsr", type=str, metavar="PATH",
        help="Type strain report (not implemented)")
    parser_prep_sqlite.set_defaults(func=prepare_sqlite_db)

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


    args.func(args)