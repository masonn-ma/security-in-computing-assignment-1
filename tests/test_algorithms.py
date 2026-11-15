import pytest
from crypto_bench.algorithms.symmetric import SymmetricAdapter
from crypto_bench.algorithms.asymmetric import x25519_exchange, ffdh_exchange

@pytest.mark.parametrize("name", ["aes-gcm", "chacha20-poly1305"])
def test_aead_roundtrip(name):
    a = SymmetricAdapter(name)
    nonce, ciphertext = a.encrypt(b"payload")
    assert a.decrypt(nonce, ciphertext) == b"payload"

def test_key_agreement():
    assert x25519_exchange()[0]
    assert ffdh_exchange()[0]
