import hashlib
from .ascon_binding import unavailable

def digest(name, data):
    if name == "sha256": return hashlib.sha256(data).digest()
    if name == "sha3-256": return hashlib.sha3_256(data).digest()
    unavailable()
