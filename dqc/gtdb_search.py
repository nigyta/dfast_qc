#!/bin/env python

import os
from .common import get_logger, is_empty_file
from .select_target_genomes import main as select_target_genomes
from .prepare_marker_fasta import main as prepare_marker_fasta
from .calc_ani import main as calc_ani

from .config import config

logger = get_logger(__name__)

def run():
    input_file = config.QUERY_GENOME
    out_dir = config.OUT_DIR
    prefix = config.PREFIX
    num_hits = config.MASH_OPTION
    logger.info("===== Start GTDB Search =====")

    # query_marker_fasta = prepare_marker_fasta(input_file, out_dir, prefix=prefix)
    # if is_empty_file(query_marker_fasta):
    #     logger.error("GTDB Search failed. No marker genes found.")
    #     gtdb_result = []
    #     return gtdb_result
    target_genome_list_file = select_target_genomes(input_file, out_dir,num_hits,for_gtdb=True)
    #target_genome_list_file = select_target_genomes(input_file , out_dir,for_gtdb=True)
    if is_empty_file(target_genome_list_file):
        logger.error("Task failed. No target genome found.")
        gtdb_result = []
        return gtdb_result

    gtdb_result = calc_ani(input_file, target_genome_list_file, out_dir, for_gtdb=True)
    logger.info("===== GTDB Search completed =====")
    return gtdb_result