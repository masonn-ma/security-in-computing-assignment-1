import pytest

from crypto_bench.algorithms.ascon_binding import aead_decrypt, aead_encrypt, hash256


def _require_ascon():
    try:
        hash256(b"")
    except RuntimeError as exc:
        pytest.skip(str(exc))


def test_ascon_aead_official_empty_vector():
    _require_ascon()
    key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    nonce = bytes.fromhex("101112131415161718191A1B1C1D1E1F")
    expected = bytes.fromhex("4F9C278211BEC9316BF68F46EE8B2EC6")
    ciphertext = aead_encrypt(key, nonce, b"", b"")
    assert ciphertext == expected
    assert aead_decrypt(key, nonce, b"", ciphertext) == b""


def test_ascon_aead_rejects_modified_tag():
    _require_ascon()
    key = bytes.fromhex("000102030405060708090A0B0C0D0E0F")
    nonce = bytes.fromhex("101112131415161718191A1B1C1D1E1F")
    ciphertext = bytearray(aead_encrypt(key, nonce, b"", b"payload"))
    ciphertext[-1] ^= 1
    with pytest.raises(ValueError, match="authentication"):
        aead_decrypt(key, nonce, b"", bytes(ciphertext))


def test_ascon_hash_official_empty_vector():
    _require_ascon()
    expected = bytes.fromhex(
        "0B3BE5850F2F6B98CAF29F8FDEA89B64"
        "A1FA70AA249B8F839BD53BAA304D92B2"
    )
    assert hash256(b"") == expected
