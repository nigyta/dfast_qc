import os
class DefaultConfig:
    DEBUG = False
    FORCE = False

    QUERY_GENOME = None
    OUT_DIR = "OUT"
    LOG_FILE = "application.log"
    PREFIX = ""

    DQC_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    
    # Reference data
    DQC_REFERENCE_DIR = os.path.join(DQC_ROOT_DIR, "dqc_reference")
    REFERENCE_GENOME_DIR = os.path.join(DQC_REFERENCE_DIR, "genomes")
    REFERENCE_MARKER_DIR = os.path.join(DQC_REFERENCE_DIR, "markers")
    SQLITE_REFERENCE_DB = os.path.join(DQC_REFERENCE_DIR, "references.db")
    REFERENCE_MARKERS_HMM = os.path.join(DQC_REFERENCE_DIR, "reference_markers.hmm")
    REFERENCE_MARKERS_FASTA = os.path.join(DQC_REFERENCE_DIR, "reference_markers.fasta")
    REFERENCE_SUMMARY_TSV = os.path.join(DQC_REFERENCE_DIR, "reference_summary.tsv")
    ASSEMBLY_REPORT_FILE = os.path.join(DQC_REFERENCE_DIR, "assembly_summary_genbank.txt") 
    ANI_REPORT_FILE = os.path.join(DQC_REFERENCE_DIR, "ANI_report_prokaryotes.txt") 
    TYPE_STRAIN_REPORT_FILE = os.path.join(DQC_REFERENCE_DIR, "prokaryote_type_strain_report.txt") 
    REFERENCE_MARKERS = {
        "TIGR00665": ("dnaB", "replicative DNA helicase"),
        "TIGR00717": ("rpsA", "ribosomal protein bS1"),
        "TIGR02393": ("rpoD", "RNA polymerase sigma factor RpoD"),
        "TIGR02012": ("recA", "protein RecA"),
        "TIGR01063": ("gyrA", "DNA gyrase, A subunit")
    }

    # output file names and options for prepare_marker_fasta
    PRODIGAL_CDS_FASTA = "cds.fna" 
    PRODIGAL_PROTEIN_FASTA = "protein.faa" 
    HMMER_RESULT = "hmmer_result.tsv"
    HMMER_OPTIONS = "-E 1E-5"
    MARKER_SUMMARY_FILE = "marker.summary.tsv"
    QUERY_MARKERS_FASTA = "query_markers.fasta"

    # output file names and options for select_target_genomes
    BLAST_RESULT = "blast.markers.tsv"
    TARGET_GENOME_LIST = "target_genomes.txt"
    BLAST_OPTIONS = "-outfmt 6 -max_hsps 1 -num_alignments 5"

    # output file names and options for calc_ANI
    FASTANI_THREADS = 2
    FASTANI_RESULT = "fastani_result.tsv"
    DQC_RESULT = "tc_result.tsv"
    DQC_RESULT_JSON = "tc_result.json"

    # admin settings
    NCBI_FTP_SERVER = "ftp.ncbi.nlm.nih.gov"
    URLS = {
        "asm": "ftp://ftp.ncbi.nlm.nih.gov//genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt",
        "ani": "ftp://ftp.ncbi.nlm.nih.gov//genomes/ASSEMBLY_REPORTS/ANI_report_prokaryotes.txt",
        "tsr": "ftp://ftp.ncbi.nlm.nih.gov//genomes/ASSEMBLY_REPORTS/prokaryote_type_strain_report.txt",
        "hmm": "ftp://ftp.tigr.org//pub/data/TIGRFAMs/TIGRFAMs_15.0_HMM.LIB.gz",
    }
    ADMIN = False

class DevelopmentConfig(DefaultConfig):
    DEBUG = True
    FORCE = True
    # LOG_FILE = None

    DQC_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))

    # Reference data
    DQC_REFERENCE_DIR = os.path.join(DQC_ROOT_DIR, "dqc_reference_dev")
    REFERENCE_GENOME_DIR = os.path.join(DQC_REFERENCE_DIR, "genomes")
    REFERENCE_MARKER_DIR = os.path.join(DQC_REFERENCE_DIR, "markers")
    SQLITE_REFERENCE_DB = os.path.join(DQC_REFERENCE_DIR, "references.db")
    REFERENCE_MARKERS_HMM = os.path.join(DQC_REFERENCE_DIR, "reference_markers.hmm")
    REFERENCE_MARKERS_FASTA = os.path.join(DQC_REFERENCE_DIR, "reference_markers.fasta")
    REFERENCE_SUMMARY_TSV = os.path.join(DQC_REFERENCE_DIR, "reference_summary.tsv")
    ASSEMBLY_REPORT_FILE = os.path.join(DQC_REFERENCE_DIR, "assembly_summary_genbank.txt") 
    ANI_REPORT_FILE = os.path.join(DQC_REFERENCE_DIR, "ANI_report_prokaryotes.txt") 
    TYPE_STRAIN_REPORT_FILE = os.path.join(DQC_REFERENCE_DIR, "prokaryote_type_strain_report.txt") 


DQC_ENV = os.environ.get("DQC_ENV", "default")

configs = {
    "default": DefaultConfig,
    "development": DevelopmentConfig,
}

config = configs[DQC_ENV]
