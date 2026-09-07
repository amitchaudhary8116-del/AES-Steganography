"""
encrypt_and_hide.py
--------------------
SENDER SIDE.

Takes a secret text message + a password, encrypts the message with
AES-256, hides the encrypted bytes inside a cover image using LSB
steganography, and saves a new stego image that looks identical to
the original but secretly contains the encrypted message.

Usage (run in VS Code terminal or `python encrypt_and_hide.py`):
    python encrypt_and_hide.py --image cover.png --output stego.png --message "Attack at dawn"

Or run with no arguments and follow the interactive prompts.
"""

import argparse
import getpass
import os

from crypto_utils import encrypt_message
from stego_utils import hide_data, max_capacity_bytes


def run(image_path: str, output_path: str, message: str, password: str):
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Cover image not found: {image_path}")

    print(f"[1/3] Encrypting message with AES-256 ...")
    encrypted_blob = encrypt_message(message, password)
    print(f"      -> {len(encrypted_blob)} bytes of ciphertext (incl. salt/IV)")

    capacity = max_capacity_bytes(image_path)
    print(f"[2/3] Cover image capacity: {capacity} bytes")
    if len(encrypted_blob) > capacity:
        raise ValueError(
            "Message is too large to hide in this image. "
            "Use a larger image or a shorter message."
        )

    print(f"[3/3] Hiding ciphertext inside image via LSB steganography ...")
    hide_data(image_path, encrypted_blob, output_path)

    print(f"\nDone! Stego image saved to: {output_path}")
    print("Send this image file to the receiver, along with the password "
          "(share the password through a separate, secure channel).")


def main():
    parser = argparse.ArgumentParser(
        description="Encrypt a message with AES-256 and hide it inside an image."
    )
    parser.add_argument("--image", help="Path to the cover image (png/jpg/bmp)")
    parser.add_argument("--output", help="Path to save the output stego PNG")
    parser.add_argument("--message", help="Secret message to hide")
    parser.add_argument(
        "--password", help="Password used to derive the AES key (omit to be prompted securely)"
    )
    args = parser.parse_args()

    image_path = args.image or input("Path to cover image: ").strip()
    output_path = args.output or input("Path to save stego image (e.g. stego.png): ").strip()
    message = args.message or input("Secret message to hide: ")
    password = args.password or getpass.getpass("Password (kept secret, not echoed): ")

    run(image_path, output_path, message, password)


if __name__ == "__main__":
    main()
