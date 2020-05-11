import os
class DefaultConfig:
    DEBUG = False
    FORCE = False

    QUERY_GENOME = None
    OUT_DIR = "OUT"
    CHECKM_TAXID = None
    PREFIX = ""  # for debugging use
    NUM_THREADS = 1
    LOG_FILE = "application.log"

    DISABLE_TC = False
    DISABLE_CC = False
    
    DQC_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    
    # Reference data
    DQC_REFERENCE_DIR = os.path.join(DQC_ROOT_DIR, "dqc_reference")
    REFERENCE_GENOME_DIR = "genomes"
    REFERENCE_MARKER_DIR = "markers"
    SQLITE_REFERENCE_DB = "references.db"
    REFERENCE_MARKERS_HMM = "reference_markers.hmm"
    REFERENCE_MARKERS_FASTA = "reference_markers.fasta"
    REFERENCE_SUMMARY_TSV = "reference_summary.tsv"
    ASSEMBLY_REPORT_FILE = "assembly_summary_genbank.txt"
    ANI_REPORT_FILE = "ANI_report_prokaryotes.txt"
    TYPE_STRAIN_REPORT_FILE = "prokaryote_type_strain_report.txt"
    CHECKM_DATA_ROOT = "checkm_data"
    REFERENCE_MARKERS = {
        "TIGR00665": ("dnaB", "replicative DNA helicase"),
        "TIGR00717": ("rpsA", "ribosomal protein bS1"),
        # "TIGR02393": ("rpoD", "RNA polymerase sigma factor RpoD"),
        "TIGR02012": ("recA", "protein RecA"),
        "TIGR01063": ("gyrA", "DNA gyrase, A subunit"),
        "TIGR00468": ("pheS", "phenylalanine--tRNA ligase, alpha subunit"),
        "TIGR00755": ("ksgA", "ribosomal RNA small subunit methyltransferase A"),
    }

    # output file names and options for prepare_marker_fasta
    PRODIGAL_CDS_FASTA = "cds.fna" 
    PRODIGAL_PROTEIN_FASTA = "protein.faa" 
    HMMER_RESULT = "hmmer_result.tsv"
    HMMER_OPTIONS = "-E 1E-5"
    MARKER_SUMMARY_FILE = "marker.summary.tsv"
    QUERY_MARKERS_FASTA = "markers.fasta"

    # output file names and options for select_target_genomes
    BLAST_RESULT = "blast.markers.tsv"
    TARGET_GENOME_LIST = "target_genomes.txt"
    BLAST_OPTIONS = "-outfmt 6 -max_hsps 1 -num_alignments 5"

    # output file names and options for calc_ANI
    FASTANI_RESULT = "fastani_result.tsv"
    TC_RESULT = "tc_result.tsv"

    # output file names and options for completeness check (CheckM)
    CHECKM_INPUT_DIR = "checkm_input"
    CHECKM_RESULT_DIR = "checkm_result"
    CC_RESULT = "cc_result.tsv"

    # DQC result json
    DQC_RESULT_JSON = "dqc_result.json"

    # admin settings
    NCBI_FTP_SERVER = "ftp.ncbi.nlm.nih.gov"
    ETE3_SQLITE_DB = "ete3_taxonomy.db"
    URLS = {
        "asm": "ftp://ftp.ncbi.nlm.nih.gov//genomes/ASSEMBLY_REPORTS/assembly_summary_genbank.txt",
        "ani": "ftp://ftp.ncbi.nlm.nih.gov//genomes/ASSEMBLY_REPORTS/ANI_report_prokaryotes.txt",
        "tsr": "ftp://ftp.ncbi.nlm.nih.gov//genomes/ASSEMBLY_REPORTS/prokaryote_type_strain_report.txt",
        "hmm": "ftp://ftp.tigr.org//pub/data/TIGRFAMs/TIGRFAMs_15.0_HMM.LIB.gz",
        "checkm": "https://data.ace.uq.edu.au/public/CheckM_databases/checkm_data_2015_01_16.tar.gz",
        "taxdump": "https://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz"
    }
    ADMIN = False

class DevelopmentConfig(DefaultConfig):
    DEBUG = False
    FORCE = True
    # LOG_FILE = None

    # Reference data
    DQC_ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
    DQC_REFERENCE_DIR = os.path.join(DQC_ROOT_DIR, "dqc_reference")



DQC_ENV = os.environ.get("DQC_ENV", "default")
configs = {
    "default": DefaultConfig,
    "development": DevelopmentConfig,
}
config = configs[DQC_ENV]
