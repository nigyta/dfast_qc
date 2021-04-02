import os
from ftplib import FTP
from ftplib import all_errors as FTP_all_errors
from concurrent.futures import ThreadPoolExecutor, as_completed
from more_itertools import distribute
from .common import get_logger, get_ref_path
from .config import config

logger = get_logger(__name__)
timeout = 60  # timeout for FTP connection 60s

def download_genomes_from_assembly(accessions, out_dir=None):
    def _get_ftp_directory(accession):
        path1, path2, path3, path4 = accession[0:3], accession[4:7], accession[7:10], accession[10:13]
        return "/".join(["/genomes", "all", path1, path2, path3, path4])

    def _download_genome(accession, ftp, max_retry=3):
        n_trial = 1
        while n_trial <= max_retry:
            if n_trial > 1:
                logger.warning(f"(Try {n_trial}/{max_retry})")
            try:
                directory = _get_ftp_directory(accession)
                ftp.cwd(directory)
                remore_file_list = ftp.nlst()
                remore_file_list = sorted([file_name for file_name in remore_file_list if file_name.startswith(accession)])
                if len(remore_file_list) == 0:
                    logger.warning("File not found. Will try again to retrieve file for %s", accession)
                    n_trial += 1
                    continue
                asm_name = remore_file_list[-1]
                target_file = "/".join([directory, asm_name, asm_name + "_genomic.fna.gz"])
                logger.debug("Downloading %s", ncbi_ftp_server + directory + "/" + asm_name + "/" + asm_name + "_genomic.fna.gz")
                output_file = os.path.join(out_dir, "_".join(asm_name.split("_")[0:2]) + ".fna.gz")
                with open(output_file, "wb") as f:
                    ftp.retrbinary(f"RETR {target_file}", f.write)
                remote_file_size = ftp.size(target_file)
            except FTP_all_errors as e:
                logger.error("FTP error %s", e)
                n_trial += 1
            else:
                if _check_file_size(output_file, remote_file_size, accession):
                    return "SUCCESS", output_file, target_file
                else:
                    logger.warning("Will try again to retrieve file for %s", accession)
                    n_trial += 1
        logger.error(f"Failed to download the genome FASTA for {accession}")
        return "FAIL", "-", "-"

    def _check_file_size(local_file, remote_file_size, accession):
        if remote_file_size is None:
            return False
        local_file_size = os.path.getsize(local_file)
        logger.debug(f"Checking file sizes. Accession={accession} Remote={remote_file_size} Local={local_file_size}")
        if local_file_size == remote_file_size:
            return True
        else:
            logger.warning(f"File size does not match. Accession={accession} Remote={remote_file_size} Local={local_file_size}")
            return False

    ncbi_ftp_server = config.NCBI_FTP_SERVER
    logger.debug("Logging in to the FTP server. [%s]", ncbi_ftp_server)
    if out_dir is None:
        out_dir = get_ref_path(config.REFERENCE_GENOME_DIR)
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
    futures = []
    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        for _accessions in list_of_accessions:
            f = executor.submit(download_genomes_from_assembly, _accessions, out_dir)
            futures.append(f)
    [f.result() for f in as_completed(futures)]  # wait until all the jobs finish

if __name__ == "__main__":
    pass
    # download test
    # accessions = open("dev/acc_list.100.txt").readlines()
    # accessions = [_.strip() for _ in accessions]

    # for debug
    # accessions = ["GCA_002101575.1"]
    # download_genomes_parallel(accessions, out_dir=".", threads=4)
    

    # download_genomes_from_assembly(["GCF_000185045.1"], "dev_download")
    # download_genomes_from_assembly(["GCF_000185045.2", "GCF_000376825.1", "GCF_000185045.1","GCF_000185045.1"], "dev_download")

    # download_genomes_from_assembly(["GCF_000159355.1", "GCF_001434515.1"])
    # download_genome_from_assembly("GCF_000181335.3", "dev_download")


    # download_genomes_from_assembly("GCF_000376825.1", "dqc_reference/genomes")

