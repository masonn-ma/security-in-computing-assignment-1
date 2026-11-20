# IIoT Cryptography Benchmark

A reproducible Python benchmark comparing cryptographic algorithms for an
academic IIoT study. The benchmark measures execution time, process memory,
and operation-specific output overhead in a constrained Docker environment.

The Danfoss AK-SM / AK-SC systems are case-study context only. These
experiments do not run on Danfoss hardware and do not claim to represent
Danfoss performance.

## Prerequisites

- Windows 11 with WSL2 and Ubuntu
- Docker Desktop using the WSL2 backend
- Git

Clone the repository and its pinned Ascon submodule:

```powershell
git clone --recurse-submodules <repository-url>
cd security-in-computing-assignment-1
```

If the submodule was not downloaded:

```powershell
git submodule sync --recursive
git submodule update --init --recursive
```

## Build the environment

From the repository root:

```powershell
docker compose build
```

The image installs the locked Python dependencies and builds the vendored
Ascon libraries. The Compose service applies the supported benchmark profile:
1 CPU, 512 MiB RAM, and no additional swap.

## Check the setup

Run the environment preflight:

```powershell
docker compose run --rm benchmark python -m crypto_bench preflight
```

Validate all configured algorithms before collecting measurements:

```powershell
docker compose run --rm benchmark python -m crypto_bench validate
```

The validation command should report `OK` for every algorithm. Do not
benchmark an algorithm that fails validation.

## Run a benchmark

Run all categories:

```powershell
docker compose run --rm benchmark python -m crypto_bench run --category all
```

Run one category:

```powershell
docker compose run --rm benchmark python -m crypto_bench run --category symmetric
docker compose run --rm benchmark python -m crypto_bench run --category asymmetric
docker compose run --rm benchmark python -m crypto_bench run --category hashing
```

Restrict a run to one algorithm or payload size:

```powershell
docker compose run --rm benchmark python -m crypto_bench run `
  --category symmetric --algorithm aes-gcm --payload-size 1024
```

Select one operation with `--operation`:

```powershell
# symmetric: encrypt or decrypt
# hashing: digest
# asymmetric: exchange
docker compose run --rm benchmark python -m crypto_bench run `
  --category hashing --algorithm sha256 --operation digest --payload-size 1024
```

Available algorithms are:

| Category | Algorithms |
|---|---|
| Symmetric | `aes-gcm`, `chacha20-poly1305`, `ascon-aead128` |
| Asymmetric | `x25519`, `ffdh-group14`, `ml-kem-768` |
| Hashing | `sha256`, `sha3-256`, `ascon-hash256` |

Use the CLI help for all filters and options:

```powershell
docker compose run --rm benchmark python -m crypto_bench run --help
```

## Analyse and export results

Each completed run creates a directory under `results/` containing:

```text
results/<run-id>/
├── metadata.json
├── raw_measurements.csv
└── summary.xlsx
```

Analyse an existing raw CSV:

```powershell
docker compose run --rm benchmark python -m crypto_bench analyse `
  --input results/<run-id>/raw_measurements.csv
```

Rebuild its Excel workbook:

```powershell
docker compose run --rm benchmark python -m crypto_bench export `
  --input results/<run-id>/raw_measurements.csv
```

An interrupted run is marked `incomplete` in its metadata. Inspect or repeat
incomplete runs before drawing conclusions.

## Documentation

- [Experiment design](docs/EXPERIMENT_DESIGN.md) — measurements and analysis
- [Algorithm implementations](docs/ALGORITHM_IMPLEMENTATIONS.md) — libraries
  and the pinned Ascon implementation
- [Reproducibility](docs/REPRODUCIBILITY.md) — how to reproduce and archive runs

## Troubleshooting

- **Docker is unavailable:** start Docker Desktop and confirm that the WSL2
  backend is enabled.
- **The Ascon submodule or library is missing:** update the submodule, then
  rebuild with `docker compose build`.
- **Preflight reports unexpected limits:** check `compose.yaml` and restart
  Docker Desktop. Use `--allow-unconstrained` only for deliberate diagnostic
  runs; do not combine those results with constrained runs.
- **The container runs out of memory:** run one category, algorithm, or payload
  size at a time instead of changing the benchmark limits.
