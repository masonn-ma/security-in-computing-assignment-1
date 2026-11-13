# IIoT Cryptography Benchmark

## Project Overview

This repository contains a small, reproducible Python benchmark for a
hypothetical industrial refrigeration IIoT study. It compares cryptographic
algorithms used for protected controller communications, secure-channel
establishment, and firmware-integrity verification. The Danfoss AK-SM / AK-SC
systems are case-study context only: these experiments do not run on Danfoss
hardware and do not claim to represent Danfoss performance.

The benchmark records three primary measurements:

1. Execution time.
2. Process memory usage.
3. Category-specific communication or output overhead in bytes.

Execution-time samples are summarised descriptively and analysed with one-way
ANOVA within a cryptographic category. The project is for academic comparison,
not a production cryptographic library.

## Candidate Algorithms

| Category | CLI identifier | Purpose |
|---|---|---|
| Symmetric encryption | `aes-gcm` | AES-128-GCM authenticated message protection |
| Symmetric encryption | `chacha20-poly1305` | ChaCha20-Poly1305 authenticated message protection |
| Symmetric encryption | `ascon-aead128` | NIST SP 800-232 Ascon-AEAD128 authenticated message protection |
| Asymmetric key establishment | `x25519` | Two-party ephemeral X25519 key agreement |
| Asymmetric key establishment | `ffdh-group14` | RFC 3526 2048-bit finite-field Diffie-Hellman |
| Asymmetric key establishment | `ml-kem-768` | FIPS 203 ML-KEM-768 encapsulation and decapsulation |
| Hashing | `sha256` | SHA-256 firmware-payload digest |
| Hashing | `sha3-256` | SHA3-256 firmware-payload digest |
| Hashing | `ascon-hash256` | NIST SP 800-232 Ascon-Hash256 firmware-payload digest |

Symmetric algorithms evaluate authenticated encryption and decryption.
Asymmetric algorithms evaluate complete key establishment, not bulk message
encryption. Hashing algorithms evaluate digest computation.

## Prerequisites

The supported measurement environment is:

- Windows 11.
- WSL2 with Ubuntu.
- Docker Desktop using the WSL2 backend.
- Git.
- VS Code (recommended, but not required).

Clone the repository with its official Ascon submodule:

```powershell
git clone --recurse-submodules <repository-url>
cd security-in-computing-assignment-1
```

If the submodule is missing or empty:

```powershell
git submodule sync --recursive
git submodule update --init --recursive
```

The submodule is pinned to a commit. Do not replace it with a moving branch or
with the unrelated PyPI `ascon` package.

## Build the Docker Environment

Build the image from the repository root:

```powershell
docker compose build
```

The image installs the pinned Python dependencies, compiles the official
Ascon-AEAD128 and Ascon-Hash256 reference implementations as shared libraries,
and configures the container Git trust rule needed to inspect the mounted
repository.

`compose.yaml` enforces these limits:

| Resource | Limit |
|---|---:|
| CPU | 1.0 CPU equivalent |
| RAM | 512 MiB |
| Additional swap | 0 MiB |

`memswap_limit` equals `mem_limit`, so the container has no additional swap
space.

## Environment Preflight

Run preflight before validation or benchmarking:

```powershell
docker compose run --rm benchmark python -m crypto_bench preflight
```

Preflight reads the available cgroup CPU, memory, and swap limits and compares
them with `configs/default.yaml`. A successful result reports `"ok": true`,
`"cpu_quota": 1.0`, `"memory_bytes": 536870912`, and `"swap_bytes": 0`.
It also reports the Python runtime, platform, and architecture.

If limits are missing or different, correct the Docker Compose configuration
and restart Docker Desktop before collecting data. The supported override is:

```powershell
docker compose run --rm benchmark python -m crypto_bench preflight --allow-unconstrained
```

The same override is available on `run`. It is intended only for deliberate
diagnostic runs; results collected without the intended limits must be labelled
unconstrained and should not be combined with constrained runs.

## Algorithm Validation

Validate all nine configured candidates:

```powershell
docker compose run --rm benchmark python -m crypto_bench validate
```

The `validate` command checks that each candidate can be loaded and performs
basic runtime correctness checks, including:

- Authenticated-encryption/decryption round trips.
- X25519 and finite-field DH shared-secret agreement.
- ML-KEM-768 encapsulation/decapsulation agreement.
- SHA-256 and SHA3-256 digest computation.

Every algorithm should print `OK`. Do not collect benchmark data for an
algorithm that fails validation.

The test suite additionally verifies the official Ascon-AEAD128 and
Ascon-Hash256 empty-message known-answer vectors and verifies rejection of a
modified Ascon authentication tag:

```powershell
docker compose run --rm benchmark python -m pytest -q
```

## Running Experiments

The `run` command always executes serially. It creates a unique run directory,
flushes completed rows to CSV, and writes metadata. The CLI does not expose a
parallel-worker option.

### Command Reference

Global option (must appear before the subcommand):

| Option | Accepted value | Behaviour |
|---|---|---|
| `--config PATH` | YAML path; default `configs/default.yaml` | Load another validated configuration |

`run` options:

| Option | Accepted values | Behaviour |
|---|---|---|
| `--category` | `all`, `symmetric`, `asymmetric`, `hashing`; default `all` | Select one category or all categories |
| `--algorithm` | An enabled algorithm identifier | Restrict the selected category to one candidate |
| `--operation` | `encrypt`, `decrypt`, `digest`, `exchange` | Restrict the operation; operation must match the category |
| `--payload-size` | One configured positive size | Restrict symmetric or hashing data to one payload size |
| `--allow-unconstrained` | Flag | Permit a run when Docker limits do not match the profile |

Asymmetric runs ignore payload sizes because key establishment does not encrypt
a bulk payload. With no filters, the configured algorithms, payload sizes, and
operations are selected. The value `all` is accepted only for `--category`.

### Run all categories

```powershell
docker compose run --rm benchmark python -m crypto_bench run --category all
```

### Run one category

```powershell
docker compose run --rm benchmark python -m crypto_bench run --category symmetric
docker compose run --rm benchmark python -m crypto_bench run --category asymmetric
docker compose run --rm benchmark python -m crypto_bench run --category hashing
```

### Run one algorithm

```powershell
docker compose run --rm benchmark python -m crypto_bench run --category symmetric --algorithm aes-gcm
docker compose run --rm benchmark python -m crypto_bench run --category symmetric --algorithm chacha20-poly1305
docker compose run --rm benchmark python -m crypto_bench run --category symmetric --algorithm ascon-aead128
docker compose run --rm benchmark python -m crypto_bench run --category asymmetric --algorithm x25519
docker compose run --rm benchmark python -m crypto_bench run --category asymmetric --algorithm ffdh-group14
docker compose run --rm benchmark python -m crypto_bench run --category asymmetric --algorithm ml-kem-768
docker compose run --rm benchmark python -m crypto_bench run --category hashing --algorithm sha256
docker compose run --rm benchmark python -m crypto_bench run --category hashing --algorithm sha3-256
docker compose run --rm benchmark python -m crypto_bench run --category hashing --algorithm ascon-hash256
```

### Run one payload size

The configured payload sizes are 64 bytes, 256 bytes, 1 KiB (1024 bytes),
64 KiB (65536 bytes), and 1 MiB (1048576 bytes):

```powershell
docker compose run --rm benchmark python -m crypto_bench run `
  --category symmetric --algorithm aes-gcm --payload-size 1024
```

The same filter applies to hashing. It is not meaningful for asymmetric
key-establishment runs and should not be used there.

### Run one operation

Symmetric encryption and decryption can be selected independently:

```powershell
docker compose run --rm benchmark python -m crypto_bench run `
  --category symmetric --algorithm aes-gcm --operation encrypt

docker compose run --rm benchmark python -m crypto_bench run `
  --category symmetric --algorithm aes-gcm --operation decrypt --payload-size 1024
```

Hash computation uses `digest`:

```powershell
docker compose run --rm benchmark python -m crypto_bench run `
  --category hashing --algorithm sha256 --operation digest --payload-size 1024
```

Asymmetric complete key establishment uses `exchange`:

```powershell
docker compose run --rm benchmark python -m crypto_bench run `
  --category asymmetric --algorithm x25519 --operation exchange
```

Filters can be combined. Invalid algorithm/category combinations, unsupported
operations, and payload sizes not present in the configuration are rejected.

## Experimental Methodology

The default configuration in [configs/default.yaml](configs/default.yaml) uses:

| Setting | Default |
|---|---:|
| Warm-up trials | 5 |
| Measured trials | 30 |
| Payload sizes | 64, 256, 1024, 65536, 1048576 bytes |
| Random data seed | 20250101 |
| ANOVA alpha | 0.05 |
| Pre-run idle period | 30 seconds |

The idle period occurs once before a benchmark session, not before every
operation. The same synthetic payload sizes and seed are used for comparable
conditions. Candidate order is randomised within each trial block, but each
operation still runs one at a time in one worker. There are no parallel
workers, multiprocessing tasks, or concurrent candidate runs.

Each measured observation is written to the raw CSV as it completes. This
serial design reduces contention in the one-CPU, 512 MiB environment and
preserves partial data if the process is interrupted.

## Analysing Results

After a run, analyse its raw measurements:

```powershell
docker compose run --rm benchmark python -m crypto_bench analyse `
  --input results/<run-id>/raw_measurements.csv
```

`<run-id>` is a placeholder for the actual directory name. The command prints
descriptive statistics and ANOVA results. Descriptive statistics are grouped by
category, algorithm, operation, and payload size. ANOVA is performed only
within a category, operation, and payload-size group with at least two
algorithms having sufficient observations. Different cryptographic categories
are never pooled into one test because their operations have different
purposes and scales.

The configured significance level is 0.05. The output includes sample count,
mean, standard deviation, minimum, maximum, and a 95% confidence interval for
descriptive groups, plus the ANOVA F-statistic, p-value, alpha, and significance
flag. The current implementation does not calculate post-hoc comparisons,
despite reserving a workbook sheet for them.

Do not use incomplete runs for final ANOVA conclusions.

## Exporting Results

Create or rebuild the workbook from a raw CSV:

```powershell
docker compose run --rm benchmark python -m crypto_bench export `
  --input results/<run-id>/raw_measurements.csv
```

The workbook is written beside the input CSV as `summary.xlsx`. It contains:

- `Run Metadata`
- `Raw Timings`
- `Memory`
- `Overhead`
- `Descriptive Stats`
- `ANOVA`
- `Post Hoc` (currently an empty placeholder; no post-hoc calculation is implemented)

Open `results/<run-id>/summary.xlsx` in Excel after the export command
completes. A completed `run` creates this workbook automatically; `export` is
useful when rebuilding it from an existing raw CSV.

## Understanding the Results Directory

The output layout is:

```text
results/
└── <run-id>/
    ├── metadata.json
    ├── raw_measurements.csv
    └── summary.xlsx
```

Each run receives a unique ID and its own directory. `metadata.json` records
the configuration, environment limits, dependency versions, Git commit,
Ascon source revision, and whether the Git worktree was dirty. The raw CSV
contains one measured observation per row, including explicit units.

Completed rows remain in the CSV if a process is interrupted. The metadata
status is `complete` for a successful run and `incomplete` when an exception
stops collection. Incomplete runs do not automatically receive a final
analysis and should be inspected or repeated before drawing conclusions.
Categories can be run separately, producing separate run IDs.

## Troubleshooting

### Docker daemon is unavailable

Start Docker Desktop and confirm that the WSL2 backend is enabled, then retry
`docker compose build` or `docker compose run`.

### Preflight reports incorrect or unconstrained limits

Run `docker compose build` and inspect `docker compose.yaml`. It must specify
`cpus: "1.0"`, `mem_limit: 512m`, and `memswap_limit: 512m`. The latter reports
zero additional swap. Do not use `--allow-unconstrained` for normal data
collection.

### The Ascon submodule is missing

Run:

```powershell
git submodule sync --recursive
git submodule update --init --recursive
docker compose build
```

### An Ascon shared library cannot be found

Rebuild the image. The Dockerfile compiles both reference libraries into
`/usr/local/lib`. Do not install the older PyPI `ascon` package as a workaround.

### Algorithm validation fails

Run `docker compose build` again, then rerun `validate`. Check that the
submodule is at the pinned commit and that the failure is not caused by a
missing dependency. Do not benchmark a failing candidate.

### Git reports dubious ownership inside Docker

The image adds only `/workspace` to Git's trusted directories. Rebuild the
image so this setting is installed:

```powershell
docker compose build
docker compose run --rm benchmark git -C /workspace rev-parse HEAD
```

The repository's ownership and permissions are not changed.

### The container runs out of memory

Reduce the selected scope by running one algorithm, category, or payload size
at a time. Do not increase limits and then compare those results with the
constrained profile.

### A benchmark is interrupted

Use the existing run directory's CSV to inspect completed rows. Its metadata
will be marked `incomplete`; start a new run after correcting the cause.

### Excel export fails or a file is missing

Confirm that the input path points to an existing
`raw_measurements.csv` and rerun `export`. The input CSV must have been
produced by this benchmark; fabricated data is not a valid experiment result.

## Reproducibility

To reproduce a run, use the same:

- Git commit and pinned `vendor/ascon-c` submodule revision.
- `requirements.lock.txt` and Python 3.12 Docker image.
- Docker CPU, RAM, and swap limits.
- `configs/default.yaml` or an archived equivalent.
- Random seed and trial counts.
- Recorded dependency versions and Ascon source revision.

The metadata also records `git_worktree_dirty`. A dirty worktree means the
commit SHA alone does not fully identify the tested source, so preserve the
working-tree changes or repeat the run from a clean checkout.

## CLI Help

The parser provides help for the main command and each subcommand:

```powershell
docker compose run --rm benchmark python -m crypto_bench --help
docker compose run --rm benchmark python -m crypto_bench preflight --help
docker compose run --rm benchmark python -m crypto_bench validate --help
docker compose run --rm benchmark python -m crypto_bench run --help
docker compose run --rm benchmark python -m crypto_bench analyse --help
docker compose run --rm benchmark python -m crypto_bench export --help
```

The implementation does not currently provide progress output by category,
algorithm, payload, and trial, chart generation, or post-hoc statistical
comparisons. Those are documentation/feature gaps rather than supported CLI
options.
