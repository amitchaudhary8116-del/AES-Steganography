"""
decrypt_and_reveal.py
-----------------------
RECEIVER SIDE.

Takes a stego image (produced by encrypt_and_hide.py) + the shared
password, extracts the hidden AES-encrypted bytes from the image,
and decrypts them back into the original secret message.

Usage:
    python decrypt_and_reveal.py --image stego.png

Or run with no arguments and follow the interactive prompts.
"""

import argparse
import getpass
import os

from crypto_utils import decrypt_message
from stego_utils import extract_data


def run(image_path: str, password: str) -> str:
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Stego image not found: {image_path}")

    print("[1/2] Extracting hidden data from image ...")
    encrypted_blob = extract_data(image_path)
    print(f"      -> extracted {len(encrypted_blob)} bytes")

    print("[2/2] Decrypting with AES-256 ...")
    message = decrypt_message(encrypted_blob, password)

    return message


def main():
    parser = argparse.ArgumentParser(
        description="Extract and decrypt a hidden message from a stego image."
    )
    parser.add_argument("--image", help="Path to the stego image")
    parser.add_argument(
        "--password", help="Password used to derive the AES key (omit to be prompted securely)"
    )
    args = parser.parse_args()

    image_path = args.image or input("Path to stego image: ").strip()
    password = args.password or getpass.getpass("Password (kept secret, not echoed): ")

    try:
        message = run(image_path, password)
    except ValueError as e:
        print(f"\nFailed: {e}")
        return

    print("\n--- Recovered secret message ---")
    print(message)
    print("---------------------------------")


if __name__ == "__main__":
    main()
