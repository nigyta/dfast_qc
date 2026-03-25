# ShigaPass Integration into dfast_qc: Requirements Report

## Overview

ShigaPass is an *in silico* tool (v1.5.0, GPLv3 licensed) that predicts *Shigella* serotypes and differentiates between *Shigella*, EIEC (Enteroinvasive *E. coli*), and non-*Shigella*/EIEC. This report describes everything required to integrate it into dfast_qc so that it runs automatically when the taxonomy check classifies a genome as `"indistinguishable"` and any ANI hit matches *Escherichia* or *Shigella*.

---

## 1. System Dependencies

ShigaPass is a Bash script that relies on external command-line tools. Some are standard Unix utilities already present on the system; others must be installed.

| Tool | Required By | Installed? | How to Install |
|------|-------------|------------|----------------|
| **blastn** | All BLAST searches (ipaH, RFB, MLST, fliC, CRISPR) | **No** | `apt-get install ncbi-blast+` or `conda install -c bioconda blast` |
| **makeblastdb** | Database initialization (`-u` flag) | **No** | Included in ncbi-blast+ |
| bash | ShigaPass.sh interpreter | Yes | -- |
| awk | Text processing / profile matching | Yes | -- |
| sed | Stream editing | Yes | -- |
| sort | Result sorting | Yes | -- |
| cut | Column extraction | Yes | -- |
| head | First-line extraction | Yes | -- |
| grep | Pattern matching | Yes | -- |
| paste | Column joining (CRISPR step) | Yes | -- |
| cat | File reading | Yes | -- |
| wc | Line counting (multiple RFB detection) | Yes | -- |

**BLAST+ is the critical missing dependency.** Without it, ShigaPass cannot run. The minimum tested version is 2.12.0.

---

## 2. BLAST Databases

ShigaPass uses pre-built BLAST nucleotide databases stored under `ShigaPass_DataBases/`. Each subdirectory contains `.fasta` source files and their BLAST index files (`.ndb`, `.nhr`, `.nin`, `.njs`, `.not`, `.nsq`, `.ntf`, `.nto`).

| Database | Directory | Purpose |
|----------|-----------|---------|
| ipaH | `IPAH/` | ipaH checkpoint -- determines if isolate is Shigella/EIEC |
| RFB serotypes A-C | `RFB/` | O-antigen gene cluster typing (primary) |
| RFB serogroup D | `RFB/` | Serogroup D detection (secondary) |
| galF_SB1 | `RFB/` | Distinguishes C1 vs C20 |
| taurine_SB6 | `RFB/` | Distinguishes C10 vs C6 |
| POAC genes | `RFB/` | Phage/plasmid O-antigen modification (FlexSerotyping) |
| RFB A16/AprovBEDP | `RFB/` | Distinguishes A2/A3/A16 subtypes |
| MLST (7 genes) | `MLST/` | Multi-locus sequence typing (adk, fumC, gyrB, icd, mdh, purA, recA) |
| ST profiles | `MLST/ST_profiles.txt` | ST lookup table (9,536 profiles) |
| fliC | `FLIC/` | Flagellin gene typing |
| CRISPR spacers | `CRISPR/` | CRISPR-based typing |
| Meta profiles | `ShigaPass_meta_profiles_v5.csv` | Serotype prediction from combined MLST+fliC+CRISPR+RFB |
| RFB hit counts | `RFB_hits_count.csv` | Expected hit counts for coverage calculation |

The databases in the source copy (`ShigaPass/SCRIPT/ShigaPass_DataBases/`) and the bundled copy (`dqc/shigapass/ShigaPass_DataBases/`) are already indexed. The integration code (`shigapass_check.py`) detects missing index files and passes the `-u` flag to trigger `makeblastdb` on first run if needed.

---

## 3. Python Dependencies

No new Python packages are required. The integration module (`dqc/shigapass_check.py`) uses only standard library modules: `os`, `glob`, `gzip`, `shutil`, `csv`. ShigaPass itself runs as an external Bash process invoked via `subprocess` (through the existing `run_command()` utility).

Current Python dependencies in `requirements.txt` remain unchanged:

```
checkm-genome==1.2.2
ete3==3.1.2
more-itertools
peewee
```

---

## 4. Docker Images

Both Dockerfiles (`Dockerfile` and `Dockerfile.dev`) install tools via conda but **do not currently include BLAST+**. The conda install lines need to be updated:

**Current** (both files):
```
conda install -y -c bioconda mash skani gsl==2.6 hmmer prodigal
```

**Required**:
```
conda install -y -c bioconda mash skani gsl==2.6 hmmer prodigal blast
```

The `DockerConfig` class in `config.py` uses `/dqc_reference` for reference data but inherits the ShigaPass paths from `DefaultConfig`, which resolve relative to the `dqc/` package directory. No additional Docker config changes are needed since the databases are bundled inside the package tree.

---

## 5. Test Data

### Existing examples (all Lactobacillus -- will NOT trigger ShigaPass):

| File | Organism |
|------|----------|
| `examples/GCA_000829395.1.fna.gz` | *Paucilactobacillus hokkaidonensis* |
| `examples/GCA_002849935.1.fna.gz` | *Lactobacillus helveticus* |
| `examples/GCA_007989525.1.fna.gz` | *Lactobacillus japonicus* |

### Needed for testing ShigaPass:

| Purpose | Suggested Genome | Expected Result |
|---------|-----------------|-----------------|
| Positive control (Shigella sonnei) | A known *S. sonnei* assembly from NCBI | Serotype predicted (e.g., SS) |
| Positive control (Shigella flexneri) | A known *S. flexneri* assembly | Serotype + FlexSerotype predicted |
| EIEC detection | A known EIEC assembly | ipaH+ but EIEC classification |
| Negative control (non-pathogenic E. coli) | A commensal *E. coli* assembly | ipaH- / "Not Shigella/EIEC" |
| Non-triggering organism | The existing Lactobacillus example | ShigaPass should NOT run |
| `--disable_shigapass` test | Any Shigella genome with the flag | ShigaPass skipped |
| `--disable_tc` test | Any genome with `--disable_tc` | ShigaPass skipped (depends on TC) |

---

## 6. Test Infrastructure

A pytest-based test suite has been added under `tests/`. No external tools (mash, skani, blastn, etc.) are required to run the tests.

### Files

| File | Description |
|------|-------------|
| `tests/__init__.py` | Empty package init |
| `tests/conftest.py` | `sys.path` setup so `import dqc` works; `make_tc_result` factory fixture for building tc_result dicts |
| `tests/test_shigapass_check.py` | 50 unit tests covering all 6 functions in `shigapass_check.py` |

### Running tests

```bash
export PATH="/home/dfast/miniforge3/envs/dfast_qc/bin:$HOME/local/bin:$PATH"
cd dfast_qc
python -m pytest tests/test_shigapass_check.py -v
```

### Test coverage by function

| Function | Tests | Approach |
|----------|-------|----------|
| `should_run_shigapass` | 17 | Pure logic: organism matching, status gating, case variations, edge cases (None, empty, missing keys), multi-hit scanning |
| `_needs_db_init` | 5 | `tmp_path` + `monkeypatch` on config: filesystem setups with/without BLAST index files |
| `_prepare_input` | 4 | `tmp_path`: plain and gzipped fasta handling, filename stripping, list file content |
| `parse_summary` | 12 | `tmp_path`: real CSV data, key renames (`MLST`, `CRISPR`, `Predicted_Serotype`, `Predicted_FlexSerotype`, `Comments`), `organism` derivation from serotype prefix (SB/SD/SF/SS), key ordering, missing/empty/header-only/short-row files |
| `parse_flex_summary` | 4 | `tmp_path`: phage genes parsing, missing/empty files |
| `run` | 8 | Mock-based orchestration: command structure, `-u` flag, temp file cleanup, flex result inclusion |

### Still needed

- Integration tests that run the full pipeline on Shigella and non-Shigella genomes
- Optionally, a GitHub Actions workflow or similar CI configuration

---

## 7. Multi-Genome Runner (`dqc_multi`)

The batch processing script `dqc_multi` constructs `dfast_qc` commands for multiple input genomes. It currently exposes `--disable_tc`, `--disable_cc`, and `--enable_gtdb` but **does not expose `--disable_shigapass`**. Users running batch jobs cannot opt out of ShigaPass per-batch without editing the script.

The fix is to add a `--disable_shigapass` argument to `dqc_multi`'s parser and pass it through to each constructed `dfast_qc` command.

---

## 8. Code Changes Summary

The following changes have already been made to wire ShigaPass into the pipeline:

### New files

| File | Description |
|------|-------------|
| `dqc/shigapass/ShigaPass.sh` | ShigaPass Bash script (copied from source) |
| `dqc/shigapass/ShigaPass_DataBases/` | BLAST databases and profile data (copied from source) |
| `dqc/shigapass_check.py` | Python wrapper module: trigger logic, input prep, execution, output parsing |

### Modified files

| File | Changes |
|------|---------|
| `dqc/config.py` | Added `ENABLE_SHIGAPASS`, `DISABLE_SHIGAPASS`, `SHIGAPASS_SCRIPT`, `SHIGAPASS_DB_DIR`, `SHIGAPASS_OUTPUT_DIR`, `SHIGAPASS_SUMMARY`, `SHIGAPASS_FLEX_SUMMARY` to `DefaultConfig` |
| `dfast_qc` | Added `--disable_shigapass` CLI argument; added auto-trigger logic after taxonomy check; added `shigapass_result` to output JSON |
| `dqc/common.py` | Added ShigaPass summary files and output directory to cleanup lists in `prepare_output_directory()` |
| `mss_validate/read_dqc_result.py` | Added `shigapass_header`, `ShigaPassResult` dataclass, `load_shigapass_result()` function, and `shigapass_result` field to `DQCResult` |
| `dqc/shigapass_check.py` | Updated `should_run_shigapass()` trigger condition: now requires **both** `status == "indistinguishable"` **and** an Escherichia/Shigella organism name in any hit. Extracted `_is_shigapass_genus()` helper. Renamed 5 output keys (`mlst`→`MLST`, `crispr`→`CRISPR`, `predicted_serotype`→`Predicted_Serotype`, `predicted_flex_serotype`→`Predicted_FlexSerotype`, `comments`→`Comments`). Added derived `organism` field based on `Predicted_Serotype` prefix (SB→*S. boydii*, SD→*S. dysenteriae*, SF→*S. flexneri*, SS→*S. sonnei*, else→*E. coli*). See Section 9 for details. |

### New test files

| File | Description |
|------|-------------|
| `tests/__init__.py` | Empty package init |
| `tests/conftest.py` | `sys.path` setup + `make_tc_result` factory fixture |
| `tests/test_shigapass_check.py` | 50 pytest unit tests for all `shigapass_check.py` functions |

### Not yet modified

| File | Required Change |
|------|----------------|
| `Dockerfile` | Add `blast` to conda install |
| `Dockerfile.dev` | Add `blast` to conda install |
| `dqc_multi` | Expose `--disable_shigapass` option |

---

## 9. Pipeline Flow

ShigaPass slots into the existing dfast_qc pipeline as follows:

```
1. Taxonomy Check (ANI-based)
   └── tc_result: list of top hits with organism_name, ANI, etc.
          │
          ▼
2. ShigaPass  [NEW]
   ├── Trigger condition: status is "indistinguishable" AND any hit organism_name
   │   contains "Escherichia" or "Shigella" (case-insensitive)
   ├── Guard conditions: --disable_shigapass NOT set, --disable_tc NOT set
   ├── Steps: ipaH check → RFB typing → MLST → fliC → CRISPR → serotype prediction
   └── shigapass_result: dict with renamed keys (MLST, CRISPR, Predicted_Serotype,
   │   Predicted_FlexSerotype, Comments) and derived organism field
          │
          ▼
3. Completeness Check (CheckM)
   └── cc_result: completeness, contamination, genome size
          │
          ▼
4. GTDB Search (optional)
   └── gtdb_result: GTDB species, ANI
          │
          ▼
5. Write dqc_result.json
   └── Contains: tc_result, shigapass_result, cc_result, gtdb_result
```

---

## 10. Completed Work

- [x] Updated `should_run_shigapass()` trigger logic: requires both `status == "indistinguishable"` and Escherichia/Shigella organism name
- [x] Renamed 5 `shigapass_result` keys to match ShigaPass CSV headers (`MLST`, `CRISPR`, `Predicted_Serotype`, `Predicted_FlexSerotype`, `Comments`)
- [x] Added derived `organism` field to `shigapass_result` (SB→*S. boydii*, SD→*S. dysenteriae*, SF→*S. flexneri*, SS→*S. sonnei*, else→*E. coli*), inserted after `ipaH`
- [x] Set up pytest test framework (`tests/` directory, `conftest.py`, fixtures)
- [x] Wrote 50 unit tests for all 6 functions in `shigapass_check.py` (no external tools required)
- [x] Validated against 5 sample genomes in `sample/dfastqc_test_data/`:
  - 4 Shigella genomes (SB, SD, SF, SS): status `"indistinguishable"` with Escherichia/Shigella hits -- ShigaPass triggers, organism correctly derived
  - 1 E. coli genome (ecoli): status `"conclusive"` -- ShigaPass does NOT trigger

## 11. Remaining Work Checklist

- [ ] Install BLAST+ on the host system (`apt-get install ncbi-blast+` or `conda install blast`)
- [ ] Update `Dockerfile` and `Dockerfile.dev` to include BLAST+ in conda dependencies
- [ ] Add `--disable_shigapass` option to `dqc_multi`
- [ ] Run end-to-end validation on a known Shigella genome and verify JSON output
- [ ] Run with `--disable_shigapass` and confirm it is skipped
- [ ] Run with `--disable_tc` and confirm ShigaPass does not run
- [ ] (Optional) Add integration tests for the full pipeline
- [ ] (Optional) Set up CI/CD for automated testing
