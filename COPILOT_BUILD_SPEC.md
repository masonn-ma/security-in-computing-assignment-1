# IIoT Cryptography Benchmark — Copilot Build Specification

> **Purpose:** Build a small, reproducible Python benchmarking repository for an RMIT cybersecurity assignment. This file is the implementation brief. Read it completely before changing or creating files.
>
> **Development workflow:** The repository will be edited and managed in VS Code. The benchmark itself will run inside a Docker container with fixed resource limits. Do not build a desktop GUI; a clear command-line interface (CLI) and Excel/CSV outputs are sufficient.

## 1. Project context

The study uses a hypothetical evaluation for an industrial refrigeration environment, with Danfoss AK-SM / AK-SC system managers as the case-study context. The report considers three cryptographic use cases:

1. **Symmetric encryption:** Protect temperature readings, alarms, and control commands exchanged between refrigeration controllers and remote management systems.
2. **Asymmetric cryptography:** Establish a secure communication channel between controllers and remote management systems. For the selected algorithms, implement and benchmark the key-establishment operation (key agreement or key encapsulation), not bulk public-key file encryption.
3. **Hashing:** Verify the integrity of firmware update packages before installation.

This is a hypothetical comparative evaluation. Do not claim that Danfoss deploys these exact algorithms, that the experiments run on Danfoss hardware, or that the results represent actual AK-SM / AK-SC performance.

## 2. Project objective

Build a compact benchmarking tool that:

- Implements and validates the nine candidate algorithms listed below.
- Executes comparable operations under a controlled, resource-constrained Docker environment.
- Collects no more than three primary measurements: execution time, process memory usage, and communication / output overhead in bytes.
- Exports raw measurements and summaries to CSV and Excel (`.xlsx`).
- Performs one-way ANOVA on execution-time samples within each cryptographic category, without comparing raw runtimes across different categories.
- Records enough environment metadata to make each run reproducible.

Prioritise correctness, repeatability, transparent methodology, and straightforward output over feature count. Keep the implementation appropriate for a small university assignment, not a production cryptographic product.

## 3. Candidate algorithms — fixed scope

Implement exactly these candidates unless a genuine technical blocker is found. Do not silently replace one with a different algorithm.

### 3.1 Symmetric authenticated encryption

| Candidate | Required operation | Fixed parameters |
|---|---|---|
| AES-GCM | Authenticated encryption and decryption | AES-128-GCM; 12-byte nonce; 16-byte authentication tag |
| ChaCha20-Poly1305 | Authenticated encryption and decryption | Standard ChaCha20-Poly1305; 12-byte nonce; 16-byte tag |
| Ascon-AEAD128 | Authenticated encryption and decryption | NIST SP 800-232 version; 16-byte key, 16-byte nonce, 16-byte tag |

Use AEAD implementations for all three. Do not benchmark bare AES or bare ChaCha20 because the chosen IIoT communication use case needs both confidentiality and integrity/authentication.

### 3.2 Asymmetric key establishment

| Candidate | Required operation | Fixed parameters |
|---|---|---|
| X25519 (ECDH) | Two-party ephemeral key agreement | X25519 standard parameters |
| Finite-field Diffie–Hellman | Two-party key agreement | RFC 3526 MODP Group 14, 2048-bit modulus |
| ML-KEM-768 | Key encapsulation and decapsulation | FIPS 203 ML-KEM-768 parameter set |

Important distinctions:

- X25519 and finite-field DH are key-agreement mechanisms. For one complete exchange, generate an ephemeral key pair for each peer and derive the shared secret at both peers. Verify that both derived secrets match.
- ML-KEM-768 is a key-encapsulation mechanism (KEM), not traditional Diffie–Hellman. For one complete KEM flow, generate the recipient key pair, encapsulate to its public key, and decapsulate at the recipient. Verify that both shared secrets match.
- Measure the complete operation needed to establish the shared secret for each candidate. Also retain phase-level timings (key generation, agreement / encapsulation, decapsulation) where practical, but report the complete exchange as the main asymmetric execution-time result.
- Do not describe these mechanisms as directly encrypting operational messages. The resulting shared secret is intended to support symmetric session-key derivation / secure-channel establishment.

### 3.3 Hashing

| Candidate | Required operation | Output |
|---|---|---|
| SHA-256 | Hash input payload | 32-byte digest |
| SHA3-256 | Hash input payload | 32-byte digest |
| Ascon-Hash256 | Hash input payload | 32-byte digest |

Use `hashlib` for SHA-256 and SHA3-256. Ascon must implement the final NIST SP 800-232 version, not the older Ascon v1.2 / competition-submission variant.

## 4. Experimental design and controls

### 4.1 Main factors and test conditions

- **Comparison groups:** Candidate algorithm within each cryptographic category.
- **Payload-size variable:** Apply to symmetric encryption and hashing, where message size is meaningful.
- **Asymmetric key-establishment tests:** Use each candidate's fixed parameter set and benchmark a complete exchange. Do not invent a bulk payload-size test for key-establishment algorithms; they do not encrypt the firmware or telemetry payload directly.
- Keep the asymmetric parameter sets fixed for the whole experiment. Record the chosen standards / parameter set in run metadata.

Use these configurable default payload sizes for symmetric and hashing tests:

```text
64 bytes
256 bytes
1 KiB (1,024 bytes)
64 KiB (65,536 bytes)
1 MiB (1,048,576 bytes)
```

These are synthetic test sizes spanning small operational messages through a modest firmware-data sample. They are experimental input sizes, not claims about actual Danfoss message or firmware sizes. Store the sizes in a configuration file so they can be changed without editing source code.

Generate synthetic input bytes locally. Use a fixed seed for reproducible test payloads. Never use seeded pseudo-random data to generate cryptographic keys or nonces. Generate keys with the library's secure random source. Every AEAD encryption under a given key must use a unique nonce; never reuse a nonce with the same key. Prepare inputs and nonces outside the timed region unless a measurement explicitly states otherwise.

### 4.2 Repetitions and execution order

Initial defaults:

- Warm-up trials: 5 per candidate / condition.
- Measured trials: 30 per candidate / condition.
- Timing clock: `time.perf_counter_ns()`.
- **Run all benchmark work serially: one measured cryptographic operation at a time, with no parallel candidate execution and no concurrent benchmark workers.**
- Randomise or interleave the *serial* candidate execution order within each condition to reduce ordering, thermal, and background-load bias. For example, execute one trial for each candidate in a shuffled order, then proceed to the next trial round. This is sequential execution, not parallel execution.
- Record each individual measured trial; do not save only averages.

Make warm-up count and measured-trial count configurable. If timing resolution or noise is problematic for very short operations, use a documented batch-timing method that reports average time per operation. A batch must still execute operations sequentially in one worker; do not use concurrency to increase throughput. Do not silently mix single-operation and batch measurements. Record the batch size in the raw data and metadata.

Do not add arbitrary delays between individual operations as a substitute for controlled measurement. Instead, provide a configurable pre-run idle period (for example, 30 seconds) before a benchmark session, and allow the operator to pause between categories or run batches. Record the selected idle / pause settings. If the host is visibly busy, thermally throttling, or running other heavy workloads, advise the user to postpone or repeat the run rather than trying to correct the measurements mathematically.

### 4.3 Controlled environment

The intended measurement environment is the user's Docker Desktop Linux container running through WSL2 with:

- CPU quota: 1.0 CPU
- Memory limit: 512 MiB
- Memory + swap limit: 512 MiB (therefore no additional swap)
- Python: 3.12 series initially; record the exact runtime version

The benchmark must include a **preflight environment check**. On cgroup v2, inspect `/sys/fs/cgroup/cpu.max`, `/sys/fs/cgroup/memory.max`, and `/sys/fs/cgroup/memory.swap.max` when available. Display the detected limits and compare them with the configured profile. If limits are missing or do not match, warn clearly and refuse a normal benchmark run unless the user supplies an explicit override such as `--allow-unconstrained`. Do not assume the limits are active merely because Docker was launched with flags.

Record host/container details that are available: OS, kernel, architecture, Python version, CPU information, Docker resource limits, library versions, run timestamp, random seed, Git commit hash, and benchmark configuration.

**Interpretation limit:** Docker limits available CPU time and memory; it does not emulate the processor architecture or reproduce the physical characteristics of a Danfoss controller. All results must be labelled as measurements from the stated constrained Docker environment, not controller-hardware benchmarks.

### 4.4 Serial execution and host-load control

The constrained container has only one CPU's worth of processing capacity and 512 MiB of memory. The benchmark must therefore be designed for **slow, controlled, one-at-a-time execution**, not maximum throughput:

- Never execute two algorithms, payload conditions, or benchmark runs concurrently.
- Do not use `multiprocessing`, `ProcessPoolExecutor`, `ThreadPoolExecutor`, joblib parallelism, async task fan-out, or other parallel execution for benchmark workloads.
- At most one benchmark worker process may be active at any moment. If an isolated child process is used to measure RSS, run it to completion, collect its result, and terminate it before starting the next condition.
- The CLI must support running a single category, a single algorithm, a single operation, and a single payload size, as well as running a whole category or the full experiment. This allows the user to run and inspect small portions of the experiment independently.
- The full experiment may be started as one command, but it must process all conditions serially and report progress. It must never launch parallel jobs to shorten the run.
- Write / flush each completed trial (or use a clearly documented, very small safe batch) so interruption does not destroy previously collected data. Mark interrupted runs as incomplete.
- Do not run analysis, chart generation, Excel exports, dependency installation, or compilation concurrently with timing measurements. Perform these steps after the measurement run has finished.
- Before a run, show the operator a reminder to close CPU- or memory-intensive applications and avoid running other benchmarks. The user should keep the laptop on the same power mode and connected to AC power for all comparison runs. Record available power / environment information where practical, but do not invent values.
- Use randomized serial trial ordering within each comparison block rather than running all repetitions of one candidate first and then all repetitions of the next. This reduces systematic drift while preserving one-at-a-time execution.
- Do not claim that adding arbitrary sleeps makes results more accurate. Use the pre-run idle period and optional manual pauses between categories / batches to let the host settle when needed.

The goal is repeatability and reduced contention, not artificially slow execution. The CPU quota limits the container to one CPU's worth of time; it does not force the benchmark to consume that full quota continuously.

## 5. Primary measurements (three only)

Do not add throughput, energy use, latency percentiles, CPU temperature, or other metrics as additional primary measurements. Derived descriptive summaries are fine.

### 5.1 Execution time — primary statistical outcome

Store raw nanosecond measurements and human-readable milliseconds.

- **Symmetric:** Measure encryption time and decryption time separately for each payload size. Use valid ciphertext and verify successful decryption outside the timed region when possible. Keep key setup and test-data generation outside the timed encryption / decryption operation. Use a fresh nonce for every encryption.
- **Asymmetric:** Measure the complete shared-secret establishment flow for each candidate. Also store phase-level timings if the implementation can collect them without materially changing the timed operation.
- **Hashing:** Measure digest-computation time for each payload size.

For each trial, verify output correctness, but avoid including unrelated file I/O, logging, Excel writing, random test-data generation, or plot creation inside the timed region.

### 5.2 Memory usage

Measure process resident memory (RSS) during each candidate's workload, preferably in an isolated worker process per candidate / condition. Record:

- Baseline RSS after importing the relevant implementation and before the measured workload.
- Peak RSS observed during the workload.
- Peak-minus-baseline RSS as an approximate incremental figure, if meaningful.

Use a documented method such as `psutil` sampling or an appropriate Linux process high-water mark. State the sampling method and its limitations. RSS includes Python, imported libraries, native libraries, and runtime overhead; it is **not** a precise measurement of algorithm-only memory. Do not use `tracemalloc` as the only measure because it does not account for all native allocations.

### 5.3 Communication / output overhead (bytes)

Report the extra public or output data required by the relevant operation. The exact meaning differs by category; document the counting rule for each one.

- **Symmetric AEAD:** Report nonce bytes + authentication-tag bytes added per message, and total ciphertext length minus plaintext length. Exclude pre-shared key provisioning from per-message overhead. Fix nonce and tag lengths as specified in Section 3.
- **Asymmetric key establishment:** Report the sizes of public values transmitted in one modeled exchange. Count public keys and KEM ciphertexts; exclude private keys and the derived shared secret. Encode finite-field DH public values to the fixed modulus length. Record individual object sizes and total exchange bytes.
  - X25519: count both peers' 32-byte public keys in the modeled two-party exchange.
  - FFDH Group 14: count both peers' public values using fixed-width 256-byte encoding.
  - ML-KEM-768: count the 1,184-byte encapsulation/public key and 1,088-byte KEM ciphertext (2,272 bytes in total for this modeled exchange). Confirm the sizes against the selected implementation and FIPS 203 rather than hard-coding unverified assumptions.
- **Hashing:** Report digest output size. Each selected hash produces a 32-byte digest.

Do not present these three category-specific byte counts as if they were identical protocol designs. Clearly label them as the modeled per-message AEAD expansion, key-establishment exchange data, and digest size respectively. Exclude IP/TCP/TLS framing and application-protocol headers unless a separate, clearly labelled model is added later.

## 6. Implementation fairness and cryptographic correctness

### 6.1 Use maintained, documented implementations

- Use the Python `cryptography` package for AES-GCM, ChaCha20-Poly1305, X25519, and finite-field DH unless a documented compatibility issue requires another established library.
- Use a maintained implementation of FIPS 203 ML-KEM-768. Check the current stable API and package documentation before selecting a package. `pqcrypto` is one candidate; if used, record its exact version and upstream implementation. Do not assume an API from an old tutorial.
- For Ascon, use the official `ascon/ascon-c` repository's **NIST SP 800-232** implementation and a thin, clearly documented Python binding (for example, `ctypes` or `cffi`). Inspect the actual C headers and build instructions before writing the binding. Prefer the portable reference implementation initially and compile it with documented, repeatable compiler flags. Do not use an old Ascon v1.2 package or an unverified implementation.
- Use Python's standard `hashlib` for SHA-256 and SHA3-256.
- Pin exact dependency versions in a lock / requirements file after compatibility testing. Record native compiler and Ascon source revision as well.

### 6.2 Fairness rules

- Use one implementation per algorithm throughout a run; do not silently switch implementations between runs.
- Clearly identify native versus pure-Python implementations. Avoid comparing a pure-Python Ascon implementation with native OpenSSL / compiled implementations as though the implementation-language difference were an algorithm-only difference. Prefer the official compiled Ascon C reference implementation.
- Keep the same input bytes and payload sizes across symmetric candidates and across hashing candidates.
- Use the same warm-up, measured-trial, randomisation, and timing rules for candidates in the same category.
- Fix AEAD key, nonce, tag, and associated-data conventions and record them. Nonces must be unique per encryption under the same key.
- Keep key generation included or excluded consistently within each asymmetric category. The primary asymmetric metric is the full exchange, so include the key-generation steps required by the modeled exchange.
- Never compare absolute timing values between symmetric encryption, asymmetric key establishment, and hashing. Their operations serve different functions.
- Do not claim that measured performance alone determines security. The project measures performance and data-size overhead; security properties and deployment compatibility require separate discussion in the report.

## 7. Data analysis

Use `scipy` for statistical analysis and `pandas` / `openpyxl` for tabular exports.

- Execution time is the primary outcome for inferential statistical testing.
- Use one-way ANOVA to compare candidate algorithms **within each cryptographic category**.
- For symmetric encryption and hashing, run separate comparisons for each payload size; for symmetric encryption, analyse encryption and decryption separately.
- For asymmetric key establishment, compare complete-exchange timing samples across the three fixed candidate parameter sets.
- Use significance level `alpha = 0.05`.
- Report group sample size, mean, standard deviation, median, and 95% confidence interval where practical, plus F-statistic, p-value, and the test conclusion.
- If an ANOVA result is significant, run an appropriate post-hoc comparison (such as Tukey HSD) and report it. Do not perform post-hoc testing when the overall test is not significant.
- Include basic checks / warnings for missing observations and ANOVA assumptions. Do not silently discard outliers. Preserve raw observations so decisions can be reviewed.
- Memory and overhead should primarily be compared descriptively; do not inflate the project with extra hypothesis tests unless explicitly justified.
- Do not pool different payload sizes into one one-way ANOVA. Do not combine timings from different cryptographic categories in the same ANOVA.

## 8. Expected repository structure

Create a clean, modular project similar to the following. Small adjustments are allowed if they improve maintainability, but avoid unnecessary abstraction.

```text
iiot-crypto-benchmark/
├── README.md
├── COPILOT_BUILD_SPEC.md
├── pyproject.toml
├── requirements.lock.txt
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .gitignore
├── configs/
│   └── default.yaml
├── docs/
│   ├── EXPERIMENT_DESIGN.md
│   ├── ALGORITHM_IMPLEMENTATIONS.md
│   └── REPRODUCIBILITY.md
├── src/
│   └── crypto_bench/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── environment.py
│       ├── data_generation.py
│       ├── timing.py
│       ├── memory.py
│       ├── overhead.py
│       ├── statistics.py
│       ├── export.py
│       ├── algorithms/
│       │   ├── __init__.py
│       │   ├── symmetric.py
│       │   ├── asymmetric.py
│       │   ├── hashing.py
│       │   └── ascon_binding.py
│       └── runners/
│           ├── __init__.py
│           ├── symmetric_runner.py
│           ├── asymmetric_runner.py
│           └── hashing_runner.py
├── vendor/
│   └── ascon-c/                 # pinned Git submodule or reproducibly fetched source
├── tests/
│   ├── test_symmetric.py
│   ├── test_asymmetric.py
│   ├── test_hashing.py
│   ├── test_ascon_vectors.py
│   ├── test_measurements.py
│   ├── test_environment.py
│   └── test_exports.py
├── scripts/
│   └── run_experiment.sh
└── results/
    ├── raw/.gitkeep
    └── reports/.gitkeep
```

Generated datasets, raw run output, Excel workbooks, plots, caches, virtual environments, and secrets must be excluded from Git by default. Keep only `.gitkeep` placeholders in result folders. Do not commit benchmark output unless the user explicitly asks.

## 9. Configuration

Place experiment settings in `configs/default.yaml`, not scattered through source files. Include at least:

- Profile name (for example, `docker-constrained-1cpu-512m`).
- Expected CPU, memory, and swap limits.
- Payload sizes in bytes.
- Warm-up and measured-trial counts.
- Random data seed.
- ANOVA alpha.
- Output directory and export format options.
- Algorithm enable/disable list, defaulting to all nine candidates.
- AEAD parameter choices and the DH group identifier.

Validate configuration on startup and display the effective configuration in the run metadata. Reject invalid sizes, zero repetitions, unsupported algorithm names, and duplicate payload-size entries.

## 10. CLI behaviour

Implement a simple, documented CLI. Suggested commands (exact command names may be adjusted consistently):

```bash
# Validate that libraries and algorithm implementations work
python -m crypto_bench validate

# Check Python, Docker/cgroup limits, libraries, and configuration
python -m crypto_bench preflight

# Run all experiments (serially; never in parallel)
python -m crypto_bench run --category all

# Run one category only
python -m crypto_bench run --category symmetric
python -m crypto_bench run --category asymmetric
python -m crypto_bench run --category hashing

# Run one candidate / condition at a time
python -m crypto_bench run --category symmetric --algorithm aes-gcm
python -m crypto_bench run --category hashing --algorithm sha256 --payload-size 1024
python -m crypto_bench run --category symmetric --algorithm chacha20-poly1305 --operation encrypt --payload-size 65536

# Analyse a previous run without repeating it
python -m crypto_bench analyse --input results/raw/<run-id>.csv

# Export or rebuild an Excel workbook from raw data
python -m crypto_bench export --input results/raw/<run-id>.csv
```

Requirements:

- Commands must provide helpful `--help` text.
- Provide filters for category, algorithm, operation, and payload size so the user can run a single candidate / condition or a whole category.
- **All benchmark execution must be serial.** Do not expose a parallel-jobs option; do not add concurrency for candidate execution or repeated trials. At most one benchmark operation / worker may be active at a time.
- A run must receive a unique run ID and persist each completed trial, or use a small documented flush interval, so interrupted runs do not lose everything.
- Support running categories separately and preserve the raw outputs as separate run IDs. The user must be able to inspect one run before starting another.
- At the beginning of a run, print the selected profile, resource limits, selected candidates / conditions, trial counts, and an estimated workload count. Do not promise an exact duration.
- Print progress by category, algorithm, payload size, and trial count.
- Handle unsupported libraries / missing Ascon binary with a clear error; never silently skip an algorithm or substitute a different one.
- Preserve partial raw results if a run fails. Mark the run as incomplete in metadata.
- Do not run analysis automatically on incomplete data unless the user explicitly requests it.
- Support an explicit override for running without the intended Docker resource limits, and clearly mark those results as unconstrained. Normal constrained runs should fail preflight if limits are missing or incorrect.

## 11. Result files and presentation

For every run, create a run-specific directory under `results/`, containing:

- `metadata.json`: run ID, timestamp, Git commit, configuration, environment, dependency versions, Ascon source revision, and completion status.
- `raw_measurements.csv`: one row per measured observation with category, algorithm, operation, payload size (nullable for asymmetric), trial number, timing, memory fields, overhead fields, and batch count if applicable.
- `summary.xlsx`: a workbook with clearly named sheets, at minimum:
  - `Run Metadata`
  - `Raw Timings`
  - `Memory`
  - `Overhead`
  - `Descriptive Stats`
  - `ANOVA`
  - `Post Hoc` (only when applicable)
- `charts/`: report-ready PNG charts, if chart generation is implemented.

Use explicit units in column names, for example `execution_time_ms`, `baseline_rss_mib`, `peak_rss_mib`, `incremental_peak_rss_mib`, `overhead_bytes`, `payload_size_bytes`. Do not mix milliseconds and nanoseconds in a single column. Preserve raw nanoseconds separately if useful.

Charts should make within-category comparisons easy to read:

- Execution time against payload size for symmetric and hashing algorithms.
- Complete key-establishment time for asymmetric candidates.
- Memory usage by candidate.
- Communication / output overhead by candidate.

Do not use decorative dashboards or a web UI. Excel and simple static plots are sufficient.

## 12. Correctness and validation tests

Before collecting performance data, every algorithm must pass correctness tests.

### Symmetric

- Encrypt then decrypt returns the original plaintext for all payload sizes.
- Altered ciphertext or authentication tag is rejected.
- Nonce length, tag length, and ciphertext expansion match the configured parameters.
- The nonce generator never reuses a nonce under the same key during a run.

### Asymmetric

- X25519: both peers derive identical shared secrets.
- FFDH Group 14: both peers derive identical shared secrets; public-value encoding has the expected fixed width.
- ML-KEM-768: encapsulated and decapsulated shared secrets match; key and ciphertext lengths match the selected FIPS 203 implementation.

### Hashing

- SHA-256 and SHA3-256 match Python `hashlib` known-answer outputs.
- Ascon-Hash256 passes known-answer tests from the NIST SP 800-232 implementation / official test vectors.
- Digest outputs are 32 bytes.

### Framework

- Preflight correctly detects the expected cgroup limits and deliberately fails when a limit does not match.
- Warm-up trials are not mixed into measured raw samples.
- CSV and Excel exports preserve units, run identifiers, null asymmetric payload sizes, and all raw observations.
- ANOVA is run only on valid within-category groups with sufficient observations.
- Tests must not generate fake benchmark results that could be mistaken for real experimental data.

## 13. Docker and reproducibility

Create a `Dockerfile` and `compose.yaml` so the experiment can be run consistently from the repository. The container should:

- Use Python 3.12 initially and pin Python package versions.
- Install only required system build tools (for example, `gcc` / `build-essential`, `make`, and `git`) needed for the Ascon C build.
- Build or load the pinned official Ascon C implementation reproducibly.
- Mount the repository into the container and write result files to the mounted `results/` folder.
- Apply the verified resource limits: `cpus: "1.0"`, `mem_limit: 512m`, and `memswap_limit: 512m` (confirm the effective cgroup values inside the running container).
- Avoid running as root for the benchmark process if this can be done without complicating the setup; document any permissions needed for mounted result folders.

Document the exact command to build and start the environment, run preflight, validate algorithms, run the benchmark, and retrieve the generated Excel workbook. Record the actual cgroup values on every benchmark run.

## 14. Documentation requirements

`README.md` should cover:

- Project purpose and non-production / academic scope.
- Candidate algorithms and their use cases.
- Windows + WSL2 + Docker Desktop prerequisites.
- Explicit instructions for running one category / algorithm / payload condition at a time, and confirmation that the benchmark is always serial (no parallel workers).
- Advice to keep the host idle, use consistent AC-power and power-mode conditions, and avoid background workloads during measurements.
- Initial clone steps, including submodule initialisation if Ascon is a Git submodule.
- Docker build / run commands.
- CLI commands for validation, preflight, benchmarking, analysis, and export.
- Where results are saved and how to open the workbook in Excel.
- A clear note that container constraints do not emulate Danfoss hardware.

`docs/EXPERIMENT_DESIGN.md` should explain independent / comparison factors, controlled conditions, payload-size levels, trial counts, the three measurements, and the ANOVA approach in language that can be adapted into the report.

`docs/ALGORITHM_IMPLEMENTATIONS.md` should document the library and exact implementation / version used for each candidate, parameter sizes, Ascon standard revision, known implementation limitations, and any differences in implementation language or native acceleration.

`docs/REPRODUCIBILITY.md` should document how to recreate a run from a Git commit, config file, dependency lock file, Docker image, and metadata.

## 15. Git and Copilot working rules

- Inspect the existing repository and its instructions before making changes. Preserve existing files and conventions unless there is a clear reason to change them.
- Work on a dedicated feature branch; do not make the implementation directly on `main`.
- Implement in small stages and run the relevant tests after each stage.
- Prefer small, descriptive commits. Do not force-push, rewrite shared history, or commit generated results / secrets.
- Add or update `.gitignore` before creating large generated files.
- Do not invent benchmark results, citations, hardware specifications, or claims about Danfoss products.
- Do not silently downgrade standards, use obsolete Ascon variants, or switch cryptographic implementations without documenting the change.
- Ask for user input only when a decision materially changes the research design or cannot be resolved from this specification. Otherwise use a conservative, documented implementation choice.

## 16. Suggested implementation order

Build incrementally in this order:

1. **Repository scaffold:** `pyproject.toml`, source package, config, `.gitignore`, Dockerfile, Compose file, and initial README.
2. **Environment and configuration:** validated configuration loader, cgroup preflight, metadata capture, and CLI skeleton.
3. **Algorithm adapters:** symmetric, asymmetric, hashing, and official Ascon C binding. Keep a small common result interface, but do not force unrelated operations into an inaccurate abstraction.
4. **Correctness validation:** implement unit tests and known-answer / round-trip tests for all nine candidates.
5. **Measurement framework:** timing, memory, overhead, warm-up, repetition, randomized *serial* execution order, one-worker-at-a-time enforcement, per-trial persistence, and raw CSV output.
6. **Analysis and export:** descriptive statistics, within-category ANOVA, conditional post-hoc testing, Excel workbook, and static plots.
7. **End-to-end validation:** build the image, verify cgroup limits, run a small smoke test, then run the full configured experiment.
8. **Documentation and handoff:** complete README and experiment-design docs; provide the exact commands for the user to clone, build, validate, and run the benchmark.

Do not begin with the full benchmark implementation in one large change. Complete each stage, verify it, and keep the repository runnable.

## 17. Definition of done

The project is complete when:

- All nine candidates are implemented using the specified standards and parameters.
- All correctness tests pass.
- The container reports and enforces 1 CPU, 512 MiB memory, and 0 additional swap.
- The preflight command detects incorrect or missing limits.
- The experiment produces raw per-trial data for all configured candidates and conditions.
- Benchmark operations run strictly one at a time; no parallel workers or concurrent benchmark processes are used.
- The CLI supports isolated runs by category, algorithm, operation, and payload size, and preserves completed observations if a run is interrupted.
- The three primary measurements are calculated and documented with clear units and counting rules.
- The analysis performs only valid within-category ANOVA comparisons and reports the relevant statistics.
- An Excel workbook and report-ready charts are generated from actual raw measurements.
- The run metadata is sufficient to identify the software, configuration, environment, and source revision used.
- Documentation explains limitations and does not imply that the Docker container reproduces actual Danfoss hardware.
- No fabricated performance results or generated datasets are committed as if they were experimental findings.

## 18. Technical references to consult

Use the current official documentation and the exact source revisions selected during implementation. Do not rely on outdated blog snippets for cryptographic API behaviour.

- NIST SP 800-232, Ascon-based lightweight cryptography standard (Ascon-AEAD128 and Ascon-Hash256): <https://csrc.nist.gov/pubs/sp/800/232/final>
- Official Ascon C implementations (select the NIST SP 800-232 implementation, not the older v1.2 submission): <https://github.com/ascon/ascon-c>
- Ascon implementations collection and version warning: <https://github.com/ascon/ascon_collection>
- NIST FIPS 203, Module-Lattice-Based Key-Encapsulation Mechanism (ML-KEM): <https://csrc.nist.gov/pubs/fips/203/final>
- Python `cryptography` asymmetric algorithm documentation: <https://cryptography.io/en/latest/hazmat/primitives/asymmetric/>
- `pqcrypto` package documentation, if selected for ML-KEM: <https://pypi.org/project/pqcrypto/>
- Docker resource constraints: <https://docs.docker.com/engine/containers/resource_constraints/>
- RFC 3526, MODP Diffie–Hellman groups (Group 14): <https://www.rfc-editor.org/rfc/rfc3526>

---

**Final instruction to Copilot:** Implement the project described here, not a different or expanded project. Keep the code readable and maintainable for a student who will inspect, explain, and defend it. Prioritise accurate cryptographic operations, fair measurements, reproducibility, and transparent limitations over extra features.