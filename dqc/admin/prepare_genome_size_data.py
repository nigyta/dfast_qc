import os
from ..common import get_logger, get_ref_path
from ..config import config
from ..models import init_db, db, Genome_Size
from .download_master_files import download_file

logger = get_logger(__name__)

def add_genome_size_to_db():
    expected_genome_size_file = get_ref_path(config.EXPECTED_GENOME_SIZE_FILE)
    logger.info("Parsing %s", expected_genome_size_file)
    # check output file (delete and regenerate)
    output_sqlitedb_file = get_ref_path(config.SQLITE_REFERENCE_DB)
    if os.path.exists(output_sqlitedb_file):
        Genome_Size.drop_table()
        db.create_tables([Genome_Size])
        logger.warning("Dropped and re-created 'Genome_Size' table. [%s]", output_sqlitedb_file)
    else:
        init_db()
        logger.info("New SQLite DB is created. [%s]", output_sqlitedb_file)

    logger.info("Inserting expected genome size data into SQLite DB file (references.db)")
    with open(expected_genome_size_file, 'r') as f:
        # skip first line
        #species_taxid  min_ungapped_length     max_ungapped_length     expected_ungapped_length        number_of_genomes       method_determined
        next(f)
        cnt = 0
        for line in f:
            cols = line.strip().split("\t")
            Genome_Size.create(
                species_taxid=int(cols[0]),
                min_ungapped_length=int(cols[1]),
                max_ungapped_length=int(cols[2]),
                expected_ungapped_length=int(cols[3]),
                number_of_genomes=int(cols[4]),
                method_determined=cols[5]
            )
            cnt += 1
    logger.info("Inserted %d Genome_Size records.", cnt)

def download_expected_genome_size_file():
    out_dir = config.DQC_REFERENCE_DIR
    url = config.URLS["egs"]  # egs: expected genome size
    download_file(url, out_dir)

def prepare_genome_size_data():
    logger.info("===== Prepare expected genome size data =====")
    download_expected_genome_size_file()
    add_genome_size_to_db()
    logger.info("===== Completed preparing expected genome size data =====")

if __name__ == "__main__":
    prepare_genome_size_data()

    # genome_size = Genome_Size.get_or_none(Genome_Size.species_taxid==1590)
    # print(genome_size)
    # print(genome_size.expected_ungapped_length)
    # print(genome_size.method_determined)

