# Algorithm implementations

AES-GCM, ChaCha20-Poly1305, X25519 and finite-field DH use `cryptography`.
FFDH uses RFC 3526 Group 14 and fixed-width 256-byte public values. ML-KEM-768
uses `pqcrypto`'s FIPS 203 implementation. SHA-2 and SHA3 use `hashlib`.
The official `ascon/ascon-c` repository is pinned as the `vendor/ascon-c`
submodule. The Python adapter deliberately does not install the unrelated
PyPI `ascon` package because that package implements the older competition
variant rather than NIST SP 800-232. On the documented x86-64 benchmark
target, the Dockerfile compiles the vendored `opt64` implementations into
shared libraries using the vendored project's release flags
(`-std=c99 -O2 -fomit-frame-pointer -march=native -mtune=native`), and the
adapter calls their documented C APIs with ctypes. Benchmark metadata records
the Ascon source revision, compiler, and build flags.
The library handles and function prototypes are cached so repeated
measurements time the operation instead of repeated dynamic-loader setup.
Missing libraries produce an explicit error instead of silently substituting
an obsolete implementation.
