import os
import gzip
from argparse import ArgumentParser
from urllib.request import urlretrieve
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..common import get_logger
from ..config import config

logger = get_logger(__name__)


def download_file(url, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    base_name = os.path.basename(url)
    out_file = os.path.join(out_dir, base_name)
    logger.info("Downloading %s to %s", base_name, out_dir)
    logger.debug("Source URL: %s", url)
    urlretrieve(url, out_file)
    logger.info("Downloaded %s", base_name)
    if base_name.endswith(".txt.gz"):
        decompress_gzip(out_file, out_dir)

def decompress_gzip(gzip_file, out_dir):
    base_name = os.path.basename(gzip_file)
    base_name = base_name.replace(".gz", "")
    out_file = os.path.join(out_dir, base_name)
    logger.info("Decompressing %s to %s", gzip_file, base_name)
    with gzip.open(gzip_file, "rb") as f_in:
        with open(out_file, "wb") as f_out:
            f_out.write(f_in.read())
    os.remove(gzip_file)


def download_master_files(target_files):
    
    out_dir = config.DQC_REFERENCE_DIR
    threads = config.NUM_THREADS

    logger.info("===== Download master files =====")
    logger.info("Files will be downloaded to %s", out_dir)
    futures = []
    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        for target in target_files:
            if target in config.URLS:
                target_url = config.URLS[target]
                f = executor.submit(download_file, target_url, out_dir)
                futures.append(f)
            else:
                logger.warn("Target file '%s' not found. Skipping...")
    [f.result() for f in as_completed(futures)]  # wait until all the jobs finish

    logger.info("===== Completed downloading master files =====")


