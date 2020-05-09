#!/bin/env python

import os
import shutil
import gzip
from .common import get_logger, is_empty_file, run_command
from .ete3_helper import get_ascendants, get_names
from .models import Taxon
from .config import config

logger = get_logger(__name__)


def prepare_checkm_genome(input_file, checkm_input_dir):
    os.makedirs(checkm_input_dir, exist_ok=True)
    checkm_input_file = os.path.join(checkm_input_dir, "query.fna")
    if input_file.endswith(".gz"):
        with gzip.open(input_file, "rt") as f_in:
            open(checkm_input_file, "w").write(f_in.read())            
    else:
        shutil.copy(input_file, checkm_input_file)


def get_checkm_taxon(taxid):
    ascendants = list(get_ascendants(taxid))
    ascendant_taxa = get_names(ascendants)  # for debugging
    logger.debug("Ascendant taxa [%s]", ", ".join(ascendant_taxa))
    for tid in ascendants:
        taxon = Taxon.get_or_none(Taxon.taxid == tid)
        if taxon:
            logger.info("Selected '%s' markers (%s, taxid=%d) for CheckM",
                        taxon.taxon, taxon.rank, tid)
            return taxon.rank, taxon.taxon
    else:
        root_tax = Taxon.get_or_none(Taxon.taxid == 0)
        logger.warning(
            "Cannot find CheckM taxon for taxid:%d. %s markers will be used.", taxid, root_tax.taxon)
        return root_tax.rank, root_tax.taxon


def parse_result(checkm_result_file):
    with open(checkm_result_file) as f:
        next(f)  # skip first line
        line = next(f)
        cols = line.strip("\n").split("\t")
        completeness, contamination, heterogeneity = float(
            cols[11]), float(cols[12]), float(cols[13])
    return completeness, contamination, heterogeneity


def run():
    input_file = config.QUERY_GENOME
    out_dir = config.OUT_DIR
    if config.CHECKM_TAXID:
        checkm_taxid = config.CHECKM_TAXID
    else:
        checkm_taxid = 0

    checkm_input_dir = os.path.join(out_dir, config.CHECKM_INPUT_DIR)
    checkm_result_dir = os.path.join(out_dir, config.CHECKM_RESULT_DIR)
    checkm_result_file = os.path.join(out_dir, config.CC_RESULT)
    checkm_result_json = os.path.join(out_dir, config.CC_RESULT_JSON)

    logger.info("===== Start completeness check using CheckM =====")
    checkm_rank, checkm_taxon = get_checkm_taxon(checkm_taxid)
    prepare_checkm_genome(input_file, checkm_input_dir)
    cmd = [
        "checkm", "taxonomy_wf", "--tab_table", "-f", checkm_result_file,
        checkm_rank, f'"{checkm_taxon}"', checkm_input_dir, checkm_result_dir
    ]
    run_command(cmd, task_name="CheckM")
    completeness, contamination, heterogeneity = parse_result(
        checkm_result_file)
    logger.info("Completeness check finished.\n%s\nCompleteness: %.2f%%\nContamintation: %.2f%%\nStrain heterogeneity: %.2f%%\n%s",
                "-"*80, completeness, contamination, heterogeneity, "-"*80
                )
    cc_result = {
        "completeness": completeness,
        "contamination": contamination,
        "strain_heterogeneity": heterogeneity
    }
    logger.info("===== Completeness check finished =====")
    return cc_result