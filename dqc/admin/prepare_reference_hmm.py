import os
import gzip
from argparse import ArgumentParser

from ..common import get_logger
from ..config import config
from .download_master_files import download_file

logger = get_logger(__name__)

def extract_target_hmms(master_hmm_file, output_hmm_file, target_hmms):
    def _hmm_parser(file_name):
        if file_name.endswith(".gz"):
            fh = gzip.open(master_hmm_file, "rt")
        else:
            fh = open(file_name)

        hmm_profile_buffer = []
        for line in fh:
            hmm_profile_buffer.append(line)
            if line.startswith("//"):
                yield hmm_profile_buffer
                hmm_profile_buffer = []

    def _get_acc(hmm_profile_buffer):
        for line in hmm_profile_buffer:
            if line.startswith("ACC"):
                accession = line.replace("ACC", "").strip()
                return accession

    ret = ""
    cnt = 0
    for hmm_profile in _hmm_parser(master_hmm_file):
        accession = _get_acc(hmm_profile)
        if accession in target_hmms:
            cnt += 1
            ret += "".join(hmm_profile)
    with open(output_hmm_file, "w") as f:
        f.write(ret)
    logger.info("Found %d HMMs and extracted to %s", cnt, output_hmm_file)

def prepare_reference_hmm(master_hmm_file=None, out_dir=None):
    logger.info("===== Prepare reference profile HMM (reference_markers.hmm) =====")
    reference_marker_hmm = config.REFERENCE_MARKERS_HMM
    reference_marker_hmm_base = os.path.basename(reference_marker_hmm)
    target_hmms = list(config.REFERENCE_MARKERS.keys())
    if out_dir is None:
        out_dir = config.DQC_REFERENCE_DIR
    os.makedirs(out_dir, exist_ok=True)

    # check master hmm file. Will be downloaded if not exists.
    if master_hmm_file is None:
        master_hmm_url = config.URLS["hmm"]
        master_hmm_basename = os.path.basename(master_hmm_url)  # TIGRFAMs_15.0_HMM.LIB.gz
        master_hmm_file = os.path.join(out_dir, master_hmm_basename)
        if not os.path.exists(master_hmm_file):
            logger.warn("%s does not exist in DQC_REFERENCE_DIR. Will try to download.", master_hmm_basename)
            download_file(master_hmm_url, out_dir)

    output_hmm_file = os.path.join(out_dir, reference_marker_hmm_base)
    logger.info("Will create '%s' in %s", reference_marker_hmm_base, out_dir)
    logger.info("Target HMMs: %s", target_hmms)
    extract_target_hmms(master_hmm_file, output_hmm_file, target_hmms)
    logger.info("===== Completed preparing reference profile HMM =====")
