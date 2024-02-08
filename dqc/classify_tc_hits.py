#!/bin/env python

import os
import dataclasses
from .common import get_logger, get_ref_path
# from .select_target_genomes import main as select_target_genomes
# from .prepare_marker_fasta import main as prepare_marker_fasta
# from .calc_ani import main as calc_ani

from .config import config

logger = get_logger(__name__)

igp_file = get_ref_path(config.INDISTINGUISHABLE_GROUPS_PROKARYOTE)
# default_ani_threshold = config.ANI_THRESHOLD

if not os.path.exists(igp_file):
    logger.error("INDISTINGUISHABLE_GROUPS_PROKARYOTE file does not exist. [%s]\nDownload it by 'dqc_admin_tools.py download_master_files --targets igp'", igp_file)
    exit(1)

@dataclasses.dataclass
class IndistinguishableSpecies:
    """
    Species that are difficult to distinguish with ANI
    See https://ftp.ncbi.nlm.nih.gov/genomes/ASSEMBLY_REPORTS/indistinguishable_groups_prokaryotes.txt
    """
    group_id: str
    taxid: int
    name: str

def parse_igp_file():
    dict_indistinguishable_species = {}
    for line in open(igp_file):
        line = line.strip()
        if line.startswith("#"):
            continue
        if not line:
            continue
        cols = line.split("\t")
        group_id, taxid, name = int(cols[0]), int(cols[1]), cols[2]
        indistinguishable_species = IndistinguishableSpecies(group_id, taxid, name)
        dict_indistinguishable_species[taxid] = indistinguishable_species
    return dict_indistinguishable_species

dict_indistinguishable_species = parse_igp_file()

def get_indistinguishable_group(taxid):
    indistinguishable_species = dict_indistinguishable_species.get(taxid)
    if indistinguishable_species:
        indistinguishable_group = [x for x in dict_indistinguishable_species.values() if x.group_id == indistinguishable_species.group_id]
        return {x.taxid: x.name for x in indistinguishable_group}
    else:
        return {} 

def classify_tc_hits_deprecated(tc_result):
    # status: conclusive, indistinguishable, inconsistent, below_threshold
    status = None
    accepted_hits_taxid = set([x["species_taxid"] for x in tc_result if x["ani"] >= ani_threshold])
    dict_indistinguishable_species = None
    for taxid in accepted_hits_taxid:
        tmp_dict_indistinguishable_group = get_indistinguishable_group(taxid)
        if dict_indistinguishable_species is None:
            dict_indistinguishable_species = tmp_dict_indistinguishable_group
        elif tmp_dict_indistinguishable_group != dict_indistinguishable_species:
            status = "inconsistent"
            logger.warning(f"The ANI hits belong to more than one indistinguishable-group. The ANI hits will be classified as 'insonsistent'. %s, %s", dict_indistinguishable_species, tmp_dict_indistinguishable_group)
            break
        else:
            assert tmp_dict_indistinguishable_group == dict_indistinguishable_species
    set_indistinguishable_taxids = set(dict_indistinguishable_species.keys()) if dict_indistinguishable_species else set()
    logger.debug("ANI hit taxids: %s", str(accepted_hits_taxid))

    if len(set_indistinguishable_taxids) and status is None:
        # Confirm if the ANI hits belong to a indistinguishable group.
        logger.debug("Indistinguishable taxids: %s", str(set_indistinguishable_taxids))
        indistinguishable_species_names = ", ".join([f"{name}({taxid})" for taxid, name in dict_indistinguishable_species.items()])
        logger.warning("Following organisms are indistinguishable with ANI. [%s]", indistinguishable_species_names)

    if len(accepted_hits_taxid) == 0:
        if len(tc_result) > 0:
            status = "below_threshold"
        else:
            status = "no_hit"
    elif len(accepted_hits_taxid) == 1:
        status = "conclusive"
    else:
        if accepted_hits_taxid.issubset(set_indistinguishable_taxids):
            status = "indistinguishable"
        else:
            status = "inconsistent"

    for result in tc_result:
        if result["ani"] >= ani_threshold:
            assert status
            result["status"] = status
        else:
            result["status"] = "below_threshold"
    assert status
    return status


def classify_tc_hits(tc_result):
    # status: conclusive, indistinguishable, inconsistent, below_threshold, 
    status = None
    accepted_hits_taxid = set([x["species_taxid"] for x in tc_result if x["ani"] >= x["ani_threshold"]])
    logger.debug("Taxids for accepted ANI hits: %s", str(accepted_hits_taxid))

    dict_indistinguishable_species = None
    # the process below is too complex. Must be refactored
    for taxid in accepted_hits_taxid:
        tmp_dict_indistinguishable_group = get_indistinguishable_group(taxid)
        if dict_indistinguishable_species is None:
            dict_indistinguishable_species = tmp_dict_indistinguishable_group
        elif tmp_dict_indistinguishable_group != dict_indistinguishable_species:
            status = "inconclusive,indistinguishable"
            logger.warning(f"The ANI hits belong to more than one indistinguishable-group. The ANI hits will be classified as 'inconclusive,indistinguishable'. %s, %s", dict_indistinguishable_species, tmp_dict_indistinguishable_group)
            break
        else:
            assert tmp_dict_indistinguishable_group == dict_indistinguishable_species
    set_indistinguishable_taxids = set(dict_indistinguishable_species.keys()) if dict_indistinguishable_species else set()

    if len(set_indistinguishable_taxids) and status is None:
        # Confirm if the ANI hits belong to a indistinguishable group.
        logger.debug("Indistinguishable taxids: %s", str(set_indistinguishable_taxids))
        indistinguishable_species_names = ", ".join([f"{name}({taxid})" for taxid, name in dict_indistinguishable_species.items()])
        logger.warning("Following organisms are indistinguishable with ANI. [%s]", indistinguishable_species_names)

    if len(accepted_hits_taxid) == 0:
        if len(tc_result) > 0:
            status = "below_threshold"
        else:
            status = "no_hit"
    elif len(accepted_hits_taxid) == 1:
        status = "conclusive"
    else:
        if accepted_hits_taxid.issubset(set_indistinguishable_taxids):
            status = "indistinguishable"
        else:
            status = "inconclusive"

    for result in tc_result:
        if result["ani"] >= result["ani_threshold"]:
            result["status"] = status
        else:
            result["status"] = "below_threshold"
    assert status
    return status

def classify_tc_hits_GTDB(tc_result):
    # status: conclusive, indistinguishable, inconsistent, below_threshold, 
    status = None
    accepted_hits_taxid = set([x["gtdb_species"] for x in tc_result if x["ani"] >= x["ani_circumscription_radius"]])
    logger.debug("Taxids for accepted ANI hits: %s", str(accepted_hits_taxid))

    dict_indistinguishable_species = None
    # the process below is too complex. Must be refactored
    for taxid in accepted_hits_taxid:
        tmp_dict_indistinguishable_group = get_indistinguishable_group(taxid)
        if dict_indistinguishable_species is None:
            dict_indistinguishable_species = tmp_dict_indistinguishable_group
        elif tmp_dict_indistinguishable_group != dict_indistinguishable_species:
            status = "inconclusive,indistinguishable"
            logger.warning(f"The ANI hits belong to more than one indistinguishable-group. The ANI hits will be classified as 'inconclusive,indistinguishable'. %s, %s", dict_indistinguishable_species, tmp_dict_indistinguishable_group)
            break
        else:
            assert tmp_dict_indistinguishable_group == dict_indistinguishable_species
    set_indistinguishable_taxids = set(dict_indistinguishable_species.keys()) if dict_indistinguishable_species else set()

    if len(set_indistinguishable_taxids) and status is None:
        # Confirm if the ANI hits belong to a indistinguishable group.
        logger.debug("Indistinguishable taxids: %s", str(set_indistinguishable_taxids))
        indistinguishable_species_names = ", ".join([f"{name}({taxid})" for taxid, name in dict_indistinguishable_species.items()])
        logger.warning("Following organisms are indistinguishable with ANI. [%s]", indistinguishable_species_names)

    if len(accepted_hits_taxid) == 0:
        if len(tc_result) > 0:
            status = "below_threshold"
        else:
            status = "no_hit"
    elif len(accepted_hits_taxid) == 1:
        status = "conclusive"
    else:
        if accepted_hits_taxid.issubset(set_indistinguishable_taxids):
            status = "indistinguishable"
        else:
            status = "inconclusive"

    for result in tc_result:
        if result["ani"] >= result["ani_circumscription_radius"]:
            result["status"] = status
        else:
            result["status"] = "below_threshold"
    assert status
    return status

if __name__ == "__main__":
    print(get_indistinguishable_group(622))
    print(get_indistinguishable_group(1590))
