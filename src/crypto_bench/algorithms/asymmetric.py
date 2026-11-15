from cryptography.hazmat.primitives.asymmetric import x25519, dh
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

GROUP14_P = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
 "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
 "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
 "E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED"
 "EE386BFB5A899FA5AE9F24117C4B1FE649286651ECE65381"
 "FFFFFFFFFFFFFFFF", 16)

def x25519_exchange():
    a, b = x25519.X25519PrivateKey.generate(), x25519.X25519PrivateKey.generate()
    sa, sb = a.exchange(b.public_key()), b.exchange(a.public_key())
    return sa, {"public_bytes": 64, "public_a": a.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw), "public_b": b.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)}

def ffdh_exchange():
    params = dh.DHParameterNumbers(GROUP14_P, 2).parameters()
    a, b = params.generate_private_key(), params.generate_private_key()
    sa, sb = a.exchange(b.public_key()), b.exchange(a.public_key())
    width = (GROUP14_P.bit_length() + 7) // 8
    return sa, {"public_bytes": width * 2, "public_a": a.public_key().public_numbers().y.to_bytes(width, "big"), "public_b": b.public_key().public_numbers().y.to_bytes(width, "big")}

def ml_kem_exchange():
    try:
        from pqcrypto.kem.ml_kem_768 import generate_keypair, encrypt, decrypt
    except ImportError as e:
        raise RuntimeError("pqcrypto with ML-KEM-768 is required") from e
    public, secret = generate_keypair()
    ciphertext, shared = encrypt(public)
    recovered = decrypt(secret, ciphertext)
    return shared, {"public_bytes": len(public) + len(ciphertext), "ciphertext_bytes": len(ciphertext), "public_key_bytes": len(public), "matches": shared == recovered}
