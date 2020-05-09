import os
from argparse import ArgumentParser
from urllib.request import urlretrieve
from concurrent.futures import ThreadPoolExecutor

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


def download_master_files(target_files):
    
    out_dir = config.DQC_REFERENCE_DIR
    threads = config.NUM_THREADS

    logger.info("===== Download master files =====")
    logger.info("Files will be downloaded to %s", out_dir)

    with ThreadPoolExecutor(max_workers=threads, thread_name_prefix="thread") as executor:
        for target in target_files:
            if target in config.URLS:
                target_url = config.URLS[target]
                executor.submit(download_file, target_url, out_dir)
            else:
                logger.warn("Target file '%s' not found. Skipping...")

    logger.info("===== Completed downloading master files =====")


