import os
import re
import hashlib
from urllib.request import urlretrieve, urlopen
from urllib.error import HTTPError, URLError
from http.client import RemoteDisconnected
from concurrent.futures import ThreadPoolExecutor, as_completed
from more_itertools import distribute
from .common import get_logger, get_ref_path, get_gtdb_ref_genome_dir
from .config import config

logger = get_logger(__name__)

def download_genomes_from_assembly(accessions, out_dir=None, for_gtdb=False):
    def _get_base_directory(accession):
        path1, path2, path3, path4 = accession[0:3], accession[4:7], accession[7:10], accession[10:13]
        return "/".join(["/genomes", "all", path1, path2, path3, path4])

    def _get_target_path(accession):
        base_dir = config.NCBI_FTP_SERVER + _get_base_directory(accession)
        acceesion_escaped = accession.replace(".", "\\.")
        pat_dir_name = re.compile(f'<a href="({acceesion_escaped}_.+?)/">')

        # Get directory name
        resp_base_dir = urlopen(base_dir).read().decode()
        m1 = pat_dir_name.search(resp_base_dir)
        file_prefix = None if not m1 else m1.group(1)

        if file_prefix is None:
            logger.error(f"Could not determine the download directory for {accession}.")
            return None, None  # target_url, md5

        target_file = file_prefix + "_genomic.fna.gz"
        target_file_escaped = target_file.replace(".", "\\.")

        # Get md5 for remote file
        pat_md5 = re.compile(f"(.+?)\\s+?\\./({target_file_escaped})")
        md5_url = os.path.join(base_dir, file_prefix, "md5checksums.txt")
        resp_md5 = urlopen(md5_url).read().decode()
        m2 = pat_md5.search(resp_md5)
        md5 = None if not m2 else m2.group(1)

        if file_prefix is None:
            logger.error(f"Failed to get MD5 for {accession}.")
            return None, None  # target_url, md5

        target_url = os.path.join(base_dir, file_prefix, target_file)
        return target_url, md5

    def _check_md5(file_name, md5):
        md5_local = hashlib.md5(open(file_name, "rb").read()).hexdigest()
        logger.debug(f"Checking MD5: FileName={file_name} Local={md5_local}, Remote={md5}")
        if md5 == md5_local:
            return True
        else:
            logger.warning(f"MD5 does not match. ({accession} Local={md5_local}, Remote={md5})")
            return False

    def delete_file_if_exists(file_name):
        if os.path.exists(file_name):
            os.remove(file_name)
            logger.warning(f"Removed broken file [{file_name}]")

    def _download_genome(accession, max_retry=3, out_dir=None, for_gtdb=for_gtdb):
        if for_gtdb:
            output_file = os.path.join(out_dir, accession + "_genomic.fna.gz")
        else:
            output_file = os.path.join(out_dir, accession + ".fna.gz")            
        logger.debug(f"Downloading genomic FASTA file for {accession}")
        n_trial = 1
        while n_trial <= max_retry:
            if n_trial > 1:
                logger.warning(f"(Try {n_trial}/{max_retry} [{accession}])")
            try:
                # check target file and MD5
                target_url, md5 = _get_target_path(accession)
                logger.debug(f"{accession}\tTargetURL={target_url} RemoteMD5={md5}")
                if target_url and md5:
                    urlretrieve(target_url, output_file)
                    if _check_md5(output_file, md5):
                        return "SUCCESS", output_file, target_url
                    else:
                        delete_file_if_exists(output_file)
                        n_trial += 1
                else:
                    logger.warning("Target file not found for %s", accession)
                    delete_file_if_exists(output_file)
                    n_trial += 1
                    continue
            except HTTPError as e:
                logger.error("%s", e)
                delete_file_if_exists(output_file)
                n_trial += 1
            except URLError as e:
                logger.error("%s", e)
                delete_file_if_exists(output_file)
                n_trial += 1
            except RemoteDisconnected as e:
                logger.error("%s", e)
                delete_file_if_exists(output_file)
                n_trial += 1

        logger.error(f"Failed to download the genome FASTA for {accession}")
        return "FAIL", "-", "-"

    if out_dir is None and not for_gtdb:
        out_dir = get_ref_path(config.REFERENCE_GENOME_DIR)
        logger.debug("Files will be downloaded to %s", out_dir)
    if out_dir is not None and not os.path.exists(out_dir):
        os.makedirs(out_dir)
        logger.debug("Created output directory [%s]", out_dir)

    num_succeeded = 0
    for accession in accessions:
        if out_dir is None and for_gtdb:
            out_dir = get_gtdb_ref_genome_dir(accession)
            logger.debug("GTDB reference genome will be downloaded to %s", out_dir)
            os.makedirs(out_dir, exist_ok=True)

        status, retrieved_file, target_file = _download_genome(accession, out_dir=out_dir, for_gtdb=for_gtdb)
        if status == "SUCCESS":
            num_succeeded += 1
        logger.info("\t".join([accession, status, retrieved_file, target_file]))
    return num_succeeded

def download_genomes_parallel(accessions, out_dir=None, threads=1, for_gtdb=False):
    logger.debug(f"Start downloading genomes using {threads} threads.")
    list_of_accessions = distribute(threads, accessions)  # divide accession list into num of threads
    futures = []
    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        for _accessions in list_of_accessions:
            f = executor.submit(download_genomes_from_assembly, _accessions, out_dir, for_gtdb=for_gtdb)
            futures.append(f)
    results = [f.result() for f in as_completed(futures)]  # wait until all the jobs finish
    return sum(results)   # number of genomes successfully retrieved

if __name__ == "__main__":
    pass
    # download test
    # accessions = open("dev/acc_list.100.txt").readlines()
    # accessions = [_.strip() for _ in accessions]

    # for debug
    # accessions = ["GCA_002101575.1","GCA_024172185.1"]
    # num_succeeded = download_genomes_parallel(accessions, out_dir=".", threads=4)
    # print(num_succeeded)

    # for GTDB debug
    accessions = ["GCA_910585095.1"]
    num_succeeded = download_genomes_parallel(accessions, out_dir=None, threads=4, for_gtdb=True)
    print(num_succeeded)


    # download_genomes_parallel(["GCF_000159355.1", "GCF_001434515.1", "GCF_000185045.1","GCF_000185045.1"], out_dir=".", threads=4)
    # accessions = ["GCA_000001405.28"]  # homo sapiens
    # download_genomes_parallel(accessions, out_dir=".", threads=4)
    

    # download_genomes_from_assembly(["GCF_000185045.1"], "dev_download")
    # download_genomes_from_assembly(["GCF_000185045.2", "GCF_000376825.1", "GCF_000185045.1","GCF_000185045.1"], "dev_download")

    # download_genome_from_assembly("GCF_000181335.3", "dev_download")


    # download_genomes_from_assembly("GCF_000376825.1", "dqc_reference/genomes")

