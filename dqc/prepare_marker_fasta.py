import sys
import os
import tempfile
import subprocess
from argparse import ArgumentError, ArgumentParser
from logging import StreamHandler, Formatter, INFO, DEBUG, getLogger
from Bio import SeqIO
from .common import get_logger, run_command, get_ref_path
from .config import config

logger = get_logger(__name__)

def run_prodigal(input_file, cds_fasta, protein_fasta, gcode=11):
    if input_file.endswith(".gz"):
        cmd = ["gunzip", "-c", input_file, "|", "prodigal", "-d", cds_fasta,
               "-a", protein_fasta, "-g", str(gcode), "-q", "> /dev/null"]
    else:
        cmd = ["cat", input_file, "|",
               "prodigal", "-d", cds_fasta, "-a", protein_fasta, "-g", str(gcode), "-q", "> /dev/null"]
    run_command(cmd, task_name="Prodigal", shell=True)


def run_hmmsearch(protein_fasta, hmm_result_out, profile_hmm):
    hmmer_options = config.HMMER_OPTIONS
    cmd = ["hmmsearch", "--tblout", hmm_result_out, hmmer_options,
           profile_hmm, protein_fasta, "> /dev/null"]
    run_command(cmd, task_name="HMMsearch", shell=True)


def parse_hmmer_result(hmm_result_file, allow_multi_hit=False):
    D = {key: [] for key in config.REFERENCE_MARKERS.keys()}
    for line in open(hmm_result_file):
        if line.startswith("#"):
            continue
        cols = line.split()
        hmm_accession, gene_id = cols[3], cols[0]
        if allow_multi_hit:
            D[hmm_accession].append(gene_id)
        else:
            if not D[hmm_accession]:
                D[hmm_accession].append(gene_id)
    return D


def write_fasta(cds_fasta, hmm_result, out_fasta, prefix=None):
    cds_dict = SeqIO.to_dict(SeqIO.parse(cds_fasta, "fasta"))
    out_buffer = ""
    for hmm_accession, gene_ids in hmm_result.items():
        for i, gene_id in enumerate(gene_ids, 1):
            cds = cds_dict[gene_id]
            gene_symbol, product = config.REFERENCE_MARKERS[hmm_accession]
            num = "-" + str(i) if len(gene_ids) > 1 else ""
            if prefix:
                header = f">{prefix}_{gene_symbol}{num} {product}"
            else:
                header = f">{gene_id}_{gene_symbol}{num} {product}"
            out_buffer += f"{header}\n{str(cds.seq)}\n"
    with open(out_fasta, "w") as f:
        f.write(out_buffer)


def prepare_work_dir(work_dir):
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)


def print_found_markers(hmm_result):
    ret = ""
    for key, (gene, product) in config.REFERENCE_MARKERS.items():
        found_genes = hmm_result.get(key)
        if found_genes:
            found_genes = ",".join(found_genes)
        else:
            found_genes = "not-found"
        ret += "\t".join([key, found_genes, gene, product]) + "\n"
    logger.debug("\n%s\n%s%s", "-"*80, ret, "-"*80)


def cleanup_files(work_dir):
    file_names = [config.PRODIGAL_CDS_FASTA, config.PRODIGAL_PROTEIN_FASTA, config.HMMER_RESULT]
    for file_name in file_names:
        file_name = os.path.join(work_dir, file_name)
        if os.path.exists(file_name):
            os.remove(file_name)


def main(input_file, out_dir, prefix=None):

    input_file_abs = os.path.abspath(input_file)
    cds_fasta = os.path.join(out_dir, config.PRODIGAL_CDS_FASTA)
    protein_fasta = os.path.join(out_dir, config.PRODIGAL_PROTEIN_FASTA)
    reference_marker_hmm = get_ref_path(config.REFERENCE_MARKERS_HMM)
    hmm_result_file = os.path.join(out_dir, config.HMMER_RESULT)
    out_query_marker_fasta = os.path.join(out_dir, config.QUERY_MARKERS_FASTA)
    out_summary_file = os.path.join(out_dir, config.MARKER_SUMMARY_FILE)

    if os.path.exists(out_query_marker_fasta):
        logger.info("Query marker FASTA already exists. Will reuse it. (%s)", out_query_marker_fasta)
        return out_query_marker_fasta
    if not os.path.exists(reference_marker_hmm):
        logger.error("Reference marker HMM does not exist. (%s)", reference_marker_hmm)
        exit(1)

    prepare_work_dir(out_dir)
    run_prodigal(input_file_abs, cds_fasta, protein_fasta)
    run_hmmsearch(protein_fasta, hmm_result_file, reference_marker_hmm)
    hmm_result = parse_hmmer_result(hmm_result_file, allow_multi_hit=True)
    found_markers = [hmm_accession for hmm_accession, gene_ids in hmm_result.items() if gene_ids]
    cnt_found_markers = len(found_markers)
    total_markers = len(hmm_result)
    if cnt_found_markers < total_markers:
        logger.warning("Found %d/%d markers. [%s]", cnt_found_markers, total_markers, input_file)
    else:
        if prefix:
            logger.info("%s: Found %d/%d markers.", prefix, cnt_found_markers, total_markers)
        else:
            logger.info("Found %d/%d markers.", cnt_found_markers, total_markers)
    print_found_markers(hmm_result)
    write_fasta(cds_fasta, hmm_result, out_query_marker_fasta, prefix=prefix)
    summary = [input_file, prefix if prefix else "-", str(cnt_found_markers), str(total_markers), ",".join(found_markers)]
    with open(out_summary_file, "w") as f:
        f.write("\t".join(summary) + "\n")
    if not config.DEBUG:
        cleanup_files(out_dir)
    logger.info("Query marker FASTA was written to %s", out_query_marker_fasta)
    return out_query_marker_fasta

if __name__ == '__main__':

    def parse_args():
        parser = ArgumentParser()
        parser.add_argument(
            "-i",
            "--input_fasta",
            type=str,
            required=True,
            help="Input FASTA file (raw or gzipped) [required]",
            metavar="PATH"
        )
        parser.add_argument(
            "-o",
            "--out_dir",
            default=".",
            type=str,
            help="Output directory (default: .)",
            metavar="PATH"
        )
        parser.add_argument(
            "-p",
            "--prefix",
            type=str,
            default=None,
            help="Prefix for output (default: None)",
            metavar="STR"
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Debug mode'
        )
        args = parser.parse_args()
        return args

    args = parse_args()
    if args.debug:
        settings["debug"] = True
        handler.setLevel(DEBUG)
        logger.setLevel(DEBUG)
    main(args.input_fasta, args.out_dir, prefix=args.prefix)
