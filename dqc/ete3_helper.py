import os
from ete3 import NCBITaxa
from .config import config
from .common import get_logger, get_ref_path

logger = get_logger(__name__)


ete3_db_file = get_ref_path(config.ETE3_SQLITE_DB)
if not os.path.exists(ete3_db_file):
    logger.error("ETE3 DB file does not exist. Run 'dqc_admin_tools.py update_taxdump' to create it.")
    exit()

ncbi_taxonomy = NCBITaxa(dbfile=ete3_db_file)

def is_prokaryote(taxid):
    lineage = ncbi_taxonomy.get_lineage(taxid)
    return 2 in lineage or 2157 in lineage  # 2: Bacteria, 2157: Archaea

def get_rank(taxid):
    rank_dict = ncbi_taxonomy.get_rank([taxid])
    rank = rank_dict.get(taxid, "")
    if rank == "superkingdom":
        rank = "domain"  # for Bacteria, Archaea
    return rank

def get_taxid(taxon_name, rank):
    taxid_dict = ncbi_taxonomy.get_name_translator([taxon_name])

    taxid_candidates = taxid_dict.get(taxon_name, [])
    taxid_candidates = [taxid for taxid in taxid_candidates if is_prokaryote(taxid)]
    taxid_candidates = [taxid for taxid in taxid_candidates if get_rank(taxid)==rank]
    if len(taxid_candidates) > 1:
        logger.warning("Cannot determine taxid for '%s (%s)'. %s", taxon_name, rank, str(taxid_candidates))
        return None
    elif len(taxid_candidates) == 0:
        logger.warning("Cannot find taxid for '%s (%s)'.", taxon_name, rank)
        return None
    else:
        return taxid_candidates[0]

def get_ascendants(taxid):
    lineage = ncbi_taxonomy.get_lineage(taxid)
    if lineage is None:
        return [0]
    return reversed(lineage)

def get_name(taxid):
    names = ncbi_taxonomy.get_taxid_translator([taxid])
    return names[taxid]

def get_valid_name(taxid):
    """
    Return organism name with valid taxon rank
    e.g.
        Lactobacillus delbrueckii subsp. jakobsenii ZN7a-9 = DSM 26046 (taxid: 1217420)
        ==> Lactobacillus delbrueckii subsp. jakobsenii
    """
    for _tid in get_ascendants(taxid):
        rank = get_rank(_tid)
        if rank in ["no rank", "strain", "isolate"] :
            continue
        else:
            if not (rank == "species" or rank == "subspecies"):
                logger.warning("'%s' (taxid: %s, rank=%s) may not be a valid species or subspecies name.", get_name(_tid), str(_tid), rank)
            return _tid, get_name(_tid)
    else:
        return None, None

def get_names(taxid_list):  # only used for debugging
    if len(taxid_list) == 1 and taxid_list[0] == 0:
        return ["Prokaryote"]  # taxid 0 for Prokaryote 
    names = ncbi_taxonomy.get_taxid_translator(taxid_list)
    taxon_names = [f"{taxid}:{names[taxid]}" for taxid in taxid_list]
    return taxon_names

if __name__ == "__main__":
    print(list(get_ascendants(1570)))
    print(get_taxid("Lactobacilluss", "genus"))