"""Unit tests for dqc.shigapass_check — no external tools required."""

import gzip
import os

import pytest

from dqc.shigapass_check import (
    should_run_shigapass,
    _needs_db_init,
    _prepare_input,
    parse_summary,
    parse_flex_summary,
    run,
)


# ---------------------------------------------------------------------------
# 1. should_run_shigapass
# ---------------------------------------------------------------------------
class TestShouldRunShigapass:
    # --- requires both: Escherichia/Shigella organism AND indistinguishable status ---

    def test_shigella_indistinguishable(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("Shigella boydii", status="indistinguishable")) is True

    def test_escherichia_indistinguishable(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("Escherichia coli O103:H25", status="indistinguishable")) is True

    def test_uppercase_indistinguishable(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("SHIGELLA BOYDII", status="indistinguishable")) is True

    def test_mixed_case_indistinguishable(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("escherichia Coli", status="indistinguishable")) is True

    # --- organism match alone is not enough (status must be indistinguishable) ---

    def test_shigella_conclusive_rejected(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("Shigella boydii", status="conclusive")) is False

    def test_escherichia_no_status_rejected(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("Escherichia coli")) is False

    def test_escherichia_below_threshold_rejected(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("Escherichia coli", status="below_threshold")) is False

    # --- indistinguishable status alone is not enough (need organism match) ---

    def test_unrelated_organism_indistinguishable(self, make_tc_result):
        assert should_run_shigapass(make_tc_result("Paucilactobacillus hokkaidonensis", status="indistinguishable")) is False

    def test_indistinguishable_without_shigella_escherichia(self):
        tc_result = [
            {"organism_name": "Salmonella enterica", "status": "indistinguishable"},
            {"organism_name": "Klebsiella pneumoniae", "status": "indistinguishable"},
        ]
        assert should_run_shigapass(tc_result) is False

    # --- edge cases ---

    def test_empty_list(self):
        assert should_run_shigapass([]) is False

    def test_none(self):
        assert should_run_shigapass(None) is False

    def test_missing_organism_name_key(self):
        assert should_run_shigapass([{"strain": "x", "status": "indistinguishable"}]) is False

    def test_empty_organism_name(self):
        assert should_run_shigapass([{"organism_name": "", "status": "indistinguishable"}]) is False

    # --- multi-hit: Escherichia/Shigella in a later hit still triggers ---

    def test_indistinguishable_shigella_in_later_hit(self):
        tc_result = [
            {"organism_name": "Salmonella enterica", "status": "indistinguishable"},
            {"organism_name": "Shigella sonnei", "status": "indistinguishable"},
        ]
        assert should_run_shigapass(tc_result) is True

    def test_indistinguishable_escherichia_in_later_hit(self):
        tc_result = [
            {"organism_name": "Salmonella enterica", "status": "indistinguishable"},
            {"organism_name": "Escherichia coli", "status": "indistinguishable"},
        ]
        assert should_run_shigapass(tc_result) is True

    def test_conclusive_does_not_scan_later_hits(self):
        tc_result = [
            {"organism_name": "Salmonella enterica", "status": "conclusive"},
            {"organism_name": "Shigella sonnei", "status": "conclusive"},
        ]
        assert should_run_shigapass(tc_result) is False

    def test_indistinguishable_escherichia_in_first_hit(self):
        tc_result = [
            {"organism_name": "Escherichia coli", "status": "indistinguishable"},
            {"organism_name": "Salmonella enterica", "status": "indistinguishable"},
        ]
        assert should_run_shigapass(tc_result) is True


# ---------------------------------------------------------------------------
# 2. _needs_db_init
# ---------------------------------------------------------------------------
_SHIGAPASS_SUBDIRS = ["IPAH", "RFB", "FLIC", "CRISPR", "MLST"]


class TestNeedsDbInit:
    def _setup_db_dir(self, tmp_path, subdirs_spec):
        """Helper: create subdirs with files according to spec.

        subdirs_spec is a dict mapping subdir name to a list of filenames.
        """
        db_dir = tmp_path / "ShigaPass_DataBases"
        db_dir.mkdir()
        for subdir_name, files in subdirs_spec.items():
            d = db_dir / subdir_name
            d.mkdir()
            for fname in files:
                (d / fname).write_text("")
        return str(db_dir)

    def test_all_indexed_ndb(self, tmp_path, monkeypatch):
        spec = {s: ["seq.fasta", "seq.fasta.ndb"] for s in _SHIGAPASS_SUBDIRS}
        db_dir = self._setup_db_dir(tmp_path, spec)
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_DB_DIR", db_dir)
        assert _needs_db_init() is False

    def test_one_missing_index(self, tmp_path, monkeypatch):
        spec = {s: ["seq.fasta", "seq.fasta.ndb"] for s in _SHIGAPASS_SUBDIRS}
        # CRISPR has fasta but no index
        spec["CRISPR"] = ["seq.fasta"]
        db_dir = self._setup_db_dir(tmp_path, spec)
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_DB_DIR", db_dir)
        assert _needs_db_init() is True

    def test_nhr_counts_as_indexed(self, tmp_path, monkeypatch):
        spec = {s: ["seq.fasta", "seq.fasta.nhr"] for s in _SHIGAPASS_SUBDIRS}
        db_dir = self._setup_db_dir(tmp_path, spec)
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_DB_DIR", db_dir)
        assert _needs_db_init() is False

    def test_empty_subdirs_no_fasta(self, tmp_path, monkeypatch):
        spec = {s: [] for s in _SHIGAPASS_SUBDIRS}
        db_dir = self._setup_db_dir(tmp_path, spec)
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_DB_DIR", db_dir)
        assert _needs_db_init() is False

    def test_no_subdirs(self, tmp_path, monkeypatch):
        db_dir = tmp_path / "ShigaPass_DataBases"
        db_dir.mkdir()
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_DB_DIR", str(db_dir))
        assert _needs_db_init() is False


# ---------------------------------------------------------------------------
# 3. _prepare_input
# ---------------------------------------------------------------------------
class TestPrepareInput:
    def test_plain_fasta(self, tmp_path):
        fasta = tmp_path / "genome.fasta"
        fasta.write_text(">seq1\nACGT\n")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        list_path, temp_path = _prepare_input(str(fasta), str(out_dir))

        assert temp_path is None
        assert os.path.exists(list_path)
        content = open(list_path).read().strip()
        assert content == str(fasta.resolve())

    def test_gzipped_fasta(self, tmp_path):
        fasta_gz = tmp_path / "genome.fasta.gz"
        original = b">seq1\nACGT\n"
        with gzip.open(str(fasta_gz), "wb") as f:
            f.write(original)
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        list_path, temp_path = _prepare_input(str(fasta_gz), str(out_dir))

        assert temp_path is not None
        assert os.path.exists(temp_path)
        assert open(temp_path, "rb").read() == original

        list_content = open(list_path).read().strip()
        assert list_content == temp_path

    def test_gz_filename_stripped(self, tmp_path):
        fasta_gz = tmp_path / "genome.fna.gz"
        with gzip.open(str(fasta_gz), "wb") as f:
            f.write(b">seq\nA\n")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        _, temp_path = _prepare_input(str(fasta_gz), str(out_dir))

        assert os.path.basename(temp_path) == "genome.fna"

    def test_input_list_has_one_line(self, tmp_path):
        fasta = tmp_path / "genome.fasta"
        fasta.write_text(">s\nA\n")
        out_dir = tmp_path / "out"
        out_dir.mkdir()

        list_path, _ = _prepare_input(str(fasta), str(out_dir))
        lines = open(list_path).readlines()
        assert len(lines) == 1


# ---------------------------------------------------------------------------
# 4. parse_summary
# ---------------------------------------------------------------------------
_SUMMARY_HEADER = "Name;rfb;rfb_hits,(%);MLST;fliC;CRISPR;ipaH;Predicted_Serotype;Predicted_FlexSerotype;Comments\n"


class TestParseSummary:
    def test_real_data(self, tmp_path):
        csv_file = tmp_path / "ShigaPass_summary.csv"
        csv_file.write_text(
            _SUMMARY_HEADER
            + "ERR5888634;C2;79,(48.2%);ST145;ShH57(ShH3cplx);A-var2;ipaH+;SB2;;\n"
        )
        result = parse_summary(str(csv_file))
        assert result["name"] == "ERR5888634"
        assert result["rfb"] == "C2"
        assert result["rfb_hits"] == "79,(48.2%)"
        assert result["MLST"] == "ST145"
        assert result["fliC"] == "ShH57(ShH3cplx)"
        assert result["CRISPR"] == "A-var2"
        assert result["ipaH"] == "ipaH+"
        assert result["organism"] == "Shigella boydii"
        assert result["Predicted_Serotype"] == "SB2"
        assert result["Predicted_FlexSerotype"] == ""
        assert result["Comments"] == ""

    def test_key_order(self, tmp_path):
        csv_file = tmp_path / "ShigaPass_summary.csv"
        csv_file.write_text(
            _SUMMARY_HEADER
            + "sample;C2;80;ST1;fliC1;CR1;ipaH+;SF1;;\n"
        )
        result = parse_summary(str(csv_file))
        keys = list(result.keys())
        assert keys.index("ipaH") < keys.index("organism")
        assert keys.index("organism") < keys.index("Predicted_Serotype")

    def test_organism_sb_prefix(self, tmp_path):
        csv_file = tmp_path / "s.csv"
        csv_file.write_text(_SUMMARY_HEADER + "s;;;;;;;;;SB4;;\n")
        # SB4 only has 3 fields before it... let me fix
        csv_file.write_text(_SUMMARY_HEADER + "s;r;h;m;f;c;i;SB4;;\n")
        assert parse_summary(str(csv_file))["organism"] == "Shigella boydii"

    def test_organism_sd_prefix(self, tmp_path):
        csv_file = tmp_path / "s.csv"
        csv_file.write_text(_SUMMARY_HEADER + "s;r;h;m;f;c;i;SD1;;\n")
        assert parse_summary(str(csv_file))["organism"] == "Shigella dysenteriae"

    def test_organism_sf_prefix(self, tmp_path):
        csv_file = tmp_path / "s.csv"
        csv_file.write_text(_SUMMARY_HEADER + "s;r;h;m;f;c;i;SF1-5;;\n")
        assert parse_summary(str(csv_file))["organism"] == "Shigella flexneri"

    def test_organism_ss_prefix(self, tmp_path):
        csv_file = tmp_path / "s.csv"
        csv_file.write_text(_SUMMARY_HEADER + "s;r;h;m;f;c;i;SS;;\n")
        assert parse_summary(str(csv_file))["organism"] == "Shigella sonnei"

    def test_organism_not_shigella(self, tmp_path):
        csv_file = tmp_path / "s.csv"
        csv_file.write_text(_SUMMARY_HEADER + "s;r;h;m;f;c;i;Not Shigella/EIEC;;\n")
        assert parse_summary(str(csv_file))["organism"] == "Escherichia coli"

    def test_organism_empty_serotype(self, tmp_path):
        csv_file = tmp_path / "s.csv"
        csv_file.write_text(_SUMMARY_HEADER + "s;r;h;m;f;c;i;;;\n")
        assert parse_summary(str(csv_file))["organism"] == "Escherichia coli"

    def test_file_not_found(self, tmp_path):
        assert parse_summary(str(tmp_path / "nonexistent.csv")) == {}

    def test_empty_file(self, tmp_path):
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("")
        assert parse_summary(str(csv_file)) == {}

    def test_header_only(self, tmp_path):
        csv_file = tmp_path / "header.csv"
        csv_file.write_text(_SUMMARY_HEADER)
        assert parse_summary(str(csv_file)) == {}

    def test_short_row(self, tmp_path):
        csv_file = tmp_path / "short.csv"
        csv_file.write_text(_SUMMARY_HEADER + "sample;A;B;C;D\n")
        result = parse_summary(str(csv_file))
        assert result["name"] == "sample"
        assert result["rfb"] == "A"
        assert result["rfb_hits"] == "B"
        assert result["MLST"] == "C"
        assert result["fliC"] == "D"
        assert result["CRISPR"] == ""
        assert result["Comments"] == ""
        assert result["organism"] == "Escherichia coli"


# ---------------------------------------------------------------------------
# 5. parse_flex_summary
# ---------------------------------------------------------------------------
class TestParseFlexSummary:
    def test_typical_two_phage_genes(self, tmp_path):
        csv_file = tmp_path / "flex.csv"
        csv_file.write_text("sample1;geneA;geneB;Flex2\n")
        result = parse_flex_summary(str(csv_file))
        assert result["name"] == "sample1"
        assert result["phage_genes"] == ["geneA", "geneB"]
        assert result["flex_serotype"] == "Flex2"

    def test_no_phage_genes(self, tmp_path):
        csv_file = tmp_path / "flex.csv"
        csv_file.write_text("sample1;Flex2\n")
        result = parse_flex_summary(str(csv_file))
        assert result["name"] == "sample1"
        assert result["phage_genes"] == []
        assert result["flex_serotype"] == "Flex2"

    def test_file_not_found(self, tmp_path):
        assert parse_flex_summary(str(tmp_path / "nope.csv")) == {}

    def test_empty_file(self, tmp_path):
        csv_file = tmp_path / "flex.csv"
        csv_file.write_text("")
        assert parse_flex_summary(str(csv_file)) == {}


# ---------------------------------------------------------------------------
# 6. run  — mock-based orchestration
# ---------------------------------------------------------------------------
class TestRun:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path, monkeypatch):
        """Common setup for all run() tests."""
        self.tmp = tmp_path
        self.out_dir = tmp_path / "OUT"
        self.out_dir.mkdir()
        self.sp_out = self.out_dir / "shigapass_output"
        self.sp_out.mkdir()

        # Create a plain input fasta
        self.fasta = tmp_path / "genome.fasta"
        self.fasta.write_text(">s\nACGT\n")

        # Patch config attributes
        monkeypatch.setattr("dqc.shigapass_check.config.QUERY_GENOME", str(self.fasta))
        monkeypatch.setattr("dqc.shigapass_check.config.OUT_DIR", str(self.out_dir))
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_OUTPUT_DIR", "shigapass_output")
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_SCRIPT", "/mock/ShigaPass.sh")
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_DB_DIR", str(tmp_path / "db"))
        monkeypatch.setattr("dqc.shigapass_check.config.NUM_THREADS", 2)
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_SUMMARY", "ShigaPass_summary.csv")
        monkeypatch.setattr("dqc.shigapass_check.config.SHIGAPASS_FLEX_SUMMARY", "ShigaPass_Flex_summary.csv")

        # Default: no db init needed
        monkeypatch.setattr("dqc.shigapass_check._needs_db_init", lambda: False)

        # Capture run_command calls
        self.captured_cmds = []

        def mock_run_command(cmd, **kwargs):
            self.captured_cmds.append(cmd)

        monkeypatch.setattr("dqc.shigapass_check.run_command", mock_run_command)

    def _write_summary(self, content=None):
        if content is None:
            content = _SUMMARY_HEADER + "sample;C2;80;ST1;fliC1;CR1;ipaH+;SB2;;\n"
        (self.sp_out / "ShigaPass_summary.csv").write_text(content)

    def _write_flex_summary(self, content=None):
        if content is None:
            content = "sample;geneX;Flex1\n"
        (self.sp_out / "ShigaPass_Flex_summary.csv").write_text(content)

    def test_basic_flow(self):
        self._write_summary()
        result = run()
        assert result["name"] == "sample"
        assert result["Predicted_Serotype"] == "SB2"
        assert result["organism"] == "Shigella boydii"
        assert len(self.captured_cmds) == 1

    def test_command_structure(self):
        self._write_summary()
        run()
        cmd = self.captured_cmds[0]
        assert cmd[0] == "bash"
        assert cmd[1] == "/mock/ShigaPass.sh"
        assert "-l" in cmd
        assert "-o" in cmd
        assert "-p" in cmd
        assert "-t" in cmd
        t_idx = cmd.index("-t")
        assert cmd[t_idx + 1] == "2"

    def test_db_init_flag_present(self, monkeypatch):
        monkeypatch.setattr("dqc.shigapass_check._needs_db_init", lambda: True)
        self._write_summary()
        run()
        assert "-u" in self.captured_cmds[0]

    def test_no_db_init_flag(self):
        self._write_summary()
        run()
        assert "-u" not in self.captured_cmds[0]

    def test_gzipped_input_cleanup(self, tmp_path, monkeypatch):
        gz_path = tmp_path / "genome.fasta.gz"
        with gzip.open(str(gz_path), "wb") as f:
            f.write(b">s\nACGT\n")
        monkeypatch.setattr("dqc.shigapass_check.config.QUERY_GENOME", str(gz_path))
        self._write_summary()
        run()
        temp_fasta = self.out_dir / "genome.fasta"
        assert not temp_fasta.exists()

    def test_input_list_cleanup(self):
        self._write_summary()
        run()
        input_list = self.out_dir / "shigapass_input_list.txt"
        assert not input_list.exists()

    def test_with_flex_result(self):
        self._write_summary()
        self._write_flex_summary()
        result = run()
        assert "flex_result" in result
        assert result["flex_result"]["flex_serotype"] == "Flex1"

    def test_without_flex_result(self):
        self._write_summary()
        result = run()
        assert "flex_result" not in result
