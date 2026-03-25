"""Integration tests for the dfast_qc pipeline.

These tests run the actual dfast_qc command as a subprocess against real genomes.
They require external tools (mash, skani, checkm, blastn) to be installed and
reference data to be present in dqc_reference/.

Run with:
    python3 -m pytest tests/test_integration.py -v

Slow tests (completeness check) are marked with @pytest.mark.slow and can be
skipped with:
    python3 -m pytest tests/test_integration.py -v -m "not slow"
"""

import json
import os
import subprocess
import shutil

import pytest

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DFAST_QC = os.path.join(PROJECT_ROOT, "dfast_qc")
EXAMPLES_DIR = os.path.join(PROJECT_ROOT, "examples")
SAMPLE_DIR = os.path.join(PROJECT_ROOT, "sample", "dfastqc_test_data")

# Example genomes (non-Shigella)
LACTO_GENOME = os.path.join(EXAMPLES_DIR, "GCA_000829395.1.fna.gz")

# Shigella test genomes
SHIGELLA_SF = os.path.join(SAMPLE_DIR, "GCA_000006925.2.SF.fna")
SHIGELLA_SB = os.path.join(SAMPLE_DIR, "GCA_000012025.1.SB.fna")


def _run_dfast_qc(args, timeout=600):
    """Run dfast_qc with given arguments and return (returncode, stdout, stderr)."""
    cmd = ["python3", DFAST_QC] + args
    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout,
        cwd=PROJECT_ROOT,
    )
    return result.returncode, result.stdout, result.stderr


def _load_result(out_dir):
    """Load dqc_result.json from the given output directory."""
    result_file = os.path.join(out_dir, "dqc_result.json")
    with open(result_file) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def out_dir(tmp_path):
    """Provide a temporary output directory and clean up after the test."""
    d = str(tmp_path / "dqc_out")
    yield d
    if os.path.exists(d):
        shutil.rmtree(d)


# ---------------------------------------------------------------------------
# Precondition checks
# ---------------------------------------------------------------------------
def _tool_available(name):
    """Check if a command-line tool is available."""
    return shutil.which(name) is not None


def _genome_exists(path):
    return os.path.exists(path)


requires_mash = pytest.mark.skipif(not _tool_available("mash"), reason="mash not installed")
requires_skani = pytest.mark.skipif(not _tool_available("skani"), reason="skani not installed")
requires_checkm = pytest.mark.skipif(not _tool_available("checkm"), reason="checkm not installed")
requires_blastn = pytest.mark.skipif(not _tool_available("blastn"), reason="blastn not installed")
requires_pipeline = pytest.mark.usefixtures()  # combined below

requires_lacto = pytest.mark.skipif(
    not _genome_exists(LACTO_GENOME),
    reason=f"Example genome not found: {LACTO_GENOME}",
)
requires_shigella_sf = pytest.mark.skipif(
    not _genome_exists(SHIGELLA_SF),
    reason=f"Shigella SF genome not found: {SHIGELLA_SF}",
)
requires_shigella_sb = pytest.mark.skipif(
    not _genome_exists(SHIGELLA_SB),
    reason=f"Shigella SB genome not found: {SHIGELLA_SB}",
)

pytestmark = [requires_mash, requires_skani]


# ---------------------------------------------------------------------------
# 1. Non-Shigella genome: full pipeline (taxonomy + completeness)
# ---------------------------------------------------------------------------
@requires_lacto
@requires_checkm
@pytest.mark.slow
class TestLactobacillusFullPipeline:
    """Full pipeline run on Paucilactobacillus hokkaidonensis."""

    def test_pipeline_succeeds(self, out_dir):
        rc, stdout, stderr = _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force",
        ])
        assert rc == 0, f"dfast_qc failed:\n{stderr}"
        assert "DFAST_QC completed!" in stdout

    def test_result_json_structure(self, out_dir):
        _run_dfast_qc(["-i", LACTO_GENOME, "-o", out_dir, "--force"])
        result = _load_result(out_dir)

        assert "tc_result" in result
        assert "cc_result" in result
        assert "gtdb_result" in result
        assert "shigapass_result" in result

    def test_taxonomy_check_conclusive(self, out_dir):
        _run_dfast_qc(["-i", LACTO_GENOME, "-o", out_dir, "--force"])
        result = _load_result(out_dir)

        tc = result["tc_result"]
        assert len(tc) > 0
        assert tc[0]["status"] == "conclusive"
        assert "hokkaidonensis" in tc[0]["organism_name"].lower()

    def test_completeness_check_populated(self, out_dir):
        _run_dfast_qc(["-i", LACTO_GENOME, "-o", out_dir, "--force"])
        result = _load_result(out_dir)

        cc = result["cc_result"]
        assert "completeness" in cc
        assert "contamination" in cc
        assert cc["completeness"] > 90.0

    def test_shigapass_not_triggered(self, out_dir):
        _run_dfast_qc(["-i", LACTO_GENOME, "-o", out_dir, "--force"])
        result = _load_result(out_dir)

        assert result["shigapass_result"] == {}


# ---------------------------------------------------------------------------
# 2. Non-Shigella genome: taxonomy check only (faster)
# ---------------------------------------------------------------------------
@requires_lacto
class TestLactobacillusTaxonomyOnly:
    """Taxonomy-only run (--disable_cc) for faster testing."""

    def test_pipeline_succeeds(self, out_dir):
        rc, stdout, stderr = _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force", "--disable_cc",
        ])
        assert rc == 0, f"dfast_qc failed:\n{stderr}"
        assert "DFAST_QC completed!" in stdout

    def test_taxonomy_conclusive(self, out_dir):
        _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)

        tc = result["tc_result"]
        assert len(tc) > 0
        assert tc[0]["status"] == "conclusive"
        assert "hokkaidonensis" in tc[0]["organism_name"].lower()

    def test_completeness_empty_when_disabled(self, out_dir):
        _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)
        assert result["cc_result"] == {}

    def test_shigapass_not_triggered(self, out_dir):
        _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)
        assert result["shigapass_result"] == {}


# ---------------------------------------------------------------------------
# 3. Shigella genome: ShigaPass auto-triggers
# ---------------------------------------------------------------------------
@requires_shigella_sf
@requires_blastn
class TestShigellaFlexneri:
    """Shigella flexneri genome — ShigaPass should auto-trigger."""

    def test_pipeline_succeeds(self, out_dir):
        rc, stdout, stderr = _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force", "--disable_cc",
        ])
        assert rc == 0, f"dfast_qc failed:\n{stderr}"
        assert "DFAST_QC completed!" in stdout

    def test_taxonomy_indistinguishable(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)

        tc = result["tc_result"]
        assert len(tc) > 0
        assert tc[0]["status"] == "indistinguishable"

    def test_shigapass_triggered(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)

        sp = result["shigapass_result"]
        assert sp != {}
        assert sp["ipaH"] == "ipaH+"
        assert sp["Predicted_Serotype"].startswith("SF")
        assert sp["organism"] == "Shigella flexneri"

    def test_shigapass_result_keys(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)
        sp = result["shigapass_result"]

        expected_keys = {"name", "rfb", "rfb_hits", "MLST", "fliC", "CRISPR",
                         "ipaH", "organism", "Predicted_Serotype",
                         "Predicted_FlexSerotype", "Comments"}
        assert expected_keys.issubset(sp.keys())

    def test_flex_result_present(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)
        sp = result["shigapass_result"]

        assert "flex_result" in sp
        flex = sp["flex_result"]
        assert "name" in flex
        assert "phage_genes" in flex
        assert "flex_serotype" in flex


@requires_shigella_sb
@requires_blastn
class TestShigellaBoydii:
    """Shigella boydii genome — ShigaPass should auto-trigger."""

    def test_shigapass_triggered(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SB, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)

        sp = result["shigapass_result"]
        assert sp != {}
        assert sp["ipaH"] == "ipaH+"
        assert sp["Predicted_Serotype"].startswith("SB")
        assert sp["organism"] == "Shigella boydii"

    def test_no_flex_result(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SB, "-o", out_dir, "--force", "--disable_cc",
        ])
        result = _load_result(out_dir)
        sp = result["shigapass_result"]

        # Shigella boydii should NOT have a flex_result
        assert "flex_result" not in sp


# ---------------------------------------------------------------------------
# 4. --disable_shigapass flag
# ---------------------------------------------------------------------------
@requires_shigella_sf
@requires_blastn
class TestDisableShigapass:
    """ShigaPass should be skipped when --disable_shigapass is set."""

    def test_shigapass_skipped(self, out_dir):
        _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force",
            "--disable_cc", "--disable_shigapass",
        ])
        result = _load_result(out_dir)

        assert result["shigapass_result"] == {}

    def test_shigapass_not_mentioned_in_log(self, out_dir):
        rc, stdout, stderr = _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force",
            "--disable_cc", "--disable_shigapass",
        ])
        assert "Start ShigaPass" not in stdout


# ---------------------------------------------------------------------------
# 5. --disable_tc implies no ShigaPass
# ---------------------------------------------------------------------------
@requires_shigella_sf
@requires_checkm
@pytest.mark.slow
class TestDisableTcImpliesNoShigapass:
    """When taxonomy check is disabled, ShigaPass cannot trigger."""

    def test_shigapass_not_triggered(self, out_dir):
        rc, stdout, stderr = _run_dfast_qc([
            "-i", SHIGELLA_SF, "-o", out_dir, "--force",
            "--disable_tc", "--taxid", "0",
        ])
        assert rc == 0, f"dfast_qc failed:\n{stderr}"
        result = _load_result(out_dir)

        assert result["tc_result"] == []
        assert result["shigapass_result"] == {}


# ---------------------------------------------------------------------------
# 6. --force overwrites previous results
# ---------------------------------------------------------------------------
@requires_lacto
class TestForceOverwrite:
    """Running with --force should cleanly overwrite previous output."""

    def test_double_run(self, out_dir):
        _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force", "--disable_cc",
        ])
        result1 = _load_result(out_dir)

        # Run again with --force
        rc, stdout, stderr = _run_dfast_qc([
            "-i", LACTO_GENOME, "-o", out_dir, "--force", "--disable_cc",
        ])
        assert rc == 0
        result2 = _load_result(out_dir)

        assert result1["tc_result"][0]["organism_name"] == result2["tc_result"][0]["organism_name"]
