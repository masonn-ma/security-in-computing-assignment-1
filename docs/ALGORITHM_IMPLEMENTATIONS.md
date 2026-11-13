# Algorithm implementations

AES-GCM, ChaCha20-Poly1305, X25519 and finite-field DH use `cryptography`.
FFDH uses RFC 3526 Group 14 and fixed-width 256-byte public values. ML-KEM-768
uses `pqcrypto`'s FIPS 203 implementation. SHA-2 and SHA3 use `hashlib`.
The official `ascon/ascon-c` repository is pinned as the `vendor/ascon-c`
submodule. The Python adapter deliberately does not install the unrelated
PyPI `ascon` package because that package implements the older competition
variant rather than NIST SP 800-232. A thin ctypes build of the vendored
reference implementation is still required before Ascon validation or
benchmarking can run; the CLI reports this as an explicit blocker instead of
silently substituting an obsolete implementation.
