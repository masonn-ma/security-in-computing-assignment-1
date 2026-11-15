import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from .ascon_binding import aead_decrypt, aead_encrypt

class SymmetricAdapter:
    def __init__(self, name):
        self.name = name
        self.key = os.urandom(16 if name == "aes-gcm" else 32 if name == "chacha20-poly1305" else 16)
        self.nonce_size = 16 if name == "ascon-aead128" else 12
        self._nonces = set()
    def encrypt(self, plaintext, nonce=None):
        nonce = nonce or os.urandom(self.nonce_size)
        if len(nonce) != self.nonce_size or nonce in self._nonces:
            raise ValueError("nonce must have the configured length and be unique for this key")
        self._nonces.add(nonce)
        if self.name == "aes-gcm": out = AESGCM(self.key).encrypt(nonce, plaintext, None)
        elif self.name == "chacha20-poly1305": out = ChaCha20Poly1305(self.key).encrypt(nonce, plaintext, None)
        else: out = aead_encrypt(self.key, nonce, b"", plaintext)
        return nonce, out
    def decrypt(self, nonce, ciphertext):
        if self.name == "aes-gcm": return AESGCM(self.key).decrypt(nonce, ciphertext, None)
        if self.name == "chacha20-poly1305": return ChaCha20Poly1305(self.key).decrypt(nonce, ciphertext, None)
        return aead_decrypt(self.key, nonce, b"", ciphertext)
