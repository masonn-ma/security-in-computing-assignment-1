# IIoT Cryptography Benchmark

Academic, serial benchmark for AES-GCM, ChaCha20-Poly1305, Ascon-AEAD128,
X25519, FFDH Group 14, ML-KEM-768, SHA-256, SHA3-256 and Ascon-Hash256.
It is not a production library and does not represent Danfoss controller
performance.

On Windows install Docker Desktop with WSL2:

```powershell
git clone --recurse-submodules <repository-url>
cd security-in-computing-assignment-1
docker compose build
docker compose run --rm benchmark python -m crypto_bench preflight
docker compose run --rm benchmark python -m crypto_bench validate
docker compose run --rm benchmark python -m crypto_bench run --category symmetric
```

Use `--allow-unconstrained` only deliberately. Results are flushed per trial
to `results/<run-id>/` and interrupted runs remain incomplete. The benchmark
never uses parallel workers. Keep the host idle, on consistent AC power and
power mode. Ascon requires an explicitly installed final NIST SP 800-232
binding from the pinned `vendor/ascon-c` submodule; the current adapter reports
an explicit build blocker until that ctypes binding is compiled. It refuses to
substitute obsolete Ascon v1.2 code. The other seven candidates can be
validated independently while the binding is completed.
