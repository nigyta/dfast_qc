#!/usr/bin/env python3

"""
A script file to run DFAST_QC against genomes submitted via MSS

arguments:
    input_dir: str - The directory containing the MSS files
    fasta: str - acceptable file extension for the fasta files, default: fa,fasta,fna
    ann: str - acceptable file extension for the annotation files, default: ann,annot,ann.tsv,annot.tsv
    output: str - output file name, default: dqc_report.tsv
    taxid: int - taxid of the genomes (-1: auto, 0:prokaryote), default: 0
    thread: int - number of threads to use, default: 1
"""

import os
import glob
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
# import log module
import logging



DQC_BASE_COMMAND = "dfast_qc --input_fasta {input_fasta} --out_dir {out_dir} --force"
REF_DIR = ""

# initialize logger
logger = logging.getLogger(__name__)

# Function to parse the command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description="Run DFAST_QC against genomes submitted via MSS")
    parser.add_argument("input_dir", type=str, help="The directory containing the MSS files")
    parser.add_argument("--fasta", type=str, default="fa,fasta,fna,seq.fa", help="acceptable file extension for the fasta files")
    parser.add_argument("--ann", type=str, default="ann,annot,ann.tsv,annot.tsv", help="acceptable file extension for the annotation files")
    parser.add_argument("--out_dir", "-O", type=str, default="dqc_out", help="output dir name")
    parser.add_argument("--output", type=str, default="dqc_report.tsv", help="output file name")
    parser.add_argument("--taxid", type=int, default=0, help="taxid of the genomes (-1: auto, 0:prokaryote)")
    parser.add_argument("--thread", "-t", type=int, default=1, help="number of threads to use")
    args = parser.parse_args()
    return args


def run_dqc(input_fasta, out_dir, taxid=None, ref_dir=None, disable_tc=False, disable_cc=False, enable_gtdb=False):
    dqc_command = DQC_BASE_COMMAND.format(input_fasta=input_fasta, out_dir=out_dir)
    if ref_dir:
        dqc_command += f" --ref_dir {ref_dir}"
    if taxid >= 0:  # -1 for auto, 0 for prokaryote
        dqc_command += f" --taxid {taxid}"
    if disable_cc:
        dqc_command += " --disable_cc"
    if disable_tc:
        dqc_command += " --disable_tc"
    if enable_gtdb:
        dqc_command += " --enable_gtdb"
    logger.warning(f"Running DFAST_QC: {dqc_command}")
    dqc_command = dqc_command.split()
    result = subprocess.run(dqc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8")
    return result.stdout, result.stderr

def run_dqc_dummy(input_fasta, out_dir, taxid=None, ref_dir=None):
    dqc_command = DQC_BASE_COMMAND.format(input_fasta=input_fasta, out_dir=out_dir)
    if ref_dir:
        dqc_command += f" --ref_dir {ref_dir}"
    if taxid >= 0:  # -1 for auto, 0 for prokaryote
        dqc_command += f" --taxid {taxid}"
    dqc_command = f"echo '{dqc_command}'"
    logger.warning(f"Running DFAST_QC: {dqc_command}")
    result = subprocess.run(dqc_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", shell=True)
    return result.stdout, result.stderr

def get_fasta_files(input_dir, fasta_ext="fa,fasta,fna,fa.gz,fasta.gz,fna.gz"):
    fasta_files = []
    for ext in fasta_ext.split(","):
        fasta_files.extend(glob.glob(f"{input_dir}/**/*.{ext}", recursive=True))
    fasta_files = list(set(fasta_files))  # remove redundant
    return fasta_files

def run_dqc_parallel(fasta_files, out_dir, taxid=None, ref_dir=None, threads=1, disable_tc=False, disable_cc=False, enable_gtdb=False):
    logger.warning(f"Start running DFAST_QC using {threads} threads.")
    # list_of_fasta_files = distribute(threads, fasta_files)  # divide fasta files into num of threads
    futures = []
    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        for fasta_file in fasta_files:
            base_name = os.path.basename(fasta_file)
            # prefix, _ext = os.path.splitext(base_name)
            
            dqc_out_dir = os.path.join(out_dir, base_name)
            f = executor.submit(run_dqc, fasta_file, dqc_out_dir, taxid=taxid, ref_dir=ref_dir, disable_tc=disable_tc, disable_cc=disable_cc, enable_gtdb=enable_gtdb)
            futures.append(f)
    results = [f.result() for f in as_completed(futures)]  # wait until all the jobs finish
    return results


if __name__ == "__main__":
    args = parse_args()
    fasta_files = get_fasta_files(args.input_dir, args.fasta)
    out_dir = args.out_dir

    # execute DFAST_QC
    results = run_dqc_parallel(fasta_files, out_dir, taxid=args.taxid, ref_dir=None, threads=args.thread)
    # for result in results:
    #     print(result)

    print("Done!")
    print(f"Execute command to retrieve the results: read_dqc_result.py -O {args.out_dir} {args.input_dir}")
