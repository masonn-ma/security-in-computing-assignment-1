import hashlib
from .ascon_binding import hash256

def digest(name, data):
    if name == "sha256": return hashlib.sha256(data).digest()
    if name == "sha3-256": return hashlib.sha3_256(data).digest()
    if name == "ascon-hash256": return hash256(data)
    raise ValueError(f"unknown hash algorithm: {name}")
