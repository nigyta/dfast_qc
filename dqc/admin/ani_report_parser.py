import sys
import dataclasses
from ..common import get_logger

logger = get_logger(__name__)

@dataclasses.dataclass
class ANIreport:

    genbank_accession: str
    refseq_accession: str
    taxid: str
    species_taxid: str
    organism_name: str
    species_name: str
    assembly_name: str
    assembly_type_category: str
    excluded_from_refseq: str
    declared_type_assembly: str
    declared_type_organism_name: str
    declared_type_category: str
    declared_type_ANI: str
    declared_type_qcoverage: str
    declared_type_scoverage: str
    best_match_type_assembly: str
    best_match_species_taxid: str
    best_match_species_name: str
    best_match_type_category: str
    best_match_type_ANI: str
    best_match_type_qcoverage: str
    best_match_type_scoverage: str
    best_match_status: str
    comment: str

    def to_tabular(self):
        return "\t".join([
            self.genbank_accession,
            self.refseq_accession,
            self.taxid,
            self.species_taxid,
            self.organism_name,
            self.species_name,
            self.assembly_name,
            self.assembly_type_category,
            self.excluded_from_refseq,
            self.declared_type_assembly,
            self.declared_type_organism_name,
            self.declared_type_category,
            self.declared_type_ANI,
            self.declared_type_qcoverage,
            self.declared_type_scoverage,
            self.best_match_type_assembly,
            self.best_match_species_taxid,
            self.best_match_species_name,
            self.best_match_type_category,
            self.best_match_type_ANI,
            self.best_match_type_qcoverage,
            self.best_match_type_scoverage,
            self.best_match_status,
            self.comment
            ])

    def validate(self):
        """
        Validate ANI report record
            first return value: is_filtered
            second return value; is_valid
        """
        if self.excluded_from_refseq != "na":
            return False, False  # exclude non-Refseq genomes
        if self.assembly_type_category != "na":  # case of any type
            if self.declared_type_assembly == "no-type":
                logger.warning("%s may have undergone current reclassification, and metadata may have not been updated.\n%s", self.genbank_accession, str(self))  # reclassified but ANI not calculated
                return False, False
            # assert self.declared_type_assembly != "no-type"
            if self.best_match_status == "mismatch":
                if self.comment == "Assembly is the type-strain, mismatch is within genus and expected":
                    return True, True
                elif self.comment == "Assembly is type-strain, failed to match other type-strains on its species":
                    return True, False
                elif self.comment == "na":
                    return False, False
                else:
                    sys.stderr.write("Assertion error: unexpected comment\n")
                    sys.stderr.write(str(self) + "\n")
                    raise AssertionError
            elif self.best_match_status == "na":
                if self.comment == "Assembly is the type-strain, no match is expected":
                    return True, True
                else:
                    sys.stderr.write("Assertion error: unexpected best_match_status\n")
                    sys.stderr.write(str(self) + "\n")
                    raise AssertionError
            else:
                if self.comment == "Assembly is type-strain, failed to match other type-strains on its species":
                    return True, False
                else:
                    return True, True
        else:  # case of non type
            return False, False


def get_filtered_ANI_report(ANI_report_file):
    D = {}
    set_valid = set()
    f = open(ANI_report_file)
    line = next(f)
    assert line.startswith("#")
    for line in f:
        cols = line.strip("\n").split("\t")
        report = ANIreport(*cols)
        is_filtered, is_valid = report.validate()
        if is_filtered:
            if report.genbank_accession in D:
                logger.warning("Redundant ANI record [%s] %s", report.genbank_accession, report)
            D[report.genbank_accession] = report
            if is_valid:
                set_valid.add(report.genbank_accession)
    cnt_filtered = len(D)
    cnt_filtered_valid = len(set_valid)
    logger.info("Parsed ANI report. Number of selected genomes: %d (valid: %d)", cnt_filtered, cnt_filtered_valid)
    return D

# deprecated (keep this for future update.)
def filter_assembly_report(ANI_report_file, out_filtered, out_filtered_invalid):
    fo1 = open(out_filtered, "w")
    fo2 = open(out_filtered_invalid, "w")
    f = open(ANI_report_file)
    line = next(f)
    assert line.startswith("#")
    cnt_filtered, cnt_filtered_valid = 0, 0
    for line in f:
        cols = line.strip("\n").split("\t")
        report = ANIreport(*cols)
        is_filtered, is_valid = report.validate()
        if is_filtered:
            cnt_filtered += 1
            if is_valid:
                cnt_filtered_valid += 1
                fo1.write(report.to_tabular() + "\n")
            else:
                fo2.write(report.to_tabular() + "\n")

    sys.stderr.write(f"Number of selected genomes {cnt_filtered} (valid: {cnt_filtered_valid})\n")

if __name__ == '__main__':
    import sys
    file_name = sys.argv[1]
    out_filtered = sys.argv[2]
    out_filtered_invalid = sys.argv[3]
    filter_assembly_report(file_name, out_filtered, out_filtered_invalid)


