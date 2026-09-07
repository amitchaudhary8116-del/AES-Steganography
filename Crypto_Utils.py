"""
crypto_utils.py
----------------
Handles AES-256 (CBC mode) encryption and decryption for the
Secure Communication System.

Key derivation: PBKDF2-HMAC-SHA256 (password -> 256-bit key), with a
random salt stored alongside the ciphertext so the receiver can
re-derive the same key from the same password.

Output format produced by encrypt_message():
    salt (16 bytes) + iv (16 bytes) + ciphertext (variable length)

This whole blob is what gets hidden inside the image by stego_utils.py.
"""

import os
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

SALT_SIZE = 16      # bytes
IV_SIZE = 16         # bytes (AES block size)
KEY_SIZE = 32        # 32 bytes = 256-bit key
PBKDF2_ITERATIONS = 200_000


def _derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a password + salt using PBKDF2-HMAC-SHA256."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_message(plaintext: str, password: str) -> bytes:
    """
    Encrypt a plaintext string with AES-256-CBC.

    Returns: salt + iv + ciphertext (all concatenated as raw bytes)
    """
    salt = os.urandom(SALT_SIZE)
    iv = os.urandom(IV_SIZE)
    key = _derive_key(password, salt)

    # PKCS7 padding so plaintext length is a multiple of the AES block size
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()

    return salt + iv + ciphertext


def decrypt_message(blob: bytes, password: str) -> str:
    """
    Reverse of encrypt_message(). Expects blob = salt + iv + ciphertext.
    Raises ValueError if the password is wrong / data is corrupted.
    """
    if len(blob) < SALT_SIZE + IV_SIZE:
        raise ValueError("Encrypted data is too short / corrupted.")

    salt = blob[:SALT_SIZE]
    iv = blob[SALT_SIZE:SALT_SIZE + IV_SIZE]
    ciphertext = blob[SALT_SIZE + IV_SIZE:]

    key = _derive_key(password, salt)

    try:
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        plaintext = unpadder.update(padded_data) + unpadder.finalize()
    except Exception as e:
        raise ValueError(
            "Decryption failed. Wrong password or corrupted/tampered data."
        ) from e

    return plaintext.decode("utf-8")


if __name__ == "__main__":
    # Quick self-test
    msg = "This is a top secret message."
    pwd = "correct-horse-battery-staple"
    blob = encrypt_message(msg, pwd)
    print(f"Encrypted blob length: {len(blob)} bytes")
    recovered = decrypt_message(blob, pwd)
    assert recovered == msg
    print("Self-test passed:", recovered)
