#!/usr/bin/env python3

# This script is still under development.


import json
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import re
import os
import glob
import logging

logger = logging.getLogger(__name__)


tc_header = ["organism_name", "strain", "accession", "species_taxid", "ani", "align_fraction_ref", "align_fraction_query", "ani_threshold", "status"]
cc_header = ["completeness", "contamination", "strain_heterogeneity", "ungapped_genome_size", "expected_size", "genome_size_check"]
gtdb_header = ["accession", "gtdb_species", "ani", "align_fraction_ref", "align_fraction_query", "ani_circumscription_radius", "status"]

@dataclass
class TCResult:
    organism_name: str
    strain: str
    accession: str
    taxid: int
    species_taxid: int
    relation_to_type: str
    validated: bool
    ani: float
    align_fraction_ref: float
    align_fraction_query: float
    ani_threshold: float
    status: str

    def to_list(self):
        return [getattr(self, key) for key in tc_header]

@dataclass
class CCResult:
    """    "cc_result": {
        "completeness": 100.0,
        "contamination": 0.0,
        "strain_heterogeneity": 0.0
    },"""
    completeness: float
    contamination: float
    strain_heterogeneity: float
    ungapped_genome_size: int
    expected_size_min: int
    expected_size_max: int
    expected_size: str
    genome_size_check: str

    def to_list(self):
        return [getattr(self, key) for key in cc_header]

@dataclass
class GTDBResult:
    accession: str
    gtdb_species: str
    ani: float
    align_fraction_ref: float
    align_fraction_query: float
    gtdb_taxonomy: str
    ani_circumscription_radius: float
    mean_intra_species_ani: float
    min_intra_species_ani: float
    mean_intra_species_af: float
    min_intra_species_af: float
    num_clustered_genomes: int
    status: str

    def to_list(self):
        return [getattr(self, key) for key in gtdb_header]

@dataclass
class SourceData:
    organism: str
    strain: str
    subsp: str = ""
    is_type: bool = False
    attrs: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def load_from_ann(ann_file_path: str) -> 'SourceData':

        # read ANN file and extract source feature
        source_dict = {}
        with open(ann_file_path, 'r') as f:
            is_source = False
            for line in f:
                fields = line.strip("\n").split("\t")
                # print(fields)
                # print(len(fields))
                feature = fields[1]
                if feature == "source":
                    is_source = True
                elif is_source and feature != "":
                    break
                if is_source:
                    qualifier, value = fields[3], fields[4]
                    source_dict[qualifier] = value
        
        organism = source_dict.pop('organism', '')
        strain = source_dict.pop('strain', '')
        subsp = source_dict.pop('subsp', '')
        is_type = source_dict.pop('is_type', 'False').lower() == 'true'

        return SourceData(
            organism=organism,
            strain=strain,
            subsp=subsp,
            is_type=is_type,
            attrs=source_dict
        )

def load_dqc_result(file_path: str) -> List[TCResult]:
    with open(file_path, 'r') as file:
        data = json.load(file)
        if "tc_result" in data:
            tc_result_list = [TCResult(**item) for item in data["tc_result"]]
        else:
            tc_result_list = []
        if "cc_result" in data and len(data["cc_result"]) > 0:
            cc_result = CCResult(**data["cc_result"])
        else:
            cc_result = None
    return tc_result_list, cc_result

def load_gtdb_result(file_path: str) -> List[GTDBResult]:
    with open(file_path, 'r') as file:
        data = json.load(file)
        if "gtdb_result" in data:
            gtdb_result_list = [GTDBResult(**item) for item in data["gtdb_result"]]
        else:
            gtdb_result_list = []
    return gtdb_result_list


def read_mss_ann(ann_file_path: str) -> Dict[str, str]:
    # 5-column tab-separated file
    # 2nd column: feature, 4th and 5th: key-value
    D = {}
    with open(ann_file_path, 'r') as f:
        is_source = False
        for line in f:
            fields = line.strip("\n").split("\t")
            # print(fields)
            # print(len(fields))
            feature = fields[1]
            if feature == "source":
                is_source = True
            elif is_source and feature != "":
                return D
            if is_source:
                qualifier, value = fields[3], fields[4]
                D[qualifier] = value
# print(source)
# print(read_mss_ann(ann_file_path))

import re

def remove_extension(filename: str, extensions: Optional[List[str]] = None) -> str:
    # r'(.*?)(?:\.ann|\.annot|\.ann\.tsv|\.annot\.tsv)?$'
    if extensions is None:
        # extensions = ["ann", "annot", "ann.tsv", "annot.tsv"]
        extensions = ["fa", "fas", "fasta", "fna"]
    ext_pat_join = "|".join([("." + ext).replace(".", r"\.") for ext in extensions])
    ext_pat = f"(.*?)(?:{ext_pat_join})?$"
    pattern = re.compile(ext_pat)
    match = pattern.match(filename)
    if match:
        return match.group(1)
    return filename

def get_associated_files(fasta_file: str, out_dir: str, extensions: Optional[List[str]] = None) -> str:
    dir_name = os.path.dirname(fasta_file)
    base_name = os.path.basename(fasta_file)
    prefix = remove_extension(base_name, extensions)
    dqc_result_file = os.path.join(out_dir, prefix, "dqc_result.json")
    ann_file = os.path.join(dir_name, prefix + ".ann")
    return ann_file, dqc_result_file


@dataclass
class DQCResult:
    query: str
    tc_result_list: List[TCResult]|None = None
    cc_result: CCResult|None = None
    gtdb_result: List[GTDBResult]|None = None

    @staticmethod
    def load(query, dqc_result_file) -> 'DQCResult':
        tc_result_list, cc_result = load_dqc_result(dqc_result_file)
        gtdb_result = load_gtdb_result(dqc_result_file)
        return DQCResult(query, tc_result_list, cc_result, gtdb_result)

    def to_list(self, disable_tc=False, disable_cc=False, enable_gtdb=False):
        ret = [self.query]
        if not disable_cc:
            if self.cc_result:
                ret.extend(self.cc_result.to_list())
            else:
                ret.extend(["-"] * len(cc_header))
        if not disable_tc:
            if self.tc_result_list:
                ret.extend(self.tc_result_list[0].to_list())
            else:
                ret.extend(["-"] * len(tc_header))
        if enable_gtdb:
            if self.gtdb_result:
                ret.extend(self.gtdb_result[0].to_list())
        return ret


def collect_dqc_results(fasta_files: List[str], out_dir: str) -> List[DQCResult]:
    dqc_results = []
    for fasta_file in fasta_files:
        query = os.path.basename(fasta_file)
        dqc_result_file = os.path.join(out_dir, query, "dqc_result.json")
        if not os.path.exists(dqc_result_file):
            logger.warning(f"File not found: {dqc_result_file}. The task may have failed. Skipping...")
            continue
        dqc_result = DQCResult.load(query, dqc_result_file)
        dqc_results.append(dqc_result)
    return dqc_results

def save_report(dqc_results: List[DQCResult], output_file: str, disable_tc=False, disable_cc=False, enable_gtdb=False):
    with open(output_file, 'w') as f:
        header = ["query"]
        if not disable_cc:
            header.extend(cc_header)
        if not disable_tc:
            header.extend(tc_header)
        if enable_gtdb:
            gtdb_header_mod =[col_name if col_name.startswith("gtdb_") else "gtdb_" + col_name for col_name in gtdb_header]
            header.extend(gtdb_header_mod)
        f.write("\t".join(header) + "\n")
        for dqc_result in dqc_results:
            f.write("\t".join(map(str, dqc_result.to_list(disable_tc, disable_cc, enable_gtdb))) + "\n")


@dataclass
class DQCResult_MSS:  # For MSS validation
    query: str
    source: SourceData|None = None
    tc_result_list: List[TCResult]|None = None
    cc_result: CCResult|None = None
    best_hit: TCResult|None = None
    declared_species_hit: TCResult|None = None
    status: str = ""
    comments: List[str] = field(default_factory=list)

    @staticmethod
    def load(fasta_file: str, out_dir: str) -> 'DQCResult_MSS':
        ann_file, dqc_result_file = get_associated_files(fasta_file, out_dir)
        source = SourceData.load_from_ann(ann_file)
        tc_result_list, cc_result = load_dqc_result(dqc_result_file)
        return DQCResult_MSS(fasta_file, source, tc_result_list, cc_result)

    def set_best_hit(self):
        if self.tc_result_list:
            self.best_hit = sorted(self.tc_result_list, key=lambda x: -x.ani)[0]
            

    def set_declared_species_hit(self):
        organism = self.source.organism
        declared_species_name = " ".join(organism.split()[:2])
        for tc_result in sorted(self.tc_result_list, key=lambda x: -x.ani):
            if tc_result.organism_name == declared_species_name:
                self.declared_species_hit = tc_result
                break

    def to_tsv(self):
        best_hit_result = [self.best_hit.organism_name, self.best_hit.ani, self.best_hit.status]
        if self.declared_species_hit:
            if self.best_hit.accession == self.declared_species_hit.accession:
                declared_species_result = ["=", "=", "="]
            else:
                declared_species_result = [self.declared_species_hit.organism_name, self.declared_species_hit.ani, self.declared_species_hit.status]
        else:
            declared_species_result = ["-", "-", "-"]
        ret = [self.query, self.source.organism, self.source.strain,
               self.status, ",".join(self.comments)] +\
              best_hit_result + declared_species_result +\
              [self.cc_result.completeness, self.cc_result.contamination]

        return "\t".join(map(str, ret))
        
    def classify(self):
        # best_hitは一番スコアが高かったもの
        # declared_species_hitはアノテーションファイルに書かれている種名に対応するもの
        # それぞれのステータスに応じて、statusとcommentを設定する

        if self.best_hit is None: # ベストヒットが存在しない場合
            self.status = "NO_HIT"
            self.comments.append("possible new species")
        elif self.best_hit and self.declared_species_hit is None:
            # ベストヒットはあるがdeclared_species_hitがない場合
            if self.best_hit.status == "conclusive":
                self.status = "FAIL"
                self.comments.append("mismatch_or_mislabeling")
            elif self.best_hit.status == "inconclusive":
                self.status = "WARNING"
                self.comments.append("mismatch_within_inconclusive_hits, possible_mislabeling")
            elif self.best_hit.status == "indistinguishable":
                self.status = "WARNING"
                self.comments.append("mismatch_within_indistinguishable_species, possible_mislabeling")
            elif self.best_hit.status == "below_threshold":
                self.status = "WARNING"
                self.comments.append("possible new species")
        elif self.best_hit.accession == self.declared_species_hit.accession:
            # ベストヒットとdeclared_species_hitが一致する場合
            if self.best_hit.status == "conclusive":
                self.status = "OK"
                self.comments.append("species_match")
            elif self.best_hit.status == "inconclusive":
                self.status = "OK"
                self.comments.append("inconclusive_species_match")
            elif self.best_hit.status == "indistinguishable":
                self.status = "OK"
                self.comments.append("indistinguishable_species_match")
            elif self.best_hit.status == "below_threshold":
                self.status = "WARNING"
                self.comments.append("species_match_below_threshold, possible outlier or new species")
        elif self.best_hit.accession != self.declared_species_hit.accession:
            # ベストヒットと declared_species_hitが一致しない場合
            if self.best_hit.status == "conclusive":
                self.status = "FAIL"
                self.comments.append("mismatch")
            elif self.best_hit.status == self.declared_species_hit.status == "inconclusive":
                self.status = "WARNING"
                self.comments.append("mismatch_within_inconclusive_hits")
            elif self.best_hit.status == self.declared_species_hit.status == "indistinguishable":
                self.status = "WARNING"
                self.comments.append("mismatch_within_indistinguishable_species")
            elif self.best_hit.status == "below_threshold":
                self.status = "WARNING"
                self.comments.append("possible new species")

# L = ["hoge.ann","hoge.annot","hoge.ann.tsv","hoge.annot.tsv"]
# for a in L:
#     print(remove_suffix(a))

def get_fasta_files(input_dir, fasta_ext):
    fasta_files = []
    for ext in fasta_ext.split(","):
        fasta_files.extend(glob.glob(f"{input_dir}/**/*.{ext}", recursive=True))
    fasta_files = list(set(fasta_files))  # remove redundant
    return fasta_files

if __name__ == '__main__':
    # サンプルのjsonファイルを読み込んでインスタンスリストを作成する例
    # fasta_file = "data/SAMD00772880_K23.fasta"
    # fasta_file = "data/SAMD00772879_K02.fasta"
    # fasta_file = "data/SAMD00754404_JMUB6875.fasta"
    # fasta_file, out_dir = "hok/SAMD999999_LOOC260.fasta", "hokout"
    # fasta_file, out_dir =  "data/SAMD00754404_JMUB6875.fasta", "test_out"
    # fasta_file, out_dir =  "data/SAMD00788766_MK7559.fasta", "test_out"

    # input_dir = "data"
    # out_dir = "test_out"

    # input_dir = "aeruginosa"
    # out_dir = "aeruginosa_out"
    # arg
    # input_dir
    # output_dir
    def parse_arg():
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("input_dir", type=str)
        parser.add_argument("--output_dir", "-O", type=str)
        return parser.parse_args()
    args = parse_arg()
    input_dir = args.input_dir
    out_dir = args.output_dir

    fasta_files = get_fasta_files(input_dir, fasta_ext="fa,fasta")
    # print(fasta_files)

    for fasta_file in fasta_files:
        dqc_result = DQCResult_MSS.load(fasta_file, out_dir)
        dqc_result.set_best_hit()
        dqc_result.set_declared_species_hit()
        dqc_result.classify()
        print(dqc_result.to_tsv())

    # print(DQCResult.load(fasta_file, out_dir))

    # dqc_result = DQCResult.load(fasta_file, out_dir)
    # # print(dqc_result)
    # dqc_result.set_best_hit()
    # dqc_result.set_declared_species_hit()
    # dqc_result.classify()
    # print(dqc_result.to_tsv())
    # print(dqc_result.best_hit)
    # print(dqc_result.declared_species_hit)
    # ann_file, dqc_result_file = get_associated_files(fasta_file, "test_out")
    # # file_path = 'test_out/SAMD00772880_K23/dqc_result.json'
    # # tc_result_list, cc_result = load_dqc_result(file_path)


    # # ann_file_path = "data/SAMD00772880_K23.ann"
    # source = SourceData.load_from_ann(ann_file)
    # print(source)
    # dqc_result = DQCResult(fasta_file)
    # print(dqc_result)
    # print(ann_file, dqc_result_file)
    # tc_result_list, cc_result = load_dqc_result(dqc_result_file)
    # # インスタンスの表示
    # for tc_result in tc_result_list:
    #     print(tc_result)
    # print(cc_result)
