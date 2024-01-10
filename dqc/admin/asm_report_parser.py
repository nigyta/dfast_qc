import dataclasses
import os
import sys
from ftplib import FTP
from logging import getLogger, StreamHandler, INFO, basicConfig


@dataclasses.dataclass
class Assembly:
    assembly_accession: str
    bioproject: str
    biosample: str
    wgs_master: str
    refseq_category: str
    taxid: str
    species_taxid: str
    organism_name: str
    infraspecific_name: str
    isolate: str
    version_status: str
    assembly_level: str
    release_type: str
    genome_rep: str
    seq_rel_date: str
    asm_name: str
    submitter: str
    gbrs_paired_asm: str
    paired_asm_comp: str
    ftp_path: str
    excluded_from_refseq: str
    relation_to_type_material: str
    asm_not_live_date: str

    @staticmethod
    def parse(asm_report_file):
        f = open(asm_report_file)
        line1 = next(f)
        line2 = next(f)
        assert line1.startswith("#") and line2.startswith("#")
        for line in f:
            cols = line.strip("\n").split("\t")
            asm = Assembly(*cols[:23])
            yield asm

