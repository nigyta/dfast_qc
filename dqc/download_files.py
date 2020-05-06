import os
from ftplib import FTP
from ftplib import all_errors as FTP_all_errors
from concurrent.futures import ThreadPoolExecutor
from more_itertools import distribute
from .common import get_logger
from .config import config

logger = get_logger(__name__)
timeout = 60  # timeout for FTP connection 60s

def download_genomes_from_assembly(accessions, out_dir=None):
    def _get_ftp_directory(accession):
        path1, path2, path3, path4 = accession[0:3], accession[4:7], accession[7:10], accession[10:13]
        return "/".join(["/genomes", "all", path1, path2, path3, path4])

    def _download_genome(accession, ftp):
        try:
            directory = _get_ftp_directory(accession)
            ftp.cwd(directory)
            remore_file_list = ftp.nlst()
            remore_file_list = sorted([file_name for file_name in remore_file_list if file_name.startswith(accession)])
            if len(remore_file_list) == 0:
                logger.warning("File not found. Skip retrieving file for %s", accession)
                return "NOT-FOUND", "-", "-"
            asm_name = remore_file_list[-1]
            target_file = "/".join([directory, asm_name, asm_name + "_genomic.fna.gz"])
            logger.debug("Downloading %s", ncbi_ftp_server + directory + "/" + asm_name + "/" + asm_name + "_genomic.fna.gz")
            output_file = os.path.join(out_dir, "_".join(asm_name.split("_")[0:2]) + ".fna.gz")
            with open(output_file, "wb") as f:
                ftp.retrbinary(f"RETR {target_file}", f.write)
        except FTP_all_errors as e:
            logger.error("FTP error %s", e)
            return "FAIL", "-", target_file
        else:
            return "SUCCESS", output_file, target_file

    ncbi_ftp_server = config.NCBI_FTP_SERVER
    logger.debug("Logging in to the FTP server. [%s]", ncbi_ftp_server)
    if out_dir is None:
        out_dir = config.REFERENCE_GENOME_DIR
    logger.debug("Files will be downloaded to %s", out_dir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    with FTP(host=ncbi_ftp_server, timeout=timeout) as ftp:
        ftp.login()
        for accession in accessions:
            status, retrieved_file, target_file = _download_genome(accession, ftp)
            logger.info("\t".join([accession, status, retrieved_file, target_file]))

def download_genomes_parallel(accessions, out_dir=None, threads=1):

    list_of_accessions = distribute(threads, accessions)  # divide accession list into num of threads
    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        for _accessions in list_of_accessions:
            executor.submit(download_genomes_from_assembly, _accessions, out_dir)

if __name__ == "__main__":
    pass
    # download test
    # accessions = open("dev/acc_list.100.txt").readlines()
    # accessions = [_.strip() for _ in accessions]
    # download_genomes_parallel(accessions, out_dir=None, threads=4)
    

    # download_genomes_from_assembly(["GCF_000185045.1"], "dev_download")
    # download_genomes_from_assembly(["GCF_000185045.2", "GCF_000376825.1", "GCF_000185045.1","GCF_000185045.1"], "dev_download")

    # download_genomes_from_assembly(["GCF_000159355.1", "GCF_001434515.1"])
    # download_genome_from_assembly("GCF_000181335.3", "dev_download")


    # download_genomes_from_assembly("GCF_000376825.1", "dqc_reference/genomes")

