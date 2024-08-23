import os
import gzip
from .common import get_logger, get_ref_path
from .config import config
from .models import init_db, db, Genome_Size

logger = get_logger(__name__)

def get_genome_size(input_fasta):
    # read FASTA file (or gzipped FASTA file) and return the length of the genome
    if input_fasta.endswith(".gz"):
        with gzip.open(input_fasta, "rt") as f:
            data = f.readlines()
    else:
        with open(input_fasta) as f:
            data = f.readlines()
    data = "".join([_ for _ in data if not _.startswith(">")])
    data = data.upper().replace("N", "").replace("/", "").replace(" ", "").replace("\n", "")
    return len(data)

def table_exists():
    cursor = db.execute_sql(f"SELECT name FROM sqlite_master WHERE type='table' AND name='genome_size';")
    return bool(cursor.fetchone())

def get_expected_size(taxid):
    if table_exists():
        return Genome_Size.get_or_none(Genome_Size.species_taxid==taxid)
    else:
        logger.warning("Genome_Size table does not exist. Genome size check will be skipped.")
        return None

def genome_size_check(input_fasta, taxid):
    genome_size = get_genome_size(input_fasta)
    expected_size = get_expected_size(taxid)
    if expected_size is None:
        logger.warning(f"Expected genome size data is not available for taxid={taxid}")
        ret = {"ungapped_genome_size": genome_size, "expected_size": None, "expected_size_min": None, "expected_size_max": None, "genome_size_check": "expected_size_not_available"}
    else:
        if expected_size.min_ungapped_length <= genome_size <= expected_size.max_ungapped_length:
            status = "OK"
        elif genome_size < expected_size.min_ungapped_length:
            status = "genome_size_too_small"
        elif genome_size > expected_size.max_ungapped_length:
            status = "genome_size_too_large"
        ret = {"ungapped_genome_size": genome_size, "expected_size": expected_size.expected_ungapped_length, 
                "expected_size_min": expected_size.min_ungapped_length, "expected_size_max": expected_size.max_ungapped_length,
                "genome_size_check": status}
    msg = "Genome size check completed.\n" + "-"*80 + "\n"
    for key, value in ret.items():
        if isinstance(value, int):
            msg += f"{key}: {value:,}\n"
        else:
            msg += f"{key}: {value}\n"
    msg += "-"*80
    logger.info(msg)
    return ret


if __name__ == "__main__":
    # print(get_genome_size("/workspace/dev/2025206003_8.fna"))
    # print(get_genome_size("/workspace/dev/parakefiri_GCA_001434215.1.fna"))
    input_fasta = "/workspace/dev/parakefiri_GCA_001434215.1.fna"
    taxid = 33962
    import json
    ret = genome_size_check(input_fasta, taxid)
    # print(json.dumps(ret, indent=2))