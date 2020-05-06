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

    query_marker_fasta = prepare_marker_fasta(input_file, out_dir, prefix=prefix)
    if is_empty_file(query_marker_fasta):
        logger.error("Task failed. No marker genes found.")
        exit(1)
    target_genome_list_file = select_target_genomes(query_marker_fasta, out_dir)
    if is_empty_file(target_genome_list_file):
        logger.error("Task failed. No target genome found. Aborted.")
        exit(1)

    calc_ani(input_file, target_genome_list_file, out_dir)
