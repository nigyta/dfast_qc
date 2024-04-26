import sys
import os
from .common import get_logger, run_command, get_ref_path, get_ref_genome_fasta
from argparse import ArgumentError, ArgumentParser
from logging import StreamHandler, Formatter, INFO, DEBUG, getLogger


logger = get_logger(__name__)
from .config import config

def print_selected_genomes(str_result):
    logger.debug("\n%s\n%s%s", "-"*80, str_result, "-"*80)

def run_mash(input_file, mash_sketch_file, mash_result_file):
    num_threads = config.NUM_THREADS
    cmd_mash = ["mash", "dist", mash_sketch_file,input_file,">", mash_result_file,"-p",str(num_threads)]
    run_command(cmd_mash, task_name="mash_search")
    return mash_result_file

def main(Query, out_dir, hits = 10, for_gtdb=False):
    if for_gtdb:
        mash_sketch = get_ref_path(config.GTDB_MASH_SKETCH_FILE)
        mash_result = os.path.join(out_dir, config.MASH_RESULT_GTDB)
    else:
        mash_sketch = get_ref_path(config.MASH_SKETCH_FILE)
        mash_result = os.path.join(out_dir, config.MASH_RESULT_REF)
    run_mash(Query,mash_sketch,mash_result)
    L = []
    for line in open(mash_result):
        cols = line.strip("\n").split("\t")
        L.append(cols)
    L = sorted(L, key=lambda x: float(x[2]))
    top_10 = L[: hits]
    target_accessions = set()
    ret, target_cnt = "", 0
    for dat in top_10:
        accession = dat[0].split("/")[-1]
        if for_gtdb:
            accession = accession.replace("_genomic.fna.gz","")
            target_accessions.add(accession)
        else: 
            accession = accession.replace(".fna.gz","")
            target_accessions.add(accession)
    for accession in target_accessions:
        target_genome_path = get_ref_genome_fasta(accession, for_gtdb=for_gtdb)
        target_cnt += 1
        ret += target_genome_path + "\n"
    if for_gtdb:
        target_genome_list_file = os.path.join(out_dir, config.GTDB_TARGET_GENOME_LIST)
    else:
        target_genome_list_file = os.path.join(out_dir, config.TARGET_GENOME_LIST)

    with open(target_genome_list_file, "w") as f:
        f.write(ret)
    if not config.DEBUG:
        os.remove(mash_result)
    logger.info("Selected %d target genomes.", target_cnt)
    logger.info("Target genome list was writen to %s", target_genome_list_file)
    print_selected_genomes(ret)
    return target_genome_list_file 

if __name__ == '__main__':
    def parse_args():
        parser = ArgumentParser()
        parser.add_argument(
            "-i",
            "--input",
            type=str,
            required=True,
            help="Query marker FASTA file [required]",
            metavar="PATH"
        )
        parser.add_argument(
            "-hits",
            "--num_hits",
            default="10",
            type=int,
            help="Number of top hits by MASH(default: 10)",
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
            '--for_gtdb',
            action='store_true',
            help='Search against GTDB.'
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
        config.DEBUG = True

    main(args.input, args.out_dir, args.num_hits,args.for_gtdb)  

