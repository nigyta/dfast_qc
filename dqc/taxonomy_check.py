#!/bin/env python

import os
from .common import get_logger, is_empty_file
from .select_target_genomes import main as select_target_genomes
from .calc_ani import main as calc_ani

from .config import config

logger = get_logger(__name__)

def run():
    input_file = config.QUERY_GENOME
    out_dir = config.OUT_DIR
    num_hits = config.MASH_OPTION
    logger.info("===== Start taxonomy check using ANI =====")

    target_genome_list_file = select_target_genomes(input_file, out_dir,num_hits)
    if is_empty_file(target_genome_list_file):
        logger.error("Task failed. No target genome found.")
        tc_result = []
        return tc_result

    tc_result = calc_ani(input_file, target_genome_list_file, out_dir)
    logger.info("===== Taxonomy check completed =====")
    return tc_result