import dataclasses
import os
import sys
from ftplib import FTP
from logging import getLogger, StreamHandler, INFO, basicConfig
from concurrent.futures import ThreadPoolExecutor

# num_parallel_workers = 6
# ncbi_ftp_server = "ftp.ncbi.nlm.nih.gov"
# logger = getLogger("")
# logger.setLevel(INFO)
# basicConfig(level=INFO, format='%(asctime)s- %(name)s - %(levelname)s - %(message)s')

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

    @staticmethod
    def parse(asm_report_file):
        f = open(asm_report_file)
        line1 = next(f)
        line2 = next(f)
        assert line1.startswith("#") and line2.startswith("#")
        for line in f:
            cols = line.strip("\n").split("\t")
            asm = Assembly(*cols)
            yield asm

    # def get_fasta(self, out_dir="."):
    #     raise NotImplementedError
        # def _get_ftp_directory(accession):
        #     path1, path2, path3, path4 = accession[0:3], accession[4:7], accession[7:10], accession[10:13]
        #     return "/".join(["/genomes", "all", path1, path2, path3, path4])

        # directory = _get_ftp_directory(self.assembly_accession)
        # ftp = FTP(host=ncbi_ftp_server)
        # logger.info("\tLogging in to the FTP server. {}".format(ncbi_ftp_server + directory))
        # ftp.login()
        # ftp.cwd(directory)
        # L = ftp.nlst()
        # if len(L) == 0:
        #     logger.warning("\tFile not found. Skip retrieving file for {}".format(self.assembly_accession))
        #     return None
        # asm_name = sorted([x for x in L if x.startswith(self.assembly_accession)])[-1]
        # target_file = "/".join([directory, asm_name, asm_name + "_genomic.fna.gz"])
        # logger.info("\tDownloading {}".format(ncbi_ftp_server + directory + "/" + asm_name + "/" + asm_name + "_genomic.fna.gz"))
        # output_file = os.path.join(out_dir, "_".join(asm_name.split("_")[0:2]) + ".fna.gz")
        # with open(output_file, "wb") as f:
        #     ftp.retrbinary("RETR " + target_file, f.write)
        # ftp.quit()
        # return output_file


# def download_genome(asm, out_dir):
#     logger.info("Downloading %s ...", asm.assembly_accession)
#     asm.get_fasta(out_dir)
#     # test_task.sh is a shell script that requires a single argument
#     # cmd = ['/bin/bash', 'p50_vcf_filtration_fat.sh', str(num)]

# def download_all_genomes():
#     out_dir = "reference_genomes/genomes"
#     os.makedirs(out_dir, exist_ok=True)
#     target_reports = get_filtered_ANI_report("ANI_report_prokaryotes.txt")

#     with ThreadPoolExecutor(max_workers=num_parallel_workers, thread_name_prefix="thread") as executor:
#         for asm in Assembly.parse("assembly_summary_refseq.txt"):
#             if asm.assembly_accession in target_reports:

#                 executor.submit(download_genome, asm, out_dir)

#         logger.info("Job submission completed")



