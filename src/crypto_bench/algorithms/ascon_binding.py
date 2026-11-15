"""ctypes binding for the pinned official Ascon SP 800-232 reference code."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path

_U8 = ctypes.POINTER(ctypes.c_ubyte)
_ULL = ctypes.POINTER(ctypes.c_ulonglong)


def _library_dir() -> Path:
    configured = os.environ.get("ASCON_LIBRARY_DIR")
    if configured:
        return Path(configured)
    return Path(__file__).resolve().parents[3] / "vendor" / "ascon-c" / "build"


def _load(name: str) -> ctypes.CDLL:
    candidates = {
        "aead": ("libascon_aead.so", "libascon_aead.dylib", "ascon_aead.dll"),
        "hash": ("libascon_hash.so", "libascon_hash.dylib", "ascon_hash.dll"),
    }[name]
    directory = _library_dir()
    for candidate in candidates:
        path = directory / candidate
        if path.exists():
            return ctypes.CDLL(str(path))
    raise RuntimeError(
        f"Ascon {name} library not found in {directory}; build the official "
        "vendor/ascon-c reference libraries first"
    )


def _buffer(data: bytes, size: int | None = None):
    return ctypes.create_string_buffer(data, size or max(1, len(data)))


def _pointer(buffer):
    return ctypes.cast(buffer, _U8)


def aead_encrypt(key: bytes, nonce: bytes, associated_data: bytes, plaintext: bytes) -> bytes:
    if len(key) != 16 or len(nonce) != 16:
        raise ValueError("Ascon-AEAD128 requires a 16-byte key and nonce")
    library = _load("aead")
    function = library.crypto_aead_encrypt
    function.argtypes = [_U8, _ULL, _U8, ctypes.c_ulonglong, _U8,
                         ctypes.c_ulonglong, _U8, _U8, _U8]
    function.restype = ctypes.c_int
    output = _buffer(b"\0" * (len(plaintext) + 16))
    plaintext_buffer = _buffer(plaintext)
    associated_data_buffer = _buffer(associated_data)
    nonce_buffer = _buffer(nonce)
    key_buffer = _buffer(key)
    output_length = ctypes.c_ulonglong()
    result = function(
        _pointer(output), ctypes.byref(output_length), _pointer(plaintext_buffer),
        len(plaintext), _pointer(associated_data_buffer), len(associated_data),
        None, _pointer(nonce_buffer), _pointer(key_buffer),
    )
    if result != 0:
        raise RuntimeError(f"Ascon encryption failed with code {result}")
    return output.raw[: output_length.value]


def aead_decrypt(key: bytes, nonce: bytes, associated_data: bytes, ciphertext: bytes) -> bytes:
    if len(key) != 16 or len(nonce) != 16:
        raise ValueError("Ascon-AEAD128 requires a 16-byte key and nonce")
    if len(ciphertext) < 16:
        raise ValueError("Ascon ciphertext must contain a 16-byte tag")
    library = _load("aead")
    function = library.crypto_aead_decrypt
    function.argtypes = [_U8, _ULL, _U8, _U8, ctypes.c_ulonglong, _U8,
                         ctypes.c_ulonglong, _U8, _U8]
    function.restype = ctypes.c_int
    output = _buffer(b"\0" * len(ciphertext))
    ciphertext_buffer = _buffer(ciphertext)
    associated_data_buffer = _buffer(associated_data)
    nonce_buffer = _buffer(nonce)
    key_buffer = _buffer(key)
    output_length = ctypes.c_ulonglong()
    result = function(
        _pointer(output), ctypes.byref(output_length), None,
        _pointer(ciphertext_buffer), len(ciphertext),
        _pointer(associated_data_buffer), len(associated_data),
        _pointer(nonce_buffer), _pointer(key_buffer),
    )
    if result != 0:
        raise ValueError("Ascon authentication failed")
    return output.raw[: output_length.value]


def hash256(message: bytes) -> bytes:
    library = _load("hash")
    function = library.crypto_hash
    function.argtypes = [_U8, _U8, ctypes.c_ulonglong]
    function.restype = ctypes.c_int
    output = _buffer(b"\0" * 32)
    message_buffer = _buffer(message)
    result = function(_pointer(output), _pointer(message_buffer), len(message))
    if result != 0:
        raise RuntimeError(f"Ascon hashing failed with code {result}")
    return output.raw[:32]


def source_revision() -> str | None:
    revision_file = os.environ.get("ASCON_SOURCE_REVISION_FILE")
    if revision_file:
        try:
            return Path(revision_file).read_text(encoding="ascii").strip()
        except OSError:
            return None
    return os.environ.get("ASCON_SOURCE_REVISION")
