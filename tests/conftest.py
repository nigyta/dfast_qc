import sys
import os

# Insert the dfast_qc project root so `import dqc` works
# (the project is not pip-installable).
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')")


@pytest.fixture
def make_tc_result():
    """Factory fixture that builds tc_result hit dicts with sensible defaults."""

    def _make(organism_name="Escherichia coli", **overrides):
        hit = {
            "organism_name": organism_name,
            "strain": "type strain",
            "gcf_id": "GCF_000005845.2",
            "assembly_name": "ASM584v2",
            "ani": 99.98,
            "aligned_fraction": 95.0,
            "ref_aligned_fraction": 94.5,
            "mash_distance": 0.0001,
            "mash_pvalue": 0.0,
            "mash_matching_hashes": "999/1000",
            "taxid": 562,
            "species_taxid": 562,
        }
        hit.update(overrides)
        return [hit]

    return _make
